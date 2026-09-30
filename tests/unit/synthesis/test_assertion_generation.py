"""Unit tests for evidence-derived assertion generator."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.models import (
    ReproductionAttemptResult,
    ReproductionEvidence,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
)
from apps.worker.synthesis.assertions import AssertionGenerator
from apps.worker.synthesis.config import SynthesisConfig
from apps.worker.synthesis.models import AssertionCategory


def test_navigation_assertion_generation():
    """Verify navigation assertion derives path from evidence."""
    clf = RegressionClassification(
        classification_id="clf_nav_1",
        difference_id="diff_nav_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.NAVIGATION,
        rule_id="RULE-NAV-DESTINATION-MISMATCH",
        reason="Target failed to navigate to checkout.",
        evidence=ClassificationEvidence(
            difference_id="diff_nav_1",
            details={"expected_url": "http://localhost:3000/checkout", "actual_url": "http://localhost:3000/404"},
        ),
    )
    gen = AssertionGenerator()
    assertions = gen.generate_assertions(clf)
    assert len(assertions) == 1
    assert assertions[0].category == AssertionCategory.NAVIGATION
    assert assertions[0].assertion_type == "toHaveURL"
    assert "/checkout" in str(assertions[0].expected_value)


def test_api_assertion_generation_with_volatile_field_filtering():
    """Verify API assertions sanitize volatile fields (timestamp, request_id)."""
    clf = RegressionClassification(
        classification_id="clf_api_1",
        difference_id="diff_api_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.API_CONTRACT,
        rule_id="RULE-API-STATUS-MISMATCH",
        reason="HTTP status discrepancy on coupon endpoint.",
        evidence=ClassificationEvidence(
            difference_id="diff_api_1",
            details={
                "status_a": 200,
                "status_b": 500,
                "endpoint": "/api/coupons/apply",
                "payload_diff": {
                    "discount_applied": True,
                    "timestamp": "2026-09-30T10:00:00Z",
                    "request_id": "req-999-volatile",
                },
            },
        ),
    )
    gen = AssertionGenerator()
    assertions = gen.generate_assertions(clf)
    assert len(assertions) >= 2
    # Status assertion
    assert any(a.assertion_type == "toBe" and a.expected_value == 200 for a in assertions)
    # Payload assertion for discount_applied
    assert any(a.subject == "apiBody.discount_applied" and a.expected_value is True for a in assertions)
    # Ensure volatile fields are NOT asserted
    assert not any("timestamp" in a.subject for a in assertions)
    assert not any("request_id" in a.subject for a in assertions)


def test_calculation_assertion_generation():
    """Verify calculation numeric assertions."""
    clf = RegressionClassification(
        classification_id="clf_calc_1",
        difference_id="diff_calc_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.CALCULATION,
        rule_id="RULE-CALC-DISCOUNT-INCORRECT",
        reason="Discount amount calculated incorrectly.",
        evidence=ClassificationEvidence(
            difference_id="diff_calc_1",
            details={"expected_value": "$90.00", "actual_value": "$100.00", "target_field": "order_total"},
        ),
    )
    gen = AssertionGenerator()
    assertions = gen.generate_assertions(clf)
    assert len(assertions) == 1
    assert assertions[0].category == AssertionCategory.CALCULATION
    assert assertions[0].expected_value == "$90.00"


def test_accessibility_assertion_generation():
    """Verify accessibility attribute assertion."""
    clf = RegressionClassification(
        classification_id="clf_a11y_1",
        difference_id="diff_a11y_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.ACCESSIBILITY,
        rule_id="RULE-A11Y-ARIA-STRIPPED",
        reason="Button aria-expanded attribute missing.",
        evidence=ClassificationEvidence(
            difference_id="diff_a11y_1",
            details={"attribute": "aria-expanded", "expected_value": "false", "target": "#menu-btn"},
        ),
    )
    gen = AssertionGenerator()
    assertions = gen.generate_assertions(clf)
    assert len(assertions) == 1
    assert assertions[0].category == AssertionCategory.ACCESSIBILITY
    assert assertions[0].assertion_type == "toHaveAttribute"
    assert assertions[0].expected_value == "false"


def test_runtime_error_assertion_generation():
    """Verify runtime error assertion."""
    clf = RegressionClassification(
        classification_id="clf_err_1",
        difference_id="diff_err_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.RUNTIME_ERROR,
        rule_id="RULE-RUNTIME-UNHANDLED-EXCEPTION",
        reason="Unhandled TypeError thrown in cart checkout.",
        evidence=ClassificationEvidence(
            difference_id="diff_err_1",
            details={"error_count_b": 1},
        ),
    )
    gen = AssertionGenerator()
    assertions = gen.generate_assertions(clf)
    assert len(assertions) == 1
    assert assertions[0].category == AssertionCategory.RUNTIME_ERROR
    assert assertions[0].expected_value == 0


def test_performance_assertion_conservative_when_samples_insufficient():
    """Verify performance assertions require manual review when samples < threshold."""
    clf = RegressionClassification(
        classification_id="clf_perf_1",
        difference_id="diff_perf_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.PERFORMANCE,
        rule_id="RULE-PERF-LATENCY-SPIKE",
        reason="Page load latency increased by 1200ms.",
        evidence=ClassificationEvidence(
            difference_id="diff_perf_1",
            details={"latency_a": 150.0, "latency_b": 1350.0},
        ),
    )
    # Only 1 sample in reproduction
    repro = ReproductionResult(
        reproduction_id="repro_perf_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="p1", trajectory_id=uuid4(), classification_id=clf.classification_id,
            difference_id=clf.difference_id, seed_url="http://127.0.0.1/", path_signature="nav",
        ),
        attempts=[
            ReproductionAttemptResult(
                attempt_number=1,
                strategy=ReproductionStrategy.DIRECT_REPLAY,
                status=ReproductionStatus.REPRODUCED,
                evidence=ReproductionEvidence(sample_measurements_ms_a=[150.0], sample_measurements_ms_b=[1350.0]),
            )
        ],
    )
    config = SynthesisConfig(min_performance_samples_for_assertion=3)
    gen = AssertionGenerator(config=config)
    assertions = gen.generate_assertions(clf, reproduction=repro)
    assert len(assertions) == 1
    assert assertions[0].manual_review_required is True
    assert assertions[0].expected_value == "MANUAL_REVIEW_REQUIRED"


def test_performance_assertion_bounded_when_samples_sufficient():
    """Verify performance assertions are bounded when >= threshold samples exist."""
    clf = RegressionClassification(
        classification_id="clf_perf_2",
        difference_id="diff_perf_2",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.PERFORMANCE,
        rule_id="RULE-PERF-LATENCY-SPIKE",
        reason="Page load latency increased.",
        evidence=ClassificationEvidence(difference_id="diff_perf_2"),
    )
    repro = ReproductionResult(
        reproduction_id="repro_perf_2",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="p2", trajectory_id=uuid4(), classification_id=clf.classification_id,
            difference_id=clf.difference_id, seed_url="http://127.0.0.1/", path_signature="nav",
        ),
        attempts=[
            ReproductionAttemptResult(
                attempt_number=1,
                strategy=ReproductionStrategy.DIRECT_REPLAY,
                status=ReproductionStatus.REPRODUCED,
                evidence=ReproductionEvidence(
                    sample_measurements_ms_a=[100.0, 110.0, 105.0],
                    sample_measurements_ms_b=[800.0, 850.0, 820.0],
                ),
            )
        ],
    )
    config = SynthesisConfig(min_performance_samples_for_assertion=3)
    gen = AssertionGenerator(config=config)
    assertions = gen.generate_assertions(clf, reproduction=repro)
    assert len(assertions) == 1
    assert assertions[0].manual_review_required is False
    assert isinstance(assertions[0].expected_value, float)
    assert assertions[0].expected_value > 100.0
