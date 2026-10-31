"""Tests for agent routing and intent classification."""

import pytest
from app.agents.base import DecisionEngine
from app.models.schemas import IntentEnum, ActionEnum, AgentDecisionSchema


class TestIntentClassification:
    """Test the DecisionEngine intent classification."""

    def test_sales_intent(self) -> None:
        """Test that sales keywords are classified correctly."""
        assert DecisionEngine.classify_intent("What is the price?") == IntentEnum.SALES
        assert DecisionEngine.classify_intent("I want to buy a plan") == IntentEnum.SALES
        assert DecisionEngine.classify_intent("How much does it cost?") == IntentEnum.SALES
        assert DecisionEngine.classify_intent("Tell me about your pricing") == IntentEnum.SALES

    def test_support_intent(self) -> None:
        """Test that support keywords are classified correctly."""
        assert DecisionEngine.classify_intent("I need help") == IntentEnum.SUPPORT
        assert DecisionEngine.classify_intent("There is an issue with my account") == IntentEnum.SUPPORT
        assert DecisionEngine.classify_intent("Something is not working") == IntentEnum.SUPPORT
        assert DecisionEngine.classify_intent("I have a problem") == IntentEnum.SUPPORT

    def test_booking_intent(self) -> None:
        """Test that booking keywords are classified correctly."""
        assert DecisionEngine.classify_intent("I want to book a demo") == IntentEnum.BOOKING
        assert DecisionEngine.classify_intent("Can I schedule a meeting?") == IntentEnum.BOOKING
        assert DecisionEngine.classify_intent("What times are available?") == IntentEnum.BOOKING

    def test_general_chat_intent(self) -> None:
        """Test that general messages default to chat."""
        assert DecisionEngine.classify_intent("Hello") == IntentEnum.CHAT
        assert DecisionEngine.classify_intent("Good morning") == IntentEnum.CHAT
        assert DecisionEngine.classify_intent("Thanks") == IntentEnum.CHAT

    def test_ambiguous_intent(self) -> None:
        """Test ambiguous messages with multiple intent signals."""
        # Should pick the dominant intent
        result = DecisionEngine.classify_intent(
            "I have a problem with pricing and need help with the cost"
        )
        assert result in [IntentEnum.SALES, IntentEnum.SUPPORT]


class TestDecisionValidation:
    """Test agent decision validation."""

    def test_valid_respond_decision(self) -> None:
        """Test validation of a valid respond decision."""
        decision = AgentDecisionSchema(
            intent=IntentEnum.CHAT,
            action=ActionEnum.RESPOND,
            response="Hello! How can I help?",
        )
        assert DecisionEngine.validate_decision(decision) is True

    def test_valid_tool_decision(self) -> None:
        """Test validation of a valid tool call decision."""
        decision = AgentDecisionSchema(
            intent=IntentEnum.SALES,
            action=ActionEnum.CALL_TOOL,
            tool_name="send_demo_link",
            parameters={"phone": "1234567890"},
            response="Here's your demo link!",
        )
        assert DecisionEngine.validate_decision(decision) is True

    def test_invalid_tool_decision_no_name(self) -> None:
        """Test that tool call without tool_name is invalid."""
        decision = AgentDecisionSchema(
            intent=IntentEnum.SALES,
            action=ActionEnum.CALL_TOOL,
            tool_name=None,
            response="response text",
        )
        assert DecisionEngine.validate_decision(decision) is False

    def test_invalid_empty_response(self) -> None:
        """Test that empty response is invalid."""
        decision = AgentDecisionSchema(
            intent=IntentEnum.CHAT,
            action=ActionEnum.RESPOND,
            response="",
        )
        assert DecisionEngine.validate_decision(decision) is False
