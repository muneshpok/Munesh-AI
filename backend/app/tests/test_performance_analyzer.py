"""Tests for Performance Analyzer service and API endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models.models import Lead, LeadStatus, Message
from app.services.performance_analyzer import PerformanceAnalyzer


# Test database setup — use unique file to avoid collisions with other test modules
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_performance_analyzer.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


def _setup_test_db():
    """Create all tables for a fresh test database."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class TestPerformanceAnalyzer:
    """Test the PerformanceAnalyzer service."""

    def setup_method(self):
        _setup_test_db()
        self.analyzer = PerformanceAnalyzer()

    def _seed_leads(self, db):
        """Seed test leads with different statuses."""
        leads = [
            Lead(phone="1111", name="Alice", status=LeadStatus.CONTACTED, source="whatsapp"),
            Lead(phone="2222", name="Bob", status=LeadStatus.DEMO_BOOKED, source="whatsapp"),
            Lead(phone="3333", name="Charlie", status=LeadStatus.CLOSED, source="whatsapp"),
            Lead(phone="4444", name="Diana", status=LeadStatus.NEW, source="whatsapp"),
            Lead(phone="5555", name="Eve", status=LeadStatus.LOST, source="whatsapp"),
        ]
        for lead in leads:
            db.add(lead)
        db.commit()
        return leads

    def _seed_messages(self, db):
        """Seed test messages."""
        messages = [
            Message(phone="1111", direction="inbound", content="Hello", message_type="text"),
            Message(phone="1111", direction="outbound", content="Hi!", message_type="text", agent_type="chat"),
            Message(phone="2222", direction="inbound", content="I want a demo", message_type="text"),
            Message(phone="2222", direction="outbound", content="Sure!", message_type="text", agent_type="booking"),
            Message(phone="3333", direction="inbound", content="Buy now", message_type="text"),
            Message(phone="3333", direction="outbound", content="Great!", message_type="text", agent_type="sales"),
            Message(phone="4444", direction="inbound", content="Info please", message_type="text"),
        ]
        for msg in messages:
            db.add(msg)
        db.commit()

    def test_analyze_empty_db(self):
        """Test analysis with no leads."""
        db = TestingSessionLocal()
        try:
            result = self.analyzer.analyze_performance(db)
            assert result["total_leads"] == 0
            assert result["conversion_rate"] == 0
            assert result["close_rate"] == 0
            assert result["total_messages"] == 0
            assert result["avg_messages_per_lead"] == 0
            assert "analyzed_at" in result
        finally:
            db.close()

    def test_analyze_with_leads(self):
        """Test analysis returns correct metrics."""
        db = TestingSessionLocal()
        try:
            self._seed_leads(db)
            self._seed_messages(db)
            result = self.analyzer.analyze_performance(db)

            assert result["total_leads"] == 5
            assert result["booked"] == 1
            assert result["closed"] == 1
            assert result["lost"] == 1
            assert result["conversion_rate"] == 20.0
            assert result["close_rate"] == 20.0
            assert result["loss_rate"] == 20.0
            assert result["total_messages"] == 7
            assert result["inbound_messages"] == 4
            assert result["outbound_messages"] == 3
            assert result["avg_messages_per_lead"] == 1.4
        finally:
            db.close()

    def test_status_breakdown(self):
        """Test that status breakdown counts are correct."""
        db = TestingSessionLocal()
        try:
            self._seed_leads(db)
            result = self.analyzer.analyze_performance(db)

            breakdown = result["status_breakdown"]
            assert breakdown["new"] == 1
            assert breakdown["contacted"] == 1
            assert breakdown["demo_booked"] == 1
            assert breakdown["closed"] == 1
            assert breakdown["lost"] == 1
            assert breakdown["follow_up"] == 0
        finally:
            db.close()

    def test_fallback_suggestions_low_conversion(self):
        """Test fallback suggestions when conversion is low."""
        metrics = {
            "total_leads": 10,
            "booked": 1,
            "closed": 0,
            "lost": 5,
            "conversion_rate": 10.0,
            "close_rate": 0.0,
            "loss_rate": 50.0,
            "total_messages": 15,
            "avg_messages_per_lead": 1.5,
        }
        result = self.analyzer._generate_fallback_suggestions(metrics)
        assert "Sales Messages" in result
        assert "below 20%" in result
        assert "Follow-ups" in result
        assert "Conversion Optimization" in result
        assert "High loss rate" in result

    def test_fallback_suggestions_moderate_conversion(self):
        """Test fallback suggestions with moderate conversion."""
        metrics = {
            "total_leads": 10,
            "booked": 3,
            "closed": 2,
            "lost": 1,
            "conversion_rate": 30.0,
            "close_rate": 20.0,
            "loss_rate": 10.0,
            "total_messages": 50,
            "avg_messages_per_lead": 5.0,
        }
        result = self.analyzer._generate_fallback_suggestions(metrics)
        assert "A/B test" in result
        assert "Optimize timing" in result

    def test_fallback_suggestions_no_bookings(self):
        """Test fallback suggestions when no demos booked."""
        metrics = {
            "total_leads": 5,
            "booked": 0,
            "closed": 0,
            "lost": 0,
            "conversion_rate": 0.0,
            "close_rate": 0.0,
            "loss_rate": 0.0,
            "total_messages": 10,
            "avg_messages_per_lead": 2.0,
        }
        result = self.analyzer._generate_fallback_suggestions(metrics)
        assert "No demos booked" in result
        assert "scheduling links" in result

    @pytest.mark.asyncio
    async def test_generate_improvements_returns_string(self):
        """Test that generate_improvements returns a non-empty string (LLM or fallback)."""
        metrics = {
            "total_leads": 5,
            "booked": 1,
            "closed": 0,
            "lost": 2,
            "conversion_rate": 20.0,
            "close_rate": 0.0,
            "loss_rate": 40.0,
            "total_messages": 10,
            "avg_messages_per_lead": 2.0,
        }
        result = await self.analyzer.generate_improvements(metrics)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_run_analysis(self):
        """Test full analysis pipeline."""
        db = TestingSessionLocal()
        try:
            self._seed_leads(db)
            self._seed_messages(db)
            result = await self.analyzer.run_analysis(db)

            assert "metrics" in result
            assert "suggestions" in result
            assert "log" in result
            assert result["metrics"]["total_leads"] == 5
            assert result["log"]["status"] == "logged"
            assert isinstance(result["suggestions"], str)
        finally:
            db.close()

    def test_apply_improvements(self):
        """Test that improvements are logged."""
        result = self.analyzer.apply_improvements("Test suggestions")
        assert result["status"] == "logged"
        assert "timestamp" in result
        assert result["suggestions"] == "Test suggestions"


