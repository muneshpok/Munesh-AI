"""Tests for WhatsApp webhook parsing and processing."""

import pytest
from app.services.whatsapp import WhatsAppService


class TestWebhookParsing:
    """Test WhatsApp webhook payload parsing."""

    def setup_method(self) -> None:
        self.service = WhatsAppService()

    def test_parse_valid_text_message(self) -> None:
        """Test parsing a valid text message webhook payload."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "wamid.test123",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello, I need help"},
                                    }
                                ],
                                "contacts": [
                                    {
                                        "profile": {"name": "Test User"},
                                        "wa_id": "1234567890",
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }

        result = self.service.parse_webhook_payload(payload)
        assert result is not None
        assert result["phone"] == "1234567890"
        assert result["text"] == "Hello, I need help"
        assert result["message_id"] == "wamid.test123"
        assert result["contact_name"] == "Test User"
        assert result["type"] == "text"

    def test_parse_empty_payload(self) -> None:
        """Test parsing an empty payload."""
        assert self.service.parse_webhook_payload({}) is None
        assert self.service.parse_webhook_payload({"entry": []}) is None

    def test_parse_status_update(self) -> None:
        """Test parsing a status update (no message)."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": "wamid.test",
                                        "status": "delivered",
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        result = self.service.parse_webhook_payload(payload)
        assert result is None

    def test_parse_payload_no_contacts(self) -> None:
        """Test parsing a payload with missing contacts."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "9876543210",
                                        "id": "wamid.test456",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hi"},
                                    }
                                ],
                                "contacts": [],
                            }
                        }
                    ]
                }
            ]
        }
        result = self.service.parse_webhook_payload(payload)
        assert result is not None
        assert result["phone"] == "9876543210"
        assert result["text"] == "Hi"
