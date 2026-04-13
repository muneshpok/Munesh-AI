"""Self-Improvement Agent — Analyzes interactions and autonomously improves the system.

Flow: User Messages → WhatsApp AI System → Logs + CRM + Metrics → Self-Improvement Agent
Updates: Prompts, Responses, Follow-ups, Strategy
"""

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func

from app.models.models import (
    Lead, LeadStatus, Message, AgentDecision,
    PromptVersion, ImprovementLog, StrategyConfig,
)
from app.services.analytics import analytics_engine
from app.services.llm import llm_service
from app.core.logging import logger


# Default agent prompts (initial versions)
DEFAULT_PROMPTS = {
    "chat": (
        "You are Munesh AI, a friendly and helpful business assistant on WhatsApp.\n"
        "You help users with general questions about the business.\n"
        "Be concise, professional, and helpful.\n"
        "If the user seems interested in products or services, mention that you can connect them with sales.\n"
        "If they have an issue, offer to connect them with support.\n"
        "Keep responses under 200 words."
    ),
    "sales": (
        "You are Munesh AI Sales Assistant on WhatsApp.\n"
        "Your goals:\n"
        "1. Understand the user's needs\n"
        "2. Explain relevant products/services\n"
        "3. Highlight key benefits and features\n"
        "4. Guide them toward booking a demo or making a purchase\n"
        "5. Be persuasive but not pushy\n\n"
        "If the user shows strong buying intent, suggest booking a demo.\n"
        "Keep responses under 200 words and use bullet points for features."
    ),
    "support": (
        "You are Munesh AI Support Assistant on WhatsApp.\n"
        "Your goals:\n"
        "1. Understand the user's issue or question\n"
        "2. Provide clear, helpful solutions\n"
        "3. Reference FAQs when applicable\n"
        "4. Escalate complex issues by suggesting they contact support team\n\n"
        "Common FAQs:\n"
        "- Business hours: Monday-Friday, 9 AM - 6 PM\n"
        "- Response time: Usually within 1 hour\n"
        "- Refund policy: 30-day money-back guarantee\n"
        "- Technical support: Available via email and WhatsApp\n\n"
        "Keep responses clear, empathetic, and under 200 words."
    ),
    "booking": (
        "You are Munesh AI Booking Assistant on WhatsApp.\n"
        "Your goals:\n"
        "1. Help users schedule demos and appointments\n"
        "2. Confirm booking details\n"
        "3. Send scheduling links\n"
        "4. Update the user's CRM status\n\n"
        "When the user wants to book, ask for:\n"
        "- Preferred date and time\n"
        "- Their name (if not known)\n"
        "- Purpose of the meeting\n\n"
        "Keep responses friendly and under 150 words."
    ),
}

# Default strategy configuration
DEFAULT_STRATEGY = {
    "follow_up_delay_hours": {
        "value": "24",
        "type": "int",
        "category": "timing",
        "description": "Hours to wait before sending follow-up to inactive leads",
    },
    "max_follow_ups_per_cycle": {
        "value": "10",
        "type": "int",
        "category": "timing",
        "description": "Maximum follow-up messages per daily cycle",
    },
    "nurture_message_template": {
        "value": (
            "Hi{name}! 👋 Thanks for reaching out to Munesh AI. "
            "We'd love to help you automate your business. "
            "Would you like to learn more about our solutions, "
            "or would you prefer to book a quick demo?"
        ),
        "type": "string",
        "category": "templates",
        "description": "Default nurture message for new leads",
    },
    "high_intent_score_threshold": {
        "value": "50",
        "type": "int",
        "category": "thresholds",
        "description": "Minimum lead score to flag as high-intent",
    },
    "sales_keywords": {
        "value": json.dumps([
            "price", "pricing", "cost", "buy", "purchase", "plan",
            "subscribe", "offer", "discount", "package", "quote", "product",
            "interested", "how much", "features", "comparison", "trial",
        ]),
        "type": "json",
        "category": "keywords",
        "description": "Keywords that trigger sales intent classification",
    },
    "support_keywords": {
        "value": json.dumps([
            "help", "issue", "problem", "error", "bug", "fix", "broken",
            "not working", "support", "complaint", "refund", "cancel",
            "trouble", "assist", "faq", "question",
        ]),
        "type": "json",
        "category": "keywords",
        "description": "Keywords that trigger support intent classification",
    },
    "booking_keywords": {
        "value": json.dumps([
            "book", "schedule", "appointment", "meeting", "calendar",
            "slot", "availability", "reserve", "demo booking", "demo",
            "call", "available",
        ]),
        "type": "json",
        "category": "keywords",
        "description": "Keywords that trigger booking intent classification",
    },
    "response_max_words": {
        "value": "200",
        "type": "int",
        "category": "thresholds",
        "description": "Maximum word count for agent responses",
    },
}


