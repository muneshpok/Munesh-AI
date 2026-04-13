"""Sales Agent - Detects buying intent and drives conversions."""

from typing import List

from app.agents.base import BaseAgent
from app.models.schemas import AgentDecisionSchema, IntentEnum, ActionEnum
from app.services.llm import llm_service
from app.core.logging import logger


class SalesAgent(BaseAgent):
    """Handles sales-related queries, detects buying intent, pushes demo bookings."""

    agent_type = "sales"

    SYSTEM_PROMPT = """You are Munesh AI Sales Assistant on WhatsApp.
Your goals:
1. Understand the user's needs
2. Explain relevant products/services
3. Highlight key benefits and features
4. Guide them toward booking a demo or making a purchase
5. Be persuasive but not pushy

If the user shows strong buying intent, suggest booking a demo.
Keep responses under 200 words and use bullet points for features."""

    async def process(self, phone: str, message: str, history: List[dict]) -> AgentDecisionSchema:
        """Process a sales-related message."""
        logger.info(f"SalesAgent processing message from {phone}")

        context = self._build_context(history)
        prompt = f"""Previous conversation:
{context}

User message: {message}

Respond as a sales assistant. If the user seems ready to buy or wants a demo,
include "SUGGEST_DEMO" at the end of your response."""

        response = await llm_service.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        # Check if we should trigger demo booking
        should_book_demo = "SUGGEST_DEMO" in response
        clean_response = response.replace("SUGGEST_DEMO", "").strip()

        if should_book_demo:
            return AgentDecisionSchema(
                intent=IntentEnum.SALES,
                action=ActionEnum.CALL_TOOL,
                tool_name="send_demo_link",
                parameters={"phone": phone},
                response=clean_response,
            )

        return AgentDecisionSchema(
            intent=IntentEnum.SALES,
            action=ActionEnum.RESPOND,
            tool_name=None,
            parameters=None,
            response=clean_response,
        )
