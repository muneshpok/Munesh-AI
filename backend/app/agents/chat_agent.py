"""Chat Agent - Handles general conversation queries."""

from typing import List

from app.agents.base import BaseAgent
from app.models.schemas import AgentDecisionSchema, IntentEnum, ActionEnum
from app.services.llm import llm_service
from app.core.logging import logger


class ChatAgent(BaseAgent):
    """Handles general conversation and queries."""

    agent_type = "chat"

    SYSTEM_PROMPT = """You are Munesh AI, a friendly and helpful business assistant on WhatsApp.
You help users with general questions about the business.
Be concise, professional, and helpful.
If the user seems interested in products or services, mention that you can connect them with sales.
If they have an issue, offer to connect them with support.
Keep responses under 200 words."""

    async def process(self, phone: str, message: str, history: List[dict]) -> AgentDecisionSchema:
        """Process a general chat message."""
        logger.info(f"ChatAgent processing message from {phone}")

        context = self._build_context(history)
        prompt = f"""Previous conversation:
{context}

User message: {message}

Respond helpfully and concisely."""

        response = await llm_service.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        return AgentDecisionSchema(
            intent=IntentEnum.CHAT,
            action=ActionEnum.RESPOND,
            tool_name=None,
            parameters=None,
            response=response,
        )
