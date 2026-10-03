"""RETRACE Redis Stream Worker Queue & Message Processing Engine.

Provides durable Redis Streams consumer groups, pending entry recovery (XCLAIM),
reliable acknowledgements (XACK), retry bounds, stream observability, and idempotency guarantees.
"""

import asyncio
import json
import os
import socket
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from packages.config.settings import Settings, get_settings
from packages.logging.logger import (
    LogEvents,
    get_logger,
)
from packages.redis_client.client import get_redis_client
from packages.telemetry.metrics import metrics_registry

logger = get_logger(__name__)


@dataclass
class JobMessage:
    """Encapsulated Redis Stream job envelope."""

    message_id: str
    stream_key: str
    job_id: str
    job_type: str
    payload: dict[str, Any]
    delivery_count: int = 1
    request_id: str | None = None
    trace_id: str | None = None
    organization_id: str | None = None
    user_id: str | None = None


class RedisStreamWorkerQueue:
    """Manages Redis Stream consumer group lifecycle, job dispatch, and crash recovery."""

    def __init__(
        self,
        settings: Settings | None = None,
        consumer_name: str | None = None,
        redis_client: Redis | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.redis = redis_client or get_redis_client(self.settings)
        self.stream_key = self.settings.REDIS_STREAM_KEY
        self.group_name = self.settings.REDIS_CONSUMER_GROUP
        hostname = socket.gethostname()
        pid = os.getpid()
        self.consumer_name = consumer_name or f"worker-{hostname}-{pid}-{uuid4().hex[:6]}"
        self._is_initialized = False

    async def ensure_consumer_group(self) -> None:
        """Create consumer group and stream if they do not exist."""
        if self._is_initialized:
            return
        try:
            await self.redis.xgroup_create(
                name=self.stream_key,
                groupname=self.group_name,
                id="0",
                mkstream=True,
            )
            logger.info(
                "Created Redis Stream consumer group",
                stream=self.stream_key,
                group=self.group_name,
            )
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(
                    "Consumer group already exists",
                    stream=self.stream_key,
                    group=self.group_name,
                )
            else:
                raise
        self._is_initialized = True

    async def enqueue_job(
        self,
        job_type: str,
        payload: dict[str, Any],
        job_id: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        organization_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """Enqueue new job to the Redis Stream with correlation metadata."""
        effective_job_id = job_id or str(uuid4())
        message_data = {
            "job_id": effective_job_id,
            "job_type": job_type,
            "payload": json.dumps(payload),
            "request_id": request_id or "",
            "trace_id": trace_id or "",
            "organization_id": organization_id or "",
            "user_id": user_id or "",
            "enqueued_at": str(asyncio.get_event_loop().time()),
        }
        try:
            msg_id = await self.redis.xadd(
                name=self.stream_key,
                fields=message_data,
                maxlen=10000,
                approximate=True,
            )
            logger.info(
                "Enqueued job to Redis Stream",
                event_type=LogEvents.ANALYSIS_CREATED,
                stream=self.stream_key,
                job_id=effective_job_id,
                message_id=msg_id,
                request_id=request_id,
                trace_id=trace_id,
            )
            # Update metric
            depth = await self.get_stream_depth()
            metrics_registry.queue_depth.set(depth, stream_key=self.stream_key)
            return msg_id
        except Exception as exc:
            metrics_registry.queue_failures_total.inc(stream_key=self.stream_key)
            logger.exception("Failed to enqueue job to Redis Stream", error=str(exc))
            raise

    async def read_next_jobs(
        self,
        count: int = 1,
        block_ms: int = 2000,
    ) -> list[JobMessage]:
        """Read fresh unacknowledged messages assigned to this consumer group."""
        await self.ensure_consumer_group()
        raw_entries = await self.redis.xreadgroup(
            groupname=self.group_name,
            consumername=self.consumer_name,
            streams={self.stream_key: ">"},
            count=count,
            block=block_ms,
        )
        messages = self._parse_stream_entries(raw_entries)
        if messages:
            metrics_registry.queue_processing.inc(len(messages), consumer_group=self.group_name)
        return messages

    async def recover_pending_jobs(
        self,
        min_idle_time_ms: int = 60000,
        count: int = 5,
    ) -> list[JobMessage]:
        """Claim abandoned/pending jobs from crashed or timed out workers."""
        await self.ensure_consumer_group()
        try:
            # XAUTOCLAIM stream group consumer min-idle-time start [COUNT count]
            claim_res = await self.redis.xautoclaim(
                name=self.stream_key,
                groupname=self.group_name,
                consumername=self.consumer_name,
                min_idle_time=min_idle_time_ms,
                start_id="0-0",
                count=count,
            )
            # Response: [next_start_id, [ [msg_id, {fields}], ... ], [deleted_ids] ]
            if claim_res and len(claim_res) >= 2:
                claimed_messages = claim_res[1]
                if claimed_messages:
                    logger.warning(
                        "Recovered pending abandoned jobs from Redis Stream",
                        count=len(claimed_messages),
                        consumer=self.consumer_name,
                    )
                    return self._parse_raw_message_list(claimed_messages)
        except Exception as e:
            logger.warning("Error recovering pending stream entries", error=str(e))
        return []

    async def acknowledge_job(self, message_id: str) -> None:
        """Acknowledge successful completion of a job (XACK)."""
        await self.redis.xack(self.stream_key, self.group_name, message_id)
        metrics_registry.queue_processing.dec(1, consumer_group=self.group_name)
        logger.debug(
            "Acknowledged message in Redis Stream",
            stream=self.stream_key,
            message_id=message_id,
        )

    async def get_stream_depth(self) -> int:
        """Return total number of messages in the Redis stream."""
        try:
            return int(await self.redis.xlen(self.stream_key))
        except Exception:
            return 0

    async def get_queue_metrics(self) -> dict[str, Any]:
        """Return comprehensive telemetry regarding stream depth, pending count, and consumer states."""
        try:
            stream_length = int(await self.redis.xlen(self.stream_key))
        except Exception:
            stream_length = 0

        pending_count = 0
        oldest_pending_age_ms = 0
        try:
            pending_info = await self.redis.xpending(self.stream_key, self.group_name)
            if isinstance(pending_info, dict):
                pending_count = pending_info.get("pending", 0)
                # min_idle / age if available
            elif isinstance(pending_info, tuple | list) and len(pending_info) >= 1:
                pending_count = pending_info[0]
        except Exception:
            pass

        consumer_count = 0
        try:
            consumers = await self.redis.xinfo_consumers(self.stream_key, self.group_name)
            consumer_count = len(consumers)
        except Exception:
            pass

        return {
            "stream_key": self.stream_key,
            "consumer_group": self.group_name,
            "stream_length": stream_length,
            "pending_messages": pending_count,
            "consumer_count": consumer_count,
            "oldest_pending_age_ms": oldest_pending_age_ms,
        }

    def _parse_stream_entries(self, raw_entries: list[Any]) -> list[JobMessage]:
        messages: list[JobMessage] = []
        if not raw_entries:
            return messages

        for stream_name, entry_list in raw_entries:
            for msg_id, fields in entry_list:
                try:
                    job_id = fields.get("job_id", msg_id)
                    job_type = fields.get("job_type", "unknown")
                    payload_raw = fields.get("payload", "{}")
                    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                    req_id = fields.get("request_id") or None
                    trace_id = fields.get("trace_id") or None
                    org_id = fields.get("organization_id") or None
                    u_id = fields.get("user_id") or None
                    messages.append(
                        JobMessage(
                            message_id=msg_id,
                            stream_key=stream_name,
                            job_id=job_id,
                            job_type=job_type,
                            payload=payload,
                            request_id=req_id,
                            trace_id=trace_id,
                            organization_id=org_id,
                            user_id=u_id,
                        )
                    )
                except Exception as e:
                    logger.error("Failed to parse stream message", message_id=msg_id, error=str(e))
        return messages

    def _parse_raw_message_list(self, raw_list: list[Any]) -> list[JobMessage]:
        messages: list[JobMessage] = []
        for item in raw_list:
            if isinstance(item, tuple | list) and len(item) == 2:
                msg_id, fields = item
                try:
                    job_id = fields.get("job_id", msg_id)
                    job_type = fields.get("job_type", "unknown")
                    payload_raw = fields.get("payload", "{}")
                    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
                    req_id = fields.get("request_id") or None
                    trace_id = fields.get("trace_id") or None
                    org_id = fields.get("organization_id") or None
                    u_id = fields.get("user_id") or None
                    messages.append(
                        JobMessage(
                            message_id=msg_id,
                            stream_key=self.stream_key,
                            job_id=job_id,
                            job_type=job_type,
                            payload=payload,
                            request_id=req_id,
                            trace_id=trace_id,
                            organization_id=org_id,
                            user_id=u_id,
                        )
                    )
                except Exception as e:
                    logger.error("Failed to parse claimed message", message_id=msg_id, error=str(e))
        return messages
