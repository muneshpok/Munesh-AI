"""Health check and system routes."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["System"])


@router.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@router.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
