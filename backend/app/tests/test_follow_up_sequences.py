"""Tests for Smart Follow-Up Sequences and Sales Agent improvements."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.models.models import Lead, LeadStatus, Message, FollowUp, AutomationLog
from app.services.follow_up_sequences import (
    FollowUpSequencer,
    follow_up_sequencer,
    FOLLOW_UP_SEQUENCES,
)
from app.agents.sales_agent import SalesAgent
from app.agents.chat_agent import ChatAgent


# --- Follow-Up Sequence Service Tests ---


class TestFollowUpSequences:
    """Tests for the FollowUpSequencer service."""

    def setup_method(self):
        self.engine = create_engine("sqlite:///test_follow_up_sequences.db")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.db = self.SessionLocal()
        self.sequencer = FollowUpSequencer()

    def teardown_method(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        import os
        try:
            os.remove("test_follow_up_sequences.db")
        except FileNotFoundError:
            pass

    def _create_lead(self, phone="1234567890", name="Test User", status=LeadStatus.NEW):
        lead = Lead(phone=phone, name=name, status=status)
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def test_get_sequence_for_new_lead(self):
        """New leads get the 'new_lead' sequence (5 steps)."""
        lead = self._create_lead(status=LeadStatus.NEW)
        sequence = self.sequencer.get_sequence_for_lead(lead)
        assert len(sequence) == 5
        assert sequence[0]["angle"] == "value"
        assert sequence[1]["angle"] == "social_proof"
        assert sequence[2]["angle"] == "case_study"
        assert sequence[3]["angle"] == "limited_offer"
        assert sequence[4]["angle"] == "final_touch"

    def test_get_sequence_for_contacted_lead(self):
        """Contacted leads get the 'contacted_stale' sequence (3 steps)."""
        lead = self._create_lead(status=LeadStatus.CONTACTED)
        sequence = self.sequencer.get_sequence_for_lead(lead)
        assert len(sequence) == 3
        assert sequence[0]["angle"] == "re_engage"

    def test_get_sequence_for_demo_booked_lead(self):
        """Demo-booked leads get the 'demo_booked_nurture' sequence (2 steps)."""
        lead = self._create_lead(status=LeadStatus.DEMO_BOOKED)
        sequence = self.sequencer.get_sequence_for_lead(lead)
        assert len(sequence) == 2
        assert sequence[0]["angle"] == "pre_demo"
        assert sequence[1]["angle"] == "post_demo"

    def test_get_sequence_for_closed_lead(self):
        """Closed leads get no sequence."""
        lead = self._create_lead(status=LeadStatus.CLOSED)
        sequence = self.sequencer.get_sequence_for_lead(lead)
        assert len(sequence) == 0

    def test_get_sequence_for_lost_lead(self):
        """Lost leads get no sequence."""
        lead = self._create_lead(status=LeadStatus.LOST)
        sequence = self.sequencer.get_sequence_for_lead(lead)
        assert len(sequence) == 0

    def test_get_current_step_no_follow_ups(self):
        """A lead with no follow-ups is at step 0."""
        lead = self._create_lead()
        step = self.sequencer.get_current_step(self.db, lead.phone)
        assert step == 0

    def test_get_current_step_with_follow_ups(self):
        """A lead with 2 sent follow-ups is at step 2."""
        lead = self._create_lead()
        for _ in range(2):
            fu = FollowUp(
                phone=lead.phone,
                message="Test follow-up",
                scheduled_at=datetime.now(timezone.utc),
                sent=1,
                sequence_type="new_lead",
            )
            self.db.add(fu)
        self.db.commit()
        step = self.sequencer.get_current_step(self.db, lead.phone, sequence_type="new_lead")
        assert step == 2

    def test_get_next_message_first_step(self):
        """First step message is returned immediately for a new lead."""
        lead = self._create_lead(name="Alice")
        msg = self.sequencer.get_next_message(self.db, lead)
        assert msg is not None
        assert msg["step"] == 1
        assert msg["angle"] == "value"
        assert "Alice" in msg["message"]

    def test_get_next_message_respects_delay(self):
        """Second step message is not returned if delay hasn't elapsed."""
        lead = self._create_lead()
        # Add a follow-up sent just now
        fu = FollowUp(
            phone=lead.phone,
            message="Step 1 msg",
            scheduled_at=datetime.now(timezone.utc),
            sent=1,
            sequence_type="new_lead",
        )
        self.db.add(fu)
        self.db.commit()

        msg = self.sequencer.get_next_message(self.db, lead)
        # Step 2 has 24h delay, so it shouldn't be due yet
        assert msg is None

    def test_get_next_message_sequence_complete(self):
        """Returns None when all steps in the sequence are done."""
        lead = self._create_lead(status=LeadStatus.DEMO_BOOKED)
        # Add 2 follow-ups (demo_booked_nurture has 2 steps)
        for i in range(2):
            fu = FollowUp(
                phone=lead.phone,
                message=f"Step {i+1}",
                scheduled_at=datetime.now(timezone.utc) - timedelta(hours=100),
                sent=1,
                sequence_type="demo_booked_nurture",
            )
            self.db.add(fu)
        self.db.commit()

        msg = self.sequencer.get_next_message(self.db, lead)
        assert msg is None

    def test_get_next_message_pauses_on_lead_response(self):
        """Sequence pauses when the lead has responded after the last follow-up."""
        lead = self._create_lead()
        # Add a follow-up sent 2 hours ago
        fu = FollowUp(
            phone=lead.phone,
            message="Step 1",
            scheduled_at=datetime.now(timezone.utc) - timedelta(hours=2),
            sent=1,
            sequence_type="new_lead",
        )
        self.db.add(fu)
        # Add a lead response 1 hour ago (after the follow-up)
        inbound = Message(
            phone=lead.phone,
            direction="inbound",
            content="Hi, interested!",
        )
        self.db.add(inbound)
        self.db.commit()

        msg = self.sequencer.get_next_message(self.db, lead)
        # Should pause because lead responded
        assert msg is None

    def test_get_sequence_status(self):
        """get_sequence_status returns correct structure."""
        lead = self._create_lead()
        status = self.sequencer.get_sequence_status(self.db, lead.phone)
        assert status["phone"] == lead.phone
        assert status["lead_status"] == "new"
        assert status["sequence_type"] == "new_lead"
        assert status["total_steps"] == 5
        assert status["current_step"] == 0
        assert status["completed"] is False

    def test_get_sequence_status_not_found(self):
        """get_sequence_status returns error for unknown phone."""
        status = self.sequencer.get_sequence_status(self.db, "9999999999")
        assert "error" in status

    @pytest.mark.asyncio
    async def test_execute_sequences_sends_messages(self):
        """execute_sequences sends follow-up messages to eligible leads."""
        lead = self._create_lead(name="Bob")
        with patch("app.services.follow_up_sequences.whatsapp_service") as mock_wa, \
             patch("app.services.follow_up_sequences.memory_service") as mock_mem:
            mock_wa.send_text_message = AsyncMock()
            results = await self.sequencer.execute_sequences(self.db)
            assert results["messages_sent"] == 1
            assert results["leads_processed"] == 1
            mock_wa.send_text_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_sequences_skips_closed_leads(self):
        """execute_sequences skips closed/lost leads entirely."""
        self._create_lead(phone="111", status=LeadStatus.CLOSED)
        self._create_lead(phone="222", status=LeadStatus.LOST)
        with patch("app.services.follow_up_sequences.whatsapp_service"), \
             patch("app.services.follow_up_sequences.memory_service"):
            results = await self.sequencer.execute_sequences(self.db)
            assert results["messages_sent"] == 0
            assert results["leads_processed"] == 0


