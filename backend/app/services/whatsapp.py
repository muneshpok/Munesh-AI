"""WhatsApp Cloud API service."""

from typing import Optional

import httpx

from app.core.config import settings
from app.core.logging import logger


class WhatsAppService:
    """Service for interacting with WhatsApp Cloud API."""

    def __init__(self) -> None:
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_ACCESS_TOKEN

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    @property
    def _messages_url(self) -> str:
        return f"{self.api_url}/{self.phone_number_id}/messages"

    async def send_text_message(self, phone: str, text: str) -> dict:
        """Send a text message via WhatsApp Cloud API."""
        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp credentials not configured, skipping send")
            return {"status": "skipped", "reason": "credentials_not_configured"}

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": text},
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    self._messages_url, json=payload, headers=self._headers
                )
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"WhatsApp message sent to {phone}: {data}")
                return data
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.status_code} - {e.response.text}")
            return {"status": "error", "detail": str(e)}
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {"status": "error", "detail": str(e)}

    async def send_template_message(
        self, phone: str, template_name: str, language: str = "en_US"
    ) -> dict:
        """Send a template message via WhatsApp Cloud API."""
        if not self.access_token or not self.phone_number_id:
            logger.warning("WhatsApp credentials not configured, skipping send")
            return {"status": "skipped", "reason": "credentials_not_configured"}

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    self._messages_url, json=payload, headers=self._headers
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.error(f"WhatsApp template send failed: {e}")
            return {"status": "error", "detail": str(e)}

    @staticmethod
    def parse_webhook_payload(payload: dict) -> Optional[dict]:
        """Parse incoming WhatsApp webhook payload and extract message info."""
        try:
            entry = payload.get("entry", [])
            if not entry:
                return None

            changes = entry[0].get("changes", [])
            if not changes:
                return None

            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None

            msg = messages[0]
            contacts = value.get("contacts", [])
            contact = contacts[0] if contacts else {}

            return {
                "phone": msg.get("from", ""),
                "message_id": msg.get("id", ""),
                "timestamp": msg.get("timestamp", ""),
                "type": msg.get("type", "text"),
                "text": msg.get("text", {}).get("body", ""),
                "contact_name": contact.get("profile", {}).get("name", ""),
            }
        except (IndexError, KeyError, TypeError) as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return None


# Singleton instance
whatsapp_service = WhatsAppService()
