"""Report Section Builder for Investigation Reports.

Builds the 11 mandatory, evidence-derived report sections with strict status preservation
and unranked engineering transparency.
"""

from apps.worker.regression.models import RegressionClassification
from apps.worker.reporting.config import ReportingConfig
from apps.worker.reporting.models import EvidenceChain, ReportSection
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.models import CommitAttributionType, RootCauseResult, RootCauseStatus
from apps.worker.synthesis.models import GeneratedTest


class ReportSectionBuilder:
    """Builds all 11 standardized investigation report sections."""

    def __init__(self, config: ReportingConfig | None = None) -> None:
        self.config = config or ReportingConfig()

    def build_all_sections(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        root_cause: RootCauseResult | None = None,
        generated_test: GeneratedTest | None = None,
        evidence_chain: EvidenceChain | None = None,
    ) -> list[ReportSection]:
        """Generate all 11 standardized sections in canonical order."""
        sections = [
            self._build_section_1_executive_summary(classification, reproduction, root_cause, generated_test),
            self._build_section_2_classification(classification),
            self._build_section_3_reproduction(reproduction),
            self._build_section_4_behavioral_difference(classification),
            self._build_section_5_reproduction_path(reproduction),
            self._build_section_6_expected_vs_actual(classification, reproduction),
            self._build_section_7_source_localization(root_cause),
            self._build_section_8_commit_attribution(root_cause),
            self._build_section_9_evidence_chain(evidence_chain),
            self._build_section_10_generated_test(generated_test),
            self._build_section_11_limitations(classification, reproduction, root_cause),
        ]
        return sections

    def _build_section_1_executive_summary(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        root_cause: RootCauseResult | None,
        generated_test: GeneratedTest | None,
    ) -> ReportSection:
        cat_val = classification.category.value if hasattr(classification.category, "value") else str(classification.category)
        stat_val = classification.status.value if hasattr(classification.status, "value") else str(classification.status)
        repro_val = reproduction.status.value if reproduction else "NOT_ATTEMPTED"
        rc_val = root_cause.status.value if root_cause else "NOT_ANALYZED"
        test_val = generated_test.status.value if generated_test else "NOT_GENERATED"

        lines = [
            "### Overview",
            f"- **Classification**: `{stat_val}` ({cat_val})",
            f"- **Reproduction**: `{repro_val}`",
            f"- **Root Cause Localization**: `{rc_val}`",
            f"- **Regression Test Synthesis**: `{test_val}`",
            "",
            "### Key Finding",
            f"RETRACE identified a `{cat_val}` regression triggered by deterministic rule `{classification.rule_id}`.",
        ]

        if root_cause and root_cause.primary_attribution:
            primary = root_cause.primary_attribution
            loc = primary.source_location
            lines.append(
                f"- **Localized Source Region**: `{loc.file_path}` (Lines {loc.start_line}-{loc.end_line}) in symbol `{loc.symbol_name or 'top-level'}`"
            )
            if primary.commit:
                lines.append(
                    f"- **Attributed Commit**: `{primary.commit.commit_hash[:8]}` ({primary.commit_attribution_type.value}) by {primary.commit.author_name}"
                )

        return ReportSection(
            section_id="sec_1_executive_summary",
            section_number=1,
            title="1. Executive Summary",
            content_markdown="\n".join(lines),
            evidence_ids=[classification.classification_id],
        )

    def _build_section_2_classification(self, classification: RegressionClassification) -> ReportSection:
        cat_val = classification.category.value if hasattr(classification.category, "value") else str(classification.category)
        lines = [
            f"- **Classification ID**: `{classification.classification_id}`",
            f"- **Category**: `{cat_val}`",
            f"- **Status**: `{classification.status.value}`",
            f"- **Deterministic Rule**: `{classification.rule_id}`",
            f"- **Reasoning**: {classification.reason}",
        ]
        if classification.evidence:
            lines.append(f"- **Canonical Subject**: `{classification.evidence.canonical_subject}`")
            lines.append(f"- **Difference ID**: `{classification.evidence.difference_id}`")

        return ReportSection(
            section_id="sec_2_regression_classification",
            section_number=2,
            title="2. Regression Classification",
            content_markdown="\n".join(lines),
            evidence_ids=[classification.classification_id],
        )

    def _build_section_3_reproduction(self, reproduction: ReproductionResult | None) -> ReportSection:
        if not reproduction:
            content = "No autonomous reproduction replay was performed for this classification."
            e_ids = []
        else:
            lines = [
                f"- **Reproduction ID**: `{reproduction.reproduction_id}`",
                f"- **Outcome**: `{reproduction.status.value}`",
                f"- **Strategy**: `{reproduction.strategy.value}`",
                f"- **Total Duration**: {round(reproduction.total_duration_ms, 2)} ms",
                f"- **Replay Attempts**: {len(reproduction.attempts)}",
            ]
            if reproduction.final_verification:
                v = reproduction.final_verification
                lines.append(f"- **Match Status**: `{v.match_status.value}` (Observed Match: `{v.observed_match}`)")
                if v.notes:
                    lines.append(f"- **Verification Notes**: {v.notes}")
            content = "\n".join(lines)
            e_ids = [reproduction.reproduction_id]

        return ReportSection(
            section_id="sec_3_reproduction_result",
            section_number=3,
            title="3. Reproduction Result",
            content_markdown=content,
            evidence_ids=e_ids,
        )

    def _build_section_4_behavioral_difference(self, classification: RegressionClassification) -> ReportSection:
        details = classification.evidence.details if classification.evidence else {}
        lines = ["Detailed semantic behavioral delta observed between baseline and target versions:"]
        if not details:
            lines.append("- *(No granular difference payload details attached)*")
        else:
            for k, v in details.items():
                lines.append(f"- **{k}**: `{v}`")

        return ReportSection(
            section_id="sec_4_behavioral_difference",
            section_number=4,
            title="4. Behavioral Difference",
            content_markdown="\n".join(lines),
            evidence_ids=[classification.difference_id],
        )

    def _build_section_5_reproduction_path(self, reproduction: ReproductionResult | None) -> ReportSection:
        if not reproduction or not reproduction.path or not reproduction.path.steps:
            content = "No reproduction action path recorded."
            e_ids = []
        else:
            lines = [
                f"Minimal verified causal reproduction path ({len(reproduction.path.steps)} steps):",
                "",
                "| Step # | Action | Target / Strategy | Value | Timeout |",
                "|---|---|---|---|---|",
            ]
            for step in reproduction.path.steps:
                target_repr = step.accessible_name or step.stable_target_identity or step.raw_target or "page"
                val_repr = step.value if step.value else "-"
                lines.append(
                    f"| {step.step_index + 1} | `{step.action_type.value}` | `{target_repr}` ({step.target_strategy}) | `{val_repr}` | {int(step.timeout_ms)}ms |"
                )
            content = "\n".join(lines)
            e_ids = [reproduction.reproduction_id]

        return ReportSection(
            section_id="sec_5_reproduction_path",
            section_number=5,
            title="5. Reproduction Path",
            content_markdown=content,
            evidence_ids=e_ids,
        )

    def _build_section_6_expected_vs_actual(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
    ) -> ReportSection:
        details = classification.evidence.details if classification.evidence else {}
        exp_val = details.get("expected_value") or details.get("url_a") or details.get("status_a") or details.get("text_a") or "Baseline normal behavior"
        act_val = details.get("actual_value") or details.get("url_b") or details.get("status_b") or details.get("text_b") or "Observed regressed behavior"

        lines = [
            "| Dimension | Version A (Baseline) | Version B (Target / Candidate) |",
            "|---|---|---|",
            f"| **Observed State** | `{exp_val}` | `{act_val}` |",
            "| **Status** | Expected Functional Behavior | Regression Observed |",
        ]
        return ReportSection(
            section_id="sec_6_expected_vs_actual",
            section_number=6,
            title="6. Expected vs Actual Behavior",
            content_markdown="\n".join(lines),
            evidence_ids=[classification.classification_id],
        )

    def _build_section_7_source_localization(self, root_cause: RootCauseResult | None) -> ReportSection:
        if not root_cause:
            content = "Root cause localization analysis was not performed or yielded no results."
            e_ids = []
        else:
            status_heading = (
                "CONFIRMED SOURCE LOCALIZATION"
                if root_cause.status == RootCauseStatus.LOCATED
                else f"{root_cause.status.value} SOURCE LOCALIZATION"
            )

            lines = [
                f"### Status: `{status_heading}`",
                f"- **Root Cause Status**: `{root_cause.status.value}`",
            ]

            if root_cause.status == RootCauseStatus.CANDIDATE_ONLY:
                lines.append(
                    "> [!NOTE]\n"
                    "> Available source evidence identifies candidate modified regions, but does not conclusively establish causality."
                )
            elif root_cause.status == RootCauseStatus.INCONCLUSIVE:
                lines.append(
                    "> [!NOTE]\n"
                    "> Source diff analysis was inconclusive; no definitive source change could be linked to the behavioral regression."
                )

            if root_cause.primary_attribution:
                primary = root_cause.primary_attribution
                loc = primary.source_location
                lines.append("")
                lines.append("#### Primary Localized Source Location:")
                lines.append(f"- **File**: `{loc.file_path}`")
                lines.append(f"- **Lines**: `{loc.start_line} - {loc.end_line}`")
                if loc.symbol_name:
                    lines.append(f"- **Enclosing Symbol**: `{loc.symbol_name}` ({loc.symbol_kind.value if loc.symbol_kind else 'unknown'})")
                lines.append(f"- **Relationship**: `{primary.relationship_type.value}`")
                lines.append(f"- **Explanation**: {primary.explanation}")

                if primary.diff_hunk and self.config.include_full_diff_hunks:
                    lines.append("")
                    lines.append("```diff")
                    for d_line in primary.diff_hunk.lines[: self.config.max_diff_lines_per_hunk]:
                        prefix = "+" if d_line.change_type.value == "LINE_ADDED" else ("-" if d_line.change_type.value == "LINE_DELETED" else " ")
                        lines.append(f"{prefix}{d_line.content}")
                    lines.append("```")

            content = "\n".join(lines)
            e_ids = [root_cause.root_cause_id]

        return ReportSection(
            section_id="sec_7_source_localization",
            section_number=7,
            title="7. Source Localization",
            content_markdown=content,
            evidence_ids=e_ids,
        )

    def _build_section_8_commit_attribution(self, root_cause: RootCauseResult | None) -> ReportSection:
        if not root_cause or not root_cause.primary_attribution or not root_cause.primary_attribution.commit:
            content = "No Git commit could be authoritatively attributed to this regression."
            e_ids = []
        else:
            primary = root_cause.primary_attribution
            cmt = primary.commit
            attr_type = primary.commit_attribution_type

            lines = [
                f"### Commit Attribution Classification: `{attr_type.value}`",
                "",
                f"- **Commit Hash**: `{cmt.commit_hash}`",
                f"- **Author**: `{cmt.author_name} <{cmt.author_email}>`",
                f"- **Summary**: {cmt.message}",
            ]
            if cmt.timestamp:
                lines.insert(4, f"- **Committed At**: `{cmt.timestamp}`")

            if attr_type == CommitAttributionType.INTRODUCING_COMMIT:
                lines.append(
                    "> [!NOTE]\n"
                    "> Git blame identified this commit as introducing or modifying the relevant source lines."
                )
            elif attr_type == CommitAttributionType.CAUSAL_COMMIT:
                lines.append(
                    "> [!IMPORTANT]\n"
                    "> Multi-phase behavioral and diff evidence corroborates this commit as the direct causal change for the regression."
                )

            content = "\n".join(lines)
            e_ids = [cmt.commit_hash]

        return ReportSection(
            section_id="sec_8_commit_attribution",
            section_number=8,
            title="8. Commit Attribution",
            content_markdown=content,
            evidence_ids=e_ids,
        )

    def _build_section_9_evidence_chain(self, evidence_chain: EvidenceChain | None) -> ReportSection:
        if not evidence_chain or not evidence_chain.nodes:
            content = "No causal evidence chain nodes available."
            e_ids = []
        else:
            lines = [
                "Unbroken causal attribution graph linking observed difference to source attribution:",
                "",
                "```text",
            ]
            for idx, node in enumerate(evidence_chain.nodes):
                arrow = "  ↓" if idx > 0 else ""
                if arrow:
                    lines.append(arrow)
                lines.append(f"[{node.phase_origin}] {node.title} -> {node.status}")
                lines.append(f"    Evidence IDs: {', '.join(node.evidence_ids)}")
                lines.append(f"    Summary:      {node.summary}")
            lines.append("```")
            content = "\n".join(lines)
            e_ids = [evidence_chain.chain_id]

        return ReportSection(
            section_id="sec_9_evidence_chain",
            section_number=9,
            title="9. Evidence Chain",
            content_markdown=content,
            evidence_ids=e_ids,
        )

    def _build_section_10_generated_test(self, generated_test: GeneratedTest | None) -> ReportSection:
        if not generated_test or not generated_test.generated_source:
            content = "No automated regression test was synthesized for this finding."
            e_ids = []
        else:
            lines = [
                f"- **Test ID**: `{generated_test.test_id}`",
                f"- **Framework**: `{generated_test.framework.value}` ({generated_test.language.value})",
                f"- **Synthesis Status**: `{generated_test.status.value}`",
                f"- **Validation Status**: `{generated_test.validation_status.value}`",
                f"- **Action Steps**: `{len(generated_test.steps)}`",
                f"- **Evidence Assertions**: `{len(generated_test.assertions)}`",
                "",
                "```typescript",
                generated_test.generated_source,
                "```",
            ]
            content = "\n".join(lines)
            e_ids = [generated_test.test_id]

        return ReportSection(
            section_id="sec_10_generated_test",
            section_number=10,
            title="10. Generated Regression Test",
            content_markdown=content,
            evidence_ids=e_ids,
        )

    def _build_section_11_limitations(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        root_cause: RootCauseResult | None,
    ) -> ReportSection:
        lines = [
            "### Investigation Scope & Boundary Constraints",
            "- **Zero Automated Code Mutation**: RETRACE produces read-only investigations and executable reproduction scripts; no application source code was modified.",
            "- **Ground-Truth Isolation**: All findings are derived exclusively from dynamic browser execution, Git diff history, and deterministic AST symbol analysis.",
            "- **Heuristic / AI Independence**: Analysis contains zero stochastic LLM text generation, vector embeddings, or ungrounded heuristics.",
        ]
        if classification.category.value == "PERFORMANCE":
            lines.append(
                "- **Performance Bounding**: Latency measurements are subject to network and host noise; timing differences require manual review before automated gating."
            )
        return ReportSection(
            section_id="sec_11_limitations",
            section_number=11,
            title="11. Limitations & Scope Boundaries",
            content_markdown="\n".join(lines),
            evidence_ids=[],
        )
