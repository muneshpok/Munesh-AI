"""CRM service - Lead management operations."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.models.models import Lead, LeadStatus, Message
from app.models.schemas import LeadCreate, LeadUpdate, LeadResponse, DashboardMetrics
from app.core.logging import logger


class CRMService:
    """Service for CRM lead management."""

    def get_lead(self, db: Session, phone: str) -> Optional[Lead]:
        """Get a lead by phone number."""
        return db.query(Lead).filter(Lead.phone == phone).first()

    def get_all_leads(
        self,
        db: Session,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Lead]:
        """Get all leads with optional status filter."""
        query = db.query(Lead)
        if status:
            query = query.filter(Lead.status == status)
        return query.order_by(Lead.updated_at.desc()).offset(skip).limit(limit).all()

    def create_or_update_lead(self, db: Session, lead_data: LeadCreate) -> Lead:
        """Create a new lead or update existing one."""
        existing = self.get_lead(db, lead_data.phone)
        if existing:
            if lead_data.name:
                existing.name = lead_data.name
            if lead_data.email:
                existing.email = lead_data.email
            if lead_data.notes:
                existing.notes = (existing.notes or "") + "\n" + lead_data.notes
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated lead: {lead_data.phone}")
            return existing

        lead = Lead(
            phone=lead_data.phone,
            name=lead_data.name,
            email=lead_data.email,
            notes=lead_data.notes,
            source=lead_data.source,
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        logger.info(f"Created new lead: {lead_data.phone}")
        return lead

    def update_status(self, db: Session, phone: str, status: str) -> Optional[Lead]:
        """Update lead status."""
        lead = self.get_lead(db, phone)
        if not lead:
            logger.warning(f"Lead not found for phone: {phone}")
            return None
        lead.status = LeadStatus(status)
        db.commit()
        db.refresh(lead)
        logger.info(f"Updated lead {phone} status to {status}")
        return lead

    def get_metrics(self, db: Session) -> DashboardMetrics:
        """Calculate dashboard metrics."""
        total = db.query(Lead).count()
        new_count = db.query(Lead).filter(Lead.status == LeadStatus.NEW).count()
        contacted = db.query(Lead).filter(Lead.status == LeadStatus.CONTACTED).count()
        demo_booked = db.query(Lead).filter(Lead.status == LeadStatus.DEMO_BOOKED).count()
        closed = db.query(Lead).filter(Lead.status == LeadStatus.CLOSED).count()

        conversion_rate = (closed / total * 100) if total > 0 else 0.0

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = (
            db.query(Message).filter(Message.created_at >= today_start).count()
        )

        # Count unique phones with messages in last 24 hours
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        active_conversations = (
            db.query(func.count(func.distinct(Message.phone)))
            .filter(Message.created_at >= yesterday)
            .scalar()
            or 0
        )

        return DashboardMetrics(
            total_leads=total,
            new_leads=new_count,
            contacted_leads=contacted,
            demo_booked=demo_booked,
            closed_leads=closed,
            conversion_rate=round(conversion_rate, 2),
            messages_today=messages_today,
            active_conversations=active_conversations,
        )

    def save_lead(self, db: Session, phone: str, note: str) -> Lead:
        """Save a lead with a note (tool function)."""
        return self.create_or_update_lead(
            db, LeadCreate(phone=phone, notes=note)
        )


# Singleton instance
crm_service = CRMService()
