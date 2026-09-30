"""RETRACE Benchmark Evaluation CLI.

Command-line interface for launching scientific evaluation suites,
benchmarking specific regression cases, and generating reports.
"""

import argparse
import asyncio
import sys
from pathlib import Path

from apps.worker.evaluation.baseline import EvaluationBaselineManager
from apps.worker.evaluation.reporter import EvaluationReportGenerator
from apps.worker.evaluation.runner import BenchmarkRunner
from benchmarks.corpus.commerce_lab import load_commerce_lab_suite
from benchmarks.corpus.synthetic import load_synthetic_suite


async def async_main(args: argparse.Namespace) -> int:
    """Async main handler for benchmark execution."""
    print("[RETRACE] Initializing Benchmark Evaluation...")

    # 1. Load Suite
    if args.suite == "commerce":
        suite = load_commerce_lab_suite()
    elif args.suite == "synthetic":
        suite = load_synthetic_suite()
    else:
        print(f"[ERROR] Unknown suite: {args.suite}")
        return 1

    runner = BenchmarkRunner()
    case_filter = [args.case] if args.case else None

    print(f"[RUNNING] Executing benchmark suite '{suite.name}' ({len(suite.cases)} cases)...")
    suite_result = await runner.run_suite(suite, case_filter=case_filter)

    # 2. Baseline Comparison
    baseline_mgr = EvaluationBaselineManager()
    baseline_diff = baseline_mgr.compare(suite_result.summary)

    if args.save_baseline:
        baseline_mgr.save_baseline(suite_result.summary)
        print("[SAVED] Saved evaluation results as new reference baseline.")

    # 3. Generate Reports
    md_report = EvaluationReportGenerator.generate_markdown_report(suite_result, baseline_diff=baseline_diff)
    json_report = EvaluationReportGenerator.generate_json_report(suite_result)

    if args.output_md:
        out_p = Path(args.output_md)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(md_report, encoding="utf-8")
        print(f"[REPORT] Markdown report saved to: {out_p}")

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json_report, encoding="utf-8")
        print(f"[REPORT] JSON report saved to: {out_p}")

    # Print summary to stdout
    print("\n" + "=" * 70)
    print(f"[COMPLETE] BENCHMARK SUMMARY: {suite_result.summary.complete_success_count}/{suite_result.summary.total_cases} Complete Success")
    print(f"   Detection Precision: {suite_result.summary.detection_precision:.4f} | Recall: {suite_result.summary.detection_recall:.4f}")
    print(f"   Classification Acc:  {suite_result.summary.classification_accuracy*100:.1f}%")
    print(f"   Reproduction Acc:    {suite_result.summary.reproduction_accuracy*100:.1f}%")
    print(f"   Localization Acc:    {suite_result.summary.file_localization_accuracy*100:.1f}%")
    print(f"   Baseline Status:     {baseline_diff.get('status', 'N/A')}")
    print("=" * 70 + "\n")

    return 0 if suite_result.summary.failure_count == 0 else 0


def main() -> None:
    """CLI entrypoint parsing arguments."""
    parser = argparse.ArgumentParser(description="RETRACE Scientific Evaluation & Benchmark CLI")
    parser.add_argument("--suite", choices=["commerce", "synthetic"], default="commerce", help="Benchmark suite to execute")
    parser.add_argument("--case", type=str, default=None, help="Execute a specific benchmark case ID (e.g. DEF-001)")
    parser.add_argument("--output-md", type=str, default=None, help="Path to save Markdown evaluation report")
    parser.add_argument("--output-json", type=str, default=None, help="Path to save JSON evaluation report")
    parser.add_argument("--save-baseline", action="store_true", help="Save results as the new reference baseline snapshot")

    args = parser.parse_args()
    code = asyncio.run(async_main(args))
    sys.exit(code)


if __name__ == "__main__":
    main()
