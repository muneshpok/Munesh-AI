"""CRM and lead management routes."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.crm import crm_service
from app.models.schemas import LeadResponse, LeadUpdate, DashboardMetrics, BroadcastRequest
from app.services.whatsapp import whatsapp_service
from app.core.logging import logger

router = APIRouter(prefix="/api", tags=["CRM"])


@router.get("/leads", response_model=list[LeadResponse])
async def get_leads(
    status: Optional[str] = Query(None, description="Filter by lead status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list:
    """Get all leads with optional status filter."""
    leads = crm_service.get_all_leads(db, status=status, skip=skip, limit=limit)
    return leads


@router.post("/update-status", response_model=LeadResponse)
async def update_lead_status(
    update: LeadUpdate,
    db: Session = Depends(get_db),
) -> LeadResponse:
    """Update a lead's status and details."""
    if update.status:
        lead = crm_service.update_status(db, update.phone, update.status.value)
    else:
        lead = crm_service.get_lead(db, update.phone)

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if update.name:
        lead.name = update.name
    if update.email:
        lead.email = update.email
    if update.notes:
        lead.notes = (lead.notes or "") + "\n" + update.notes

    db.commit()
    db.refresh(lead)
    return lead  # type: ignore[return-value]


@router.get("/metrics", response_model=DashboardMetrics)
async def get_metrics(db: Session = Depends(get_db)) -> DashboardMetrics:
    """Get dashboard metrics."""
    return crm_service.get_metrics(db)


@router.get("/messages/{phone}")
async def get_messages(
    phone: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list:
    """Get message history for a phone number."""
    from app.models.models import Message

    messages = (
        db.query(Message)
        .filter(Message.phone == phone)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()
    return [
        {
            "id": m.id,
            "phone": m.phone,
            "direction": m.direction,
            "content": m.content,
            "message_type": m.message_type,
            "agent_type": m.agent_type,
            "created_at": str(m.created_at) if m.created_at else None,
        }
        for m in messages
    ]


@router.post("/broadcast")
async def broadcast_message(
    request: BroadcastRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Broadcast a message to leads."""
    if request.phones:
        targets = request.phones
    else:
        leads = crm_service.get_all_leads(
            db, status=request.status_filter.value if request.status_filter else None
        )
        targets = [lead.phone for lead in leads]

    sent = 0
    failed = 0
    for phone in targets:
        result = await whatsapp_service.send_text_message(phone, request.message)
        if result.get("status") == "error":
            failed += 1
        else:
            sent += 1

    logger.info(f"Broadcast complete: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "total": len(targets)}
