"""Provenance Construction and Lineage Validation Layer.

Enforces strict separation between historical comparative observations,
fresh reproduction replay evidence, and Git/AST source history records.
"""

from uuid import UUID

from apps.worker.regression.models import RegressionClassification
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.models import (
    ComparativeBehavioralEvidence,
    FreshReproductionEvidence,
    RepositoryContext,
    RootCauseProvenance,
    SourceHistoryEvidence,
)


class RootCauseProvenanceBuilder:
    """Builder for immutable provenance records with strict evidence segregation."""

    @classmethod
    def build_provenance(
        cls,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        repo_ctx: RepositoryContext,
        diff_files_count: int = 0,
    ) -> RootCauseProvenance:
        """Construct RootCauseProvenance guaranteeing complete evidence lineage."""
        hist_ids: list[UUID] = []
        if classification.evidence.observation_a_id:
            hist_ids.append(classification.evidence.observation_a_id)
        if classification.evidence.observation_b_id:
            hist_ids.append(classification.evidence.observation_b_id)

        comp_evidence = ComparativeBehavioralEvidence(
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            historical_observation_ids=hist_ids,
            artifact_references=classification.evidence.artifact_references,
        )

        fresh_ids: list[UUID] = []
        repro_id: str | None = None
        reproduced = False
        if reproduction:
            repro_id = reproduction.reproduction_id
            reproduced = reproduction.status.value == "REPRODUCED"
            for attempt in reproduction.attempts:
                for obs in attempt.evidence.observations_a + attempt.evidence.observations_b:
                    fresh_ids.append(obs.reproduction_observation_id)

        fresh_evidence = FreshReproductionEvidence(
            reproduction_id=repro_id,
            fresh_observation_ids=fresh_ids,
            reproduced=reproduced,
        )

        commits = [c.commit_hash for c in repo_ctx.commits]
        src_history = SourceHistoryEvidence(
            repository_path=repo_ctx.repository_path or repo_ctx.version_b_path or "",
            baseline_ref=repo_ctx.baseline_ref,
            target_ref=repo_ctx.target_ref,
            commit_hashes=commits,
            diff_files_count=diff_files_count,
        )

        return RootCauseProvenance(
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            reproduction_id=repro_id,
            comparative_evidence=comp_evidence,
            reproduction_evidence=fresh_evidence,
            source_history_evidence=src_history,
            historical_observation_ids=hist_ids,
            fresh_reproduction_observation_ids=fresh_ids,
            artifact_references=classification.evidence.artifact_references,
            repository_path=repo_ctx.repository_path or repo_ctx.version_b_path or "",
            baseline_ref=repo_ctx.baseline_ref,
            target_ref=repo_ctx.target_ref,
            commit_hashes=commits,
        )
