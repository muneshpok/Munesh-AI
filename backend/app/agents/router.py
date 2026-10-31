"""Agent router - Maps intents to agents and orchestrates processing."""

from typing import List, Optional

from app.agents.base import DecisionEngine
from app.agents.chat_agent import ChatAgent
from app.agents.sales_agent import SalesAgent
from app.agents.support_agent import SupportAgent
from app.agents.booking_agent import BookingAgent
from app.models.schemas import AgentDecisionSchema, IntentEnum
from app.core.logging import logger


class AgentRouter:
    """Routes messages to appropriate agents based on intent classification."""

    def __init__(self) -> None:
        self.agents = {
            IntentEnum.CHAT: ChatAgent(),
            IntentEnum.SALES: SalesAgent(),
            IntentEnum.SUPPORT: SupportAgent(),
            IntentEnum.BOOKING: BookingAgent(),
        }
        self.decision_engine = DecisionEngine()

    async def route(
        self, phone: str, message: str, history: Optional[List[dict]] = None
    ) -> AgentDecisionSchema:
        """Route a message to the appropriate agent and return the decision."""
        if history is None:
            history = []

        # Classify intent
        intent = self.decision_engine.classify_intent(message)
        logger.info(f"Classified intent for {phone}: {intent.value}")

        # Get the appropriate agent
        agent = self.agents.get(intent, self.agents[IntentEnum.CHAT])
        logger.info(f"Routing to {agent.agent_type} agent")

        # Process the message
        decision = await agent.process(phone, message, history)

        # Validate the decision
        if not self.decision_engine.validate_decision(decision):
            logger.warning(f"Invalid decision from {agent.agent_type}, falling back to chat")
            decision = AgentDecisionSchema(
                intent=IntentEnum.CHAT,
                action="respond",
                response="I'm sorry, I didn't quite understand that. Could you please rephrase?",
            )

        return decision


# Singleton instance
agent_router = AgentRouter()
