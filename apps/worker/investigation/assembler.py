"""Investigation Assembler.

Assembles complete, developer-usable investigation packages from Phase 7-10 engines,
persisting generated artifacts to storage and establishing unified multi-phase provenance.
"""

import hashlib
from uuid import UUID, uuid4

from apps.worker.investigation.models import (
    InvestigationProvenance,
    InvestigationResult,
    InvestigationStatus,
    InvestigationSuiteResult,
    InvestigationSummary,
    compute_deterministic_investigation_id,
)
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionClassification,
    RegressionClassificationResult,
)
from apps.worker.reporting.engine import EvidenceReportEngine
from apps.worker.reporting.models import ReportFormat
from apps.worker.reporting.serializer import ReportSerializer
from apps.worker.reproduction.models import (
    ReproductionResult,
    ReproductionStatus,
    ReproductionSuiteResult,
)
from apps.worker.rootcause.models import RootCauseResult, RootCauseStatus, RootCauseSuiteResult
from apps.worker.synthesis.engine import TestSynthesisEngine
from apps.worker.synthesis.models import GeneratedTest, SynthesisStatus
from packages.domain.models import ArtifactKind, ArtifactReference
from packages.storage.base import ArtifactStorage


class InvestigationAssembler:
    """Orchestrates end-to-end investigation package assembly and artifact persistence."""

    def __init__(
        self,
        synthesis_engine: TestSynthesisEngine | None = None,
        report_engine: EvidenceReportEngine | None = None,
        storage: ArtifactStorage | None = None,
    ) -> None:
        self.synthesis_engine = synthesis_engine or TestSynthesisEngine()
        self.report_engine = report_engine or EvidenceReportEngine()
        self.storage = storage

    async def assemble_investigation(
        self,
        analysis_id: UUID,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        root_cause: RootCauseResult | None = None,
    ) -> InvestigationResult:
        """Synthesize test, generate evidence report, persist artifacts, and assemble InvestigationResult."""
        investigation_id = compute_deterministic_investigation_id(
            analysis_id=analysis_id,
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
        )

        # 1. Synthesize Playwright Regression Test
        generated_test: GeneratedTest | None = None
        if classification.status != ClassificationStatus.NON_REGRESSION:
            generated_test = self.synthesis_engine.synthesize_test(
                classification=classification,
                reproduction=reproduction,
                root_cause=root_cause,
            )

        # 2. Generate Evidence Investigation Report
        report = self.report_engine.generate_report(
            classification=classification,
            reproduction=reproduction,
            root_cause=root_cause,
            generated_test=generated_test,
            investigation_id=investigation_id,
        )

        # 3. Persist Artifacts to Storage if storage is configured
        artifacts: list[ArtifactReference] = []

        if self.storage:
            # A. Store generated Playwright test script
            if generated_test and generated_test.status != SynthesisStatus.INCOMPLETE:
                test_bytes = generated_test.generated_source.encode("utf-8")
                test_key = f"analyses/{analysis_id}/investigations/{investigation_id}/test.spec.ts"
                test_uri = await self.storage.put(test_key, test_bytes, content_type="text/typescript")
                test_hash = hashlib.sha256(test_bytes).hexdigest()
                artifacts.append(
                    ArtifactReference(
                        id=uuid4(),
                        kind=ArtifactKind.GENERATED_TEST,
                        storage_uri=test_uri,
                        mime_type="text/typescript",
                        size_bytes=len(test_bytes),
                        sha256_hash=test_hash,
                        metadata={"test_id": generated_test.test_id, "investigation_id": investigation_id},
                    )
                )

            # B. Store Markdown Report
            md_bytes = ReportSerializer.serialize(report, fmt=ReportFormat.MARKDOWN)
            md_key = f"analyses/{analysis_id}/investigations/{investigation_id}/report.md"
            md_uri = await self.storage.put(md_key, md_bytes, content_type="text/markdown")
            md_hash = hashlib.sha256(md_bytes).hexdigest()
            artifacts.append(
                ArtifactReference(
                    id=uuid4(),
                    kind=ArtifactKind.CONSOLE_LOG,  # Generic text artifact
                    storage_uri=md_uri,
                    mime_type="text/markdown",
                    size_bytes=len(md_bytes),
                    sha256_hash=md_hash,
                    metadata={"report_id": report.report_id, "format": "markdown"},
                )
            )

            # C. Store JSON Report
            json_bytes = ReportSerializer.serialize(report, fmt=ReportFormat.JSON)
            json_key = f"analyses/{analysis_id}/investigations/{investigation_id}/report.json"
            json_uri = await self.storage.put(json_key, json_bytes, content_type="application/json")
            json_hash = hashlib.sha256(json_bytes).hexdigest()
            artifacts.append(
                ArtifactReference(
                    id=uuid4(),
                    kind=ArtifactKind.DOM_SNAPSHOT,  # Structured artifact
                    storage_uri=json_uri,
                    mime_type="application/json",
                    size_bytes=len(json_bytes),
                    sha256_hash=json_hash,
                    metadata={"report_id": report.report_id, "format": "json"},
                )
            )

        # 4. Evaluate Overall Investigation Status
        if classification.status == ClassificationStatus.NON_REGRESSION:
            status = InvestigationStatus.COMPLETED
        elif (
            reproduction
            and reproduction.status == ReproductionStatus.REPRODUCED
            and root_cause
            and root_cause.status == RootCauseStatus.LOCATED
        ):
            status = InvestigationStatus.COMPLETED
        elif reproduction and reproduction.status == ReproductionStatus.REPRODUCED:
            status = InvestigationStatus.PARTIAL
        elif root_cause and root_cause.status == RootCauseStatus.INCONCLUSIVE:
            status = InvestigationStatus.INCONCLUSIVE
        else:
            status = InvestigationStatus.PARTIAL if reproduction else InvestigationStatus.INCONCLUSIVE

        # 5. Construct Unified Provenance
        provenance = InvestigationProvenance(
            analysis_id=analysis_id,
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            reproduction_id=reproduction.reproduction_id if reproduction else None,
            root_cause_id=root_cause.root_cause_id if root_cause else None,
            test_id=generated_test.test_id if generated_test else None,
            report_id=report.report_id,
            artifact_references=artifacts,
        )

        return InvestigationResult(
            investigation_id=investigation_id,
            analysis_id=analysis_id,
            regression_id=classification.classification_id,
            classification=classification,
            reproduction=reproduction,
            root_cause=root_cause,
            generated_test=generated_test,
            report=report,
            artifacts=artifacts,
            provenance=provenance,
            status=status,
        )

    async def assemble_suite(
        self,
        analysis_id: UUID,
        classification_result: RegressionClassificationResult,
        reproduction_suite: ReproductionSuiteResult | None = None,
        root_cause_suite: RootCauseSuiteResult | None = None,
    ) -> InvestigationSuiteResult:
        """Assemble all investigation packages for an analysis run."""
        repro_map: dict[str, ReproductionResult] = {}
        if reproduction_suite:
            for rep in reproduction_suite.results:
                repro_map[rep.classification_id] = rep

        rc_map: dict[str, RootCauseResult] = {}
        if root_cause_suite:
            for rc in root_cause_suite.results:
                rc_map[rc.classification_id] = rc

        sorted_classifications = sorted(
            classification_result.classifications, key=lambda c: c.deterministic_sort_key()
        )

        investigations: list[InvestigationResult] = []
        summary = InvestigationSummary(total_investigations=len(sorted_classifications))

        for clf in sorted_classifications:
            rep = repro_map.get(clf.classification_id)
            rc = rc_map.get(clf.classification_id)

            inv = await self.assemble_investigation(
                analysis_id=analysis_id,
                classification=clf,
                reproduction=rep,
                root_cause=rc,
            )
            investigations.append(inv)

            if inv.status == InvestigationStatus.COMPLETED:
                summary.completed_count += 1
            elif inv.status == InvestigationStatus.PARTIAL:
                summary.partial_count += 1
            elif inv.status == InvestigationStatus.INCONCLUSIVE:
                summary.inconclusive_count += 1
            elif inv.status == InvestigationStatus.FAILED:
                summary.failed_count += 1

        return InvestigationSuiteResult(
            analysis_id=analysis_id,
            run_a_id=classification_result.run_a_id,
            run_b_id=classification_result.run_b_id,
            investigations=investigations,
            summary=summary,
        )