# --- Sequence Definitions Tests ---


class TestSequenceDefinitions:
    """Tests for the sequence templates and structure."""

    def test_all_sequences_have_required_fields(self):
        """Every step in every sequence has step, delay_hours, angle, template."""
        for name, steps in FOLLOW_UP_SEQUENCES.items():
            for step in steps:
                assert "step" in step, f"Missing 'step' in {name}"
                assert "delay_hours" in step, f"Missing 'delay_hours' in {name}"
                assert "angle" in step, f"Missing 'angle' in {name}"
                assert "template" in step, f"Missing 'template' in {name}"

    def test_new_lead_sequence_has_five_steps(self):
        assert len(FOLLOW_UP_SEQUENCES["new_lead"]) == 5

    def test_contacted_stale_sequence_has_three_steps(self):
        assert len(FOLLOW_UP_SEQUENCES["contacted_stale"]) == 3

    def test_demo_booked_sequence_has_two_steps(self):
        assert len(FOLLOW_UP_SEQUENCES["demo_booked_nurture"]) == 2

    def test_templates_have_name_placeholder(self):
        """All templates use {name} for personalization."""
        for name, steps in FOLLOW_UP_SEQUENCES.items():
            for step in steps:
                assert "{name}" in step["template"], (
                    f"Missing {{name}} placeholder in {name} step {step['step']}"
                )

    def test_delay_hours_increase(self):
        """Delay hours should increase within each sequence."""
        for name, steps in FOLLOW_UP_SEQUENCES.items():
            for i in range(1, len(steps)):
                assert steps[i]["delay_hours"] >= steps[i-1]["delay_hours"], (
                    f"Delay hours should increase in {name}: "
                    f"step {i} ({steps[i-1]['delay_hours']}h) >= "
                    f"step {i+1} ({steps[i]['delay_hours']}h)"
                )


