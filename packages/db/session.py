"""Database Async Engine, Session Factory, and Health Checker."""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from packages.config.settings import Settings, get_settings
from packages.logging.logger import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Get or create global AsyncEngine instance."""
    global _engine
    if _engine is None:
        cfg = settings or get_settings()
        engine_kwargs: dict = {"echo": cfg.DEBUG, "future": True}
        if not cfg.DATABASE_URL.startswith("sqlite"):
            engine_kwargs["pool_size"] = cfg.DATABASE_POOL_SIZE
            engine_kwargs["max_overflow"] = cfg.DATABASE_MAX_OVERFLOW
            engine_kwargs["pool_timeout"] = cfg.DATABASE_POOL_TIMEOUT

        _engine = create_async_engine(
            cfg.DATABASE_URL,
            **engine_kwargs,
        )
    return _engine


def get_sessionmaker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    """Get or create global async_sessionmaker instance."""
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine(settings)
        _sessionmaker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining an async database session."""
    sessionmaker_inst = get_sessionmaker()
    async with sessionmaker_inst() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_health(settings: Settings | None = None) -> dict[str, str | bool]:
    """Verify database connectivity and query execution."""
    engine = get_engine(settings)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "connected", "healthy": True}
    except Exception as e:
        logger.warning("Database health check failed", error=str(e))
        return {"status": "disconnected", "healthy": False, "error": str(e)}


async def close_database() -> None:
    """Dispose of engine connections on application shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