class TestPerformanceAPI:
    """Test the Performance Analyzer API endpoints."""

    def setup_method(self):
        _setup_test_db()
        app.dependency_overrides[get_db] = override_get_db

    def teardown_method(self):
        app.dependency_overrides.pop(get_db, None)

    def _seed_data(self):
        """Seed test data for API tests."""
        db = TestingSessionLocal()
        leads = [
            Lead(phone="1111", name="Alice", status=LeadStatus.CONTACTED, source="whatsapp"),
            Lead(phone="2222", name="Bob", status=LeadStatus.DEMO_BOOKED, source="whatsapp"),
            Lead(phone="3333", name="Charlie", status=LeadStatus.NEW, source="whatsapp"),
        ]
        messages = [
            Message(phone="1111", direction="inbound", content="Hi", message_type="text"),
            Message(phone="1111", direction="outbound", content="Hello!", message_type="text", agent_type="chat"),
            Message(phone="2222", direction="inbound", content="Book demo", message_type="text"),
        ]
        for item in leads + messages:
            db.add(item)
        db.commit()
        db.close()

    def test_get_metrics_empty(self):
        """Test GET /api/performance/metrics with no data."""
        response = client.get("/api/performance/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == 0
        assert data["conversion_rate"] == 0

    def test_get_metrics_with_data(self):
        """Test GET /api/performance/metrics with seeded data."""
        self._seed_data()
        response = client.get("/api/performance/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == 3
        assert data["booked"] == 1
        assert data["total_messages"] == 3
        assert data["inbound_messages"] == 2
        assert data["outbound_messages"] == 1

    def test_get_suggestions(self):
        """Test GET /api/performance/suggestions."""
        self._seed_data()
        response = client.get("/api/performance/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "suggestions" in data
        assert isinstance(data["suggestions"], str)
        assert len(data["suggestions"]) > 0

    def test_run_full_analysis(self):
        """Test POST /api/performance/analyze."""
        self._seed_data()
        response = client.post("/api/performance/analyze")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "suggestions" in data
        assert "log" in data
        assert data["metrics"]["total_leads"] == 3
        assert data["log"]["status"] == "logged"

    def test_metrics_conversion_calculation(self):
        """Test that conversion rate is calculated correctly."""
        db = TestingSessionLocal()
        leads = [
            Lead(phone="a", name="A", status=LeadStatus.DEMO_BOOKED, source="whatsapp"),
            Lead(phone="b", name="B", status=LeadStatus.DEMO_BOOKED, source="whatsapp"),
            Lead(phone="c", name="C", status=LeadStatus.NEW, source="whatsapp"),
            Lead(phone="d", name="D", status=LeadStatus.CONTACTED, source="whatsapp"),
        ]
        for lead in leads:
            db.add(lead)
        db.commit()
        db.close()

        response = client.get("/api/performance/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == 4
        assert data["booked"] == 2
        assert data["conversion_rate"] == 50.0
