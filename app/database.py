"""SQLAlchemy Async Engine and Session Configuration."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(AsyncAttrs, DeclarativeBase):
    """SQLAlchemy declarative base class with async support."""
    pass


# Lazy-loaded engine and session maker singletons
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get the async engine singleton, creating it on first access.

    This lazy-loading pattern allows tests to configure environment
    before the engine is created.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get the async session maker singleton, creating it on first access."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_maker


async def init_db():
    """Initialize database tables.

    Models must be imported before calling this function
    to register them with Base.metadata.
    """
    # Import models to register them with Base.metadata
    from app import models  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session


def reset_engine() -> None:
    """Reset engine and session maker singletons.

    Used by tests to reset state between test runs.
    """
    global _engine, _async_session_maker
    _engine = None
    _async_session_maker = None
