"""Booking Agent - Handles scheduling and demo bookings."""

from typing import List

from app.agents.base import BaseAgent
from app.models.schemas import AgentDecisionSchema, IntentEnum, ActionEnum
from app.services.llm import llm_service
from app.core.logging import logger


class BookingAgent(BaseAgent):
    """Handles appointment scheduling, demo bookings, and calendar management."""

    agent_type = "booking"

    SYSTEM_PROMPT = """You are Munesh AI Booking Assistant on WhatsApp.
Your goals:
1. Help users schedule demos and appointments
2. Confirm booking details
3. Send scheduling links
4. Update the user's CRM status

When the user wants to book, ask for:
- Preferred date and time
- Their name (if not known)
- Purpose of the meeting

Keep responses friendly and under 150 words."""

    async def process(self, phone: str, message: str, history: List[dict]) -> AgentDecisionSchema:
        """Process a booking-related message."""
        logger.info(f"BookingAgent processing message from {phone}")

        context = self._build_context(history)
        prompt = f"""Previous conversation:
{context}

User message: {message}

Help the user book a demo or appointment. If they've provided enough info,
confirm the booking and include "BOOK_CONFIRMED" in your response."""

        response = await llm_service.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        is_confirmed = "BOOK_CONFIRMED" in response
        clean_response = response.replace("BOOK_CONFIRMED", "").strip()

        if is_confirmed:
            return AgentDecisionSchema(
                intent=IntentEnum.BOOKING,
                action=ActionEnum.CALL_TOOL,
                tool_name="send_demo_link",
                parameters={"phone": phone},
                response=clean_response,
            )

        return AgentDecisionSchema(
            intent=IntentEnum.BOOKING,
            action=ActionEnum.RESPOND,
            tool_name=None,
            parameters=None,
            response=clean_response,
        )
