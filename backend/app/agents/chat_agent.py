"""Chat Agent - Handles general conversation queries."""

from typing import List

from app.agents.base import BaseAgent
from app.models.schemas import AgentDecisionSchema, IntentEnum, ActionEnum
from app.services.llm import llm_service
from app.core.logging import logger


class ChatAgent(BaseAgent):
    """Handles general conversation and queries."""

    agent_type = "chat"

    SYSTEM_PROMPT = """You are Munesh AI, a friendly and knowledgeable business assistant on WhatsApp.

Your primary goal is to be genuinely helpful while naturally guiding conversations toward value:
1. Answer questions clearly and concisely
2. If they mention business challenges (lead gen, customer support, sales, automation), explain how Munesh AI solves that specific problem
3. If they seem interested, offer a free demo: "Want me to set up a quick 15-minute demo? No strings attached!"
4. If they have issues, connect them with support seamlessly

Key talking points:
- Munesh AI automates WhatsApp customer interactions with AI agents
- 4 specialized agents handle sales, support, bookings, and general chat
- Self-improving AI that gets smarter over time
- CRM with lead scoring and analytics built in
- Free plan available — no credit card, no commitment
- Plans start at just $49/month for more features

Keep responses under 150 words, conversational, and always end with a question to keep the dialogue going."""

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
