"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class LeadStatusEnum(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    DEMO_BOOKED = "demo_booked"
    FOLLOW_UP = "follow_up"
    CLOSED = "closed"
    LOST = "lost"


class IntentEnum(str, Enum):
    SALES = "sales"
    SUPPORT = "support"
    BOOKING = "booking"
    CHAT = "chat"


class ActionEnum(str, Enum):
    RESPOND = "respond"
    CALL_TOOL = "call_tool"


# --- Agent Decision Schema ---

class AgentDecisionSchema(BaseModel):
    """Schema for agent decision output."""
    intent: IntentEnum
    action: ActionEnum
    tool_name: Optional[str] = None
    parameters: Optional[dict] = None
    response: str


# --- Lead Schemas ---

class LeadCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    source: str = "whatsapp"


class LeadUpdate(BaseModel):
    phone: str
    status: Optional[LeadStatusEnum] = None
    name: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    status: LeadStatusEnum
    notes: Optional[str] = None
    source: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- Message Schemas ---

class MessageCreate(BaseModel):
    phone: str
    direction: str
    content: str
    message_type: str = "text"
    whatsapp_message_id: Optional[str] = None
    agent_type: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    phone: str
    direction: str
    content: str
    message_type: str
    agent_type: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# --- WhatsApp Webhook Schemas ---

class WhatsAppMessage(BaseModel):
    """Parsed WhatsApp incoming message."""
    phone: str
    message_id: str
    text: str
    timestamp: str
    message_type: str = "text"
    media_url: Optional[str] = None


# --- Dashboard Schemas ---

class DashboardMetrics(BaseModel):
    total_leads: int
    new_leads: int
    contacted_leads: int
    demo_booked: int
    closed_leads: int
    conversion_rate: float
    messages_today: int
    active_conversations: int


# --- Broadcast Schema ---

class BroadcastRequest(BaseModel):
    message: str
    status_filter: Optional[LeadStatusEnum] = None
    phones: Optional[List[str]] = None


# --- Analytics / Daily Loop Schemas ---

class DailyReportResponse(BaseModel):
    id: int
    report_date: str
    total_leads: int
    new_leads: int
    contacted_leads: int
    demo_booked: int
    closed_leads: int
    lost_leads: int
    conversion_rate: float
    messages_sent: int
    messages_received: int
    active_conversations: int
    agent_breakdown: Optional[dict] = None
    insights: Optional[List[str]] = None
    actions_taken: Optional[List[str]] = None
    stale_leads_count: int
    follow_ups_sent: int
    leads_scored: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AutomationLogResponse(BaseModel):
    id: int
    action_type: str
    phone: Optional[str] = None
    description: str
    details: Optional[dict] = None
    status: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnalyticsInsights(BaseModel):
    """Current real-time insights snapshot."""
    funnel: dict  # stage counts and percentages
    engagement: dict  # message activity metrics
    agent_performance: dict  # per-agent breakdown
    stale_leads: List[dict]  # leads needing attention
    top_leads: List[dict]  # highest scored leads
    recommendations: List[str]  # AI-generated recommendations
