"""LLM service - Abstraction layer for multiple LLM providers."""

from typing import Optional

from app.core.config import settings
from app.core.logging import logger


class LLMService:
    """Unified LLM service supporting multiple providers."""

    def __init__(self) -> None:
        self.provider = settings.LLM_PROVIDER

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Generate a response using the configured LLM provider."""
        try:
            if self.provider == "gemini":
                return await self._generate_gemini(system_prompt, user_prompt, temperature, max_tokens)
            elif self.provider == "openai":
                return await self._generate_openai(system_prompt, user_prompt, temperature, max_tokens)
            elif self.provider == "claude":
                return await self._generate_claude(system_prompt, user_prompt, temperature, max_tokens)
            else:
                return self._generate_fallback(user_prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback(user_prompt)

    async def _generate_gemini(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Generate response using Google Gemini API."""
        import httpx

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("GEMINI_API_KEY not set, using fallback")
            return self._generate_fallback(user_prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                return parts[0].get("text", "I'm sorry, I couldn't generate a response.")

        return "I'm sorry, I couldn't generate a response."

    async def _generate_openai(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Generate response using OpenAI API."""
        import httpx

        api_key = settings.OPENAI_API_KEY
        if not api_key:
            return self._generate_fallback(user_prompt)

        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]

    async def _generate_claude(
        self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int
    ) -> str:
        """Generate response using Anthropic Claude API."""
        import httpx

        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return self._generate_fallback(user_prompt)

        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return data["content"][0]["text"]

    def _generate_fallback(self, user_prompt: str) -> str:
        """Fallback response when no LLM is available."""
        lower = user_prompt.lower()
        if any(kw in lower for kw in ["price", "cost", "buy", "plan"]):
            return (
                "Thank you for your interest! We'd love to tell you more about our pricing. "
                "Would you like to schedule a demo to see our plans in detail?"
            )
        if any(kw in lower for kw in ["help", "issue", "problem", "support"]):
            return (
                "I'm sorry to hear you're having an issue. Our support team is here to help! "
                "Could you describe the problem in more detail?"
            )
        if any(kw in lower for kw in ["book", "schedule", "demo", "meeting"]):
            return (
                "I'd be happy to help you book a demo! "
                "Please let me know your preferred date and time."
            )
        return (
            "Thank you for reaching out to Munesh AI! "
            "How can I assist you today? I can help with product information, "
            "support questions, or booking a demo."
        )


# Singleton instance
llm_service = LLMService()
