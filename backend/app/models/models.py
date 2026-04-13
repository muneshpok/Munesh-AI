"""SQLAlchemy models for CRM and messaging."""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Float, Enum as SAEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class LeadStatus(str, enum.Enum):
    """Lead lifecycle statuses."""
    NEW = "new"
    CONTACTED = "contacted"
    DEMO_BOOKED = "demo_booked"
    FOLLOW_UP = "follow_up"
    CLOSED = "closed"
    LOST = "lost"


class Lead(Base):
    """CRM Lead model."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    status = Column(
        SAEnum(LeadStatus),
        default=LeadStatus.NEW,
        nullable=False,
    )
    notes = Column(Text, nullable=True)
    source = Column(String(50), default="whatsapp")
    lead_score = Column(Integer, default=0)  # 0-100 engagement score
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Message(Base):
    """Chat message history model."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), nullable=False, index=True)
    direction = Column(String(10), nullable=False)  # "inbound" or "outbound"
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, image, document, etc.
    whatsapp_message_id = Column(String(255), nullable=True)
    agent_type = Column(String(50), nullable=True)  # which agent handled it
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AgentDecision(Base):
    """Log of agent decisions for auditing."""
    __tablename__ = "agent_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), nullable=False, index=True)
    intent = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    tool_name = Column(String(100), nullable=True)
    parameters = Column(JSON, nullable=True)
    response = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FollowUp(Base):
    """Scheduled follow-up tasks."""
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent = Column(Integer, default=0)  # 0 = pending, 1 = sent
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DailyReport(Base):
    """Stores daily analysis snapshots from the Daily Loop."""
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    # Funnel metrics snapshot
    total_leads = Column(Integer, default=0)
    new_leads = Column(Integer, default=0)
    contacted_leads = Column(Integer, default=0)
    demo_booked = Column(Integer, default=0)
    closed_leads = Column(Integer, default=0)
    lost_leads = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    # Activity metrics
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    active_conversations = Column(Integer, default=0)
    # Agent performance
    agent_breakdown = Column(JSON, nullable=True)  # {"sales": 5, "support": 3, ...}
    # Insights & decisions
    insights = Column(JSON, nullable=True)  # list of insight strings
    actions_taken = Column(JSON, nullable=True)  # list of automated actions
    stale_leads_count = Column(Integer, default=0)
    follow_ups_sent = Column(Integer, default=0)
    leads_scored = Column(Integer, default=0)
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AutomationLog(Base):
    """Tracks automated actions taken by the Daily Loop."""
    __tablename__ = "automation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(50), nullable=False, index=True)  # follow_up, nurture, score, escalate
    phone = Column(String(20), nullable=True, index=True)
    description = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    status = Column(String(20), default="completed")  # completed, failed, skipped
    created_at = Column(DateTime(timezone=True), server_default=func.now())
