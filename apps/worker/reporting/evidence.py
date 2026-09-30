"""Evidence Chain Builder.

Constructs an unbroken, verifiable causal chain connecting Phase 6 differences,
Phase 7 classifications, Phase 8 reproductions, Phase 9 attributions, and Phase 10 tests.
"""

from apps.worker.regression.models import RegressionClassification
from apps.worker.reporting.models import (
    EvidenceChain,
    EvidenceChainNode,
    EvidenceNodeType,
)
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.models import RootCauseResult
from apps.worker.synthesis.models import GeneratedTest


class EvidenceChainBuilder:
    """Assembles structured, verifiable causal evidence chains across all investigation phases."""

    @classmethod
    def build_chain(
        cls,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        root_cause: RootCauseResult | None = None,
        generated_test: GeneratedTest | None = None,
    ) -> EvidenceChain:
        """Construct the complete causal chain from upstream evidence."""
        nodes: list[EvidenceChainNode] = []
        details = classification.evidence.details if classification.evidence else {}

        # 1. Observed Difference (Phase 6)
        diff_node = EvidenceChainNode(
            node_id=f"node_diff_{classification.difference_id[:8]}",
            node_type=EvidenceNodeType.OBSERVED_DIFFERENCE,
            title="Observed Semantic Difference",
            phase_origin="Phase 6: Semantic Difference Engine",
            status="OBSERVED",
            evidence_ids=[classification.difference_id],
            summary=f"Behavioral delta observed on subject '{classification.evidence.canonical_subject if classification.evidence else ''}'.",
            details=details,
        )
        nodes.append(diff_node)

        # 2. Regression Classification (Phase 7)
        cat_val = classification.category.value if hasattr(classification.category, "value") else str(classification.category)
        stat_val = classification.status.value if hasattr(classification.status, "value") else str(classification.status)
        clf_node = EvidenceChainNode(
            node_id=f"node_clf_{classification.classification_id[:8]}",
            node_type=EvidenceNodeType.REGRESSION_CLASSIFICATION,
            title=f"Regression Classification: {cat_val}",
            phase_origin="Phase 7: Regression Classification",
            status=stat_val,
            evidence_ids=[classification.classification_id],
            summary=f"Classified as {stat_val} under rule '{classification.rule_id}': {classification.reason}",
            details={"rule_id": classification.rule_id, "category": cat_val, "reason": classification.reason},
        )
        nodes.append(clf_node)

        # 3. Reproduction Replay (Phase 8)
        if reproduction:
            repro_node = EvidenceChainNode(
                node_id=f"node_repro_{reproduction.reproduction_id[:8]}",
                node_type=EvidenceNodeType.REPRODUCTION_REPLAY,
                title="Autonomous Fresh Reproduction",
                phase_origin="Phase 8: Autonomous Reproduction",
                status=reproduction.status.value,
                evidence_ids=[reproduction.reproduction_id],
                summary=f"Executed {len(reproduction.path.steps)} causal replay steps with status {reproduction.status.value}.",
                details={
                    "strategy": reproduction.strategy.value,
                    "attempts": len(reproduction.attempts),
                    "path_signature": reproduction.path.path_signature,
                },
            )
            nodes.append(repro_node)

        # 4. Root Cause Localization (Phase 9)
        if root_cause:
            rc_node = EvidenceChainNode(
                node_id=f"node_rc_{root_cause.root_cause_id[:8]}",
                node_type=EvidenceNodeType.ROOT_CAUSE_LOCALIZATION,
                title="Root Cause Localization",
                phase_origin="Phase 9: Root Cause Localization & Attribution",
                status=root_cause.status.value,
                evidence_ids=[root_cause.root_cause_id],
                summary=f"Localization status: {root_cause.status.value}.",
                details={
                    "status": root_cause.status.value,
                    "attributions_count": len(root_cause.attributions),
                    "candidate_locations_count": len(root_cause.candidate_locations),
                },
            )
            nodes.append(rc_node)

            # 5. Changed Source Region (Phase 9)
            if root_cause.primary_attribution:
                primary = root_cause.primary_attribution
                loc = primary.source_location
                loc_node = EvidenceChainNode(
                    node_id=f"node_src_{loc.start_line}_{loc.end_line}",
                    node_type=EvidenceNodeType.CHANGED_SOURCE_REGION,
                    title="Changed Source Code Region",
                    phase_origin="Phase 9: AST Symbol Locator",
                    status=primary.relationship_type.value,
                    evidence_ids=[primary.attribution_id],
                    summary=f"Localized to {loc.file_path} (Lines {loc.start_line}-{loc.end_line}) in symbol '{loc.symbol_name or 'top-level'}'.",
                    details={
                        "file_path": loc.file_path,
                        "start_line": loc.start_line,
                        "end_line": loc.end_line,
                        "symbol_name": loc.symbol_name,
                        "relationship_type": primary.relationship_type.value,
                    },
                )
                nodes.append(loc_node)

                # 6. Git Diff Hunk (Phase 9)
                if primary.diff_hunk:
                    hunk = primary.diff_hunk
                    hunk_node = EvidenceChainNode(
                        node_id=f"node_hunk_{hunk.new_start}",
                        node_type=EvidenceNodeType.GIT_DIFF_HUNK,
                        title="Unified Git Diff Hunk",
                        phase_origin="Phase 9: Safe Git Diff Parser",
                        status="DIFF_MAPPED",
                        evidence_ids=[primary.attribution_id],
                        summary=f"Diff hunk @ +{hunk.new_start},{hunk.new_lines}.",
                        details={
                            "hunk_header": hunk.header,
                            "lines_added": len(hunk.added_lines),
                            "lines_deleted": len(hunk.deleted_lines),
                        },
                    )
                    nodes.append(hunk_node)

                # 7. Commit Attribution (Phase 9)
                if primary.commit:
                    cmt = primary.commit
                    cmt_node = EvidenceChainNode(
                        node_id=f"node_cmt_{cmt.commit_hash[:8]}",
                        node_type=EvidenceNodeType.COMMIT_ATTRIBUTION,
                        title="Attributed Git Commit",
                        phase_origin="Phase 9: Commit Attributor",
                        status=primary.commit_attribution_type.value,
                        evidence_ids=[cmt.commit_hash],
                        summary=f"Commit {cmt.commit_hash[:8]} by {cmt.author_name} ({primary.commit_attribution_type.value}): {cmt.message}",
                        details={
                            "commit_hash": cmt.commit_hash,
                            "author": cmt.author_name,
                            "attribution_type": primary.commit_attribution_type.value,
                        },
                    )
                    nodes.append(cmt_node)

        # 8. Synthesized Test (Phase 10)
        if generated_test:
            test_node = EvidenceChainNode(
                node_id=f"node_test_{generated_test.test_id[:8]}",
                node_type=EvidenceNodeType.SYNTHESIZED_TEST,
                title="Synthesized Playwright Test",
                phase_origin="Phase 10: Test Synthesis",
                status=generated_test.status.value,
                evidence_ids=[generated_test.test_id],
                summary=f"Synthesized {generated_test.framework.value} test with {len(generated_test.steps)} steps and {len(generated_test.assertions)} assertions ({generated_test.validation_status.value}).",
                details={
                    "framework": generated_test.framework.value,
                    "language": generated_test.language.value,
                    "validation_status": generated_test.validation_status.value,
                },
            )
            nodes.append(test_node)

        chain_id = f"chain_{classification.classification_id[:8]}"
        root_id = nodes[0].node_id if nodes else None
        leaf_id = nodes[-1].node_id if nodes else None

        return EvidenceChain(
            chain_id=chain_id,
            nodes=nodes,
            root_node_id=root_id,
            leaf_node_id=leaf_id,
        )
