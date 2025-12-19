"""FastAPI Application Entry Point with Lifespan Management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.config import settings
from app.database import init_db
from app.scheduler import scheduler
from app.api.tasks import router as tasks_router

# Configure loguru for file logging
logger.add(
    "logs/autoai.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=settings.log_level,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle: startup and shutdown events."""
    # Startup
    logger.info("Starting AutoAI application...")
    await init_db()
    scheduler.start()
    logger.info("AutoAI application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AutoAI application...")
    scheduler.shutdown()
    logger.info("AutoAI application shutdown complete")


app = FastAPI(
    title="AutoAI",
    description="Automated AI Task Execution System",
    version="0.1.0",
    lifespan=lifespan,
)

# Register API routers
app.include_router(tasks_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
