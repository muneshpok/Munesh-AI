"""Munesh AI - FastAPI Application."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, SessionLocal
from app.core.logging import logger
from app.routes import whatsapp, crm, health, analytics, self_improvement, performance
from app.services.daily_loop import daily_loop
from app.services.self_improvement import self_improvement_agent


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-powered WhatsApp business automation platform",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.FRONTEND_URL,
            "http://localhost:3000",
            "http://localhost:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(whatsapp.router)
    app.include_router(crm.router)
    app.include_router(analytics.router)
    app.include_router(self_improvement.router)
    app.include_router(performance.router)

    @app.on_event("startup")
    async def startup() -> None:
        """Initialize database, self-improvement defaults, and start schedulers."""
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        init_db()
        logger.info("Database initialized")
        # Initialize self-improvement defaults (prompts + strategy configs)
        db = SessionLocal()
        try:
            self_improvement_agent.initialize_defaults(db)
            logger.info("Self-Improvement Agent defaults initialized")
        finally:
            db.close()
        # Start background daily loop scheduler
        asyncio.create_task(_daily_loop_scheduler())
        logger.info("Daily Loop scheduler started")

    return app


async def _daily_loop_scheduler() -> None:
    """Background task that runs the daily loop every 24 hours."""
    # Wait 60 seconds before first run to let app fully initialize
    await asyncio.sleep(60)
    while True:
        try:
            logger.info("Daily Loop scheduler: running cycle...")
            db = SessionLocal()
            try:
                await daily_loop.run(db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Daily Loop scheduler error: {e}")
        # Sleep for 24 hours until next cycle
        await asyncio.sleep(86400)


app = create_app()
