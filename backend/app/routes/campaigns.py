"""Campaign System API routes.

Endpoints for the full campaign pipeline:
  AI CEO → Campaign Planner → Audience Selector → Message Generator
        → Scheduler → WhatsApp Sender → Metrics → Optimization Loop
"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.campaigns import campaign_service

router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])


class CampaignCreate(BaseModel):
    """Request body for creating a campaign."""
    template_type: str = "custom"
    custom_name: Optional[str] = None
    custom_message: Optional[str] = None
    audience_filter: Optional[str] = None


class CampaignRunRequest(BaseModel):
    """Request body for running the full pipeline."""
    template_type: str = "custom"
    custom_name: Optional[str] = None
    custom_message: Optional[str] = None
    audience_filter: Optional[str] = None


class QuickCampaignRequest(BaseModel):
    """Request body for the lightweight quick-campaign creator."""
    name: str
    message: str
    audience: str = "all"


# ─── Templates & Filters ───

@router.get("/templates")
def get_templates():
    """Get all available campaign templates."""
    return campaign_service.get_templates()


@router.get("/audience-filters")
def get_audience_filters():
    """Get all available audience filter options."""
    return campaign_service.get_audience_filters()


# ─── Campaign CRUD ───

@router.get("/")
def list_campaigns():
    """List all campaigns."""
    return campaign_service.get_all_campaigns()


@router.get("/{campaign_id}")
def get_campaign(campaign_id: int):
    """Get a single campaign by ID."""
    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        return {"error": "Campaign not found"}
    return campaign


# ─── Pipeline Steps ───

@router.post("/plan")
def plan_campaign(body: CampaignCreate):
    """Step 1: Plan a new campaign."""
    return campaign_service.plan_campaign(
        template_type=body.template_type,
        custom_name=body.custom_name,
        custom_message=body.custom_message,
        audience_filter=body.audience_filter,
    )


@router.post("/{campaign_id}/select-audience")
def select_audience(campaign_id: int, db: Session = Depends(get_db)):
    """Step 2: Select target audience from CRM."""
    return campaign_service.select_audience(campaign_id, db)


@router.post("/{campaign_id}/generate-messages")
async def generate_messages(campaign_id: int):
    """Step 3: Generate personalized messages (uses LLM for non-custom campaigns)."""
    return await campaign_service.generate_messages(campaign_id)


@router.post("/{campaign_id}/schedule")
def schedule_campaign(campaign_id: int, send_immediately: bool = True):
    """Step 4: Schedule the campaign for sending."""
    return campaign_service.schedule_campaign(campaign_id, send_immediately)


@router.post("/{campaign_id}/execute")
async def execute_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Step 5: Execute — send all messages via WhatsApp."""
    return await campaign_service.execute_campaign(campaign_id, db)


@router.get("/{campaign_id}/metrics")
def get_metrics(campaign_id: int, db: Session = Depends(get_db)):
    """Step 6: Get real-time campaign metrics."""
    return campaign_service.get_campaign_metrics(campaign_id, db)


@router.post("/{campaign_id}/optimize")
async def optimize_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Step 7: Analyze results and get optimization suggestions."""
    return await campaign_service.optimize_campaign(campaign_id, db)


# ─── Quick Campaign Creator ───

@router.post("/quick")
async def create_quick_campaign(body: QuickCampaignRequest, db: Session = Depends(get_db)):
    """Create and send a lightweight campaign immediately — skips the full 7-step pipeline."""
    return await campaign_service.create_quick_campaign(
        name=body.name,
        message=body.message,
        audience=body.audience,
        db=db,
    )


@router.get("/quick/list")
def list_quick_campaigns():
    """List only quick-type campaigns."""
    return campaign_service.get_quick_campaigns()


# ─── Full Pipeline ───

@router.post("/run")
async def run_full_pipeline(body: CampaignRunRequest, db: Session = Depends(get_db)):
    """Run the complete campaign pipeline end-to-end in one call."""
    return await campaign_service.run_full_pipeline(
        db=db,
        template_type=body.template_type,
        custom_name=body.custom_name,
        custom_message=body.custom_message,
        audience_filter=body.audience_filter,
    )
