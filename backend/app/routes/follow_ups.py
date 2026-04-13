"""Follow-up sequence routes — API endpoints for managing smart follow-up drip campaigns."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.follow_up_sequences import follow_up_sequencer

router = APIRouter(prefix="/api/follow-ups", tags=["Follow-Up Sequences"])


@router.get("/sequences")
def get_all_sequence_info(db: Session = Depends(get_db)):
    """Get follow-up sequence definitions and stats."""
    from app.services.follow_up_sequences import FOLLOW_UP_SEQUENCES
    from app.models.models import Lead, LeadStatus, FollowUp
    from sqlalchemy import func

    # Count leads per sequence type
    active_leads = db.query(Lead).filter(
        Lead.status.notin_([LeadStatus.CLOSED, LeadStatus.LOST])
    ).all()

    stats = {
        "new_lead": {"active": 0, "total_steps": len(FOLLOW_UP_SEQUENCES["new_lead"])},
        "contacted_stale": {"active": 0, "total_steps": len(FOLLOW_UP_SEQUENCES["contacted_stale"])},
        "demo_booked_nurture": {"active": 0, "total_steps": len(FOLLOW_UP_SEQUENCES["demo_booked_nurture"])},
    }

    for lead in active_leads:
        if lead.status == LeadStatus.NEW:
            stats["new_lead"]["active"] += 1
        elif lead.status in (LeadStatus.CONTACTED, LeadStatus.FOLLOW_UP):
            stats["contacted_stale"]["active"] += 1
        elif lead.status == LeadStatus.DEMO_BOOKED:
            stats["demo_booked_nurture"]["active"] += 1

    total_follow_ups = db.query(func.count(FollowUp.id)).filter(FollowUp.sent == 1).scalar() or 0

    return {
        "sequences": stats,
        "total_follow_ups_sent": total_follow_ups,
        "total_active_leads": len(active_leads),
    }


@router.get("/status/{phone}")
def get_lead_sequence_status(phone: str, db: Session = Depends(get_db)):
    """Get the current follow-up sequence status for a specific lead."""
    return follow_up_sequencer.get_sequence_status(db, phone)


@router.post("/run")
async def run_sequences(db: Session = Depends(get_db)):
    """Manually trigger follow-up sequences for all eligible leads."""
    results = await follow_up_sequencer.execute_sequences(db)
    return results
