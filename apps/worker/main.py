"""RETRACE Background Analysis Worker Entrypoint.

Responsible for consuming jobs from Redis Streams, executing LangGraph investigation workflows,
enforcing resource boundaries, propagating correlation context, and ensuring crash recovery and graceful shutdown.
"""

import asyncio
import os
import signal
import socket
import time
from typing import Any
from uuid import UUID, uuid4

from apps.worker.orchestration.models import (
    ExecutionPolicy,
    InvestigationRequest,
    ResourceBudget,
    VersionConfig,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner
from packages.config.settings import get_settings
from packages.db.session import close_database
from packages.logging.logger import (
    LogEvents,
    clear_correlation_context,
    get_logger,
    set_correlation_context,
    setup_logging,
)
from packages.redis_client.client import check_redis_health, close_redis
from packages.redis_client.queue import JobMessage, RedisStreamWorkerQueue
from packages.telemetry.metrics import metrics_registry
from packages.telemetry.provider import setup_telemetry, start_trace_span

settings = get_settings()

setup_logging(
    service_name="retrace-worker",
    log_level=settings.LOG_LEVEL,
    environment=settings.ENVIRONMENT,
)

setup_telemetry(
    service_name="retrace-worker",
    environment=settings.ENVIRONMENT,
)

logger = get_logger(__name__)


class AnalysisWorker:
    """Production-hardened async background analysis worker process."""

    def __init__(self) -> None:
        self.running = False
        self.worker_id = f"worker-{socket.gethostname()}-{os.getpid()}-{uuid4().hex[:6]}"
        self.queue = RedisStreamWorkerQueue(consumer_name=self.worker_id)
        self.current_task: asyncio.Task[Any] | None = None
        self._processed_count = 0

    async def start(self) -> None:
        """Start worker main loop."""
        self.running = True
        logger.info(
            "RETRACE Analysis Worker started",
            worker_id=self.worker_id,
            stream_key=settings.REDIS_STREAM_KEY,
            consumer_group=settings.REDIS_CONSUMER_GROUP,
            environment=settings.ENVIRONMENT,
            max_concurrency=settings.WORKER_CONCURRENCY,
        )

        # 1. Verify Redis connectivity & initialize consumer group
        redis_status = await check_redis_health(settings)
        if not redis_status.get("healthy"):
            logger.error("Worker failed to connect to Redis on startup", redis=redis_status)
        else:
            try:
                await self.queue.ensure_consumer_group()
            except Exception as e:
                logger.warning("Could not auto-create consumer group on startup", error=str(e))

        # 2. Main Consumer Loop
        while self.running:
            try:
                # First check for abandoned/pending jobs from crashed workers
                pending_jobs = await self.queue.recover_pending_jobs(
                    min_idle_time_ms=settings.REDIS_JOB_TIMEOUT_S * 1000,
                    count=1,
                )
                if pending_jobs:
                    for job in pending_jobs:
                        if not self.running:
                            break
                        await self.process_job(job)
                    continue

                # Read next fresh jobs from stream
                jobs = await self.queue.read_next_jobs(count=1, block_ms=2000)
                for job in jobs:
                    if not self.running:
                        break
                    await self.process_job(job)

            except asyncio.CancelledError:
                logger.info("Worker received cancellation signal")
                break
            except Exception as e:
                logger.error("Error in worker main loop", error=str(e))
                await asyncio.sleep(2.0)

        await self.shutdown()

    async def process_job(self, job: JobMessage) -> None:
        """Process a single job envelope with correlation propagation and error isolation."""
        set_correlation_context(
            request_id=job.request_id,
            trace_id=job.trace_id,
            organization_id=job.organization_id,
            user_id=job.user_id,
        )

        metrics_registry.worker_jobs_claimed_total.inc(job_type=job.job_type)
        start_time = time.perf_counter()

        logger.info(
            "Claimed analysis job",
            event_type=LogEvents.WORKER_JOB_CLAIMED,
            job_id=job.job_id,
            job_type=job.job_type,
            message_id=job.message_id,
            worker_id=self.worker_id,
        )

        with start_trace_span(
            name=f"worker.{job.job_type}",
            trace_id=job.trace_id,
            attributes={
                "worker.id": self.worker_id,
                "worker.job_id": job.job_id,
                "worker.job_type": job.job_type,
            },
        ) as span:
            try:
                if job.job_type == "investigation":
                    payload = job.payload
                    analysis_id = UUID(payload.get("analysis_id", str(uuid4())))
                    project_id = payload.get("project_id", "default-project")
                    version_a = VersionConfig(**payload["version_a"])
                    version_b = VersionConfig(**payload["version_b"])
                    budget = ResourceBudget(**payload.get("budget", {}))
                    policy = ExecutionPolicy(**payload.get("policy", {}))

                    workflow_input = InvestigationRequest(
                        analysis_id=analysis_id,
                        project_id=project_id,
                        version_a=version_a,
                        version_b=version_b,
                        budget=budget,
                        policy=policy,
                    )

                    runner = InvestigationWorkflowRunner()
                    self.current_task = asyncio.create_task(
                        runner.run(workflow_input)
                    )
                    result_state = await self.current_task
                    final_status = result_state.get("status", "completed")

                    metrics_registry.worker_jobs_completed_total.inc(status=str(final_status))
                    logger.info(
                        "Investigation workflow completed",
                        event_type=LogEvents.WORKER_JOB_COMPLETED,
                        job_id=job.job_id,
                        analysis_id=str(analysis_id),
                        status=final_status,
                    )

                # Acknowledge successfully processed message
                await self.queue.acknowledge_job(job.message_id)
                self._processed_count += 1

            except Exception as e:
                span.record_exception(e)
                metrics_registry.worker_jobs_failed_total.inc(error_type=type(e).__name__)
                logger.exception(
                    "Job execution failed",
                    event_type=LogEvents.WORKER_JOB_FAILED,
                    job_id=job.job_id,
                    message_id=job.message_id,
                    error=str(e),
                )
            finally:
                duration_s = time.perf_counter() - start_time
                metrics_registry.worker_job_duration_seconds.observe(duration_s, job_type=job.job_type)
                clear_correlation_context()

    async def stop(self) -> None:
        """Signal worker to stop gracefully."""
        logger.info("Stopping RETRACE Analysis Worker...", worker_id=self.worker_id)
        self.running = False
        if self.current_task and not self.current_task.done():
            logger.info("Waiting for active investigation task to finish or checkpoint...")
            try:
                await asyncio.wait_for(asyncio.shield(self.current_task), timeout=10.0)
            except (TimeoutError, Exception) as e:
                logger.warning("Active task did not complete in grace period", error=str(e))

    async def shutdown(self) -> None:
        """Cleanup resources on exit."""
        logger.info(
            "Cleaning up worker resources...",
            worker_id=self.worker_id,
            processed_jobs=self._processed_count,
        )
        await close_database(settings)
        await close_redis(settings)
        logger.info("Worker shutdown complete.")


async def main() -> None:
    """Worker process entrypoint with OS signal handling."""
    worker = AnalysisWorker()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))
        except NotImplementedError:
            # Windows signal handling fallback
            pass

    try:
        await worker.start()
    except KeyboardInterrupt:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
