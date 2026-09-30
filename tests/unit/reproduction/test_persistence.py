"""Unit Tests for Reproduction Persistence and Domain Entity Mapping."""

from uuid import uuid4

from apps.worker.reproduction.models import (
    MatchStatus,
    ReproductionAttemptResult,
    ReproductionEvidence,
    ReproductionStatus,
    ReproductionStrategy,
    ReproductionVerification,
)
from apps.worker.reproduction.persistence import ReproductionPersistenceMapper
from packages.domain.models import ReproductionStatus as DomainReproStatus


def test_map_status_to_domain():
    """Verify mapping of engine reproduction statuses to Phase 1 domain reproduction statuses."""
    mapper = ReproductionPersistenceMapper

    assert mapper.map_status_to_domain(ReproductionStatus.REPRODUCED) == DomainReproStatus.SUCCEEDED
    assert mapper.map_status_to_domain(ReproductionStatus.NOT_REPRODUCED) == DomainReproStatus.FAILED
    assert mapper.map_status_to_domain(ReproductionStatus.FAILED) == DomainReproStatus.ERROR
    assert mapper.map_status_to_domain(ReproductionStatus.BLOCKED) == DomainReproStatus.SKIPPED
    assert mapper.map_status_to_domain(ReproductionStatus.INCONCLUSIVE) == DomainReproStatus.FAILED


def test_to_domain_attempt_entity():
    """Verify transformation of ReproductionAttemptResult to Phase 1 ReproductionAttempt."""
    finding_id = uuid4()
    session_id = uuid4()
    attempt_id = uuid4()

    verification = ReproductionVerification(
        expected_difference_id="diff-1",
        expected_classification_id="class-1",
        expected_rule_id="FUNC-HTTP-STATUS-ERROR",
        expected_category="FUNCTIONAL",
        match_status=MatchStatus.FULL_MATCH,
        observed_match=True,
    )

    attempt = ReproductionAttemptResult(
        attempt_id=attempt_id,
        attempt_number=1,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        status=ReproductionStatus.REPRODUCED,
        verification=verification,
        evidence=ReproductionEvidence(attempt_id=attempt_id),
        duration_ms=125.0,
    )

    domain_entity = ReproductionPersistenceMapper.to_domain_attempt(
        attempt=attempt,
        finding_id=finding_id,
        session_id=session_id,
        path_summary={"steps_count": 2, "signature": "abc1234"},
    )

    assert domain_entity.id == attempt_id
    assert domain_entity.finding_id == finding_id
    assert domain_entity.session_id == session_id
    assert domain_entity.attempt_number == 1
    assert domain_entity.status == DomainReproStatus.SUCCEEDED
    assert "playwright_python" in domain_entity.framework
    assert "abc1234" in domain_entity.script_code
