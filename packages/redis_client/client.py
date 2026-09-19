"""Redis Client Management and Health Check Module."""

from redis.asyncio import Redis, from_url

from packages.config.settings import Settings, get_settings
from packages.logging.logger import get_logger

logger = get_logger(__name__)

_redis_client: Redis | None = None


def get_redis_client(settings: Settings | None = None) -> Redis:
    """Get or instantiate global async Redis client."""
    global _redis_client
    if _redis_client is None:
        cfg = settings or get_settings()
        _redis_client = from_url(
            cfg.REDIS_URL,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
        )
    return _redis_client


async def check_redis_health(settings: Settings | None = None) -> dict[str, str | bool]:
    """Verify Redis server connectivity with PING command."""
    client = get_redis_client(settings)
    try:
        response = await client.ping()
        if response:
            return {"status": "connected", "healthy": True}
        return {"status": "degraded", "healthy": False, "error": "Ping failed"}
    except Exception as e:
        logger.warning("Redis health check failed", error=str(e))
        return {"status": "disconnected", "healthy": False, "error": str(e)}


async def close_redis() -> None:
    """Close Redis client connection on application shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
