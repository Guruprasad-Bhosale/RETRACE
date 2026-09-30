"""Unit Tests for Negative Reproduction Scenarios (Non-Reproduced Regressions)."""

from uuid import uuid4

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


def test_negative_reproduction_both_versions_succeed():
    """Verify that if target Version B no longer exhibits the error during fresh replay, NOT_REPRODUCED is emitted."""
    v_a = uuid4()
    v_b = uuid4()

    # Fresh replay shows BOTH versions returning HTTP 200 (error was transient or flaked)
    obs_a = [
        ReproductionObservation(
            version_id=v_a,
            step_index=1,
            url="http://localhost:3000/checkout",
            http_status=200,
            action_success=True,
        )
    ]
    obs_b = [
        ReproductionObservation(
            version_id=v_b,
            step_index=1,
            url="http://localhost:3000/checkout",
            http_status=200,
            action_success=True,
        )
    ]

    classification = RegressionClassification(
        classification_id="class-flaky-checkout",
        difference_id="diff-flaky-checkout",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-HTTP-STATUS-ERROR",
        reason="Historical 500 error",
        evidence=ClassificationEvidence(difference_id="diff-flaky-checkout"),
    )

    verif = ReproductionVerifier.verify(
        classification=classification,
        observations_a=obs_a,
        observations_b=obs_b,
        policy=VerificationPolicy(),
    )

    assert verif.match_status == MatchStatus.NO_MATCH
    assert verif.observed_match is False
    assert len(verif.mismatched_evidence) > 0
    assert "Expected HTTP error in Version B" in verif.mismatched_evidence[0]
