"""Integration test executing a Commerce Lab benchmark case with BenchmarkRunner."""

import socket
import threading
import time

import pytest
import uvicorn

from apps.worker.evaluation.models import EndToEndStatus
from apps.worker.evaluation.runner import BenchmarkRunner
from benchmarks.corpus.commerce_lab import load_commerce_lab_suite
from lab.applications.commerce.v1.app import app as app_v1
from lab.applications.commerce.v2.app import app as app_v2


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def commerce_lab_ports():
    port_v1 = get_free_port()
    port_v2 = get_free_port()

    server_v1 = uvicorn.Server(
        uvicorn.Config(app=app_v1, host="127.0.0.1", port=port_v1, log_level="error")
    )
    server_v2 = uvicorn.Server(
        uvicorn.Config(app=app_v2, host="127.0.0.1", port=port_v2, log_level="error")
    )

    t1 = threading.Thread(target=server_v1.run, daemon=True)
    t2 = threading.Thread(target=server_v2.run, daemon=True)
    t1.start()
    t2.start()

    while not server_v1.started or not server_v2.started:
        time.sleep(0.05)

    base_url_v1 = f"http://127.0.0.1:{port_v1}"
    base_url_v2 = f"http://127.0.0.1:{port_v2}"

    yield {"v1_url": base_url_v1, "v2_url": base_url_v2}

    server_v1.should_exit = True
    server_v2.should_exit = True


@pytest.mark.asyncio
async def test_commerce_benchmark_def001(commerce_lab_ports):
    base_url_a = commerce_lab_ports["v1_url"]
    base_url_b = commerce_lab_ports["v2_url"]
    suite = load_commerce_lab_suite(base_url_a=base_url_a, base_url_b=base_url_b)
    case_def001 = next(c for c in suite.cases if c.case_id == "DEF-001")

    runner = BenchmarkRunner()
    eval_res = await runner.run_case(case_def001)

    assert eval_res.case_id == "DEF-001"
    assert eval_res.detection.is_regression_detected is True
    assert eval_res.detection.true_positive is True
    assert isinstance(eval_res.end_to_end_status, EndToEndStatus)
    assert eval_res.root_cause.file_matched is True
    assert eval_res.synthesis.test_generated is True
    assert eval_res.timing.total_duration_s >= 0
    assert isinstance(eval_res.failure_taxonomy, list)
