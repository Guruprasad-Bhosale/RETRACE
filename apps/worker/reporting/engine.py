"""Evidence Report Engine.

Primary entrypoint for synthesizing comprehensive, evidence-grounded investigation
reports and unbroken causal chains across Phases 6-10.
"""

from uuid import UUID

from apps.worker.regression.models import ClassificationStatus, RegressionClassification
from apps.worker.reporting.config import ReportingConfig
from apps.worker.reporting.evidence import EvidenceChainBuilder
from apps.worker.reporting.formatter import ReportFormatter
from apps.worker.reporting.models import (
    EvidenceReport,
    ReportProvenance,
    ReportStatus,
    ReportSuiteResult,
    ReportSummary,
    compute_deterministic_report_id,
)
from apps.worker.reporting.sections import ReportSectionBuilder
from apps.worker.reproduction.models import (
    ReproductionResult,
    ReproductionStatus,
    ReproductionSuiteResult,
)
from apps.worker.rootcause.models import RootCauseResult, RootCauseStatus, RootCauseSuiteResult
from apps.worker.synthesis.models import GeneratedTest, SynthesisSuiteResult


class EvidenceReportEngine:
    """Orchestrates causal evidence chain construction and full investigation report generation."""

    def __init__(self, config: ReportingConfig | None = None) -> None:
        self.config = config or ReportingConfig()
        self.chain_builder = EvidenceChainBuilder()
        self.section_builder = ReportSectionBuilder(config=self.config)
        self.formatter = ReportFormatter()

    def generate_report(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        root_cause: RootCauseResult | None = None,
        generated_test: GeneratedTest | None = None,
        investigation_id: str | None = None,
    ) -> EvidenceReport:
        """Generate a complete evidence investigation report for a single classified regression."""
        # 1. Determine Report Status
        if classification.status == ClassificationStatus.NON_REGRESSION:
            status = ReportStatus.COMPLETE
            summary = "Non-regression change verified. No defect identified."
        elif (
            reproduction
            and reproduction.status == ReproductionStatus.REPRODUCED
            and root_cause
            and root_cause.status == RootCauseStatus.LOCATED
        ):
            status = ReportStatus.COMPLETE
            summary = f"Reproduced and localized {classification.category.value} regression."
        elif reproduction and reproduction.status == ReproductionStatus.REPRODUCED:
            status = ReportStatus.PARTIAL
            summary = f"Reproduced {classification.category.value} regression; root cause attribution partial or candidate-only."
        else:
            status = ReportStatus.PARTIAL if reproduction else ReportStatus.EVIDENCE_INSUFFICIENT
            summary = f"Investigation for {classification.category.value} regression is incomplete."

        # 2. Build Causal Evidence Chain
        evidence_chain = self.chain_builder.build_chain(
            classification=classification,
            reproduction=reproduction,
            root_cause=root_cause,
            generated_test=generated_test,
        )

        # 3. Build Standardized Sections
        sections = self.section_builder.build_all_sections(
            classification=classification,
            reproduction=reproduction,
            root_cause=root_cause,
            generated_test=generated_test,
            evidence_chain=evidence_chain,
        )

        # 4. Compute Deterministic Report ID
        report_id = compute_deterministic_report_id(
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            reproduction_id=reproduction.reproduction_id if reproduction else None,
            root_cause_id=root_cause.root_cause_id if root_cause else None,
            test_id=generated_test.test_id if generated_test else None,
        )

        cat_val = classification.category.value if hasattr(classification.category, "value") else str(classification.category)
        title = f"RETRACE Investigation Report: {cat_val} [{classification.classification_id[:8]}]"

        # 5. Assemble Provenance
        provenance = ReportProvenance(
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            reproduction_id=reproduction.reproduction_id if reproduction else None,
            root_cause_id=root_cause.root_cause_id if root_cause else None,
            test_id=generated_test.test_id if generated_test else None,
            artifact_references=classification.evidence.artifact_references if classification.evidence else [],
        )

        prov_dict = {
            "classification_id": provenance.classification_id,
            "difference_id": provenance.difference_id,
            "reproduction_id": provenance.reproduction_id,
            "root_cause_id": provenance.root_cause_id,
            "test_id": provenance.test_id,
        }

        # 6. Format Markdown & JSON
        markdown_text = self.formatter.format_markdown(
            title=title,
            status=status,
            summary=summary,
            sections=sections,
            evidence_chain=evidence_chain,
        )

        json_dict = self.formatter.format_json(
            report_id=report_id,
            regression_id=classification.classification_id,
            title=title,
            status=status,
            summary=summary,
            sections=sections,
            evidence_chain=evidence_chain,
            provenance_dict=prov_dict,
        )

        return EvidenceReport(
            report_id=report_id,
            investigation_id=investigation_id,
            regression_id=classification.classification_id,
            title=title,
            status=status,
            summary=summary,
            sections=sections,
            evidence_chain=evidence_chain,
            markdown_content=markdown_text,
            json_content=json_dict,
            provenance=provenance,
        )

    def generate_suite(
        self,
        classifications: list[RegressionClassification],
        run_a_id: UUID,
        run_b_id: UUID,
        reproduction_suite: ReproductionSuiteResult | None = None,
        root_cause_suite: RootCauseSuiteResult | None = None,
        synthesis_suite: SynthesisSuiteResult | None = None,
    ) -> ReportSuiteResult:
        """Generate complete report suite for all given classifications."""
        repro_map: dict[str, ReproductionResult] = {}
        if reproduction_suite:
            for rep in reproduction_suite.results:
                repro_map[rep.classification_id] = rep

        rc_map: dict[str, RootCauseResult] = {}
        if root_cause_suite:
            for rc in root_cause_suite.results:
                rc_map[rc.classification_id] = rc

        test_map: dict[str, GeneratedTest] = {}
        if synthesis_suite:
            for t in synthesis_suite.tests:
                test_map[t.regression_id] = t

        sorted_classifications = sorted(classifications, key=lambda c: c.deterministic_sort_key())

        reports: list[EvidenceReport] = []
        summary = ReportSummary(total_reports_generated=len(sorted_classifications))

        for clf in sorted_classifications:
            rep = repro_map.get(clf.classification_id)
            rc = rc_map.get(clf.classification_id)
            t = test_map.get(clf.classification_id)

            report = self.generate_report(
                classification=clf,
                reproduction=rep,
                root_cause=rc,
                generated_test=t,
            )
            reports.append(report)

            if report.status == ReportStatus.COMPLETE:
                summary.complete_count += 1
            elif report.status == ReportStatus.PARTIAL:
                summary.partial_count += 1
            elif report.status == ReportStatus.EVIDENCE_INSUFFICIENT:
                summary.insufficient_evidence_count += 1

        return ReportSuiteResult(
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            reports=reports,
            summary=summary,
        )
