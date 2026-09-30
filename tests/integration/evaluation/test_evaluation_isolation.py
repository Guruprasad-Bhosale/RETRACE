"""Integration test for evaluation environment and artifact storage isolation."""

import shutil
import tempfile
from pathlib import Path

import pytest

from apps.worker.evaluation.runner import BenchmarkRunner
from benchmarks.corpus.synthetic import load_synthetic_suite


@pytest.mark.asyncio
async def test_evaluation_artifact_isolation():
    tmp_dir = tempfile.mkdtemp(prefix="retrace_eval_iso_")
    try:
        storage_root = Path(tmp_dir) / "evaluation_isolated_artifacts"
        suite = load_synthetic_suite()
        runner = BenchmarkRunner(storage_root=storage_root)

        case = suite.cases[0]
        eval_res = await runner.run_case(case)

        assert eval_res.case_id == "SYNTH-001"
        assert runner.storage_root == storage_root
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
