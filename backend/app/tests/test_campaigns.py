"""Tests for the Campaign System — full marketing campaign pipeline.

Covers:
- Campaign templates and audience filters
- Campaign planning
- Audience selection
- Message generation
- Campaign scheduling
- Campaign execution and metrics
- Optimization loop
- Full pipeline
- API endpoints
- BookingAgent fix (non-confirmed bookings should NOT set demo_booked)
- Follow-up sequence_type filtering fix
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone

# ─── Campaign Service Tests ───


class TestCampaignTemplates:
    """Test campaign template definitions."""

    def test_templates_exist(self):
        from app.services.campaigns import CAMPAIGN_TEMPLATES

        assert len(CAMPAIGN_TEMPLATES) >= 6
        assert "product_launch" in CAMPAIGN_TEMPLATES
        assert "re_engagement" in CAMPAIGN_TEMPLATES
        assert "demo_push" in CAMPAIGN_TEMPLATES
        assert "upsell" in CAMPAIGN_TEMPLATES
        assert "seasonal_promo" in CAMPAIGN_TEMPLATES
        assert "custom" in CAMPAIGN_TEMPLATES

    def test_template_structure(self):
        from app.services.campaigns import CAMPAIGN_TEMPLATES

        for key, template in CAMPAIGN_TEMPLATES.items():
            assert "name" in template, f"Template '{key}' missing 'name'"
            assert "description" in template, f"Template '{key}' missing 'description'"
            assert "goal" in template, f"Template '{key}' missing 'goal'"
            assert "default_audience" in template, f"Template '{key}' missing 'default_audience'"
            assert "message_style" in template, f"Template '{key}' missing 'message_style'"
            assert "suggested_timing" in template, f"Template '{key}' missing 'suggested_timing'"

    def test_template_goals(self):
        from app.services.campaigns import CAMPAIGN_TEMPLATES

        valid_goals = {"awareness", "reactivation", "conversion", "revenue", "custom"}
        for key, template in CAMPAIGN_TEMPLATES.items():
            assert template["goal"] in valid_goals, f"Template '{key}' has invalid goal: {template['goal']}"


class TestAudienceFilters:
    """Test audience filter definitions."""

    def test_filters_exist(self):
        from app.services.campaigns import AUDIENCE_FILTERS

        assert len(AUDIENCE_FILTERS) >= 7
        assert "all" in AUDIENCE_FILTERS
        assert "all_active" in AUDIENCE_FILTERS
        assert "new_leads" in AUDIENCE_FILTERS
        assert "warm_leads" in AUDIENCE_FILTERS
        assert "stale" in AUDIENCE_FILTERS
        assert "demo_booked" in AUDIENCE_FILTERS
        assert "high_intent" in AUDIENCE_FILTERS

    def test_filter_structure(self):
        from app.services.campaigns import AUDIENCE_FILTERS

        for key, f in AUDIENCE_FILTERS.items():
            assert "name" in f, f"Filter '{key}' missing 'name'"
            assert "description" in f, f"Filter '{key}' missing 'description'"
            assert "filter_fn" in f, f"Filter '{key}' missing 'filter_fn'"
            assert callable(f["filter_fn"]), f"Filter '{key}' filter_fn is not callable"

    def test_all_filter_returns_all(self):
        from app.services.campaigns import AUDIENCE_FILTERS

        leads = [MagicMock(), MagicMock(), MagicMock()]
        result = AUDIENCE_FILTERS["all"]["filter_fn"](leads)
        assert len(result) == 3

    def test_new_leads_filter(self):
        from app.services.campaigns import AUDIENCE_FILTERS
        from app.models.models import LeadStatus

        leads = [
            MagicMock(status=LeadStatus.NEW),
            MagicMock(status=LeadStatus.CONTACTED),
            MagicMock(status=LeadStatus.NEW),
        ]
        result = AUDIENCE_FILTERS["new_leads"]["filter_fn"](leads)
        assert len(result) == 2

    def test_warm_leads_filter(self):
        from app.services.campaigns import AUDIENCE_FILTERS
        from app.models.models import LeadStatus

        leads = [
            MagicMock(status=LeadStatus.CONTACTED, lead_score=50),
            MagicMock(status=LeadStatus.CONTACTED, lead_score=20),
            MagicMock(status=LeadStatus.NEW, lead_score=60),
        ]
        result = AUDIENCE_FILTERS["warm_leads"]["filter_fn"](leads)
        assert len(result) == 1  # Only contacted with score >= 40

    def test_high_intent_filter(self):
        from app.services.campaigns import AUDIENCE_FILTERS

        leads = [
            MagicMock(lead_score=70),
            MagicMock(lead_score=30),
            MagicMock(lead_score=80),
        ]
        result = AUDIENCE_FILTERS["high_intent"]["filter_fn"](leads)
        assert len(result) == 2

    def test_demo_booked_filter(self):
        from app.services.campaigns import AUDIENCE_FILTERS
        from app.models.models import LeadStatus

        leads = [
            MagicMock(status=LeadStatus.DEMO_BOOKED),
            MagicMock(status=LeadStatus.NEW),
            MagicMock(status=LeadStatus.DEMO_BOOKED),
        ]
        result = AUDIENCE_FILTERS["demo_booked"]["filter_fn"](leads)
        assert len(result) == 2


class TestCampaignPlanning:
    """Test campaign planning."""

    def test_plan_from_template(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("demo_push")

        assert campaign["name"] == "Demo Push"
        assert campaign["goal"] == "conversion"
        assert campaign["status"] == "planned"
        assert campaign["audience_filter"] == "warm_leads"
        assert campaign["metrics"]["total_targeted"] == 0
        assert campaign["id"] == 1

    def test_plan_custom_campaign(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign(
            "custom",
            custom_name="April Promo",
            custom_message="Hi {name}! Special offer...",
            audience_filter="all_active",
        )

        assert campaign["name"] == "April Promo"
        assert campaign["custom_message"] == "Hi {name}! Special offer..."
        assert campaign["audience_filter"] == "all_active"

    def test_plan_increments_id(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        c1 = svc.plan_campaign("demo_push")
        c2 = svc.plan_campaign("re_engagement")
        assert c2["id"] == c1["id"] + 1

    def test_plan_unknown_template_uses_custom(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("nonexistent_template")
        assert campaign["goal"] == "custom"


class TestCampaignMessageGeneration:
    """Test message generation."""

    def test_custom_message_substitution(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign(
            "custom",
            custom_message="Hi{name}! Check this out.",
        )
        campaign["audience"] = [
            {"phone": "+1234", "name": "Alice", "status": "new", "score": 50},
        ]
        campaign["status"] = "audience_selected"

        result = asyncio.get_event_loop().run_until_complete(
            svc.generate_messages(campaign["id"])
        )
        assert result["messages"][0]["message"] == "Hi Alice! Check this out."
        assert result["status"] == "messages_generated"

    @patch("app.services.campaigns.llm_service.generate", new_callable=AsyncMock)
    def test_ai_message_generation(self, mock_generate):
        mock_generate.return_value = "Hey Alice! Let me show you how Munesh AI can help. Reply YES!"

        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("demo_push")
        campaign["audience"] = [
            {"phone": "+1234", "name": "Alice", "status": "contacted", "score": 60},
        ]
        campaign["status"] = "audience_selected"

        result = asyncio.get_event_loop().run_until_complete(
            svc.generate_messages(campaign["id"])
        )
        assert "Alice" in result["messages"][0]["message"]
        assert mock_generate.called

    @patch("app.services.campaigns.llm_service.generate", new_callable=AsyncMock)
    def test_ai_fallback_on_error(self, mock_generate):
        mock_generate.side_effect = Exception("LLM error")

        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("demo_push")
        campaign["audience"] = [
            {"phone": "+1234", "name": "Bob", "status": "new", "score": 30},
        ]
        campaign["status"] = "audience_selected"

        result = asyncio.get_event_loop().run_until_complete(
            svc.generate_messages(campaign["id"])
        )
        # Should use fallback template
        assert "Bob" in result["messages"][0]["message"]
        assert "Munesh AI" in result["messages"][0]["message"]

    def test_generate_for_nonexistent_campaign(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        result = asyncio.get_event_loop().run_until_complete(
            svc.generate_messages(999)
        )
        assert result == {"error": "Campaign not found"}


class TestCampaignScheduling:
    """Test campaign scheduling."""

    def test_schedule_immediate(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("demo_push")
        result = svc.schedule_campaign(campaign["id"], send_immediately=True)

        assert result["status"] == "scheduled"
        assert result["send_immediately"] is True
        assert "scheduled_at" in result

    def test_schedule_nonexistent(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        result = svc.schedule_campaign(999)
        assert result == {"error": "Campaign not found"}


class TestCampaignOptimization:
    """Test optimization suggestions."""

    def test_optimize_no_leads(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("demo_push")
        campaign["status"] = "completed"
        campaign["metrics"]["total_targeted"] = 0

        result = asyncio.get_event_loop().run_until_complete(
            svc.optimize_campaign(campaign["id"], MagicMock())
        )
        assert any("broadening" in s for s in result["suggestions"])

    def test_optimize_low_response(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("demo_push")
        campaign["status"] = "completed"
        campaign["completed_at"] = datetime.now(timezone.utc).isoformat()
        campaign["metrics"]["total_targeted"] = 100
        campaign["metrics"]["sent"] = 100
        campaign["metrics"]["response_rate"] = 5
        campaign["messages"] = []

        result = asyncio.get_event_loop().run_until_complete(
            svc.optimize_campaign(campaign["id"], MagicMock())
        )
        assert any("response rate" in s.lower() for s in result["suggestions"])

    def test_optimize_all_audience_suggestion(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        campaign = svc.plan_campaign("custom", audience_filter="all")
        campaign["status"] = "completed"
        campaign["completed_at"] = datetime.now(timezone.utc).isoformat()
        campaign["metrics"]["total_targeted"] = 50
        campaign["metrics"]["sent"] = 50
        campaign["metrics"]["response_rate"] = 30
        campaign["messages"] = []

        result = asyncio.get_event_loop().run_until_complete(
            svc.optimize_campaign(campaign["id"], MagicMock())
        )
        assert any("segmenting" in s for s in result["suggestions"])


class TestCampaignHelpers:
    """Test helper methods."""

    def test_get_all_campaigns(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        svc.plan_campaign("demo_push")
        svc.plan_campaign("re_engagement")
        assert len(svc.get_all_campaigns()) == 2

    def test_get_campaign_by_id(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        c = svc.plan_campaign("demo_push")
        result = svc.get_campaign(c["id"])
        assert result["name"] == "Demo Push"

    def test_get_nonexistent_campaign(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        assert svc.get_campaign(999) is None

    def test_get_templates(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        templates = svc.get_templates()
        assert "demo_push" in templates
        assert "custom" in templates

    def test_get_audience_filters(self):
        from app.services.campaigns import CampaignService

        svc = CampaignService()
        filters = svc.get_audience_filters()
        assert "all" in filters
        assert "name" in filters["all"]
        assert "description" in filters["all"]
        # Should not include filter_fn in the API response
        assert "filter_fn" not in filters["all"]


# ─── API Endpoint Tests ───


class TestCampaignAPI:
    """Test campaign API endpoints."""

    def _get_client(self):
        from fastapi.testclient import TestClient
        from app.main import app

        return TestClient(app)

    def test_get_templates(self):
        client = self._get_client()
        resp = client.get("/api/campaigns/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert "demo_push" in data
        assert "re_engagement" in data

    def test_get_audience_filters(self):
        client = self._get_client()
        resp = client.get("/api/campaigns/audience-filters")
        assert resp.status_code == 200
        data = resp.json()
        assert "all" in data
        assert "warm_leads" in data

    def test_list_campaigns(self):
        client = self._get_client()
        resp = client.get("/api/campaigns/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_plan_campaign(self):
        client = self._get_client()
        resp = client.post(
            "/api/campaigns/plan",
            json={"template_type": "demo_push"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Demo Push"
        assert data["status"] == "planned"

    def test_get_campaign_not_found(self):
        client = self._get_client()
        resp = client.get("/api/campaigns/99999")
        assert resp.status_code == 200
        assert resp.json() == {"error": "Campaign not found"}


# ─── BookingAgent Fix Tests ───


class TestBookingAgentFix:
    """Test that BookingAgent no longer sets demo_booked for unconfirmed bookings."""

    @patch("app.services.llm.llm_service.generate", new_callable=AsyncMock)
    def test_unconfirmed_booking_does_not_set_demo_booked(self, mock_generate):
        """When booking is NOT confirmed, should NOT call update_crm with demo_booked."""
        mock_generate.return_value = "Sure! What date works best for you?"

        from app.agents.booking_agent import BookingAgent

        agent = BookingAgent()
        result = asyncio.get_event_loop().run_until_complete(
            agent.process("+1234", "I want to book a demo", [])
        )

        # Should be RESPOND action, NOT CALL_TOOL with update_crm
        assert result.action.value == "respond"
        assert result.tool_name is None
        assert result.parameters is None

    @patch("app.services.llm.llm_service.generate", new_callable=AsyncMock)
    def test_confirmed_booking_sends_demo_link(self, mock_generate):
        """When booking IS confirmed, should call send_demo_link."""
        mock_generate.return_value = "Great! BOOK_CONFIRMED Your demo is set for Monday at 2 PM."

        from app.agents.booking_agent import BookingAgent

        agent = BookingAgent()
        result = asyncio.get_event_loop().run_until_complete(
            agent.process("+1234", "Let's do Monday at 2 PM", [])
        )

        assert result.action.value == "call_tool"
        assert result.tool_name == "send_demo_link"
        assert result.parameters == {"phone": "+1234"}


# ─── Follow-Up Sequence Type Fix Tests ───


class TestFollowUpSequenceTypeFix:
    """Test that follow-up step counter uses sequence_type for filtering."""

    def test_followup_model_has_sequence_type(self):
        """FollowUp model should have a sequence_type column."""
        from app.models.models import FollowUp

        assert hasattr(FollowUp, "sequence_type")

    def test_get_sequence_type_for_lead(self):
        """_get_sequence_type_for_lead returns correct type based on status."""
        from app.services.follow_up_sequences import FollowUpSequencer
        from app.models.models import LeadStatus

        seq = FollowUpSequencer()

        new_lead = MagicMock(status=LeadStatus.NEW)
        assert seq._get_sequence_type_for_lead(new_lead) == "new_lead"

        contacted_lead = MagicMock(status=LeadStatus.CONTACTED)
        assert seq._get_sequence_type_for_lead(contacted_lead) == "contacted_stale"

        follow_up_lead = MagicMock(status=LeadStatus.FOLLOW_UP)
        assert seq._get_sequence_type_for_lead(follow_up_lead) == "contacted_stale"

        demo_lead = MagicMock(status=LeadStatus.DEMO_BOOKED)
        assert seq._get_sequence_type_for_lead(demo_lead) == "demo_booked_nurture"

        closed_lead = MagicMock(status=LeadStatus.CLOSED)
        assert seq._get_sequence_type_for_lead(closed_lead) is None

    def test_get_current_step_accepts_sequence_type(self):
        """get_current_step should accept a sequence_type parameter."""
        from app.services.follow_up_sequences import FollowUpSequencer
        import inspect

        seq = FollowUpSequencer()
        sig = inspect.signature(seq.get_current_step)
        assert "sequence_type" in sig.parameters