class SelfImprovementAgent:
    """Autonomous self-improvement agent that analyzes system performance
    and updates prompts, responses, follow-ups, and strategy.

    Cycle: Analyze Logs → Identify Patterns → Generate Improvements → Apply & Track
    """

    def initialize_defaults(self, db: Session) -> None:
        """Initialize default prompts and strategy configs if not present."""
        # Initialize prompt versions
        for agent_type, prompt_text in DEFAULT_PROMPTS.items():
            existing = (
                db.query(PromptVersion)
                .filter(
                    PromptVersion.agent_type == agent_type,
                    PromptVersion.is_active == 1,
                )
                .first()
            )
            if not existing:
                pv = PromptVersion(
                    agent_type=agent_type,
                    version=1,
                    prompt_text=prompt_text,
                    is_active=1,
                    reason="Initial default prompt",
                )
                db.add(pv)

        # Initialize strategy configs
        for key, config in DEFAULT_STRATEGY.items():
            existing = (
                db.query(StrategyConfig)
                .filter(StrategyConfig.config_key == key)
                .first()
            )
            if not existing:
                sc = StrategyConfig(
                    config_key=key,
                    config_value=config["value"],
                    config_type=config["type"],
                    category=config["category"],
                    description=config["description"],
                    updated_by="system",
                )
                db.add(sc)

        db.commit()

    async def run_improvement_cycle(self, db: Session) -> dict:
        """Execute a full self-improvement cycle.

        1. Analyze conversation patterns and outcomes
        2. Evaluate agent prompt effectiveness
        3. Identify keyword gaps and routing issues
        4. Optimize follow-up timing and messaging
        5. Generate and apply improvements
        6. Log all changes with rationale
        """
        cycle_id = str(uuid4())[:8]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"=== Self-Improvement Cycle {cycle_id} starting ===")

        # Ensure defaults are initialized
        self.initialize_defaults(db)

        improvements: List[dict] = []
        insights: List[str] = []
        recommendations: List[str] = []

        # --- PHASE 1: Analyze conversation patterns ---
        logger.info(f"[{cycle_id}] Phase 1: Analyzing conversation patterns...")
        conv_analysis = self._analyze_conversations(db)
        insights.extend(conv_analysis.get("insights", []))

        # --- PHASE 2: Evaluate agent performance ---
        logger.info(f"[{cycle_id}] Phase 2: Evaluating agent performance...")
        perf_analysis = self._analyze_agent_performance(db)
        insights.extend(perf_analysis.get("insights", []))

        # --- PHASE 3: Optimize prompts ---
        logger.info(f"[{cycle_id}] Phase 3: Optimizing prompts...")
        prompt_improvements = await self._optimize_prompts(db, conv_analysis, perf_analysis)
        improvements.extend(prompt_improvements)

        # --- PHASE 4: Optimize keywords ---
        logger.info(f"[{cycle_id}] Phase 4: Optimizing keywords...")
        keyword_improvements = self._optimize_keywords(db, conv_analysis)
        improvements.extend(keyword_improvements)

        # --- PHASE 5: Optimize follow-up strategy ---
        logger.info(f"[{cycle_id}] Phase 5: Optimizing follow-up strategy...")
        followup_improvements = self._optimize_follow_ups(db, conv_analysis)
        improvements.extend(followup_improvements)

        # --- PHASE 6: Optimize response strategy ---
        logger.info(f"[{cycle_id}] Phase 6: Optimizing response strategy...")
        strategy_improvements = self._optimize_strategy(db, perf_analysis)
        improvements.extend(strategy_improvements)

        # Generate next-cycle recommendations
        recommendations = self._generate_next_recommendations(
            conv_analysis, perf_analysis, improvements
        )

        # Count by type
        prompts_updated = sum(1 for i in improvements if i["type"] == "prompt")
        keywords_updated = sum(1 for i in improvements if i["type"] == "keyword")
        strategies_updated = sum(1 for i in improvements if i["type"] == "strategy")
        followups_optimized = sum(1 for i in improvements if i["type"] == "follow_up")

        report = {
            "cycle_id": cycle_id,
            "timestamp": timestamp,
            "improvements_made": improvements,
            "prompts_updated": prompts_updated,
            "keywords_updated": keywords_updated,
            "strategies_updated": strategies_updated,
            "follow_ups_optimized": followups_optimized,
            "insights": insights,
            "next_recommendations": recommendations,
        }

        logger.info(
            f"=== Self-Improvement Cycle {cycle_id} complete: "
            f"{len(improvements)} improvement(s) applied ==="
        )
        return report

    # ------------------------------------------------------------------ #
    #  ANALYSIS METHODS                                                    #
    # ------------------------------------------------------------------ #

    def _analyze_conversations(self, db: Session) -> dict:
        """Analyze recent conversations to find patterns."""
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)

        # Get recent messages
        messages = (
            db.query(Message)
            .filter(Message.created_at >= since)
            .order_by(Message.created_at.desc())
            .all()
        )

        # Group by phone
        conversations: dict = {}
        for msg in messages:
            if msg.phone not in conversations:
                conversations[msg.phone] = {"inbound": [], "outbound": []}
            conversations[msg.phone][msg.direction].append(msg)

        # Calculate metrics
        total_conversations = len(conversations)
        avg_messages_per_conv = (
            len(messages) / total_conversations if total_conversations > 0 else 0
        )

        # Analyze response quality
        short_responses = 0
        long_responses = 0
        outbound_messages = [m for m in messages if m.direction == "outbound"]
        for msg in outbound_messages:
            word_count = len(msg.content.split())
            if word_count < 10:
                short_responses += 1
            elif word_count > 200:
                long_responses += 1

        # Check conversion patterns — which conversations led to demo_booked/closed
        converted_phones = set()
        leads = db.query(Lead).filter(
            Lead.status.in_([LeadStatus.DEMO_BOOKED, LeadStatus.CLOSED])
        ).all()
        for lead in leads:
            converted_phones.add(lead.phone)

        converted_conversations = sum(
            1 for phone in conversations if phone in converted_phones
        )
        conversion_rate = (
            converted_conversations / total_conversations * 100
            if total_conversations > 0
            else 0
        )

        # Identify lost leads with messages
        lost_phones = set()
        lost_leads = db.query(Lead).filter(Lead.status == LeadStatus.LOST).all()
        for lead in lost_leads:
            lost_phones.add(lead.phone)

        lost_conversations = sum(
            1 for phone in conversations if phone in lost_phones
        )

        insights: List[str] = []
        if total_conversations > 0:
            insights.append(
                f"Analyzed {total_conversations} conversations with "
                f"{avg_messages_per_conv:.1f} avg messages each."
            )
        if conversion_rate > 0:
            insights.append(
                f"Conversation-to-conversion rate: {conversion_rate:.1f}%."
            )
        if short_responses > len(outbound_messages) * 0.3 and outbound_messages:
            insights.append(
                f"{short_responses} responses were under 10 words — "
                "consider adding more detail to agent prompts."
            )
        if long_responses > len(outbound_messages) * 0.2 and outbound_messages:
            insights.append(
                f"{long_responses} responses exceeded 200 words — "
                "consider tightening response length limits."
            )
        if lost_conversations > 0:
            insights.append(
                f"{lost_conversations} conversation(s) ended in lost leads — "
                "review agent responses for improvement opportunities."
            )

        return {
            "total_conversations": total_conversations,
            "avg_messages": avg_messages_per_conv,
            "short_responses": short_responses,
            "long_responses": long_responses,
            "outbound_count": len(outbound_messages),
            "converted": converted_conversations,
            "lost": lost_conversations,
            "conversion_rate": conversion_rate,
            "insights": insights,
        }

    def _analyze_agent_performance(self, db: Session) -> dict:
        """Analyze per-agent decision quality and outcomes."""
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)

        decisions = (
            db.query(AgentDecision)
            .filter(AgentDecision.created_at >= since)
            .all()
        )

        agent_stats: dict = {}
        for d in decisions:
            agent = d.intent or "unknown"
            if agent not in agent_stats:
                agent_stats[agent] = {
                    "total": 0,
                    "tool_calls": 0,
                    "responds": 0,
                    "phones": set(),
                }
            agent_stats[agent]["total"] += 1
            if d.action == "call_tool":
                agent_stats[agent]["tool_calls"] += 1
            else:
                agent_stats[agent]["responds"] += 1
            agent_stats[agent]["phones"].add(d.phone)

        # Measure per-agent conversion (how many of their leads converted)
        for agent, stats in agent_stats.items():
            converted = 0
            for phone in stats["phones"]:
                lead = db.query(Lead).filter(Lead.phone == phone).first()
                if lead and lead.status in (LeadStatus.DEMO_BOOKED, LeadStatus.CLOSED):
                    converted += 1
            stats["converted"] = converted
            stats["phone_count"] = len(stats["phones"])
            stats["conversion_rate"] = (
                converted / stats["phone_count"] * 100
                if stats["phone_count"] > 0
                else 0
            )
            # Convert set to count for serialization
            del stats["phones"]

        insights: List[str] = []
        total_decisions = len(decisions)
        if total_decisions > 0:
            insights.append(f"Total agent decisions in last 7 days: {total_decisions}.")

        # Find best and worst performing agents
        if agent_stats:
            best_agent = max(
                agent_stats,
                key=lambda a: agent_stats[a].get("conversion_rate", 0),
            )
            worst_agent = min(
                agent_stats,
                key=lambda a: agent_stats[a].get("conversion_rate", 0),
            )
            best_rate = agent_stats[best_agent].get("conversion_rate", 0)
            worst_rate = agent_stats[worst_agent].get("conversion_rate", 0)

            if best_rate > 0:
                insights.append(
                    f"Best performing agent: {best_agent} ({best_rate:.0f}% conversion)."
                )
            if worst_rate < best_rate and total_decisions > 2:
                insights.append(
                    f"Lowest performing agent: {worst_agent} ({worst_rate:.0f}% conversion) — "
                    "prompt improvement recommended."
                )

        return {
            "agent_stats": agent_stats,
            "total_decisions": total_decisions,
            "insights": insights,
        }

    # ------------------------------------------------------------------ #
    #  OPTIMIZATION METHODS                                                #
    # ------------------------------------------------------------------ #

    async def _optimize_prompts(
        self, db: Session, conv_analysis: dict, perf_analysis: dict
    ) -> List[dict]:
        """Analyze and improve agent prompts based on performance data."""
        improvements: List[dict] = []
        agent_stats = perf_analysis.get("agent_stats", {})

        for agent_type in DEFAULT_PROMPTS:
            stats = agent_stats.get(agent_type, {})
            conversion_rate = stats.get("conversion_rate", 0)
            total = stats.get("total", 0)

            # Skip agents with too few interactions to judge
            if total < 2:
                continue

            # Get current active prompt
            current_prompt = (
                db.query(PromptVersion)
                .filter(
                    PromptVersion.agent_type == agent_type,
                    PromptVersion.is_active == 1,
                )
                .order_by(PromptVersion.version.desc())
                .first()
            )
            if not current_prompt:
                continue

            # Determine if prompt needs improvement
            needs_improvement = False
            reason_parts: List[str] = []

            if conversion_rate < 30 and agent_type in ("sales", "booking"):
                needs_improvement = True
                reason_parts.append(
                    f"low conversion rate ({conversion_rate:.0f}%)"
                )

            short_ratio = (
                conv_analysis.get("short_responses", 0)
                / max(conv_analysis.get("outbound_count", 1), 1)
            )
            if short_ratio > 0.3:
                needs_improvement = True
                reason_parts.append("too many short responses")

            if not needs_improvement:
                # Update performance score on current prompt
                current_prompt.performance_score = conversion_rate
                db.commit()
                continue

            # Generate improved prompt via LLM
            reason = "; ".join(reason_parts)
            improved_prompt = await self._generate_improved_prompt(
                agent_type, current_prompt.prompt_text, reason, conv_analysis
            )

            if improved_prompt and improved_prompt != current_prompt.prompt_text:
                # Deactivate old prompt
                current_prompt.is_active = 0
                current_prompt.performance_score = conversion_rate

                # Create new version
                new_version = current_prompt.version + 1
                new_pv = PromptVersion(
                    agent_type=agent_type,
                    version=new_version,
                    prompt_text=improved_prompt,
                    is_active=1,
                    reason=f"Auto-improved: {reason}",
                )
                db.add(new_pv)

                # Log the improvement
                log = ImprovementLog(
                    improvement_type="prompt",
                    target=f"{agent_type}_agent",
                    description=f"Updated {agent_type} agent prompt to v{new_version}",
                    old_value=current_prompt.prompt_text[:500],
                    new_value=improved_prompt[:500],
                    rationale=reason,
                    impact_metrics={
                        "previous_conversion_rate": conversion_rate,
                        "total_interactions": total,
                    },
                )
                db.add(log)
                db.commit()

                improvements.append({
                    "type": "prompt",
                    "target": f"{agent_type}_agent",
                    "description": f"Updated {agent_type} agent prompt to v{new_version}",
                    "reason": reason,
                })

        return improvements

    async def _generate_improved_prompt(
        self,
        agent_type: str,
        current_prompt: str,
        issues: str,
        conv_analysis: dict,
    ) -> Optional[str]:
        """Use LLM to generate an improved version of an agent prompt."""
        system = (
            "You are an AI prompt engineer. Your job is to improve agent system prompts "
            "based on performance data. Output ONLY the improved prompt text, nothing else."
        )
        user = (
            f"The current system prompt for the '{agent_type}' agent is:\n\n"
            f"---\n{current_prompt}\n---\n\n"
            f"Issues identified: {issues}\n"
            f"Conversation metrics: {conv_analysis.get('total_conversations', 0)} conversations, "
            f"{conv_analysis.get('conversion_rate', 0):.1f}% conversion rate.\n\n"
            "Please generate an improved version of this prompt that addresses the issues "
            "while maintaining the agent's core role. Keep it concise and action-oriented."
        )

        try:
            improved = await llm_service.generate(
                system_prompt=system,
                user_prompt=user,
                temperature=0.5,
                max_tokens=500,
            )
            return improved.strip()
        except Exception as e:
            logger.error(f"Failed to generate improved prompt: {e}")
            return None

    def _optimize_keywords(self, db: Session, conv_analysis: dict) -> List[dict]:
        """Analyze message patterns and add missing keywords for intent classification."""
        improvements: List[dict] = []

        # Get recent messages that were classified as "chat" (fallback)
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=7)

        chat_decisions = (
            db.query(AgentDecision)
            .filter(
                AgentDecision.intent == "chat",
                AgentDecision.created_at >= since,
            )
            .all()
        )

        if len(chat_decisions) < 3:
            return improvements

        # Get the messages for these decisions to look for patterns
        chat_phones = [d.phone for d in chat_decisions]
        chat_messages = (
            db.query(Message)
            .filter(
                Message.phone.in_(chat_phones),
                Message.direction == "inbound",
                Message.created_at >= since,
            )
            .all()
        )

        if not chat_messages:
            return improvements

        # Extract common words from chat-classified messages
        word_freq: dict = {}
        for msg in chat_messages:
            words = msg.content.lower().split()
            for word in words:
                clean = word.strip(".,!?;:'\"()[]{}").lower()
                if len(clean) > 3:  # Skip short words
                    word_freq[clean] = word_freq.get(clean, 0) + 1

        # Get current keyword lists from strategy config
        for intent_type in ("sales", "support", "booking"):
            config_key = f"{intent_type}_keywords"
            config = (
                db.query(StrategyConfig)
                .filter(StrategyConfig.config_key == config_key)
                .first()
            )
            if not config:
                continue

            current_keywords = json.loads(config.config_value)

            # Find frequent words in chat messages that might be misclassified
            potential_keywords: List[str] = []
            for word, freq in sorted(word_freq.items(), key=lambda x: -x[1]):
                if freq >= 2 and word not in current_keywords:
                    # Check if word frequently appears with the intent's existing keywords
                    if self._word_correlates_with_intent(
                        word, current_keywords, chat_messages
                    ):
                        potential_keywords.append(word)
                if len(potential_keywords) >= 3:
                    break

            if potential_keywords:
                new_keywords = current_keywords + potential_keywords
                old_value = config.config_value
                config.config_value = json.dumps(new_keywords)
                config.updated_by = "self_improvement"

                log = ImprovementLog(
                    improvement_type="keyword",
                    target=config_key,
                    description=(
                        f"Added {len(potential_keywords)} keyword(s) to {intent_type}: "
                        f"{', '.join(potential_keywords)}"
                    ),
                    old_value=old_value,
                    new_value=config.config_value,
                    rationale=(
                        f"Found {len(chat_decisions)} messages classified as 'chat' "
                        "that may belong to this intent based on word correlation."
                    ),
                )
                db.add(log)

                improvements.append({
                    "type": "keyword",
                    "target": config_key,
                    "description": (
                        f"Added keywords to {intent_type}: "
                        f"{', '.join(potential_keywords)}"
                    ),
                    "reason": "Frequent words in misclassified messages",
                })

        if improvements:
            db.commit()

        return improvements

    @staticmethod
    def _word_correlates_with_intent(
        word: str, intent_keywords: List[str], messages: list
    ) -> bool:
        """Check if a word frequently co-occurs with known intent keywords."""
        co_occurrences = 0
        word_occurrences = 0
        for msg in messages:
            content = msg.content.lower()
            if word in content:
                word_occurrences += 1
                if any(kw in content for kw in intent_keywords):
                    co_occurrences += 1
        # Word correlates if it co-occurs with intent keywords >40% of the time
        return (
            word_occurrences >= 2
            and co_occurrences / max(word_occurrences, 1) > 0.4
        )

    def _optimize_follow_ups(self, db: Session, conv_analysis: dict) -> List[dict]:
        """Optimize follow-up timing and messaging based on response patterns."""
        improvements: List[dict] = []

        # --- Part 1: Optimize nurture template based on response rates ---
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=14)

        auto_messages = (
            db.query(Message)
            .filter(
                Message.direction == "outbound",
                Message.agent_type == "automation",
                Message.created_at >= since,
            )
            .all()
        )

        if len(auto_messages) >= 5:
            responded = 0
            for msg in auto_messages:
                reply = (
                    db.query(Message)
                    .filter(
                        Message.phone == msg.phone,
                        Message.direction == "inbound",
                        Message.created_at > msg.created_at,
                    )
                    .first()
                )
                if reply:
                    responded += 1

            response_rate = responded / len(auto_messages) * 100

            if response_rate < 30:
                config = (
                    db.query(StrategyConfig)
                    .filter(StrategyConfig.config_key == "nurture_message_template")
                    .first()
                )
                if config:
                    old_template = config.config_value
                    new_template = (
                        "Hi{name}! 👋 Welcome to Munesh AI! "
                        "I noticed you reached out — I'd love to help you find "
                        "the perfect automation solution for your business. "
                        "Would you prefer a quick 5-minute overview or a full demo? "
                        "Just reply 'overview' or 'demo'!"
                    )
                    config.config_value = new_template
                    config.updated_by = "self_improvement"

                    log = ImprovementLog(
                        improvement_type="follow_up",
                        target="nurture_message_template",
                        description="Updated nurture message template for higher engagement",
                        old_value=old_template,
                        new_value=new_template,
                        rationale=(
                            f"Follow-up response rate is {response_rate:.0f}% "
                            f"({responded}/{len(auto_messages)}). "
                            "New template includes clear CTA with easy reply options."
                        ),
                        impact_metrics={
                            "previous_response_rate": response_rate,
                            "auto_messages_analyzed": len(auto_messages),
                        },
                    )
                    db.add(log)
                    db.commit()

                    improvements.append({
                        "type": "follow_up",
                        "target": "nurture_message_template",
                        "description": "Updated nurture template with clearer CTA",
                        "reason": f"Low response rate ({response_rate:.0f}%)",
                    })

        # --- Part 2: Optimize follow-up timing (independent of auto_messages) ---
        delay_config = (
            db.query(StrategyConfig)
            .filter(StrategyConfig.config_key == "follow_up_delay_hours")
            .first()
        )
        if delay_config and conv_analysis.get("lost", 0) > 2:
            current_delay = int(delay_config.config_value)
            if current_delay > 12:
                new_delay = max(current_delay - 6, 12)
                old_value = delay_config.config_value
                delay_config.config_value = str(new_delay)
                delay_config.updated_by = "self_improvement"

                log = ImprovementLog(
                    improvement_type="follow_up",
                    target="follow_up_delay_hours",
                    description=(
                        f"Reduced follow-up delay from {current_delay}h to {new_delay}h"
                    ),
                    old_value=old_value,
                    new_value=str(new_delay),
                    rationale=(
                        f"{conv_analysis['lost']} lost leads detected. "
                        "Faster follow-up may reduce churn."
                    ),
                )
                db.add(log)
                db.commit()

                improvements.append({
                    "type": "follow_up",
                    "target": "follow_up_delay_hours",
                    "description": f"Reduced delay from {current_delay}h to {new_delay}h",
                    "reason": f"{conv_analysis['lost']} lost leads — faster follow-up needed",
                })

        return improvements

    def _optimize_strategy(self, db: Session, perf_analysis: dict) -> List[dict]:
        """Optimize high-level strategy parameters based on performance."""
        improvements: List[dict] = []
        agent_stats = perf_analysis.get("agent_stats", {})

        # Adjust high-intent threshold based on actual conversion data
        booking_stats = agent_stats.get("booking", {})
        sales_stats = agent_stats.get("sales", {})

        total_converted = booking_stats.get("converted", 0) + sales_stats.get("converted", 0)
        total_interacted = booking_stats.get("phone_count", 0) + sales_stats.get("phone_count", 0)

        if total_interacted >= 5:
            config = (
                db.query(StrategyConfig)
                .filter(StrategyConfig.config_key == "high_intent_score_threshold")
                .first()
            )
            if config:
                current_threshold = int(config.config_value)
                actual_rate = total_converted / total_interacted * 100

                # If conversion is high, we can lower threshold to catch more leads
                if actual_rate > 50 and current_threshold > 40:
                    new_threshold = max(current_threshold - 10, 30)
                    old_value = config.config_value
                    config.config_value = str(new_threshold)
                    config.updated_by = "self_improvement"

                    log = ImprovementLog(
                        improvement_type="strategy",
                        target="high_intent_score_threshold",
                        description=(
                            f"Lowered high-intent threshold from "
                            f"{current_threshold} to {new_threshold}"
                        ),
                        old_value=old_value,
                        new_value=str(new_threshold),
                        rationale=(
                            f"High conversion rate ({actual_rate:.0f}%) suggests "
                            "we can widen the net for high-intent leads."
                        ),
                    )
                    db.add(log)
                    db.commit()

                    improvements.append({
                        "type": "strategy",
                        "target": "high_intent_score_threshold",
                        "description": (
                            f"Lowered threshold {current_threshold} → {new_threshold}"
                        ),
                        "reason": f"High conversion ({actual_rate:.0f}%)",
                    })

                # If conversion is low, raise threshold to be more selective
                elif actual_rate < 20 and current_threshold < 80:
                    new_threshold = min(current_threshold + 10, 80)
                    old_value = config.config_value
                    config.config_value = str(new_threshold)
                    config.updated_by = "self_improvement"

                    log = ImprovementLog(
                        improvement_type="strategy",
                        target="high_intent_score_threshold",
                        description=(
                            f"Raised high-intent threshold from "
                            f"{current_threshold} to {new_threshold}"
                        ),
                        old_value=old_value,
                        new_value=str(new_threshold),
                        rationale=(
                            f"Low conversion rate ({actual_rate:.0f}%) suggests "
                            "we should be more selective with high-intent flagging."
                        ),
                    )
                    db.add(log)
                    db.commit()

                    improvements.append({
                        "type": "strategy",
                        "target": "high_intent_score_threshold",
                        "description": (
                            f"Raised threshold {current_threshold} → {new_threshold}"
                        ),
                        "reason": f"Low conversion ({actual_rate:.0f}%)",
                    })

        return improvements

    @staticmethod
    def _generate_next_recommendations(
        conv_analysis: dict, perf_analysis: dict, improvements: List[dict]
    ) -> List[str]:
        """Generate recommendations for the next improvement cycle."""
        recommendations: List[str] = []

        if not improvements:
            recommendations.append(
                "No improvements needed this cycle — system is performing well."
            )

        if conv_analysis.get("total_conversations", 0) < 5:
            recommendations.append(
                "Insufficient data for deep analysis. "
                "Wait for more conversations before the next optimization."
            )

        if conv_analysis.get("conversion_rate", 0) < 20:
            recommendations.append(
                "Conversion rate is below 20%. Consider reviewing "
                "sales agent prompts and adding stronger CTAs."
            )

        agent_stats = perf_analysis.get("agent_stats", {})
        for agent, stats in agent_stats.items():
            if stats.get("total", 0) > 5 and stats.get("conversion_rate", 0) == 0:
                recommendations.append(
                    f"Agent '{agent}' has 0% conversion with {stats['total']} interactions — "
                    "investigate prompt effectiveness."
                )

        if not recommendations:
            recommendations.append(
                "Continue monitoring. Next cycle will have more data to analyze."
            )

        return recommendations

    # ------------------------------------------------------------------ #
    #  QUERY METHODS                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_active_prompts(db: Session) -> List[PromptVersion]:
        """Get all currently active agent prompts."""
        return (
            db.query(PromptVersion)
            .filter(PromptVersion.is_active == 1)
            .order_by(PromptVersion.agent_type)
            .all()
        )

    @staticmethod
    def get_prompt_history(
        db: Session, agent_type: Optional[str] = None, limit: int = 20
    ) -> List[PromptVersion]:
        """Get prompt version history."""
        query = db.query(PromptVersion)
        if agent_type:
            query = query.filter(PromptVersion.agent_type == agent_type)
        return query.order_by(PromptVersion.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_improvement_history(
        db: Session,
        improvement_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[ImprovementLog]:
        """Get improvement log history."""
        query = db.query(ImprovementLog)
        if improvement_type:
            query = query.filter(ImprovementLog.improvement_type == improvement_type)
        return query.order_by(ImprovementLog.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_strategy_configs(
        db: Session, category: Optional[str] = None
    ) -> List[StrategyConfig]:
        """Get current strategy configuration."""
        query = db.query(StrategyConfig)
        if category:
            query = query.filter(StrategyConfig.category == category)
        return query.order_by(StrategyConfig.category, StrategyConfig.config_key).all()


# Singleton instance
self_improvement_agent = SelfImprovementAgent()
