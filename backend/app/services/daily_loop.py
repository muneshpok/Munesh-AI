"""Daily Loop - Orchestrates the Data → Analyze → Decide → Improve → Deploy cycle."""

from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy.orm import Session

from app.models.models import (
    Lead, LeadStatus, Message, DailyReport, AutomationLog, FollowUp,
)
from app.services.analytics import analytics_engine
from app.services.whatsapp import whatsapp_service
from app.services.memory import memory_service
from app.core.logging import logger
from app.core.config import settings
from app.services.self_improvement import self_improvement_agent
from app.services.follow_up_sequences import follow_up_sequencer


class DailyLoop:
    """Orchestrates the automated daily improvement cycle.

    Cycle: Data → Analyze → Decide → Improve → Deploy → Repeat
    """

    async def run(self, db: Session) -> DailyReport:
        """Execute the full daily loop cycle."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        logger.info(f"=== Daily Loop starting for {today} ===")

        actions_taken: List[str] = []

        # --- STEP 1: DATA (Collect) ---
        logger.info("[1/5] Collecting data...")
        funnel = analytics_engine.get_funnel_metrics(db)
        activity = analytics_engine.get_message_activity(db, days=1)
        agent_perf = analytics_engine.get_agent_performance(db, days=1)

        # --- STEP 2: ANALYZE ---
        logger.info("[2/5] Analyzing data...")
        stale_leads = analytics_engine.find_stale_leads(
            db, stale_hours=settings.FOLLOW_UP_DELAY_HOURS
        )
        insights = analytics_engine.generate_insights(
            funnel, activity, agent_perf, stale_leads
        )
        recommendations = analytics_engine.generate_recommendations(
            funnel, stale_leads, activity
        )

        # --- STEP 3: DECIDE ---
        logger.info("[3/5] Making decisions...")
        decisions = self._make_decisions(funnel, stale_leads, activity)

        # --- STEP 4: IMPROVE (Execute decisions) ---
        logger.info("[4/5] Executing improvements...")

        # Score all leads
        scored = analytics_engine.score_all_leads(db)
        actions_taken.append(f"Scored {scored} lead(s)")
        self._log_action(db, "score", None, f"Scored {scored} leads", {"count": scored})

        # Send follow-ups to stale leads
        follow_ups_sent = 0
        if decisions.get("send_follow_ups") and stale_leads:
            follow_ups_sent = await self._send_follow_ups(db, stale_leads)
            actions_taken.append(f"Sent {follow_ups_sent} follow-up(s)")

        # Nurture new leads
        if decisions.get("nurture_new_leads"):
            nurtured = await self._nurture_new_leads(db)
            actions_taken.append(f"Nurtured {nurtured} new lead(s)")

        # Escalate high-intent leads
        if decisions.get("escalate_high_intent"):
            escalated = self._escalate_high_intent(db)
            actions_taken.append(f"Escalated {escalated} high-intent lead(s)")

        # Run smart follow-up sequences
        logger.info("[4.3/5] Running follow-up sequences...")
        try:
            seq_results = await follow_up_sequencer.execute_sequences(db)
            if seq_results["messages_sent"] > 0:
                actions_taken.append(
                    f"Follow-up sequences: {seq_results['messages_sent']} message(s) sent"
                )
            else:
                actions_taken.append("Follow-up sequences: no messages due")
        except Exception as e:
            logger.error(f"Follow-up sequences failed: {e}")
            actions_taken.append(f"Follow-up sequences: skipped (error: {e})")

        # Run self-improvement cycle
        logger.info("[4.5/5] Running self-improvement cycle...")
        try:
            si_report = await self_improvement_agent.run_improvement_cycle(db)
            si_count = len(si_report.get("improvements_made", []))
            if si_count > 0:
                actions_taken.append(
                    f"Self-improvement: {si_count} update(s) applied"
                )
                for imp in si_report["improvements_made"]:
                    actions_taken.append(
                        f"  → {imp['type']}: {imp['description']}"
                    )
            else:
                actions_taken.append("Self-improvement: no changes needed")
        except Exception as e:
            logger.error(f"Self-improvement cycle failed: {e}")
            actions_taken.append(f"Self-improvement: skipped (error: {e})")

        # --- STEP 5: DEPLOY (Save report) ---
        logger.info("[5/5] Saving daily report...")
        stages = funnel.get("stages", {})
        report = DailyReport(
            report_date=today,
            total_leads=funnel.get("total", 0),
            new_leads=stages.get("new", {}).get("count", 0),
            contacted_leads=stages.get("contacted", {}).get("count", 0),
            demo_booked=stages.get("demo_booked", {}).get("count", 0),
            closed_leads=stages.get("closed", {}).get("count", 0),
            lost_leads=stages.get("lost", {}).get("count", 0),
            conversion_rate=funnel.get("conversion_rate", 0.0),
            messages_sent=activity.get("messages_sent", 0),
            messages_received=activity.get("messages_received", 0),
            active_conversations=activity.get("active_conversations", 0),
            agent_breakdown=agent_perf.get("breakdown", {}),
            insights=insights + recommendations,
            actions_taken=actions_taken,
            stale_leads_count=len(stale_leads),
            follow_ups_sent=follow_ups_sent,
            leads_scored=scored,
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        logger.info(f"=== Daily Loop completed. Report #{report.id} saved ===")
        return report

    def _make_decisions(
        self,
        funnel: dict,
        stale_leads: List[dict],
        activity: dict,
    ) -> dict:
        """Decide which automated actions to take based on analysis."""
        decisions = {
            "send_follow_ups": False,
            "nurture_new_leads": False,
            "escalate_high_intent": False,
        }

        # Follow up stale leads
        if stale_leads:
            decisions["send_follow_ups"] = True

        # Nurture new leads that haven't been contacted
        stages = funnel.get("stages", {})
        new_count = stages.get("new", {}).get("count", 0)
        if new_count > 0:
            decisions["nurture_new_leads"] = True

        # Escalate leads that show high buying intent
        demo_count = stages.get("demo_booked", {}).get("count", 0)
        if demo_count > 0:
            decisions["escalate_high_intent"] = True

        logger.info(f"Decisions: {decisions}")
        return decisions

    async def _send_follow_ups(
        self, db: Session, stale_leads: List[dict]
    ) -> int:
        """Send follow-up messages to stale leads."""
        sent = 0
        for lead_info in stale_leads[:10]:  # Cap at 10 per cycle
            phone = lead_info["phone"]
            status = lead_info["status"]

            message = self._get_follow_up_message(status, lead_info.get("name", ""))

            # Schedule the follow-up
            follow_up = FollowUp(
                phone=phone,
                message=message,
                scheduled_at=datetime.now(timezone.utc),
                sent=1,
            )
            db.add(follow_up)

            # Send via WhatsApp
            await whatsapp_service.send_text_message(phone, message)

            # Save outbound message
            memory_service.save_message(
                db, phone, "outbound", message, agent_type="automation"
            )

            self._log_action(
                db, "follow_up", phone,
                f"Follow-up sent to {phone} (status: {status})",
                {"message": message, "hours_stale": lead_info.get("hours_since_activity", 0)},
            )
            sent += 1

        db.commit()
        logger.info(f"Sent {sent} follow-up messages")
        return sent

    async def _nurture_new_leads(self, db: Session) -> int:
        """Send welcome/nurture messages to new leads."""
        new_leads = (
            db.query(Lead)
            .filter(Lead.status == LeadStatus.NEW)
            .all()
        )

        nurtured = 0
        for lead in new_leads[:10]:  # Cap at 10 per cycle
            message = (
                f"Hi{' ' + lead.name if lead.name else ''}! 👋 "
                "Thanks for reaching out to Munesh AI. "
                "We'd love to help you automate your business. "
                "Would you like to learn more about our solutions, or would you prefer to book a quick demo?"
            )

            await whatsapp_service.send_text_message(lead.phone, message)
            memory_service.save_message(
                db, lead.phone, "outbound", message, agent_type="automation"
            )

            # Move to contacted
            lead.status = LeadStatus.CONTACTED
            self._log_action(
                db, "nurture", lead.phone,
                f"Nurture message sent to new lead {lead.phone}",
                {"moved_to": "contacted"},
            )
            nurtured += 1

        db.commit()
        logger.info(f"Nurtured {nurtured} new leads")
        return nurtured

    def _escalate_high_intent(self, db: Session) -> int:
        """Flag high-intent leads for priority attention."""
        high_intent = (
            db.query(Lead)
            .filter(Lead.status == LeadStatus.DEMO_BOOKED, Lead.lead_score >= 50)
            .all()
        )

        escalated = 0
        for lead in high_intent:
            self._log_action(
                db, "escalate", lead.phone,
                f"High-intent lead {lead.phone} flagged (score: {lead.lead_score})",
                {"lead_score": lead.lead_score, "status": "demo_booked"},
            )
            escalated += 1

        db.commit()
        logger.info(f"Escalated {escalated} high-intent leads")
        return escalated

    @staticmethod
    def _get_follow_up_message(status: str, name: str) -> str:
        """Generate a contextual follow-up message based on lead status."""
        greeting = f"Hi {name}!" if name and name != "Unknown" else "Hi there!"

        if status == "contacted":
            return (
                f"{greeting} Just following up on our conversation. "
                "Have you had a chance to think about our solutions? "
                "I'm happy to answer any questions or schedule a demo for you."
            )
        elif status == "demo_booked":
            return (
                f"{greeting} Looking forward to your demo! "
                "Is there anything specific you'd like us to cover? "
                "Feel free to share your requirements beforehand."
            )
        elif status == "follow_up":
            return (
                f"{greeting} We haven't heard from you in a while. "
                "We have some exciting updates that might interest you. "
                "Would you like to reconnect?"
            )
        else:
            return (
                f"{greeting} Thank you for your interest in Munesh AI! "
                "We'd love to help you get started. "
                "What can we help you with today?"
            )

    @staticmethod
    def _log_action(
        db: Session,
        action_type: str,
        phone: str | None,
        description: str,
        details: dict | None = None,
        status: str = "completed",
    ) -> None:
        """Log an automated action."""
        log = AutomationLog(
            action_type=action_type,
            phone=phone,
            description=description,
            details=details,
            status=status,
        )
        db.add(log)


# Singleton instance
daily_loop = DailyLoop()
