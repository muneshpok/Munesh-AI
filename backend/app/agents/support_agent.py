"""Support Agent - Handles FAQs and customer issues."""

from typing import List

from app.agents.base import BaseAgent
from app.models.schemas import AgentDecisionSchema, IntentEnum, ActionEnum
from app.services.llm import llm_service
from app.core.logging import logger


class SupportAgent(BaseAgent):
    """Handles customer support, FAQs, and issue resolution."""

    agent_type = "support"

    SYSTEM_PROMPT = """You are Munesh AI Support Assistant on WhatsApp.
Your goals:
1. Understand the user's issue or question
2. Provide clear, helpful solutions
3. Reference FAQs when applicable
4. Escalate complex issues by suggesting they contact support team

Common FAQs:
- Business hours: Monday-Friday, 9 AM - 6 PM
- Response time: Usually within 1 hour
- Refund policy: 30-day money-back guarantee
- Technical support: Available via email and WhatsApp

Keep responses clear, empathetic, and under 200 words."""

    async def process(self, phone: str, message: str, history: List[dict]) -> AgentDecisionSchema:
        """Process a support-related message."""
        logger.info(f"SupportAgent processing message from {phone}")

        context = self._build_context(history)
        prompt = f"""Previous conversation:
{context}

User message: {message}

Provide helpful support response. Be empathetic and solution-oriented."""

        response = await llm_service.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        return AgentDecisionSchema(
            intent=IntentEnum.SUPPORT,
            action=ActionEnum.RESPOND,
            tool_name=None,
            parameters=None,
            response=response,
        )
