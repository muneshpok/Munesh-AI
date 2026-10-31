"""Tool registry and execution engine."""

from typing import Optional
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.services.whatsapp import whatsapp_service
from app.services.crm import crm_service


class ToolRegistry:
    """Registry and executor for all available tools."""

    AVAILABLE_TOOLS = [
        "send_whatsapp_message",
        "save_lead",
        "update_crm",
        "send_demo_link",
    ]

    async def execute(
        self, tool_name: str, parameters: dict, db: Optional[Session] = None
    ) -> dict:
        """Execute a tool by name with given parameters."""
        logger.info(f"Executing tool: {tool_name} with params: {parameters}")

        if tool_name not in self.AVAILABLE_TOOLS:
            logger.error(f"Unknown tool: {tool_name}")
            return {"status": "error", "detail": f"Unknown tool: {tool_name}"}

        try:
            if tool_name == "send_whatsapp_message":
                return await self._send_whatsapp_message(parameters)
            elif tool_name == "save_lead":
                return self._save_lead(parameters, db)
            elif tool_name == "update_crm":
                return self._update_crm(parameters, db)
            elif tool_name == "send_demo_link":
                return await self._send_demo_link(parameters, db)
            else:
                return {"status": "error", "detail": f"Tool not implemented: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {"status": "error", "detail": str(e)}

    async def _send_whatsapp_message(self, params: dict) -> dict:
        """Send a WhatsApp message."""
        phone = params.get("phone", "")
        text = params.get("text", "")
        if not phone or not text:
            return {"status": "error", "detail": "phone and text are required"}
        result = await whatsapp_service.send_text_message(phone, text)
        return {"status": "success", "result": result}

    def _save_lead(self, params: dict, db: Optional[Session]) -> dict:
        """Save a lead to the CRM."""
        if not db:
            return {"status": "error", "detail": "Database session required"}
        phone = params.get("phone", "")
        note = params.get("note", "")
        if not phone:
            return {"status": "error", "detail": "phone is required"}
        lead = crm_service.save_lead(db, phone, note)
        return {"status": "success", "lead_id": lead.id}

    def _update_crm(self, params: dict, db: Optional[Session]) -> dict:
        """Update a lead's CRM status."""
        if not db:
            return {"status": "error", "detail": "Database session required"}
        phone = params.get("phone", "")
        status = params.get("status", "contacted")
        if not phone:
            return {"status": "error", "detail": "phone is required"}
        lead = crm_service.update_status(db, phone, status)
        if not lead:
            # Auto-create lead if not found
            crm_service.save_lead(db, phone, f"Auto-created, status: {status}")
            lead = crm_service.update_status(db, phone, status)
        return {"status": "success", "lead_phone": phone, "new_status": status}

    async def _send_demo_link(self, params: dict, db: Optional[Session]) -> dict:
        """Send a demo booking link to the user."""
        phone = params.get("phone", "")
        if not phone:
            return {"status": "error", "detail": "phone is required"}

        demo_link = "https://calendly.com/munesh-ai/demo"
        message = (
            "🎉 Great news! Here's your personalized demo link:\n\n"
            f"📅 {demo_link}\n\n"
            "Click to pick a time that works best for you. "
            "We look forward to showing you what Munesh AI can do!"
        )

        result = await whatsapp_service.send_text_message(phone, message)

        # Update CRM status
        if db:
            crm_service.update_status(db, phone, "demo_booked")

        return {"status": "success", "result": result}


# Singleton instance
tool_registry = ToolRegistry()
