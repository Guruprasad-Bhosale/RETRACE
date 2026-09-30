"""Unit Tests for Expected vs Actual Reproduction Verification."""

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


def test_verify_http_status_error():
    """Verify HTTP error in Version B is verified as FULL_MATCH."""
    v_a = uuid4()
    v_b = uuid4()

    obs_a = [
        ReproductionObservation(
            version_id=v_a,
            step_index=1,
            url="http://localhost:3000/cart",
            http_status=200,
        )
    ]
    obs_b = [
        ReproductionObservation(
            version_id=v_b,
            step_index=1,
            url="http://localhost:3000/cart",
            http_status=500,
        )
    ]

    classification = RegressionClassification(
        classification_id="class-http-500",
        difference_id="diff-http-500",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-HTTP-STATUS-ERROR",
        reason="Server 500 error",
        evidence=ClassificationEvidence(difference_id="diff-http-500"),
    )

    verif = ReproductionVerifier.verify(
        classification=classification,
        observations_a=obs_a,
        observations_b=obs_b,
        policy=VerificationPolicy(),
    )

    assert verif.match_status == MatchStatus.FULL_MATCH
    assert verif.observed_match is True
    assert len(verif.matched_evidence) > 0


def test_verify_runtime_page_error():
    """Verify unhandled page error in Version B is verified as FULL_MATCH."""
    v_a = uuid4()
    v_b = uuid4()

    obs_a = [
        ReproductionObservation(
            version_id=v_a,
            step_index=1,
            url="http://localhost:3000/",
            page_errors_count=0,
        )
    ]
    obs_b = [
        ReproductionObservation(
            version_id=v_b,
            step_index=1,
            url="http://localhost:3000/",
            page_errors_count=1,
        )
    ]

    classification = RegressionClassification(
        classification_id="class-page-err",
        difference_id="diff-page-err",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.RUNTIME_ERROR,
        rule_id="RUNTIME-PAGE-ERROR",
        reason="Uncaught TypeError in B",
        evidence=ClassificationEvidence(difference_id="diff-page-err"),
    )

    verif = ReproductionVerifier.verify(
        classification=classification,
        observations_a=obs_a,
        observations_b=obs_b,
        policy=VerificationPolicy(),
    )

    assert verif.match_status == MatchStatus.FULL_MATCH
    assert verif.observed_match is True


def test_verify_action_disappearance():
    """Verify action failure in B with success in A reproduces UI-ACTION-REMOVED."""
    v_a = uuid4()
    v_b = uuid4()

    obs_a = [
        ReproductionObservation(
            version_id=v_a,
            step_index=1,
            url="http://localhost:3000/cart",
            action_success=True,
        )
    ]
    obs_b = [
        ReproductionObservation(
            version_id=v_b,
            step_index=1,
            url="http://localhost:3000/cart",
            action_success=False,
            error_message="Element not found",
        )
    ]

    classification = RegressionClassification(
        classification_id="class-btn-removed",
        difference_id="diff-btn-removed",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.UI_BEHAVIOR,
        rule_id="UI-ACTION-REMOVED",
        reason="Checkout button removed",
        evidence=ClassificationEvidence(difference_id="diff-btn-removed"),
    )

    verif = ReproductionVerifier.verify(
        classification=classification,
        observations_a=obs_a,
        observations_b=obs_b,
        policy=VerificationPolicy(),
    )

    assert verif.match_status == MatchStatus.FULL_MATCH
    assert verif.observed_match is True


def test_verify_calculation_mismatch():
    """Verify DOM structure mismatch reproduces CALC-OUTPUT-CHANGED."""
    v_a = uuid4()
    v_b = uuid4()

    obs_a = [
        ReproductionObservation(
            version_id=v_a,
            step_index=1,
            url="http://localhost:3000/cart",
            dom_hash="hash_total_100",
        )
    ]
    obs_b = [
        ReproductionObservation(
            version_id=v_b,
            step_index=1,
            url="http://localhost:3000/cart",
            dom_hash="hash_total_120",
        )
    ]

    classification = RegressionClassification(
        classification_id="class-calc",
        difference_id="diff-calc",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.CALCULATION,
        rule_id="CALC-OUTPUT-CHANGED",
        reason="Total calculation changed",
        evidence=ClassificationEvidence(difference_id="diff-calc"),
    )

    verif = ReproductionVerifier.verify(
        classification=classification,
        observations_a=obs_a,
        observations_b=obs_b,
        policy=VerificationPolicy(),
    )

    assert verif.match_status == MatchStatus.FULL_MATCH
    assert verif.observed_match is True
