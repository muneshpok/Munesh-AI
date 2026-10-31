"""Performance Analyzer routes - Simple performance metrics and improvement suggestions."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.performance_analyzer import performance_analyzer

router = APIRouter(prefix="/api/performance", tags=["Performance Analyzer"])


@router.get("/metrics")
def get_performance_metrics(db: Session = Depends(get_db)):
    """Get current performance metrics snapshot."""
    return performance_analyzer.analyze_performance(db)


@router.get("/suggestions")
async def get_improvement_suggestions(db: Session = Depends(get_db)):
    """Get AI-generated improvement suggestions based on current metrics."""
    metrics = performance_analyzer.analyze_performance(db)
    suggestions = await performance_analyzer.generate_improvements(metrics)
    return {"metrics": metrics, "suggestions": suggestions}


@router.post("/analyze")
async def run_full_analysis(db: Session = Depends(get_db)):
    """Run full performance analysis: metrics + suggestions + logging."""
    return await performance_analyzer.run_analysis(db)
