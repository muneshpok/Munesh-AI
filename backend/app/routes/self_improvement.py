"""Self-Improvement Agent API routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging import logger
from app.services.self_improvement import self_improvement_agent
from app.models.schemas import (
    PromptVersionResponse,
    ImprovementLogResponse,
    StrategyConfigResponse,
    SelfImprovementReport,
)

router = APIRouter(prefix="/api/self-improvement", tags=["Self-Improvement"])


@router.post("/run", response_model=SelfImprovementReport)
async def run_improvement_cycle(
    db: Session = Depends(get_db),
) -> SelfImprovementReport:
    """Manually trigger a self-improvement cycle."""
    logger.info("Manual self-improvement cycle triggered via API")
    report = await self_improvement_agent.run_improvement_cycle(db)
    return SelfImprovementReport(**report)


@router.get("/prompts/active", response_model=list[PromptVersionResponse])
async def get_active_prompts(
    db: Session = Depends(get_db),
) -> list:
    """Get all currently active agent prompts."""
    return self_improvement_agent.get_active_prompts(db)


@router.get("/prompts/history", response_model=list[PromptVersionResponse])
async def get_prompt_history(
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list:
    """Get prompt version history."""
    return self_improvement_agent.get_prompt_history(db, agent_type=agent_type, limit=limit)


@router.get("/improvements", response_model=list[ImprovementLogResponse])
async def get_improvements(
    improvement_type: Optional[str] = Query(None, description="Filter by type"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list:
    """Get improvement history."""
    return self_improvement_agent.get_improvement_history(
        db, improvement_type=improvement_type, limit=limit
    )


@router.get("/strategy", response_model=list[StrategyConfigResponse])
async def get_strategy(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
) -> list:
    """Get current strategy configuration."""
    return self_improvement_agent.get_strategy_configs(db, category=category)


@router.post("/initialize")
async def initialize_defaults(
    db: Session = Depends(get_db),
) -> dict:
    """Initialize default prompts and strategy configs."""
    self_improvement_agent.initialize_defaults(db)
    return {"status": "initialized", "message": "Default prompts and strategy configs created"}
