"""Campaign System — Full marketing campaign pipeline.

AI CEO → Campaign Planner → Audience Selector → Message Generator
      → Scheduler → WhatsApp Sender → Metrics → Optimization Loop

Provides automated marketing campaigns that:
1. Plan campaigns based on business goals and current metrics
2. Select target audiences from CRM data
3. Generate personalized messages using LLM
4. Schedule sends with optimal timing
5. Execute via WhatsApp Cloud API
6. Track delivery, response, and conversion metrics
7. Self-optimize based on performance data
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Lead, LeadStatus, Message, AutomationLog
from app.services.whatsapp import whatsapp_service
from app.services.llm import llm_service
from app.core.logging import logger


# --- Campaign Templates ---

CAMPAIGN_TEMPLATES = {
    "product_launch": {
        "name": "Product Launch",
        "description": "Announce new features or products to engaged leads",
        "goal": "awareness",
        "default_audience": "all_active",
        "message_style": "exciting, benefit-focused",
        "suggested_timing": "10:00 AM",
    },
    "re_engagement": {
        "name": "Re-Engagement",
        "description": "Win back cold or stale leads who haven't responded",
        "goal": "reactivation",
        "default_audience": "stale",
        "message_style": "warm, low-pressure, value-reminder",
        "suggested_timing": "2:00 PM",
    },
    "demo_push": {
        "name": "Demo Push",
        "description": "Drive demo bookings from interested leads",
        "goal": "conversion",
        "default_audience": "warm_leads",
        "message_style": "urgent, social-proof, clear CTA",
        "suggested_timing": "11:00 AM",
    },
    "upsell": {
        "name": "Upsell Campaign",
        "description": "Upgrade existing users to higher-tier plans",
        "goal": "revenue",
        "default_audience": "demo_booked",
        "message_style": "value-focused, ROI numbers, exclusive offer",
        "suggested_timing": "3:00 PM",
    },
    "seasonal_promo": {
        "name": "Seasonal Promotion",
        "description": "Time-limited discount or offer",
        "goal": "revenue",
        "default_audience": "all_active",
        "message_style": "urgent, time-limited, discount-focused",
        "suggested_timing": "9:00 AM",
    },
    "custom": {
        "name": "Custom Campaign",
        "description": "Fully customized campaign with your own message",
        "goal": "custom",
        "default_audience": "all",
        "message_style": "user-defined",
        "suggested_timing": "10:00 AM",
    },
}

# --- Audience Filters ---

AUDIENCE_FILTERS = {
    "all": {
        "name": "All Leads",
        "description": "Every lead in CRM",
        "filter_fn": lambda leads: leads,
    },
    "all_active": {
        "name": "Active Leads",
        "description": "Leads with status: new, contacted, or demo_booked",
        "filter_fn": lambda leads: [
            l for l in leads
            if l.status in (LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.DEMO_BOOKED)
        ],
    },
    "new_leads": {
        "name": "New Leads",
        "description": "Leads who just signed up (status: new)",
        "filter_fn": lambda leads: [l for l in leads if l.status == LeadStatus.NEW],
    },
    "warm_leads": {
        "name": "Warm Leads",
        "description": "Contacted leads with score >= 40",
        "filter_fn": lambda leads: [
            l for l in leads
            if l.status == LeadStatus.CONTACTED and (l.lead_score or 0) >= 40
        ],
    },
    "stale": {
        "name": "Stale Leads",
        "description": "Contacted leads with no messages in 7+ days",
        "filter_fn": lambda leads: leads,  # handled specially in select_audience
    },
    "demo_booked": {
        "name": "Demo Booked",
        "description": "Leads who booked a demo",
        "filter_fn": lambda leads: [l for l in leads if l.status == LeadStatus.DEMO_BOOKED],
    },
    "high_intent": {
        "name": "High Intent",
        "description": "Leads with score >= 60",
        "filter_fn": lambda leads: [l for l in leads if (l.lead_score or 0) >= 60],
    },
}


class CampaignService:
    """Full campaign pipeline: plan → target → generate → schedule → send → track → optimize."""

    def __init__(self):
        self._campaigns: List[dict] = []
        self._campaign_counter = 0

    # ─── 1. Campaign Planner ───

    def plan_campaign(
        self,
        template_type: str,
        custom_name: Optional[str] = None,
        custom_message: Optional[str] = None,
        audience_filter: Optional[str] = None,
    ) -> dict:
        """Plan a new campaign from a template or custom input."""
        template = CAMPAIGN_TEMPLATES.get(template_type, CAMPAIGN_TEMPLATES["custom"])

        self._campaign_counter += 1
        campaign = {
            "id": self._campaign_counter,
            "name": custom_name or template["name"],
            "template_type": template_type,
            "description": template["description"],
            "goal": template["goal"],
            "message_style": template["message_style"],
            "audience_filter": audience_filter or template["default_audience"],
            "custom_message": custom_message,
            "status": "planned",  # planned → audience_selected → messages_generated → scheduled → sending → completed
            "created_at": datetime.now(timezone.utc).isoformat(),
            "audience": [],
            "messages": [],
            "metrics": {
                "total_targeted": 0,
                "sent": 0,
                "delivered": 0,
                "responded": 0,
                "converted": 0,
                "response_rate": 0.0,
                "conversion_rate": 0.0,
            },
            "optimization_notes": [],
        }

        self._campaigns.append(campaign)
        logger.info(f"Campaign planned: {campaign['name']} (ID: {campaign['id']})")
        return campaign

    # ─── 2. Audience Selector ───

    def select_audience(self, campaign_id: int, db: Session) -> dict:
        """Select target audience for a campaign based on its filter."""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        all_leads = db.query(Lead).all()
        filter_key = campaign["audience_filter"]

        if filter_key == "stale":
            # Special handling: find leads with no messages in 7+ days
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            stale_phones = set()
            for lead in all_leads:
                if lead.status in (LeadStatus.CONTACTED, LeadStatus.NEW):
                    last_msg = (
                        db.query(Message)
                        .filter(Message.phone == lead.phone)
                        .order_by(Message.created_at.desc())
                        .first()
                    )
                    if not last_msg or last_msg.created_at.replace(tzinfo=timezone.utc) < seven_days_ago:
                        stale_phones.add(lead.phone)
            audience = [l for l in all_leads if l.phone in stale_phones]
        else:
            filter_def = AUDIENCE_FILTERS.get(filter_key, AUDIENCE_FILTERS["all"])
            audience = filter_def["filter_fn"](all_leads)

        campaign["audience"] = [
            {
                "phone": l.phone,
                "name": l.name or "there",
                "status": l.status.value if isinstance(l.status, LeadStatus) else l.status,
                "score": l.lead_score or 0,
            }
            for l in audience
        ]
        campaign["metrics"]["total_targeted"] = len(audience)
        campaign["status"] = "audience_selected"

        logger.info(f"Campaign {campaign_id}: selected {len(audience)} leads")
        return campaign

    # ─── 3. Message Generator ───

    async def generate_messages(self, campaign_id: int) -> dict:
        """Generate personalized messages for each lead in the audience."""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        messages = []
        for lead in campaign["audience"]:
            if campaign["custom_message"]:
                # Use custom message with name substitution
                msg = campaign["custom_message"].replace("{name}", f" {lead['name']}")
            else:
                # Generate AI message based on campaign style
                msg = await self._generate_ai_message(
                    lead_name=lead["name"],
                    lead_status=lead["status"],
                    lead_score=lead["score"],
                    campaign_name=campaign["name"],
                    message_style=campaign["message_style"],
                    goal=campaign["goal"],
                )

            messages.append({
                "phone": lead["phone"],
                "name": lead["name"],
                "message": msg,
                "status": "pending",  # pending → sent → delivered → responded
            })

        campaign["messages"] = messages
        campaign["status"] = "messages_generated"

        logger.info(f"Campaign {campaign_id}: generated {len(messages)} messages")
        return campaign

    async def _generate_ai_message(
        self,
        lead_name: str,
        lead_status: str,
        lead_score: int,
        campaign_name: str,
        message_style: str,
        goal: str,
    ) -> str:
        """Use LLM to generate a personalized campaign message."""
        prompt = f"""Generate a short WhatsApp marketing message (under 100 words) for a campaign.

