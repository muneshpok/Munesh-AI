"""Smart Follow-Up Sequences — Multi-step drip campaigns that nurture leads with varied angles.

Replaces the single generic follow-up with a 5-step sequence:
  Step 1 (Day 1): Value-first — share what Munesh AI does for their specific situation
  Step 2 (Day 2): Social proof — share results other businesses have seen
  Step 3 (Day 4): Case study — concrete example of success
  Step 4 (Day 7): Limited offer — urgency with a time-bound incentive
  Step 5 (Day 14): Final touch — low-pressure re-engagement
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Lead, LeadStatus, Message, FollowUp, AutomationLog
from app.services.whatsapp import whatsapp_service
from app.services.memory import memory_service
from app.core.logging import logger


# --- Sequence Definitions ---

FOLLOW_UP_SEQUENCES = {
    "new_lead": [
        {
            "step": 1,
            "delay_hours": 0,
            "angle": "value",
            "template": (
                "Hi{name}! Thanks for reaching out to Munesh AI. "
                "We help businesses like yours automate WhatsApp conversations with AI — "
                "so you never miss a lead, even at 2 AM. "
                "What's the biggest challenge you're facing with customer communication right now?"
            ),
        },
        {
            "step": 2,
            "delay_hours": 24,
            "angle": "social_proof",
            "template": (
                "Hi{name}, quick update — businesses using Munesh AI are seeing "
                "3x more demo bookings and 40% faster response times on WhatsApp. "
                "Would you like to see how it could work for your business?"
            ),
        },
        {
            "step": 3,
            "delay_hours": 96,
            "angle": "case_study",
            "template": (
                "Hey{name}! Wanted to share a quick win — one of our clients "
                "went from 5 manual WhatsApp conversations/day to handling 50+ automatically, "
                "and their demo booking rate jumped 60%. "
                "Their secret? Our AI Sales Agent that learns and improves with every conversation. "
                "Want me to set up a free 15-minute demo to show you the same setup?"
            ),
        },
        {
            "step": 4,
            "delay_hours": 168,
            "angle": "limited_offer",
            "template": (
                "Hi{name}! Just a heads up — we're offering an extended 30-day free trial "
                "this week (normally 14 days) for new businesses. "
                "It includes all 4 AI agents, unlimited messages, and our self-improvement AI "
                "that optimizes your responses automatically. "
                "Want me to activate it for you? No credit card needed."
            ),
        },
        {
            "step": 5,
            "delay_hours": 336,
            "angle": "final_touch",
            "template": (
                "Hey{name}, just checking in one last time. "
                "If automating your WhatsApp conversations isn't a priority right now, "
                "no worries at all! But if anything changes, I'm here to help. "
                "You can always reach out and we'll get you set up in under 10 minutes."
            ),
        },
    ],
    "contacted_stale": [
        {
            "step": 1,
            "delay_hours": 0,
            "angle": "re_engage",
            "template": (
                "Hi{name}! We chatted a while back about automating your WhatsApp business. "
                "Since then, we've added some powerful new features — including an AI that "
                "automatically improves your sales messages every day. "
                "Would you like to see what's new?"
            ),
        },
        {
            "step": 2,
            "delay_hours": 72,
            "angle": "value_reminder",
            "template": (
                "Hey{name}, just a friendly reminder — while you're manually handling "
                "WhatsApp messages, your competitors might already be using AI automation. "
                "Our clients typically save 15+ hours/week. "
                "Ready for a quick 15-minute demo?"
            ),
        },
        {
            "step": 3,
            "delay_hours": 168,
            "angle": "final",
            "template": (
                "Hi{name}, last message from me! If you ever want to explore "
                "AI-powered WhatsApp automation, our door is always open. "
                "Just reply 'demo' anytime and I'll set one up instantly."
            ),
        },
    ],
    "demo_booked_nurture": [
        {
            "step": 1,
            "delay_hours": 0,
            "angle": "pre_demo",
            "template": (
                "Hi{name}! Looking forward to your demo! "
                "To make the most of our 15 minutes, could you share: "
                "1) How many WhatsApp conversations you handle daily? "
                "2) What's your biggest pain point? "
                "This helps me customize the demo to your specific needs."
            ),
        },
        {
            "step": 2,
            "delay_hours": 48,
            "angle": "post_demo",
            "template": (
                "Hi{name}! Hope you enjoyed the demo! "
                "Wanted to highlight that our Pro plan ($149/mo) includes everything we discussed — "
                "4 AI agents, unlimited messages, and the self-improvement AI. "
                "Ready to get started? I can activate your trial right now."
            ),
        },
    ],
}


class FollowUpSequencer:
    """Manages multi-step follow-up sequences for leads."""

    def get_sequence_for_lead(self, lead: Lead) -> list:
        """Determine which sequence a lead should be on based on their status."""
        if lead.status == LeadStatus.NEW:
            return FOLLOW_UP_SEQUENCES["new_lead"]
        elif lead.status in (LeadStatus.CONTACTED, LeadStatus.FOLLOW_UP):
            return FOLLOW_UP_SEQUENCES["contacted_stale"]
        elif lead.status == LeadStatus.DEMO_BOOKED:
            return FOLLOW_UP_SEQUENCES["demo_booked_nurture"]
        return []

    def _get_sequence_type_for_lead(self, lead: Lead) -> Optional[str]:
        """Get the sequence type string for a lead based on status."""
        if lead.status == LeadStatus.NEW:
            return "new_lead"
        elif lead.status in (LeadStatus.CONTACTED, LeadStatus.FOLLOW_UP):
            return "contacted_stale"
        elif lead.status == LeadStatus.DEMO_BOOKED:
            return "demo_booked_nurture"
        return None

    def get_current_step(self, db: Session, phone: str, sequence_type: Optional[str] = None) -> int:
        """Get the current step in the sequence for a given lead.

        Only counts FollowUp records that belong to the same sequence_type,
        so generic daily-loop follow-ups (sequence_type=None) don't inflate
        the step counter.
        """
        query = db.query(func.count(FollowUp.id)).filter(
            FollowUp.phone == phone, FollowUp.sent == 1
        )
        if sequence_type:
            query = query.filter(FollowUp.sequence_type == sequence_type)
        else:
            query = query.filter(FollowUp.sequence_type.isnot(None))

        count = query.scalar()
        return count or 0

    def get_next_message(
        self, db: Session, lead: Lead
    ) -> Optional[dict]:
        """Get the next follow-up message for a lead, if one is due."""
        sequence = self.get_sequence_for_lead(lead)
        if not sequence:
            return None

        seq_type = self._get_sequence_type_for_lead(lead)
        current_step = self.get_current_step(db, lead.phone, sequence_type=seq_type)

        # Check if there's a next step in the sequence
        if current_step >= len(sequence):
            return None  # Sequence complete

        step = sequence[current_step]

        # Check if enough time has passed since the last follow-up
        if current_step > 0:
            last_follow_up = (
                db.query(FollowUp)
                .filter(
                    FollowUp.phone == lead.phone,
                    FollowUp.sent == 1,
                    FollowUp.sequence_type == seq_type,
                )
                .order_by(FollowUp.created_at.desc())
                .first()
            )
            if last_follow_up:
                hours_since = (
                    datetime.now(timezone.utc) - last_follow_up.created_at.replace(tzinfo=timezone.utc)
                ).total_seconds() / 3600
                if hours_since < step["delay_hours"]:
                    return None  # Not time yet

        # Also check if the lead has responded since the last follow-up
        last_inbound = (
            db.query(Message)
            .filter(
                Message.phone == lead.phone,
                Message.direction == "inbound",
            )
            .order_by(Message.created_at.desc())
            .first()
        )
        last_outbound_auto = (
            db.query(FollowUp)
            .filter(
                FollowUp.phone == lead.phone,
                FollowUp.sent == 1,
                FollowUp.sequence_type == seq_type,
            )
            .order_by(FollowUp.created_at.desc())
            .first()
        )

        # If the lead responded after our last follow-up, pause the sequence
        if last_inbound and last_outbound_auto:
            if last_inbound.created_at > last_outbound_auto.created_at:
                return None  # Lead engaged, let agents handle it

        # Format the message
        name_str = f" {lead.name}" if lead.name and lead.name != "Unknown" else ""
        message = step["template"].format(name=name_str)

        return {
            "step": step["step"],
            "angle": step["angle"],
            "message": message,
            "delay_hours": step["delay_hours"],
        }

    async def execute_sequences(self, db: Session) -> dict:
        """Run follow-up sequences for all eligible leads."""
        results = {
            "messages_sent": 0,
            "leads_processed": 0,
            "leads_skipped": 0,
            "leads_completed": 0,
            "details": [],
        }

        # Get all active leads (not closed or lost)
        active_leads = (
            db.query(Lead)
            .filter(
                Lead.status.notin_([LeadStatus.CLOSED, LeadStatus.LOST])
            )
            .all()
        )

        for lead in active_leads:
            results["leads_processed"] += 1
            next_msg = self.get_next_message(db, lead)

            if next_msg is None:
                # Check if sequence is complete
                sequence = self.get_sequence_for_lead(lead)
                current_step = self.get_current_step(db, lead.phone)
                if current_step >= len(sequence):
                    results["leads_completed"] += 1
                else:
                    results["leads_skipped"] += 1
                continue

            # Send the follow-up
            try:
                await whatsapp_service.send_text_message(
                    lead.phone, next_msg["message"]
                )

                # Record the follow-up with sequence_type for proper step tracking
                seq_type = self._get_sequence_type_for_lead(lead)
                follow_up = FollowUp(
                    phone=lead.phone,
                    message=next_msg["message"],
                    scheduled_at=datetime.now(timezone.utc),
                    sent=1,
                    sequence_type=seq_type,
                )
                db.add(follow_up)

                # Save as outbound message
                memory_service.save_message(
                    db,
                    lead.phone,
                    "outbound",
                    next_msg["message"],
                    agent_type="follow_up_sequence",
                )

                # Log the action
                log = AutomationLog(
                    action_type="follow_up_sequence",
                    phone=lead.phone,
                    description=(
                        f"Step {next_msg['step']} ({next_msg['angle']}) "
                        f"sent to {lead.phone}"
                    ),
                    details={
                        "step": next_msg["step"],
                        "angle": next_msg["angle"],
                        "lead_status": lead.status.value,
                        "sequence_type": (
                            "new_lead"
                            if lead.status == LeadStatus.NEW
                            else "contacted_stale"
                            if lead.status in (LeadStatus.CONTACTED, LeadStatus.FOLLOW_UP)
                            else "demo_booked_nurture"
                        ),
                    },
                    status="completed",
                )
                db.add(log)

                results["messages_sent"] += 1
                results["details"].append(
                    {
                        "phone": lead.phone,
                        "step": next_msg["step"],
                        "angle": next_msg["angle"],
                        "status": lead.status.value,
                    }
                )

            except Exception as e:
                logger.error(
                    f"Failed to send follow-up to {lead.phone}: {e}"
                )
                log = AutomationLog(
                    action_type="follow_up_sequence",
                    phone=lead.phone,
                    description=f"Failed to send step {next_msg['step']} to {lead.phone}: {e}",
                    details={"error": str(e), "step": next_msg["step"]},
                    status="failed",
                )
                db.add(log)

        db.commit()
        logger.info(
            f"Follow-up sequences: {results['messages_sent']} sent, "
            f"{results['leads_skipped']} skipped, "
            f"{results['leads_completed']} completed"
        )
        return results

    def get_sequence_status(self, db: Session, phone: str) -> dict:
        """Get the current sequence status for a specific lead."""
        lead = db.query(Lead).filter(Lead.phone == phone).first()
        if not lead:
            return {"error": "Lead not found"}

        sequence = self.get_sequence_for_lead(lead)
        seq_type = self._get_sequence_type_for_lead(lead)
        current_step = self.get_current_step(db, phone, sequence_type=seq_type)

        follow_ups = (
            db.query(FollowUp)
            .filter(
                FollowUp.phone == phone,
                FollowUp.sent == 1,
                FollowUp.sequence_type == seq_type,
            )
            .order_by(FollowUp.created_at.asc())
            .all()
        )

        return {
            "phone": phone,
            "lead_status": lead.status.value,
            "sequence_type": (
                "new_lead"
                if lead.status == LeadStatus.NEW
                else "contacted_stale"
                if lead.status in (LeadStatus.CONTACTED, LeadStatus.FOLLOW_UP)
                else "demo_booked_nurture"
                if lead.status == LeadStatus.DEMO_BOOKED
                else "none"
            ),
            "total_steps": len(sequence),
            "current_step": current_step,
            "completed": current_step >= len(sequence),
            "history": [
                {
                    "step": i + 1,
                    "sent_at": fu.created_at.isoformat() if fu.created_at else None,
                    "message_preview": fu.message[:80] + "..." if len(fu.message) > 80 else fu.message,
                }
                for i, fu in enumerate(follow_ups)
            ],
        }


# Singleton instance
follow_up_sequencer = FollowUpSequencer()
