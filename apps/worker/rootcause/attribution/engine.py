"""Causal Attribution Engine and Status Decision Layer.

Evaluates localized candidates, constructs immutable RootCauseAttribution records,
and assigns definitive RootCauseStatus without heuristic scores or probabilistic ranking.
"""

from apps.worker.regression.models import RegressionCategory, RegressionClassification
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.ast.models import ASTFileIndex
from apps.worker.rootcause.attribution.commits import CommitAttributor
from apps.worker.rootcause.attribution.evidence import AttributionEvidenceBuilder
from apps.worker.rootcause.config import AttributionConfig
from apps.worker.rootcause.localization.behavioral import BehavioralLocalizer, LocalizedCandidate
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    FileDiff,
    LanguageType,
    RepositoryContext,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
    compute_deterministic_attribution_id,
    compute_deterministic_root_cause_id,
)


class AttributionEngine:
    """Deterministic attribution engine for single regression root-cause evaluation."""

    def __init__(
        self,
        config: AttributionConfig | None = None,
        behavioral_localizer: BehavioralLocalizer | None = None,
        commit_attributor: CommitAttributor | None = None,
    ):
        self.config = config or AttributionConfig()
        self.behavioral_localizer = behavioral_localizer or BehavioralLocalizer()
        self.commit_attributor = commit_attributor or CommitAttributor()

    def attribute(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        diffs: list[FileDiff],
        ast_indices: dict[str, ASTFileIndex],
        repo_ctx: RepositoryContext,
    ) -> RootCauseResult:
        """Perform end-to-end attribution for a classified regression."""
        # Non-regressions are strictly INCONCLUSIVE / not attributed
        if classification.category == RegressionCategory.NON_REGRESSION:
            prov = self._build_provenance(classification, reproduction, repo_ctx)
            rc_id = compute_deterministic_root_cause_id(
                classification_id=classification.classification_id,
                difference_id=classification.difference_id,
                status=RootCauseStatus.INCONCLUSIVE,
                primary_location_key="non_regression",
            )
            return RootCauseResult(
                root_cause_id=rc_id,
                classification_id=classification.classification_id,
                difference_id=classification.difference_id,
                reproduction_id=reproduction.reproduction_id if reproduction else None,
                category=classification.category.value,
                status=RootCauseStatus.INCONCLUSIVE,
                primary_attribution=None,
                attributions=[],
                candidate_locations=[],
                provenance=prov,
                diagnostics={"reason": "Classification is marked as NON_REGRESSION."},
            )

        # Localize candidates
        repo_path = repo_ctx.repository_path or repo_ctx.version_b_path or ""
        candidates = self.behavioral_localizer.localize(
            classification=classification,
            reproduction=reproduction,
            diffs=diffs,
            ast_indices=ast_indices,
            repo_path=repo_path,
        )

        attributions: list[RootCauseAttribution] = []
        candidate_locations: list[SourceLocation] = []

        for cand in candidates:
            candidate_locations.append(cand.source_location)

            # Resolve commit
            commit_meta, commit_type = self.commit_attributor.attribute_commit(
                candidate=cand, repo_ctx=repo_ctx
            )

            # Build evidence
            ev = AttributionEvidenceBuilder.build(
                candidate=cand,
                classification=classification,
                reproduction=reproduction,
                commit=commit_meta,
                commit_attribution_type=commit_type,
            )

            attr_id = compute_deterministic_attribution_id(
                classification_id=classification.classification_id,
                file_path=cand.source_location.file_path,
                start_line=cand.source_location.start_line,
                end_line=cand.source_location.end_line,
                relationship_type=cand.relationship_type,
            )

            attributions.append(
                RootCauseAttribution(
                    attribution_id=attr_id,
                    source_location=cand.source_location,
                    affected_symbol=cand.symbol,
                    relationship_type=cand.relationship_type,
                    commit=commit_meta,
                    commit_attribution_type=commit_type,
                    diff_hunk=cand.diff_hunk,
                    explanation=cand.explanation,
                    evidence=[ev],
                )
            )

        # Determine status
        status = self._evaluate_status(classification, candidates, ast_indices)

        # Upgrade commit attribution to CAUSAL_COMMIT if status is confirmed LOCATED
        if status == RootCauseStatus.LOCATED and attributions:
            top_attr = attributions[0]
            if top_attr.commit_attribution_type in (
                CommitAttributionType.INTRODUCING_COMMIT,
                CommitAttributionType.MODIFYING_COMMIT,
                CommitAttributionType.RELATED_COMMIT,
            ):
                top_attr.commit_attribution_type = CommitAttributionType.CAUSAL_COMMIT
                if top_attr.evidence:
                    top_attr.evidence[0].commit_attribution_type = CommitAttributionType.CAUSAL_COMMIT

        primary_attr = (
            attributions[0]
            if attributions and status in (RootCauseStatus.LOCATED, RootCauseStatus.PARTIALLY_LOCATED, RootCauseStatus.CANDIDATE_ONLY)
            else None
        )

        primary_loc_key = primary_attr.source_location.deterministic_key() if primary_attr else ""
        rc_id = compute_deterministic_root_cause_id(
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            status=status,
            primary_location_key=primary_loc_key,
        )

        provenance = self._build_provenance(classification, reproduction, repo_ctx, len(diffs))

        # Sort attributions deterministically
        attributions.sort(key=lambda a: a.deterministic_sort_key())

        return RootCauseResult(
            root_cause_id=rc_id,
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            reproduction_id=reproduction.reproduction_id if reproduction else None,
            category=classification.category.value,
            status=status,
            primary_attribution=primary_attr,
            attributions=attributions,
            candidate_locations=candidate_locations,
            provenance=provenance,
            diagnostics={
                "candidates_count": len(candidates),
                "attributions_count": len(attributions),
                "rule_id": classification.rule_id,
                "reproduction_status": reproduction.status.value if reproduction else "NOT_REPRODUCED",
            },
        )

    def _evaluate_status(
        self,
        classification: RegressionClassification,
        candidates: list[LocalizedCandidate],
        ast_indices: dict[str, ASTFileIndex],
    ) -> RootCauseStatus:
        """Deterministically determine RootCauseStatus from localized candidate strength."""
        if not candidates:
            return RootCauseStatus.INCONCLUSIVE

        top = candidates[0]
        if top.relationship_type == AttributionRelationshipType.RELATED_CHANGE or top.match_priority < 10:
            return RootCauseStatus.INCONCLUSIVE

        file_path = top.source_location.file_path
        index = ast_indices.get(file_path)
        if index and index.language == LanguageType.UNSUPPORTED_LANGUAGE:
            return RootCauseStatus.UNSUPPORTED

        if classification.category == RegressionCategory.PERFORMANCE:
            # Performance regressions are strictly CANDIDATE_ONLY; LOCATED is prohibited based on timing alone
            return RootCauseStatus.CANDIDATE_ONLY

        if top.match_priority >= 20:
            if top.relationship_type in (
                AttributionRelationshipType.DIRECTLY_CHANGED,
                AttributionRelationshipType.AFFECTED_ROUTE,
                AttributionRelationshipType.AFFECTED_SYMBOL,
            ):
                return RootCauseStatus.LOCATED
            return RootCauseStatus.PARTIALLY_LOCATED

        if top.match_priority >= 10:
            return RootCauseStatus.PARTIALLY_LOCATED

        return RootCauseStatus.CANDIDATE_ONLY

    def _build_provenance(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        repo_ctx: RepositoryContext,
        diff_files_count: int = 0,
    ) -> RootCauseProvenance:
        """Assemble immutable provenance lineage."""
        from apps.worker.rootcause.provenance import RootCauseProvenanceBuilder

        return RootCauseProvenanceBuilder.build_provenance(
            classification=classification,
            reproduction=reproduction,
            repo_ctx=repo_ctx,
            diff_files_count=diff_files_count,
        )