Campaign: {campaign_name}
Goal: {goal}
Style: {message_style}
Recipient: {lead_name} (status: {lead_status}, engagement score: {lead_score}/100)

Rules:
- Address them by name
- Keep it conversational and warm
- Include a clear call-to-action
- Use 1-2 emojis max
- Don't be pushy
- Make it specific to their engagement level"""

        try:
            response = await llm_service.generate(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"AI message generation failed: {e}")
            # Fallback to template-based message
            return (
                f"Hi {lead_name}! We have something exciting at Munesh AI that "
                f"could help automate your WhatsApp business. "
                f"Want to learn more? Reply 'YES' for a quick overview!"
            )

    # ─── 4. Scheduler ───

    def schedule_campaign(self, campaign_id: int, send_immediately: bool = True) -> dict:
        """Schedule the campaign for sending."""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        now = datetime.now(timezone.utc)
        campaign["scheduled_at"] = now.isoformat()
        campaign["send_immediately"] = send_immediately
        campaign["status"] = "scheduled"

        logger.info(f"Campaign {campaign_id}: scheduled for {'immediate' if send_immediately else 'later'} send")
        return campaign

    # ─── 5. WhatsApp Sender ───

    async def execute_campaign(self, campaign_id: int, db: Session) -> dict:
        """Execute the campaign — send all messages via WhatsApp."""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        campaign["status"] = "sending"
        sent_count = 0

        for msg in campaign["messages"]:
            try:
                result = await whatsapp_service.send_text_message(
                    msg["phone"], msg["message"]
                )
                if result.get("status") != "error":
                    msg["status"] = "sent"
                    msg["sent_at"] = datetime.now(timezone.utc).isoformat()
                    sent_count += 1
                else:
                    msg["status"] = "failed"
                    msg["error"] = result.get("detail", "unknown")
            except Exception as e:
                msg["status"] = "failed"
                msg["error"] = str(e)
                logger.error(f"Campaign send failed for {msg['phone']}: {e}")

            # Log each send
            log = AutomationLog(
                action_type="campaign_send",
                phone=msg["phone"],
                description=f"Campaign '{campaign['name']}': sent message to {msg['name']}",
                details={
                    "campaign_id": campaign_id,
                    "message_preview": msg["message"][:100],
                    "status": msg["status"],
                },
                status="completed" if msg["status"] == "sent" else "failed",
            )
            db.add(log)

        db.commit()

        campaign["metrics"]["sent"] = sent_count
        campaign["status"] = "completed"
        campaign["completed_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Campaign {campaign_id}: completed — {sent_count}/{len(campaign['messages'])} sent")
        return campaign

    # ─── 6. Metrics Tracker ───

    def get_campaign_metrics(self, campaign_id: int, db: Session) -> dict:
        """Calculate real-time metrics for a campaign by checking CRM data."""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        if campaign["status"] != "completed":
            return campaign["metrics"]

        # Check for responses: any inbound message from targeted leads after campaign send
        completed_at = campaign.get("completed_at")
        if completed_at:
            send_time = datetime.fromisoformat(completed_at)
            responded = 0
            converted = 0

            for msg in campaign["messages"]:
                if msg["status"] != "sent":
                    continue

                # Check for inbound responses after send
                response_count = (
                    db.query(Message)
                    .filter(
                        Message.phone == msg["phone"],
                        Message.direction == "inbound",
                        Message.created_at >= send_time,
                    )
                    .count()
                )
                if response_count > 0:
                    msg["status"] = "responded"
                    responded += 1

                # Check for conversions (status changed to demo_booked or closed)
                lead = db.query(Lead).filter(Lead.phone == msg["phone"]).first()
                if lead and lead.status in (LeadStatus.DEMO_BOOKED, LeadStatus.CLOSED):
                    converted += 1

            campaign["metrics"]["responded"] = responded
            campaign["metrics"]["converted"] = converted
            sent = campaign["metrics"]["sent"]
            campaign["metrics"]["response_rate"] = round(
                (responded / sent * 100) if sent > 0 else 0, 1
            )
            campaign["metrics"]["conversion_rate"] = round(
                (converted / sent * 100) if sent > 0 else 0, 1
            )

        return campaign["metrics"]

    # ─── 7. Optimization Loop ───

    async def optimize_campaign(self, campaign_id: int, db: Session) -> dict:
        """Analyze campaign results and generate optimization suggestions."""
        campaign = self._get_campaign(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        # Refresh metrics
        metrics = self.get_campaign_metrics(campaign_id, db)

        suggestions = []

        # Rule-based optimization
        response_rate = metrics.get("response_rate", 0)
        conversion_rate = metrics.get("conversion_rate", 0)
        total = metrics.get("total_targeted", 0)
        sent = metrics.get("sent", 0)

        if total == 0:
            suggestions.append("No leads targeted — try broadening your audience filter.")
        elif sent == 0:
            suggestions.append("No messages sent — check WhatsApp API credentials.")
        else:
            if response_rate < 10:
                suggestions.append(
                    "Low response rate (<10%). Try: shorter messages, stronger hook in first line, "
                    "or sending at a different time of day."
                )
            elif response_rate < 25:
                suggestions.append(
                    "Moderate response rate. Try A/B testing different message angles "
                    "(social proof vs. urgency vs. value-first)."
                )
            else:
                suggestions.append(f"Good response rate ({response_rate}%). Keep this messaging style.")

            if conversion_rate < 5:
                suggestions.append(
                    "Low conversion rate. Consider: stronger CTA, "
                    "adding a limited-time offer, or targeting higher-intent leads."
                )
            elif conversion_rate >= 20:
                suggestions.append(
                    f"Excellent conversion rate ({conversion_rate}%). "
                    "Scale this campaign to a larger audience."
                )

            # Audience-specific suggestions
            if campaign["audience_filter"] == "all":
                suggestions.append(
                    "You're targeting all leads. Try segmenting by status or score "
                    "for more personalized messaging."
                )

        # Try LLM-powered optimization
        try:
            prompt = f"""You are a marketing optimization expert. Analyze this WhatsApp campaign and suggest 2-3 improvements.

