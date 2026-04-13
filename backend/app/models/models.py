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