# --- Sales Agent Prompt Tests ---


class TestSalesAgentPrompt:
    """Tests that the improved Sales Agent prompt contains key conversion elements."""

    def test_prompt_has_social_proof(self):
        assert "3x more demo bookings" in SalesAgent.SYSTEM_PROMPT

    def test_prompt_has_objection_handling(self):
        assert "Too expensive" in SalesAgent.SYSTEM_PROMPT
        assert "Not sure I need it" in SalesAgent.SYSTEM_PROMPT
        assert "I'll think about it" in SalesAgent.SYSTEM_PROMPT

    def test_prompt_has_pricing_tiers(self):
        assert "$49" in SalesAgent.SYSTEM_PROMPT
        assert "$149" in SalesAgent.SYSTEM_PROMPT
        assert "$499" in SalesAgent.SYSTEM_PROMPT

    def test_prompt_has_free_tier(self):
        assert "Free" in SalesAgent.SYSTEM_PROMPT
        assert "$0" in SalesAgent.SYSTEM_PROMPT

    def test_prompt_has_conversion_playbook(self):
        assert "DISCOVER" in SalesAgent.SYSTEM_PROMPT
        assert "CLOSE" in SalesAgent.SYSTEM_PROMPT

    def test_prompt_has_clear_cta(self):
        assert "demo" in SalesAgent.SYSTEM_PROMPT.lower()


# --- Chat Agent Prompt Tests ---


class TestChatAgentPrompt:
    """Tests that the improved Chat Agent prompt guides toward sales."""

    def test_prompt_mentions_demo(self):
        assert "demo" in ChatAgent.SYSTEM_PROMPT.lower()

    def test_prompt_mentions_pricing(self):
        assert "$49" in ChatAgent.SYSTEM_PROMPT

    def test_prompt_mentions_free_plan(self):
        assert "Free plan" in ChatAgent.SYSTEM_PROMPT or "free plan" in ChatAgent.SYSTEM_PROMPT.lower()

    def test_prompt_has_talking_points(self):
        assert "WhatsApp" in ChatAgent.SYSTEM_PROMPT
        assert "AI agents" in ChatAgent.SYSTEM_PROMPT


# --- Follow-Up API Tests ---


class TestFollowUpAPI:
    """Tests for follow-up sequence API endpoints."""

    def setup_method(self):
        self.engine = create_engine("sqlite:///test_follow_up_api.db")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        from app.main import app
        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def teardown_method(self):
        from app.main import app
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        import os
        try:
            os.remove("test_follow_up_api.db")
        except FileNotFoundError:
            pass

    def test_get_sequences_info(self):
        """GET /api/follow-ups/sequences returns sequence definitions."""
        resp = self.client.get("/api/follow-ups/sequences")
        assert resp.status_code == 200
        data = resp.json()
        assert "sequences" in data
        assert "new_lead" in data["sequences"]
        assert data["sequences"]["new_lead"]["total_steps"] == 5
        assert "total_follow_ups_sent" in data

    def test_get_lead_sequence_status_not_found(self):
        """GET /api/follow-ups/status/{phone} returns error for unknown lead."""
        resp = self.client.get("/api/follow-ups/status/9999999999")
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_get_lead_sequence_status_with_lead(self):
        """GET /api/follow-ups/status/{phone} returns correct status."""
        db = self.SessionLocal()
        lead = Lead(phone="5551234567", name="API Test", status=LeadStatus.NEW)
        db.add(lead)
        db.commit()
        db.close()

        resp = self.client.get("/api/follow-ups/status/5551234567")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == "5551234567"
        assert data["sequence_type"] == "new_lead"
        assert data["total_steps"] == 5

    def test_run_sequences_endpoint(self):
        """POST /api/follow-ups/run triggers sequences."""
        with patch("app.services.follow_up_sequences.whatsapp_service") as mock_wa, \
             patch("app.services.follow_up_sequences.memory_service"):
            mock_wa.send_text_message = AsyncMock()
            resp = self.client.post("/api/follow-ups/run")
            assert resp.status_code == 200
            data = resp.json()
            assert "messages_sent" in data
            assert "leads_processed" in data
