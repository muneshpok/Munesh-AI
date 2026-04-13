"""Tests for analytics engine and daily loop."""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import Lead, LeadStatus, Message, AgentDecision, DailyReport, AutomationLog
from app.services.analytics import AnalyticsEngine
from app.services.daily_loop import DailyLoop


# Use separate test database
TEST_DATABASE_URL = "sqlite:///./test_analytics.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables for each test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    """Provide a test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def analytics():
    return AnalyticsEngine()


def _create_lead(db, phone: str, name: str = "Test", status: LeadStatus = LeadStatus.NEW) -> Lead:
    lead = Lead(phone=phone, name=name, status=status, source="whatsapp")
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def _create_message(
    db, phone: str, direction: str = "inbound", content: str = "Hello",
    agent_type: str | None = None,
) -> Message:
    msg = Message(
        phone=phone, direction=direction, content=content,
        message_type="text", agent_type=agent_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def _create_decision(db, phone: str, intent: str = "chat") -> AgentDecision:
    decision = AgentDecision(
        phone=phone, intent=intent, action="respond",
        response="Test response",
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


class TestFunnelMetrics:
    """Test funnel metrics collection."""

    def test_empty_funnel(self, db, analytics) -> None:
        result = analytics.get_funnel_metrics(db)
        assert result["total"] == 0
        assert result["conversion_rate"] == 0.0

    def test_funnel_with_leads(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.NEW)
        _create_lead(db, "222", status=LeadStatus.CONTACTED)
        _create_lead(db, "333", status=LeadStatus.DEMO_BOOKED)
        _create_lead(db, "444", status=LeadStatus.CLOSED)

        result = analytics.get_funnel_metrics(db)
        assert result["total"] == 4
        assert result["stages"]["new"]["count"] == 1
        assert result["stages"]["contacted"]["count"] == 1
        assert result["stages"]["demo_booked"]["count"] == 1
        assert result["stages"]["closed"]["count"] == 1
        assert result["conversion_rate"] == 25.0

    def test_funnel_percentages(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.NEW)
        _create_lead(db, "222", status=LeadStatus.NEW)

        result = analytics.get_funnel_metrics(db)
        assert result["stages"]["new"]["percentage"] == 100.0
        assert result["stages"]["new"]["count"] == 2


class TestMessageActivity:
    """Test message activity analysis."""

    def test_empty_activity(self, db, analytics) -> None:
        result = analytics.get_message_activity(db, days=1)
        assert result["messages_sent"] == 0
        assert result["messages_received"] == 0
        assert result["active_conversations"] == 0

    def test_activity_with_messages(self, db, analytics) -> None:
        _create_message(db, "111", "inbound", "Hello")
        _create_message(db, "111", "outbound", "Hi there", agent_type="chat")
        _create_message(db, "222", "inbound", "Help me")

        result = analytics.get_message_activity(db, days=1)
        assert result["messages_received"] == 2
        assert result["messages_sent"] == 1
        assert result["total_messages"] == 3
        assert result["active_conversations"] == 2


class TestAgentPerformance:
    """Test agent performance analysis."""

    def test_empty_performance(self, db, analytics) -> None:
        result = analytics.get_agent_performance(db, days=1)
        assert result["total_decisions"] == 0
        assert result["breakdown"] == {}

    def test_performance_with_decisions(self, db, analytics) -> None:
        _create_decision(db, "111", "sales")
        _create_decision(db, "222", "sales")
        _create_decision(db, "333", "support")

        result = analytics.get_agent_performance(db, days=1)
        assert result["total_decisions"] == 3
        assert result["breakdown"]["sales"] == 2
        assert result["breakdown"]["support"] == 1


class TestStaleLead:
    """Test stale lead detection."""

    def test_no_stale_leads_when_empty(self, db, analytics) -> None:
        result = analytics.find_stale_leads(db, stale_hours=24)
        assert result == []

    def test_recent_lead_not_stale(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.CONTACTED)
        _create_message(db, "111", "inbound", "Hello")  # recent message

        result = analytics.find_stale_leads(db, stale_hours=24)
        assert len(result) == 0

    def test_closed_leads_excluded(self, db, analytics) -> None:
        lead = _create_lead(db, "111", status=LeadStatus.CLOSED)
        # Even if old, closed leads shouldn't be flagged
        result = analytics.find_stale_leads(db, stale_hours=0)
        assert len(result) == 0


class TestLeadScoring:
    """Test lead scoring logic."""

    def test_score_nonexistent_lead(self, db, analytics) -> None:
        score = analytics.calculate_lead_score(db, "nonexistent")
        assert score == 0

    def test_score_new_lead_no_messages(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.NEW)
        score = analytics.calculate_lead_score(db, "111")
        # NEW status = 5 points, recent creation might add recency points
        assert score >= 5

    def test_score_increases_with_messages(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.CONTACTED)
        score_before = analytics.calculate_lead_score(db, "111")

        _create_message(db, "111", "inbound", "Hi")
        _create_message(db, "111", "outbound", "Hello")
        score_after = analytics.calculate_lead_score(db, "111")

        assert score_after > score_before

    def test_score_demo_booked_high(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.DEMO_BOOKED)
        _create_message(db, "111", "inbound", "Book demo")
        _create_message(db, "111", "outbound", "Scheduled")

        score = analytics.calculate_lead_score(db, "111")
        assert score >= 40  # demo_booked (25) + messages + recency

    def test_score_all_leads(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.NEW)
        _create_lead(db, "222", status=LeadStatus.CONTACTED)

        scored = analytics.score_all_leads(db)
        assert scored == 2

        lead1 = db.query(Lead).filter(Lead.phone == "111").first()
        lead2 = db.query(Lead).filter(Lead.phone == "222").first()
        assert lead1.lead_score >= 0
        assert lead2.lead_score >= 0

    def test_score_capped_at_100(self, db, analytics) -> None:
        _create_lead(db, "111", status=LeadStatus.CLOSED)
        for i in range(20):
            _create_message(db, "111", "inbound", f"msg {i}")
        score = analytics.calculate_lead_score(db, "111")
        assert score <= 100


class TestInsightGeneration:
    """Test insight and recommendation generation."""

    def test_insights_empty_system(self, analytics) -> None:
        funnel = {"total": 0, "stages": {}, "conversion_rate": 0}
        activity = {"total_messages": 0}
        agent_perf = {"breakdown": {}, "total_decisions": 0}

        insights = analytics.generate_insights(funnel, activity, agent_perf, [])
        assert len(insights) > 0
        assert any("lead acquisition" in i.lower() for i in insights)

    def test_insights_with_stale_leads(self, analytics) -> None:
        funnel = {"total": 5, "stages": {"new": {"count": 2, "percentage": 40}}, "conversion_rate": 0}
        activity = {"total_messages": 10, "messages_received": 5, "messages_sent": 5}
        agent_perf = {"breakdown": {"sales": 3}, "total_decisions": 3}
        stale = [{"phone": "111", "name": "Test", "status": "contacted", "hours_since_activity": 48}]

        insights = analytics.generate_insights(funnel, activity, agent_perf, stale)
        assert any("inactive" in i.lower() or "follow-up" in i.lower() for i in insights)

    def test_recommendations_with_new_leads(self, analytics) -> None:
        funnel = {"total": 3, "stages": {"new": {"count": 2, "percentage": 66}}, "conversion_rate": 0}
        activity = {"total_messages": 5}
        stale: list = []

        recs = analytics.generate_recommendations(funnel, stale, activity)
        assert any("welcome" in r.lower() or "new lead" in r.lower() for r in recs)


class TestDailyLoop:
    """Test the daily loop orchestrator."""

    @pytest.mark.asyncio
    async def test_run_empty_system(self, db) -> None:
        loop = DailyLoop()
        report = await loop.run(db)

        assert report.id is not None
        assert report.total_leads == 0
        assert report.conversion_rate == 0.0
        assert report.insights is not None
        assert report.actions_taken is not None

    @pytest.mark.asyncio
    async def test_run_with_leads(self, db) -> None:
        _create_lead(db, "111", name="Alice", status=LeadStatus.CONTACTED)
        _create_lead(db, "222", name="Bob", status=LeadStatus.DEMO_BOOKED)
        _create_message(db, "111", "inbound", "Hello")
        _create_message(db, "111", "outbound", "Hi", agent_type="chat")
        _create_decision(db, "111", "chat")

        loop = DailyLoop()
        report = await loop.run(db)

        assert report.total_leads == 2
        assert report.contacted_leads == 1
        assert report.demo_booked == 1
        assert report.leads_scored == 2
        assert "Scored 2 lead(s)" in report.actions_taken

    @pytest.mark.asyncio
    async def test_run_scores_leads(self, db) -> None:
        _create_lead(db, "111", status=LeadStatus.CONTACTED)
        _create_message(db, "111", "inbound", "Hi")

        loop = DailyLoop()
        await loop.run(db)

        lead = db.query(Lead).filter(Lead.phone == "111").first()
        assert lead.lead_score > 0

    @pytest.mark.asyncio
    async def test_run_creates_automation_logs(self, db) -> None:
        _create_lead(db, "111", status=LeadStatus.CONTACTED)

        loop = DailyLoop()
        await loop.run(db)

        logs = db.query(AutomationLog).all()
        assert len(logs) > 0
        score_logs = [l for l in logs if l.action_type == "score"]
        assert len(score_logs) == 1

    @pytest.mark.asyncio
    async def test_run_saves_report(self, db) -> None:
        loop = DailyLoop()
        await loop.run(db)

        reports = db.query(DailyReport).all()
        assert len(reports) == 1
        assert reports[0].report_date == datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @pytest.mark.asyncio
    async def test_nurtures_new_leads(self, db) -> None:
        _create_lead(db, "111", name="New User", status=LeadStatus.NEW)

        loop = DailyLoop()
        await loop.run(db)

        # Should have moved from NEW to CONTACTED
        lead = db.query(Lead).filter(Lead.phone == "111").first()
        assert lead.status == LeadStatus.CONTACTED

        # Should have nurture log
        nurture_logs = db.query(AutomationLog).filter(AutomationLog.action_type == "nurture").all()
        assert len(nurture_logs) == 1

    @pytest.mark.asyncio
    async def test_follow_up_messages(self) -> None:
        """Test follow-up message generation."""
        loop = DailyLoop()
        msg = loop._get_follow_up_message("contacted", "Alice")
        assert "Alice" in msg
        assert "following up" in msg.lower() or "conversation" in msg.lower()

        msg_unknown = loop._get_follow_up_message("new", "")
        assert "Hi there" in msg_unknown


class TestAnalyticsAPI:
    """Test analytics API endpoints."""

    def setup_method(self) -> None:
        from app.main import app
        from app.core.database import get_db
        from fastapi.testclient import TestClient

        Base.metadata.create_all(bind=test_engine)

        def override_get_db():
            db = TestSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def teardown_method(self) -> None:
        Base.metadata.drop_all(bind=test_engine)

    def test_get_insights(self) -> None:
        response = self.client.get("/api/analytics/insights")
        assert response.status_code == 200
        data = response.json()
        assert "funnel" in data
        assert "engagement" in data
        assert "agent_performance" in data
        assert "recommendations" in data

    def test_get_daily_report_empty(self) -> None:
        response = self.client.get("/api/analytics/daily-report")
        assert response.status_code == 200
        # No reports yet, returns null
        assert response.json() is None

    def test_run_loop_api(self) -> None:
        response = self.client.post("/api/analytics/run-loop")
        assert response.status_code == 200
        data = response.json()
        assert "report_date" in data
        assert "insights" in data
        assert "actions_taken" in data

    def test_get_report_after_run(self) -> None:
        self.client.post("/api/analytics/run-loop")
        response = self.client.get("/api/analytics/daily-report")
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert "report_date" in data

    def test_list_reports(self) -> None:
        self.client.post("/api/analytics/run-loop")
        response = self.client.get("/api/analytics/reports")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_automation_logs(self) -> None:
        self.client.post("/api/analytics/run-loop")
        response = self.client.get("/api/analytics/automation-logs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
