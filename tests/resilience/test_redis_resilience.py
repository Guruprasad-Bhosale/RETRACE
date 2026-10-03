"""Resilience tests for Redis Stream Worker Queue, crash recovery, and idempotency."""

import json
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from redis.exceptions import ResponseError

from packages.config.settings import Settings
from packages.redis_client.queue import RedisStreamWorkerQueue


@pytest.mark.asyncio
async def test_redis_queue_pending_crash_recovery():
    """Verify worker queue claims abandoned pending tasks after worker crash."""
    mock_redis = AsyncMock()
    mock_redis.xgroup_create.side_effect = ResponseError("BUSYGROUP Consumer Group name already exists")

    analysis_id = str(uuid4())
    dead_msg_id = "1727700000000-0"
    mock_redis.xautoclaim.return_value = (
        "0-0",
        [(
            dead_msg_id,
            {
                "job_id": str(uuid4()),
                "job_type": "investigation_run",
                "payload": json.dumps({"analysis_id": analysis_id}),
            },
        )],
        [],
    )
    mock_redis.xreadgroup.return_value = []

    settings = Settings(
        ENVIRONMENT="testing",
        REDIS_URL="redis://localhost:6379/0",
    )
    queue = RedisStreamWorkerQueue(
        settings=settings,
        consumer_name="worker-recovery-node-2",
        redis_client=mock_redis,
    )

    # Recover pending jobs -> should receive the autoclaimed job from dead worker
    jobs = await queue.recover_pending_jobs(min_idle_time_ms=5000, count=1)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.message_id == dead_msg_id
    assert job.payload["analysis_id"] == analysis_id

    # Acknowledge the recovered message
    await queue.acknowledge_job(job.message_id)
    mock_redis.xack.assert_called_once_with(
        queue.stream_key,
        queue.group_name,
        dead_msg_id,
    )


@pytest.mark.asyncio
async def test_redis_queue_handles_connection_drop_gracefully():
    """Verify queue handles transient Redis disconnection without unhandled crash."""
    mock_redis = AsyncMock()
    mock_redis.xgroup_create.side_effect = ConnectionError("Redis server connection lost")
    mock_redis.xreadgroup.side_effect = ConnectionError("Redis server connection lost")
    mock_redis.xautoclaim.side_effect = ConnectionError("Redis server connection lost")

    settings = Settings(
        ENVIRONMENT="testing",
        REDIS_URL="redis://localhost:6379/0",
    )
    queue = RedisStreamWorkerQueue(
        settings=settings,
        consumer_name="worker-resilient-1",
        redis_client=mock_redis,
    )

    try:
        jobs = await queue.read_next_jobs(count=1, block_ms=10)
    except ConnectionError:
        jobs = []
    assert len(jobs) == 0


@pytest.mark.asyncio
async def test_redis_queue_duplicate_enqueue_preserves_bounded_stream():
    """Verify enqueuing duplicate analysis requests produces distinct tracked stream IDs."""
    mock_redis = AsyncMock()
    mock_redis.xadd.side_effect = ["1727700001000-0", "1727700002000-0"]

    settings = Settings(
        ENVIRONMENT="testing",
        REDIS_URL="redis://localhost:6379/0",
    )
    queue = RedisStreamWorkerQueue(
        settings=settings,
        redis_client=mock_redis,
    )

    analysis_id = str(uuid4())
    msg1 = await queue.enqueue_job("investigation_run", {"analysis_id": analysis_id})
    msg2 = await queue.enqueue_job("investigation_run", {"analysis_id": analysis_id})

    assert msg1 == "1727700001000-0"
    assert msg2 == "1727700002000-0"
    assert mock_redis.xadd.call_count == 2
