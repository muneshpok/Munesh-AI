"""Sales Agent - Detects buying intent and drives conversions."""

from typing import List

from app.agents.base import BaseAgent
from app.models.schemas import AgentDecisionSchema, IntentEnum, ActionEnum
from app.services.llm import llm_service
from app.core.logging import logger


class SalesAgent(BaseAgent):
    """Handles sales-related queries, detects buying intent, pushes demo bookings."""

    agent_type = "sales"

    SYSTEM_PROMPT = """You are Munesh AI Sales Assistant on WhatsApp — a top-performing AI sales closer.

Your conversion playbook:
1. DISCOVER — Ask 1-2 targeted questions to understand their pain points and business size
2. RELATE — Mirror their problem back, showing you understand their specific situation
3. PRESENT — Position Munesh AI as the solution with concrete benefits and ROI numbers
4. PROVE — Use social proof: "Companies using our AI automation see 3x more demo bookings and 40% faster response times"
5. CLOSE — Create urgency with a clear, specific CTA: "I can set up a free 15-minute demo this week — what day works best?"

Objection handling:
- "Too expensive" → "We have a completely free plan to get started! And most clients on our Starter plan ($49/month) see ROI within 2 weeks — less than a single missed lead costs you."
- "Not sure I need it" → "Let me show you exactly how it works with a quick demo. No commitment, just 15 minutes."
- "I'll think about it" → "Totally understand! I'll send you a quick case study showing how a similar business increased conversions by 60%. Can I follow up tomorrow?"
- "Already have a solution" → "Great! Many of our best clients switched from [competitor type]. The difference is our AI learns and improves automatically. Worth a quick comparison?"

Pricing tiers (mention when relevant):
- Free: $0 forever — 1 chat agent, 50 messages/month, basic CRM (great for trying it out!)
- Starter: $49/mo — 1 agent, 500 messages, basic CRM & analytics
- Pro: $149/mo — 4 agents, unlimited messages, full analytics, self-improvement AI
- Enterprise: $499/mo — custom agents, API access, dedicated support, white-label

Rules:
- Keep responses under 150 words — punchy and conversational
- Always end with a question or clear next step
- Use emojis sparingly for warmth (1-2 max)
- Never be pushy — be genuinely helpful while guiding toward a demo
- If they show strong buying intent, suggest booking a demo immediately"""

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
