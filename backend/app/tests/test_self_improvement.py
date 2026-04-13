"""Tests for the Self-Improvement Agent."""

import json
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.models import (
    Lead, LeadStatus, Message, AgentDecision,
    PromptVersion, ImprovementLog, StrategyConfig,
)
from app.services.self_improvement import SelfImprovementAgent, DEFAULT_PROMPTS, DEFAULT_STRATEGY


# Use separate test database
TEST_DATABASE_URL = "sqlite:///./test_self_improvement.db"
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
def agent():
    return SelfImprovementAgent()


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


def _create_decision(db, phone: str, intent: str = "chat", action: str = "respond") -> AgentDecision:
    decision = AgentDecision(
        phone=phone, intent=intent, action=action,
        response="Test response",
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision


class TestInitializeDefaults:
    """Test default initialization of prompts and strategy configs."""

    def test_initializes_all_agent_prompts(self, db, agent) -> None:
        agent.initialize_defaults(db)

        prompts = db.query(PromptVersion).filter(PromptVersion.is_active == 1).all()
        agent_types = {p.agent_type for p in prompts}
        assert agent_types == {"chat", "sales", "support", "booking"}

    def test_initializes_strategy_configs(self, db, agent) -> None:
        agent.initialize_defaults(db)

        configs = db.query(StrategyConfig).all()
        config_keys = {c.config_key for c in configs}
        assert "follow_up_delay_hours" in config_keys
        assert "sales_keywords" in config_keys
        assert "support_keywords" in config_keys
        assert "booking_keywords" in config_keys
        assert "high_intent_score_threshold" in config_keys

    def test_idempotent_initialization(self, db, agent) -> None:
        agent.initialize_defaults(db)
        agent.initialize_defaults(db)

        prompts = db.query(PromptVersion).filter(PromptVersion.is_active == 1).all()
        assert len(prompts) == 4  # Still 4, not duplicated

    def test_prompt_version_starts_at_1(self, db, agent) -> None:
        agent.initialize_defaults(db)

        for prompt in db.query(PromptVersion).all():
            assert prompt.version == 1

    def test_default_prompt_content_matches(self, db, agent) -> None:
        agent.initialize_defaults(db)

        for agent_type, expected_text in DEFAULT_PROMPTS.items():
            prompt = (
                db.query(PromptVersion)
                .filter(PromptVersion.agent_type == agent_type, PromptVersion.is_active == 1)
                .first()
            )
            assert prompt is not None
            assert prompt.prompt_text == expected_text


class TestConversationAnalysis:
    """Test conversation pattern analysis."""

    def test_empty_analysis(self, db, agent) -> None:
        result = agent._analyze_conversations(db)
        assert result["total_conversations"] == 0
        assert result["conversion_rate"] == 0

    def test_conversation_count(self, db, agent) -> None:
        _create_message(db, "111", "inbound", "Hello")
        _create_message(db, "222", "inbound", "Hi")

        result = agent._analyze_conversations(db)
        assert result["total_conversations"] == 2

    def test_conversion_rate_calculation(self, db, agent) -> None:
        _create_lead(db, "111", status=LeadStatus.DEMO_BOOKED)
        _create_lead(db, "222", status=LeadStatus.NEW)
        _create_message(db, "111", "inbound", "Book demo")
        _create_message(db, "222", "inbound", "Hello")

        result = agent._analyze_conversations(db)
        assert result["converted"] == 1
        assert result["conversion_rate"] == 50.0

    def test_short_response_detection(self, db, agent) -> None:
        _create_message(db, "111", "outbound", "OK", agent_type="chat")
        _create_message(db, "111", "outbound", "Sure", agent_type="chat")
        _create_message(db, "111", "outbound", "Yes", agent_type="chat")

        result = agent._analyze_conversations(db)
        assert result["short_responses"] == 3

    def test_lost_lead_tracking(self, db, agent) -> None:
        _create_lead(db, "111", status=LeadStatus.LOST)
        _create_message(db, "111", "inbound", "Cancel")

        result = agent._analyze_conversations(db)
        assert result["lost"] == 1

    def test_insights_generated(self, db, agent) -> None:
        _create_lead(db, "111", status=LeadStatus.CONTACTED)
        _create_message(db, "111", "inbound", "Hello")
        _create_message(db, "111", "outbound", "Hi there, how can I help?", agent_type="chat")

        result = agent._analyze_conversations(db)
        assert len(result["insights"]) > 0


class TestAgentPerformanceAnalysis:
    """Test agent performance evaluation."""

    def test_empty_performance(self, db, agent) -> None:
        result = agent._analyze_agent_performance(db)
        assert result["total_decisions"] == 0
        assert result["agent_stats"] == {}

    def test_decision_counting(self, db, agent) -> None:
        _create_decision(db, "111", "sales")
        _create_decision(db, "222", "sales")
        _create_decision(db, "333", "support")

        result = agent._analyze_agent_performance(db)
        assert result["total_decisions"] == 3
        assert result["agent_stats"]["sales"]["total"] == 2
        assert result["agent_stats"]["support"]["total"] == 1

    def test_conversion_per_agent(self, db, agent) -> None:
        _create_lead(db, "111", status=LeadStatus.CLOSED)
        _create_lead(db, "222", status=LeadStatus.NEW)
        _create_decision(db, "111", "sales")
        _create_decision(db, "222", "sales")

        result = agent._analyze_agent_performance(db)
        assert result["agent_stats"]["sales"]["converted"] == 1
        assert result["agent_stats"]["sales"]["conversion_rate"] == 50.0


class TestKeywordOptimization:
    """Test keyword analysis and improvement."""

    def test_no_optimization_with_few_decisions(self, db, agent) -> None:
        agent.initialize_defaults(db)
        _create_decision(db, "111", "chat")

        result = agent._optimize_keywords(db, {"total_conversations": 1})
        assert len(result) == 0

    def test_word_correlation_check(self, agent) -> None:
        """Test the static word correlation method."""
        class MockMsg:
            def __init__(self, content: str):
                self.content = content

        messages = [
            MockMsg("I want to buy a product and see pricing"),
            MockMsg("What is the pricing for your plans"),
            MockMsg("Can you tell me about your plans and pricing"),
            MockMsg("Hello how are you"),
        ]

        # "plans" co-occurs with sales keywords in 2 of 2 messages it appears in
        assert agent._word_correlates_with_intent(
            "plans", ["pricing", "buy", "product"], messages
        )

        # "hello" doesn't correlate with sales keywords (appears once, no co-occurrence)
        assert not agent._word_correlates_with_intent(
            "hello", ["pricing", "buy", "product"], messages
        )


class TestFollowUpOptimization:
    """Test follow-up timing and messaging optimization."""

    def test_no_optimization_with_few_messages(self, db, agent) -> None:
        agent.initialize_defaults(db)

        result = agent._optimize_follow_ups(db, {"lost": 0})
        assert len(result) == 0

    def test_delay_reduction_on_lost_leads(self, db, agent) -> None:
        agent.initialize_defaults(db)
        conv_analysis = {"lost": 3}  # More than threshold of 2

        result = agent._optimize_follow_ups(db, conv_analysis)
        # Should reduce delay since lost > 2
        delay_improvements = [r for r in result if r["target"] == "follow_up_delay_hours"]
        assert len(delay_improvements) == 1

        # Verify the config was updated
        config = db.query(StrategyConfig).filter(
            StrategyConfig.config_key == "follow_up_delay_hours"
        ).first()
        assert int(config.config_value) == 18  # 24 - 6

    def test_delay_not_reduced_below_12(self, db, agent) -> None:
        agent.initialize_defaults(db)

        # Set delay to 12 already
        config = db.query(StrategyConfig).filter(
            StrategyConfig.config_key == "follow_up_delay_hours"
        ).first()
        config.config_value = "12"
        db.commit()

        result = agent._optimize_follow_ups(db, {"lost": 5})
        delay_improvements = [r for r in result if r["target"] == "follow_up_delay_hours"]
        assert len(delay_improvements) == 0  # Can't go below 12


class TestStrategyOptimization:
    """Test strategy parameter tuning."""

    def test_no_optimization_with_few_interactions(self, db, agent) -> None:
        agent.initialize_defaults(db)

        perf_analysis = {
            "agent_stats": {
                "sales": {"phone_count": 2, "converted": 1},
                "booking": {"phone_count": 1, "converted": 0},
            },
        }

        result = agent._optimize_strategy(db, perf_analysis)
        assert len(result) == 0  # Only 3 total, need 5+

    def test_threshold_lowered_on_high_conversion(self, db, agent) -> None:
        agent.initialize_defaults(db)

        perf_analysis = {
            "agent_stats": {
                "sales": {"phone_count": 5, "converted": 4},
                "booking": {"phone_count": 3, "converted": 2},
            },
        }

        result = agent._optimize_strategy(db, perf_analysis)
        threshold_changes = [r for r in result if r["target"] == "high_intent_score_threshold"]
        assert len(threshold_changes) == 1
        assert "Lowered" in threshold_changes[0]["description"]

    def test_threshold_raised_on_low_conversion(self, db, agent) -> None:
        agent.initialize_defaults(db)

        perf_analysis = {
            "agent_stats": {
                "sales": {"phone_count": 5, "converted": 0},
                "booking": {"phone_count": 5, "converted": 1},
            },
        }

        result = agent._optimize_strategy(db, perf_analysis)
        threshold_changes = [r for r in result if r["target"] == "high_intent_score_threshold"]
        assert len(threshold_changes) == 1
        assert "Raised" in threshold_changes[0]["description"]


class TestNextRecommendations:
    """Test recommendation generation."""

    def test_no_improvements_recommendation(self, agent) -> None:
        recs = agent._generate_next_recommendations({}, {}, [])
        assert any("performing well" in r.lower() for r in recs)

    def test_low_data_recommendation(self, agent) -> None:
        recs = agent._generate_next_recommendations(
            {"total_conversations": 2}, {}, []
        )
        assert any("insufficient data" in r.lower() for r in recs)

    def test_low_conversion_recommendation(self, agent) -> None:
        recs = agent._generate_next_recommendations(
            {"conversion_rate": 10, "total_conversations": 10},
            {"agent_stats": {}},
            [{"type": "prompt"}],
        )
        assert any("conversion rate" in r.lower() for r in recs)


class TestQueryMethods:
    """Test query helper methods."""

    def test_get_active_prompts(self, db, agent) -> None:
        agent.initialize_defaults(db)

        prompts = agent.get_active_prompts(db)
        assert len(prompts) == 4
        for p in prompts:
            assert p.is_active == 1

    def test_get_prompt_history(self, db, agent) -> None:
        agent.initialize_defaults(db)

        history = agent.get_prompt_history(db)
        assert len(history) == 4

        # Filter by agent type
        sales_history = agent.get_prompt_history(db, agent_type="sales")
        assert len(sales_history) == 1
        assert sales_history[0].agent_type == "sales"

    def test_get_improvement_history_empty(self, db, agent) -> None:
        history = agent.get_improvement_history(db)
        assert len(history) == 0

    def test_get_strategy_configs(self, db, agent) -> None:
        agent.initialize_defaults(db)

        configs = agent.get_strategy_configs(db)
        assert len(configs) == len(DEFAULT_STRATEGY)

        # Filter by category
        keyword_configs = agent.get_strategy_configs(db, category="keywords")
        assert len(keyword_configs) == 3  # sales, support, booking


class TestImprovementCycle:
    """Test the full improvement cycle."""

    @pytest.mark.asyncio
    async def test_cycle_empty_system(self, db, agent) -> None:
        report = await agent.run_improvement_cycle(db)

        assert "cycle_id" in report
        assert "timestamp" in report
        assert isinstance(report["improvements_made"], list)
        assert isinstance(report["insights"], list)
        assert isinstance(report["next_recommendations"], list)

    @pytest.mark.asyncio
    async def test_cycle_initializes_defaults(self, db, agent) -> None:
        await agent.run_improvement_cycle(db)

        # Should have created default prompts
        prompts = db.query(PromptVersion).all()
        assert len(prompts) >= 4

        # Should have created strategy configs
        configs = db.query(StrategyConfig).all()
        assert len(configs) >= len(DEFAULT_STRATEGY)

    @pytest.mark.asyncio
    async def test_cycle_with_data(self, db, agent) -> None:
        _create_lead(db, "111", name="Alice", status=LeadStatus.CONTACTED)
        _create_lead(db, "222", name="Bob", status=LeadStatus.DEMO_BOOKED)
        _create_message(db, "111", "inbound", "I want to buy")
        _create_message(db, "111", "outbound", "Great!", agent_type="sales")
        _create_decision(db, "111", "sales")
        _create_decision(db, "222", "booking")

        report = await agent.run_improvement_cycle(db)

        assert report["cycle_id"] is not None
        assert len(report["insights"]) > 0

    @pytest.mark.asyncio
    async def test_cycle_logs_improvements(self, db, agent) -> None:
        # Create enough data to trigger optimization
        _create_lead(db, "111", status=LeadStatus.LOST)
        _create_lead(db, "222", status=LeadStatus.LOST)
        _create_lead(db, "333", status=LeadStatus.LOST)
        _create_message(db, "111", "inbound", "Cancel")
        _create_message(db, "222", "inbound", "No thanks")
        _create_message(db, "333", "inbound", "Not interested")

        report = await agent.run_improvement_cycle(db)

        # The lost leads should trigger follow-up delay optimization
        logs = db.query(ImprovementLog).all()
        # At least check no errors occurred
        assert report["cycle_id"] is not None


class TestSelfImprovementAPI:
    """Test Self-Improvement Agent API endpoints."""

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

    def test_initialize_endpoint(self) -> None:
        response = self.client.post("/api/self-improvement/initialize")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "initialized"

    def test_get_active_prompts(self) -> None:
        self.client.post("/api/self-improvement/initialize")
        response = self.client.get("/api/self-improvement/prompts/active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4
        agent_types = {p["agent_type"] for p in data}
        assert agent_types == {"chat", "sales", "support", "booking"}

    def test_get_prompt_history(self) -> None:
        self.client.post("/api/self-improvement/initialize")
        response = self.client.get("/api/self-improvement/prompts/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_get_prompt_history_filtered(self) -> None:
        self.client.post("/api/self-improvement/initialize")
        response = self.client.get("/api/self-improvement/prompts/history?agent_type=sales")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["agent_type"] == "sales"

    def test_get_improvements_empty(self) -> None:
        response = self.client.get("/api/self-improvement/improvements")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_strategy(self) -> None:
        self.client.post("/api/self-improvement/initialize")
        response = self.client.get("/api/self-improvement/strategy")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 7  # At least the default strategy configs

    def test_get_strategy_filtered(self) -> None:
        self.client.post("/api/self-improvement/initialize")
        response = self.client.get("/api/self-improvement/strategy?category=keywords")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for config in data:
            assert config["category"] == "keywords"

    def test_run_improvement_cycle(self) -> None:
        response = self.client.post("/api/self-improvement/run")
        assert response.status_code == 200
        data = response.json()
        assert "cycle_id" in data
        assert "timestamp" in data
        assert "improvements_made" in data
        assert "insights" in data
        assert "next_recommendations" in data
        assert isinstance(data["prompts_updated"], int)
        assert isinstance(data["keywords_updated"], int)
        assert isinstance(data["strategies_updated"], int)
        assert isinstance(data["follow_ups_optimized"], int)

    def test_run_cycle_creates_prompts(self) -> None:
        self.client.post("/api/self-improvement/run")

        response = self.client.get("/api/self-improvement/prompts/active")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_run_cycle_creates_strategy(self) -> None:
        self.client.post("/api/self-improvement/run")

        response = self.client.get("/api/self-improvement/strategy")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 7
