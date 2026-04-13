"""Tests for the FastAPI application endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_munesh_ai.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


def _setup_test_db():
    """Ensure test DB tables exist and override is set."""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=test_engine)


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def setup_method(self) -> None:
        _setup_test_db()

    def test_root(self) -> None:
        """Test root endpoint returns app info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "Munesh AI"
        assert data["status"] == "running"

    def test_health_check(self) -> None:
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestWhatsAppWebhook:
    """Test WhatsApp webhook endpoints."""

    def setup_method(self) -> None:
        _setup_test_db()

    def test_webhook_verification_success(self) -> None:
        """Test successful webhook verification."""
        response = client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "munesh_ai_verify_token",
                "hub.challenge": "12345",
            },
        )
        assert response.status_code == 200
        assert response.json() == 12345

    def test_webhook_verification_failure(self) -> None:
        """Test failed webhook verification."""
        response = client.get(
            "/whatsapp/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "12345",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_webhook_receive_message(self) -> None:
        """Test receiving a WhatsApp message."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "1234567890",
                                        "id": "wamid.test",
                                        "timestamp": "1234567890",
                                        "type": "text",
                                        "text": {"body": "Hello"},
                                    }
                                ],
                                "contacts": [
                                    {
                                        "profile": {"name": "Test"},
                                        "wa_id": "1234567890",
                                    }
                                ],
                            }
                        }
                    ]
                }
            ]
        }
        response = client.post("/whatsapp/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_webhook_empty_payload(self) -> None:
        """Test webhook with empty payload."""
        response = client.post("/whatsapp/webhook", json={})
        assert response.status_code == 200

    def test_webhook_status_update(self) -> None:
        """Test webhook with status update (no message)."""
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {"id": "wamid.test", "status": "delivered"}
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        response = client.post("/whatsapp/webhook", json=payload)
        assert response.status_code == 200


class TestCRMEndpoints:
    """Test CRM API endpoints."""

    def setup_method(self) -> None:
        _setup_test_db()

    def test_get_leads(self) -> None:
        """Test getting leads."""
        response = client.get("/api/leads")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_metrics(self) -> None:
        """Test getting dashboard metrics."""
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_leads" in data
        assert "conversion_rate" in data
        assert "messages_today" in data

    def test_update_status_not_found(self) -> None:
        """Test updating status for non-existent lead."""
        response = client.post(
            "/api/update-status",
            json={"phone": "nonexistent_phone_99999", "status": "contacted"},
        )
        assert response.status_code == 404
