"""Analytics Engine - Collects and analyzes platform data."""

from typing import List, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import Lead, LeadStatus, Message, AgentDecision, AutomationLog
from app.core.logging import logger


class AnalyticsEngine:
    """Collects, analyzes, and generates insights from platform data."""

    # --- Data Collection ---

    def get_funnel_metrics(self, db: Session) -> dict:
        """Get lead funnel breakdown with counts and percentages."""
        total = db.query(Lead).count()
        if total == 0:
            return {
                "total": 0,
                "stages": {},
                "conversion_rate": 0.0,
            }

        stages = {}
        for status in LeadStatus:
            count = db.query(Lead).filter(Lead.status == status).count()
            stages[status.value] = {
                "count": count,
                "percentage": round(count / total * 100, 1),
            }

        closed = stages.get("closed", {}).get("count", 0)
        conversion_rate = round(closed / total * 100, 2) if total > 0 else 0.0

        return {
            "total": total,
            "stages": stages,
            "conversion_rate": conversion_rate,
        }

    def get_message_activity(
        self, db: Session, days: int = 1
    ) -> dict:
        """Get message activity metrics for the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        sent = (
            db.query(Message)
            .filter(Message.direction == "outbound", Message.created_at >= cutoff)
            .count()
        )
        received = (
            db.query(Message)
            .filter(Message.direction == "inbound", Message.created_at >= cutoff)
            .count()
        )
        active_conversations = (
            db.query(func.count(func.distinct(Message.phone)))
            .filter(Message.created_at >= cutoff)
            .scalar()
            or 0
        )

        return {
            "messages_sent": sent,
            "messages_received": received,
            "total_messages": sent + received,
            "active_conversations": active_conversations,
            "period_days": days,
        }

    def get_agent_performance(self, db: Session, days: int = 1) -> dict:
        """Get per-agent usage breakdown."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        decisions = (
            db.query(AgentDecision.intent, func.count(AgentDecision.id))
            .filter(AgentDecision.created_at >= cutoff)
            .group_by(AgentDecision.intent)
            .all()
        )

        breakdown: dict[str, int] = {}
        total = 0
        for intent, count in decisions:
            breakdown[intent] = count
            total += count

        return {
            "breakdown": breakdown,
            "total_decisions": total,
            "period_days": days,
        }

    # --- Analysis ---

    def find_stale_leads(
        self, db: Session, stale_hours: int = 24
    ) -> List[dict]:
        """Find leads that haven't had any activity in stale_hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=stale_hours)

        # Get leads that are NOT closed or lost
        active_leads = (
            db.query(Lead)
            .filter(
                Lead.status.notin_([LeadStatus.CLOSED, LeadStatus.LOST])
            )
            .all()
        )

        stale: List[dict] = []
        for lead in active_leads:
            # Find the last message for this lead
            last_msg = (
                db.query(Message)
                .filter(Message.phone == lead.phone)
                .order_by(Message.created_at.desc())
                .first()
            )

            last_activity = last_msg.created_at if last_msg else lead.created_at
            if last_activity and last_activity.replace(tzinfo=timezone.utc) < cutoff:
                hours_stale = int(
                    (datetime.now(timezone.utc) - last_activity.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                )
                stale.append({
                    "phone": lead.phone,
                    "name": lead.name or "Unknown",
                    "status": lead.status.value if isinstance(lead.status, LeadStatus) else lead.status,
                    "hours_since_activity": hours_stale,
                    "lead_score": lead.lead_score,
                })

        return sorted(stale, key=lambda x: x["hours_since_activity"], reverse=True)

    def calculate_lead_score(self, db: Session, phone: str) -> int:
        """Calculate an engagement score (0-100) for a lead."""
        lead = db.query(Lead).filter(Lead.phone == phone).first()
        if not lead:
            return 0

        score = 0

        # Message count factor (max 30 points)
        msg_count = db.query(Message).filter(Message.phone == phone).count()
        score += min(msg_count * 5, 30)

        # Inbound message ratio factor (max 20 points) - more inbound = more engaged
        inbound = (
            db.query(Message)
            .filter(Message.phone == phone, Message.direction == "inbound")
            .count()
        )
        if msg_count > 0:
            ratio = inbound / msg_count
            score += int(ratio * 20)

        # Status progression factor (max 30 points)
        status_scores = {
            "new": 5,
            "contacted": 10,
            "follow_up": 15,
            "demo_booked": 25,
            "closed": 30,
            "lost": 0,
        }
        status_val = lead.status.value if isinstance(lead.status, LeadStatus) else lead.status
        score += status_scores.get(status_val, 0)

        # Recency factor (max 20 points) - recent activity = higher score
        last_msg = (
            db.query(Message)
            .filter(Message.phone == phone)
            .order_by(Message.created_at.desc())
            .first()
        )
        if last_msg and last_msg.created_at:
            hours_ago = (
                datetime.now(timezone.utc) - last_msg.created_at.replace(tzinfo=timezone.utc)
            ).total_seconds() / 3600
            if hours_ago < 1:
                score += 20
            elif hours_ago < 6:
                score += 15
            elif hours_ago < 24:
                score += 10
            elif hours_ago < 72:
                score += 5

        return min(score, 100)

    def score_all_leads(self, db: Session) -> int:
        """Score all leads and update their lead_score. Returns count scored."""
        leads = db.query(Lead).all()
        scored = 0
        for lead in leads:
            new_score = self.calculate_lead_score(db, lead.phone)
            lead.lead_score = new_score
            scored += 1
        db.commit()
        return scored

    def get_top_leads(self, db: Session, limit: int = 10) -> List[dict]:
        """Get the highest-scored leads."""
        leads = (
            db.query(Lead)
            .order_by(Lead.lead_score.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "phone": lead.phone,
                "name": lead.name or "Unknown",
                "status": lead.status.value if isinstance(lead.status, LeadStatus) else lead.status,
                "lead_score": lead.lead_score,
            }
            for lead in leads
        ]

    # --- Insight Generation ---

    def generate_insights(
        self,
        funnel: dict,
        activity: dict,
        agent_perf: dict,
        stale_leads: List[dict],
    ) -> List[str]:
        """Generate actionable insights from analyzed data."""
        insights: List[str] = []
        total = funnel.get("total", 0)

        if total == 0:
            insights.append("No leads in the system yet. Focus on lead acquisition.")
            return insights

        stages = funnel.get("stages", {})

        # Funnel insights
        new_pct = stages.get("new", {}).get("percentage", 0)
        if new_pct > 50:
            insights.append(
                f"{new_pct}% of leads are still 'new' — consider automated outreach to engage them faster."
            )

        demo_pct = stages.get("demo_booked", {}).get("percentage", 0)
        if demo_pct > 0:
            insights.append(
                f"{demo_pct}% of leads have booked demos — strong buying intent detected."
            )

        conversion = funnel.get("conversion_rate", 0)
        if conversion > 0:
            insights.append(f"Current conversion rate: {conversion}%.")
        else:
            insights.append("No closed deals yet — prioritize leads with high engagement scores.")

        # Stale leads
        if stale_leads:
            insights.append(
                f"{len(stale_leads)} lead(s) inactive for 24+ hours — follow-ups recommended."
            )

        # Activity insights
        total_msgs = activity.get("total_messages", 0)
        if total_msgs == 0:
            insights.append("No message activity in the last 24 hours.")
        else:
            received = activity.get("messages_received", 0)
            sent = activity.get("messages_sent", 0)
            if received > sent * 2:
                insights.append(
                    "High inbound volume — consider scaling agent responses."
                )

        # Agent insights
        breakdown = agent_perf.get("breakdown", {})
        if breakdown:
            top_agent = max(breakdown, key=breakdown.get) if breakdown else None
            if top_agent:
                insights.append(
                    f"Most active agent: {top_agent} ({breakdown[top_agent]} decisions)."
                )

        return insights

    def generate_recommendations(
        self,
        funnel: dict,
        stale_leads: List[dict],
        activity: dict,
    ) -> List[str]:
        """Generate specific recommendations for improvement."""
        recs: List[str] = []
        stages = funnel.get("stages", {})
        total = funnel.get("total", 0)

        if total == 0:
            recs.append("Start by driving traffic to your WhatsApp number.")
            return recs

        # Conversion optimization
        new_count = stages.get("new", {}).get("count", 0)
        if new_count > 0:
            recs.append(f"Send welcome messages to {new_count} new lead(s) to move them to 'contacted'.")

        contacted_count = stages.get("contacted", {}).get("count", 0)
        if contacted_count > 3:
            recs.append(f"Push demo booking offers to {contacted_count} contacted leads.")

        # Stale lead recovery
        if len(stale_leads) > 0:
            recs.append(f"Re-engage {len(stale_leads)} stale lead(s) with a personalized follow-up.")

        # Activity optimization
        if activity.get("total_messages", 0) == 0:
            recs.append("No recent activity — consider running a broadcast campaign.")

        return recs


# Singleton instance
analytics_engine = AnalyticsEngine()
