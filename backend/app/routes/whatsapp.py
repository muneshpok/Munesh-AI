"""WhatsApp webhook routes."""

from fastapi import APIRouter, Request, Query, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import logger
from app.core.config import settings
from app.services.whatsapp import whatsapp_service
from app.services.memory import memory_service
from app.services.crm import crm_service
from app.agents.router import agent_router
from app.tools.registry import tool_registry
from app.models.schemas import LeadCreate
from app.models.models import AgentDecision

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> int | dict:
    """WhatsApp webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge) if hub_challenge else 0
    logger.warning("WhatsApp webhook verification failed")
    return {"status": "error", "detail": "Verification failed"}


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Receive and process incoming WhatsApp messages."""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "detail": "Invalid JSON payload"}

    # Parse the webhook payload
    parsed = whatsapp_service.parse_webhook_payload(payload)
    if not parsed:
        # Could be a status update or other non-message event
        return {"status": "ok", "detail": "No message to process"}

    phone = parsed["phone"]
    text = parsed["text"]
    message_id = parsed["message_id"]
    contact_name = parsed.get("contact_name", "")

    if not text:
        return {"status": "ok", "detail": "Empty message, skipped"}

    logger.info(f"Received message from {phone}: {text[:50]}...")

    # Save inbound message
    memory_service.save_message(
        db, phone, "inbound", text, whatsapp_message_id=message_id
    )

    # Ensure lead exists
    crm_service.create_or_update_lead(
        db, LeadCreate(phone=phone, name=contact_name or None)
    )

    # Process in background to respond quickly
    background_tasks.add_task(
        _process_message, phone, text, message_id, db
    )

    return {"status": "ok"}


async def _process_message(
    phone: str, text: str, message_id: str, db: Session
) -> None:
    """Process a message through the agent system and respond."""
    try:
        # Get conversation history
        history = memory_service.get_history(db, phone)

        # Route to appropriate agent
        decision = await agent_router.route(phone, text, history)

        # Log the decision
        agent_decision = AgentDecision(
            phone=phone,
            intent=decision.intent.value,
            action=decision.action.value,
            tool_name=decision.tool_name,
            parameters=decision.parameters,
            response=decision.response,
        )
        db.add(agent_decision)
        db.commit()

        # Execute tool if needed
        if decision.action == "call_tool" and decision.tool_name:
            tool_result = await tool_registry.execute(
                decision.tool_name,
                decision.parameters or {},
                db=db,
            )
            logger.info(f"Tool result: {tool_result}")

        # Send response via WhatsApp
        await whatsapp_service.send_text_message(phone, decision.response)

        # Save outbound message
        memory_service.save_message(
            db,
            phone,
            "outbound",
            decision.response,
            agent_type=decision.intent.value,
        )

        # Update lead status if new
        lead = crm_service.get_lead(db, phone)
        if lead and lead.status.value == "new":
            crm_service.update_status(db, phone, "contacted")

    except Exception as e:
        logger.error(f"Error processing message from {phone}: {e}")
