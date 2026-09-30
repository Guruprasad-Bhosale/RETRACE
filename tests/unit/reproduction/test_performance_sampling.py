"""Unit Tests for Performance Repeated Measurement Sampling."""

from uuid import uuid4

import pytest

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.config import VerificationPolicy
from apps.worker.reproduction.models import (
    MatchStatus,
    ReproductionObservation,
)
from apps.worker.reproduction.verification import ReproductionVerifier


def test_performance_verification_with_repeated_samples():
    """Verify performance slowdown reproduces using median of repeated sample timings."""
    v_a = uuid4()
    v_b = uuid4()

    obs_a = [ReproductionObservation(version_id=v_a, step_index=1, url="http://localhost:3000/")]
    obs_b = [ReproductionObservation(version_id=v_b, step_index=1, url="http://localhost:3000/")]

    # Sample runs for A: 100ms, 110ms, 105ms -> median 105ms
    samples_a = [100.0, 110.0, 105.0]
    # Sample runs for B: 450ms, 460ms, 440ms -> median 450ms
    # Delta: 450 - 105 = 345ms >= 200ms threshold
    samples_b = [450.0, 460.0, 440.0]

    classification = RegressionClassification(
        classification_id="class-perf-slowdown",
        difference_id="diff-perf-slowdown",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.PERFORMANCE,
        rule_id="PERF-NAVIGATION-SLOWDOWN",
        reason="Navigation latency increased",
        evidence=ClassificationEvidence(difference_id="diff-perf-slowdown"),
    )

    verif = ReproductionVerifier.verify(
        classification=classification,
        observations_a=obs_a,
        observations_b=obs_b,
        policy=VerificationPolicy(performance_delta_threshold_ms=200.0),
        sample_timings_a=samples_a,
        sample_timings_b=samples_b,
    )

    assert verif.match_status == MatchStatus.FULL_MATCH
    assert verif.observed_match is True
    assert verif.observed_difference_summary["delta_ms"] == pytest.approx(345.0)


def test_performance_verification_fails_when_delta_below_threshold():
    """Verify performance verification returns NO_MATCH when delta is below configured threshold."""
    v_a = uuid4()
    v_b = uuid4()

    obs_a = [ReproductionObservation(version_id=v_a, step_index=1, url="http://localhost:3000/")]
    obs_b = [ReproductionObservation(version_id=v_b, step_index=1, url="http://localhost:3000/")]

    samples_a = [100.0, 100.0, 100.0]
    samples_b = [150.0, 150.0, 150.0]  # Delta = 50ms < 200ms

    classification = RegressionClassification(
        classification_id="class-perf-minor",
        difference_id="diff-perf-minor",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.PERFORMANCE,
        rule_id="PERF-NAVIGATION-SLOWDOWN",
        reason="Minor latency increase",
        evidence=ClassificationEvidence(difference_id="diff-perf-minor"),
    )

    verif = ReproductionVerifier.verify(
        classification=classification,
        observations_a=obs_a,
        observations_b=obs_b,
        policy=VerificationPolicy(performance_delta_threshold_ms=200.0),
        sample_timings_a=samples_a,
        sample_timings_b=samples_b,
    )

    assert verif.match_status == MatchStatus.NO_MATCH
    assert verif.observed_match is False
