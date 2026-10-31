"""Base agent interface and decision engine."""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.schemas import AgentDecisionSchema, IntentEnum, ActionEnum
from app.core.logging import logger


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    agent_type: str = "base"

    @abstractmethod
    async def process(self, phone: str, message: str, history: List[dict]) -> AgentDecisionSchema:
        """Process a message and return a decision."""
        pass

    def _build_context(self, history: List[dict]) -> str:
        """Build conversation context from message history."""
        if not history:
            return "No previous conversation."
        lines = []
        for msg in history[-10:]:
            direction = "User" if msg.get("direction") == "inbound" else "Assistant"
            lines.append(f"{direction}: {msg.get('content', '')}")
        return "\n".join(lines)


class DecisionEngine:
    """Routes messages to the appropriate agent based on intent classification."""

    SALES_KEYWORDS = [
        "price", "pricing", "cost", "buy", "purchase", "plan",
        "subscribe", "offer", "discount", "package", "quote", "product",
        "interested", "how much", "features", "comparison", "trial",
    ]
    SUPPORT_KEYWORDS = [
        "help", "issue", "problem", "error", "bug", "fix", "broken",
        "not working", "support", "complaint", "refund", "cancel",
        "trouble", "assist", "faq", "question",
    ]
    BOOKING_KEYWORDS = [
        "book", "schedule", "appointment", "meeting", "calendar",
        "slot", "availability", "reserve", "demo booking", "demo",
        "call", "available",
    ]

    @staticmethod
    def classify_intent(message: str) -> IntentEnum:
        """Classify the intent of a message using keyword matching."""
        text = message.lower()

        sales_score = sum(1 for kw in DecisionEngine.SALES_KEYWORDS if kw in text)
        support_score = sum(1 for kw in DecisionEngine.SUPPORT_KEYWORDS if kw in text)
        booking_score = sum(1 for kw in DecisionEngine.BOOKING_KEYWORDS if kw in text)

        scores = {
            IntentEnum.SALES: sales_score,
            IntentEnum.SUPPORT: support_score,
            IntentEnum.BOOKING: booking_score,
        }

        max_score = max(scores.values())
        if max_score == 0:
            return IntentEnum.CHAT

        return max(scores, key=scores.get)  # type: ignore[arg-type]

    @staticmethod
    def validate_decision(decision: AgentDecisionSchema) -> bool:
        """Validate an agent decision before execution."""
        if decision.action == ActionEnum.CALL_TOOL:
            if not decision.tool_name:
                logger.warning("Decision has action=call_tool but no tool_name")
                return False
        if not decision.response:
            logger.warning("Decision has empty response")
            return False
        return True
