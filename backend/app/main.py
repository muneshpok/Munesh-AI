"""Munesh AI - FastAPI Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger
from app.routes import whatsapp, crm, health


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

    @app.on_event("startup")
    async def startup() -> None:
        """Initialize database on startup."""
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        init_db()
        logger.info("Database initialized")

    return app


app = create_app()
