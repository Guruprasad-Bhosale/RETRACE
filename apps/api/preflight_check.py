"""CLI tool for executing production deployment preflight verification."""

import json
import sys

from packages.config.preflight import PreflightStatus, ProductionPreflightValidator


def main() -> None:
    validator = ProductionPreflightValidator()
    report = validator.run_all_checks()

    print("=" * 70)
    print("           RETRACE PRODUCTION DEPLOYMENT PREFLIGHT CHECK")
    print("=" * 70)

    for check in report.results:
        status_symbol = (
            "[ PASS ]"
            if check.status == PreflightStatus.PASS
            else "[ FAIL ]"
            if check.status == PreflightStatus.FAIL
            else "[BLOCKED]"
        )
        dots = "." * (35 - len(check.name))
        print(f" {check.name} {dots} {status_symbol}  {check.details}")

    print("=" * 70)
    print(f" OVERALL PREFLIGHT STATUS : {report.overall_status.value}")
    print(f" SUMMARY                  : {report.summary}")
    print("=" * 70)

    if "--json" in sys.argv:
        print("\nJSON Output:")
        print(json.dumps(report.to_dict(), indent=2))

    if report.overall_status == PreflightStatus.FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()
