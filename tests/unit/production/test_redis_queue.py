"""Unit tests for Redis Stream Worker Queue."""

from unittest.mock import AsyncMock

import pytest

from packages.config.settings import Settings
from packages.redis_client.queue import RedisStreamWorkerQueue


@pytest.mark.asyncio
async def test_redis_queue_initialization_and_parsing():
    """Verify stream queue message parsing logic."""
    mock_redis = AsyncMock()
    settings = Settings(ENVIRONMENT="test")
    queue = RedisStreamWorkerQueue(settings=settings, consumer_name="test-worker", redis_client=mock_redis)

    raw_stream_response = [
        (
            "retrace:analysis:jobs",
            [
                (
                    "1711823901-0",
                    {
                        "job_id": "job-123",
                        "job_type": "investigation",
                        "payload": '{"analysis_id": "abc-456"}',
                    },
                )
            ],
        )
    ]

    messages = queue._parse_stream_entries(raw_stream_response)
    assert len(messages) == 1
    assert messages[0].job_id == "job-123"
    assert messages[0].job_type == "investigation"
    assert messages[0].payload == {"analysis_id": "abc-456"}


@pytest.mark.asyncio
async def test_redis_queue_enqueue_job():
    """Verify job enqueuing to stream."""
    mock_redis = AsyncMock()
    mock_redis.xadd.return_value = "1711823901-1"

    settings = Settings(ENVIRONMENT="test")
    queue = RedisStreamWorkerQueue(settings=settings, consumer_name="test-worker", redis_client=mock_redis)

    msg_id = await queue.enqueue_job(job_type="investigation", payload={"task": "diff"}, job_id="custom-id-99")
    assert msg_id == "1711823901-1"
    mock_redis.xadd.assert_called_once()
