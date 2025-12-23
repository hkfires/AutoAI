"""FastAPI Application Entry Point with Lifespan Management."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from loguru import logger

from app.config import get_settings, ensure_encryption_key
from app.database import init_db
from app.scheduler import start_scheduler, shutdown_scheduler
from app.api.tasks import router as tasks_router
from app.web.tasks import router as web_tasks_router
from app.web.auth import router as auth_router, AuthRedirectException

# Configure loguru for file logging
settings = get_settings()
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
    ensure_encryption_key()
    await init_db()
    await start_scheduler()
    logger.info("AutoAI application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down AutoAI application...")
    await shutdown_scheduler()
    logger.info("AutoAI application shutdown complete")


app = FastAPI(
    title="AutoAI",
    description="Automated AI Task Execution System",
    version="0.1.0",
    lifespan=lifespan,
)

# Register API routers
app.include_router(tasks_router)
app.include_router(web_tasks_router)
app.include_router(auth_router)


@app.exception_handler(AuthRedirectException)
async def auth_redirect_handler(request: Request, exc: AuthRedirectException):
    """Handle auth redirect exception by redirecting to login page."""
    return RedirectResponse(url="/login", status_code=302)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
