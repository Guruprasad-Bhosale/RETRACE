"""RETRACE Background Analysis Worker Entrypoint.

Responsible for consuming jobs from Redis Streams, executing Playwright browser runs,
performing deterministic diffing, calling AI reasoning agents, and writing verified artifacts.
"""

import asyncio
import signal

from packages.config.settings import get_settings
from packages.logging.logger import get_logger, setup_logging
from packages.redis_client.client import check_redis_health, close_redis

settings = get_settings()

setup_logging(
    service_name="retrace-worker",
    log_level=settings.LOG_LEVEL,
    environment=settings.ENVIRONMENT,
)

logger = get_logger(__name__)


class AnalysisWorker:
    """Async background worker process."""

    def __init__(self) -> None:
        self.running = False

    async def start(self) -> None:
        """Start worker main loop."""
        self.running = True
        logger.info(
            "RETRACE Analysis Worker started",
            stream_key=settings.REDIS_STREAM_KEY,
            consumer_group=settings.REDIS_CONSUMER_GROUP,
            environment=settings.ENVIRONMENT,
        )

        # Verify Redis availability
        redis_status = await check_redis_health()
        logger.info("Worker Redis connection status", redis=redis_status)

        while self.running:
            try:
                # Polling skeleton for Redis Streams (will be extended in future phases)
                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                logger.info("Worker received cancellation signal")
                break
            except Exception as e:
                logger.error("Error in worker event loop", error=str(e))
                await asyncio.sleep(2.0)

        await self.shutdown()

    async def stop(self) -> None:
        """Signal worker to stop gracefully."""
        logger.info("Stopping RETRACE Analysis Worker...")
        self.running = False

    async def shutdown(self) -> None:
        """Cleanup resources on exit."""
        logger.info("Cleaning up worker resources...")
        await close_redis()
        logger.info("Worker shutdown complete.")


async def main() -> None:
    worker = AnalysisWorker()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))
        except NotImplementedError:
            # Signal handling on Windows
            pass

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
