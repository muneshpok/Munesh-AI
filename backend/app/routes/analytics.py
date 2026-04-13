"""Analytics and Daily Loop API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import logger
from app.services.analytics import analytics_engine
from app.services.daily_loop import daily_loop
from app.models.models import DailyReport, AutomationLog
from app.models.schemas import (
    DailyReportResponse,
    AutomationLogResponse,
    AnalyticsInsights,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/insights", response_model=AnalyticsInsights)
async def get_insights(db: Session = Depends(get_db)) -> AnalyticsInsights:
    """Get real-time analytics insights snapshot."""
    funnel = analytics_engine.get_funnel_metrics(db)
    activity = analytics_engine.get_message_activity(db, days=1)
    agent_perf = analytics_engine.get_agent_performance(db, days=1)
    stale_leads = analytics_engine.find_stale_leads(db, stale_hours=24)
    top_leads = analytics_engine.get_top_leads(db, limit=5)

    recommendations = analytics_engine.generate_recommendations(
        funnel, stale_leads, activity
    )

    return AnalyticsInsights(
        funnel=funnel,
        engagement=activity,
        agent_performance=agent_perf,
        stale_leads=stale_leads,
        top_leads=top_leads,
        recommendations=recommendations,
    )


@router.get("/daily-report", response_model=Optional[DailyReportResponse])
async def get_latest_report(
    db: Session = Depends(get_db),
) -> Optional[DailyReport]:
    """Get the most recent daily report."""
    report = (
        db.query(DailyReport)
        .order_by(DailyReport.created_at.desc())
        .first()
    )
    return report


@router.get("/reports", response_model=list[DailyReportResponse])
async def list_reports(
    limit: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
) -> list:
    """List past daily reports."""
    reports = (
        db.query(DailyReport)
        .order_by(DailyReport.created_at.desc())
        .limit(limit)
        .all()
    )
    return reports


@router.post("/run-loop", response_model=DailyReportResponse)
async def run_daily_loop(
    db: Session = Depends(get_db),
) -> DailyReport:
    """Manually trigger the daily loop cycle."""
    logger.info("Manual daily loop trigger via API")
    report = await daily_loop.run(db)
    return report


@router.get("/automation-logs", response_model=list[AutomationLogResponse])
async def get_automation_logs(
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list:
    """Get automation action logs."""
    query = db.query(AutomationLog)
    if action_type:
        query = query.filter(AutomationLog.action_type == action_type)
    logs = query.order_by(AutomationLog.created_at.desc()).limit(limit).all()
    return logs
