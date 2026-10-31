"""Performance Analyzer - Simple standalone performance analysis and improvement suggestions."""

import json
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import Lead, LeadStatus, Message
from app.services.llm import llm_service
from app.core.logging import logger


class PerformanceAnalyzer:
    """Simple performance analyzer that provides quick metrics and AI-generated improvement suggestions."""

    def analyze_performance(self, db: Session) -> dict:
        """Analyze current lead performance metrics."""
        leads = db.query(Lead).all()
        total = len(leads)

        status_counts = {
            "new": 0,
            "contacted": 0,
            "demo_booked": 0,
            "follow_up": 0,
            "closed": 0,
            "lost": 0,
        }
        for lead in leads:
            status_key = lead.status.value if hasattr(lead.status, "value") else str(lead.status)
            if status_key in status_counts:
                status_counts[status_key] += 1

        booked = status_counts["demo_booked"]
        closed = status_counts["closed"]
        lost = status_counts["lost"]

        conversion = (booked / total) * 100 if total else 0
        close_rate = (closed / total) * 100 if total else 0
        loss_rate = (lost / total) * 100 if total else 0

        # Message metrics
        total_messages = db.query(Message).count()
        inbound = db.query(Message).filter(Message.direction == "inbound").count()
        outbound = db.query(Message).filter(Message.direction == "outbound").count()

        return {
            "total_leads": total,
            "status_breakdown": status_counts,
            "booked": booked,
            "closed": closed,
            "lost": lost,
            "conversion_rate": round(conversion, 2),
            "close_rate": round(close_rate, 2),
            "loss_rate": round(loss_rate, 2),
            "total_messages": total_messages,
            "inbound_messages": inbound,
            "outbound_messages": outbound,
            "avg_messages_per_lead": round(total_messages / total, 1) if total else 0,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def generate_improvements(self, metrics: dict) -> str:
        """Generate AI-powered improvement suggestions based on current metrics."""
        prompt = f"""You are an AI growth expert.

Current performance:
- Leads: {metrics['total_leads']}
- Booked demos: {metrics['booked']}
- Closed deals: {metrics['closed']}
- Lost leads: {metrics['lost']}
- Conversion rate: {metrics['conversion_rate']}%
- Close rate: {metrics['close_rate']}%
- Loss rate: {metrics['loss_rate']}%
- Total messages: {metrics['total_messages']}
- Avg messages per lead: {metrics['avg_messages_per_lead']}

Suggest:
1. Better sales messages
2. Improved follow-ups
3. Conversion optimization ideas
"""

        try:
            result = await llm_service.generate(
                system_prompt="You are a business growth consultant. Provide concise, actionable suggestions.",
                user_prompt=prompt,
                temperature=0.7,
                max_tokens=500,
            )
            return result
        except Exception as e:
            logger.warning(f"LLM not available for improvement suggestions: {e}")
            # Generate rule-based suggestions as fallback
            return self._generate_fallback_suggestions(metrics)

    def _generate_fallback_suggestions(self, metrics: dict) -> str:
        """Generate rule-based suggestions when LLM is not available."""
        suggestions = []

        # Sales message suggestions
        if metrics["conversion_rate"] < 20:
            suggestions.append(
                "📊 **Sales Messages**: Your conversion rate is below 20%. "
                "Try personalizing outreach with the lead's name and specific pain points. "
                "Use social proof and urgency in your messages."
            )
        elif metrics["conversion_rate"] < 50:
            suggestions.append(
                "📊 **Sales Messages**: Conversion rate is moderate. "
                "A/B test different call-to-action phrases and consider adding "
                "product demo videos or case studies to your messages."
            )
        else:
            suggestions.append(
                "📊 **Sales Messages**: Great conversion rate! "
                "Focus on maintaining quality while scaling outreach volume."
            )

        # Follow-up suggestions
        if metrics["avg_messages_per_lead"] < 3:
            suggestions.append(
                "📬 **Follow-ups**: Average messages per lead is low ({:.1f}). "
                "Implement a 3-touch follow-up sequence: Day 1 (intro), "
                "Day 3 (value add), Day 7 (final offer).".format(
                    metrics["avg_messages_per_lead"]
                )
            )
        else:
            suggestions.append(
                "📬 **Follow-ups**: Good engagement volume. "
                "Optimize timing — send follow-ups between 9-11 AM for best response rates."
            )

        # Conversion optimization
        if metrics["loss_rate"] > 30:
            suggestions.append(
                "🎯 **Conversion Optimization**: High loss rate ({:.1f}%). "
                "Survey lost leads to understand objections. "
                "Consider offering limited-time incentives to re-engage.".format(
                    metrics["loss_rate"]
                )
            )
        elif metrics["total_leads"] > 0 and metrics["booked"] == 0:
            suggestions.append(
                "🎯 **Conversion Optimization**: No demos booked yet. "
                "Make booking frictionless — send direct scheduling links "
                "and reduce steps needed to book a demo."
            )
        else:
            suggestions.append(
                "🎯 **Conversion Optimization**: Consider adding exit-intent "
                "triggers and retargeting sequences for leads that go quiet."
            )

        return "\n\n".join(suggestions)

    def apply_improvements(self, suggestions: str) -> dict:
        """Log improvement suggestions for tracking."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "suggestions": suggestions,
            "status": "logged",
        }
        logger.info(f"Performance improvement suggestions logged at {timestamp}")
        return log_entry

    async def run_analysis(self, db: Session) -> dict:
        """Run full performance analysis: analyze → suggest → log."""
        metrics = self.analyze_performance(db)
        suggestions = await self.generate_improvements(metrics)
        log_entry = self.apply_improvements(suggestions)

        return {
            "metrics": metrics,
            "suggestions": suggestions,
            "log": log_entry,
        }


# Singleton instance
performance_analyzer = PerformanceAnalyzer()