Campaign: {campaign['name']}
Goal: {campaign['goal']}
Audience: {campaign['audience_filter']} ({total} leads)
Sent: {sent}, Responded: {metrics.get('responded', 0)}, Converted: {metrics.get('converted', 0)}
Response Rate: {response_rate}%, Conversion Rate: {conversion_rate}%

Sample message: {campaign['messages'][0]['message'][:200] if campaign['messages'] else 'N/A'}

Give 2-3 specific, actionable suggestions to improve results. Keep each under 30 words."""

            ai_suggestions = await llm_service.generate(prompt)
            suggestions.append(f"AI Analysis: {ai_suggestions.strip()}")
        except Exception:
            pass  # AI suggestions are optional

        campaign["optimization_notes"] = suggestions
        campaign["optimized_at"] = datetime.now(timezone.utc).isoformat()

        logger.info(f"Campaign {campaign_id}: optimization complete — {len(suggestions)} suggestions")
        return {
            "campaign_id": campaign_id,
            "metrics": metrics,
            "suggestions": suggestions,
        }

    # ─── Full Pipeline ───

    async def run_full_pipeline(
        self,
        db: Session,
        template_type: str,
        custom_name: Optional[str] = None,
        custom_message: Optional[str] = None,
        audience_filter: Optional[str] = None,
    ) -> dict:
        """Run the complete campaign pipeline end-to-end."""
        logger.info(f"Starting full campaign pipeline: {template_type}")

        # 1. Plan
        campaign = self.plan_campaign(template_type, custom_name, custom_message, audience_filter)

        # 2. Select Audience
        self.select_audience(campaign["id"], db)

        if not campaign["audience"]:
            campaign["status"] = "completed"
            campaign["optimization_notes"] = ["No leads matched the audience filter."]
            return campaign

        # 3. Generate Messages
        await self.generate_messages(campaign["id"])

        # 4. Schedule (immediate)
        self.schedule_campaign(campaign["id"], send_immediately=True)

        # 5. Execute (send via WhatsApp)
        await self.execute_campaign(campaign["id"], db)

        # 6. Refresh Metrics
        self.get_campaign_metrics(campaign["id"], db)

        # 7. Optimize
        await self.optimize_campaign(campaign["id"], db)

        return campaign

    # ─── Helpers ───

    def _get_campaign(self, campaign_id: int) -> Optional[dict]:
        """Get a campaign by ID."""
        for c in self._campaigns:
            if c["id"] == campaign_id:
                return c
        return None

    def get_all_campaigns(self) -> List[dict]:
        """Get all campaigns."""
        return self._campaigns

    def get_campaign(self, campaign_id: int) -> Optional[dict]:
        """Get a single campaign by ID."""
        return self._get_campaign(campaign_id)

    def get_templates(self) -> dict:
        """Get available campaign templates."""
        return CAMPAIGN_TEMPLATES

    def get_audience_filters(self) -> dict:
        """Get available audience filters with descriptions."""
        return {
            key: {"name": val["name"], "description": val["description"]}
            for key, val in AUDIENCE_FILTERS.items()
        }


# Singleton instance
campaign_service = CampaignService()
