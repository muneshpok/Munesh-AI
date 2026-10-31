"""Tests for tool execution."""

import pytest
import pytest_asyncio
from app.tools.registry import ToolRegistry


class TestToolRegistry:
    """Test the tool registry and execution."""

    def setup_method(self) -> None:
        self.registry = ToolRegistry()

    def test_available_tools(self) -> None:
        """Test that all expected tools are registered."""
        expected = ["send_whatsapp_message", "save_lead", "update_crm", "send_demo_link"]
        assert self.registry.AVAILABLE_TOOLS == expected

    @pytest.mark.asyncio
    async def test_unknown_tool(self) -> None:
        """Test that unknown tools return an error."""
        result = await self.registry.execute("nonexistent_tool", {})
        assert result["status"] == "error"
        assert "Unknown tool" in result["detail"]

    @pytest.mark.asyncio
    async def test_send_whatsapp_missing_params(self) -> None:
        """Test send_whatsapp_message with missing parameters."""
        result = await self.registry.execute("send_whatsapp_message", {})
        assert result["status"] == "error"
        assert "required" in result["detail"]

    @pytest.mark.asyncio
    async def test_save_lead_no_db(self) -> None:
        """Test save_lead without database session."""
        result = await self.registry.execute("save_lead", {"phone": "123"})
        assert result["status"] == "error"
        assert "Database" in result["detail"]

    @pytest.mark.asyncio
    async def test_update_crm_no_db(self) -> None:
        """Test update_crm without database session."""
        result = await self.registry.execute("update_crm", {"phone": "123"})
        assert result["status"] == "error"
        assert "Database" in result["detail"]
