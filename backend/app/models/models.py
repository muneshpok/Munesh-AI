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


class PromptVersion(Base):
    """Versioned prompts for each agent — tracks prompt evolution over time."""
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(String(50), nullable=False, index=True)  # chat, sales, support, booking
    version = Column(Integer, nullable=False, default=1)
    prompt_text = Column(Text, nullable=False)
    is_active = Column(Integer, default=1)  # 1 = currently active, 0 = archived
    performance_score = Column(Float, nullable=True)  # measured after deployment
    reason = Column(Text, nullable=True)  # why this version was created
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ImprovementLog(Base):
    """Tracks all self-improvement actions and their rationale."""
    __tablename__ = "improvement_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    improvement_type = Column(String(50), nullable=False, index=True)  # prompt, keyword, follow_up, strategy
    target = Column(String(100), nullable=False)  # e.g. "sales_agent", "follow_up_timing"
    description = Column(Text, nullable=False)
    old_value = Column(Text, nullable=True)  # what it was before
    new_value = Column(Text, nullable=True)  # what it changed to
    rationale = Column(Text, nullable=True)  # why the change was made
    impact_metrics = Column(JSON, nullable=True)  # measured impact after change
    status = Column(String(20), default="applied")  # applied, reverted, pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StrategyConfig(Base):
    """Dynamic strategy configuration that the self-improvement agent can tune."""
    __tablename__ = "strategy_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    config_type = Column(String(20), default="string")  # string, int, float, json
    category = Column(String(50), nullable=False)  # keywords, timing, thresholds, templates
    description = Column(Text, nullable=True)
    updated_by = Column(String(50), default="system")  # system or self_improvement
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
