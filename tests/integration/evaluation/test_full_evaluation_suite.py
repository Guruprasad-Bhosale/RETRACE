"""Integration test for full evaluation suite execution and report generation."""

import pytest

from apps.worker.evaluation.models import EvaluationSuiteResult
from apps.worker.evaluation.reporter import EvaluationReportGenerator
from apps.worker.evaluation.runner import BenchmarkRunner
from benchmarks.corpus.synthetic import load_synthetic_suite


@pytest.mark.asyncio
async def test_full_synthetic_evaluation_suite():
    suite = load_synthetic_suite()
    runner = BenchmarkRunner()

    suite_res: EvaluationSuiteResult = await runner.run_suite(suite)

    assert suite_res.suite_id == "synthetic-suite"
    assert len(suite_res.results) == 3
    assert suite_res.summary.total_cases == 3

    # Verify report generation on suite result
    md = EvaluationReportGenerator.generate_markdown_report(suite_res)
    assert "RETRACE Benchmark Evaluation Report" in md
    assert "SYNTH-001" in md
    assert "SYNTH-002" in md
    assert "SYNTH-003" in md

    json_report = EvaluationReportGenerator.generate_json_report(suite_res)
    assert "synthetic-suite" in json_report
