"""Investigations API Router.

Exposes developer-usable investigation packages, synthesized Playwright tests,
and evidence-backed markdown/JSON investigation reports.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel

from apps.worker.investigation.models import InvestigationResult
from apps.worker.orchestration.models import InvestigationRequest
from apps.worker.orchestration.runner import default_workflow_runner
from packages.forensics.engine import ForensicIntelligenceEngine
from packages.forensics.models import (
    EvidenceGraph,
    ForensicInvestigationExplanation,
    InvestigationComparisonResult,
    ReplayResult,
)
from packages.forensics.replay import InvestigationReplayEngine


class InvestigationSummaryResponse(BaseModel):
    investigation_id: str
    analysis_id: UUID
    regression_id: str
    category: str
    status: str
    title: str
    has_generated_test: bool
    source_location: str | None = None
    commit_hash: str | None = None


router = APIRouter(prefix="/investigations", tags=["Investigations"])

# In-memory investigation cache for active analysis runs
_INVESTIGATION_REGISTRY: dict[str, InvestigationResult] = {}


def register_investigation(investigation: InvestigationResult) -> None:
    """Register an investigation result into the active cache."""
    _INVESTIGATION_REGISTRY[investigation.investigation_id] = investigation


def clear_investigations() -> None:
    """Clear all registered investigations (for testing)."""
    _INVESTIGATION_REGISTRY.clear()


def seed_sample_investigations(force: bool = False) -> None:
    """Seed sample investigation records for development and exploration."""
    if not force and len(_INVESTIGATION_REGISTRY) > 0:
        return



    from uuid import uuid4

    from apps.worker.investigation.models import InvestigationProvenance
    from apps.worker.regression.models import (
        ClassificationEvidence,
        ClassificationStatus,
        RegressionCategory,
        RegressionClassification,
    )
    from apps.worker.reporting.models import (
        EvidenceChain,
        EvidenceChainNode,
        EvidenceNodeType,
        EvidenceReport,
        ReportProvenance,
        ReportSection,
        ReportStatus,
    )
    from apps.worker.reproduction.models import (
        MatchStatus,
        ReproductionPath,
        ReproductionResult,
        ReproductionStatus,
        ReproductionStep,
        ReproductionStrategy,
        ReproductionVerification,
    )
    from apps.worker.rootcause.models import (
        AttributionRelationshipType,
        CommitAttributionType,
        CommitMetadata,
        DiffHunk,
        DiffLine,
        LineChangeType,
        RootCauseAttribution,
        RootCauseProvenance,
        RootCauseResult,
        RootCauseStatus,
        SourceLocation,
    )
    from apps.worker.synthesis.models import (
        GeneratedTest,
        SynthesisStatus,
        TestAssertion,
        TestFramework,
        TestLanguage,
        TestProvenance,
        TestStep,
        ValidationStatus,
    )
    from packages.domain.models import ActionType, ArtifactKind, ArtifactReference

    analysis_id = UUID("11111111-2222-3333-4444-555555555555")

    # 1. Investigation 1: Functional Add to Cart Disabled
    clf1 = RegressionClassification(
        classification_id="clf_comm_cart_01",
        difference_id="diff_comm_cart_01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-COMMERCE-CART-ADD-DISABLED",
        reason="Add to Cart button unexpectedly rendered disabled following item selection.",
        evidence=ClassificationEvidence(
            difference_id="diff_comm_cart_01",
            canonical_subject="button#add-to-cart",
            details={"selector": "#add-to-cart", "text_a": "Add to Cart", "text_b": "Out of Stock", "stock_a": 10, "stock_b": 0},
        ),
    )
    repro1 = ReproductionResult(
        reproduction_id="repro_comm_cart_01",
        classification_id="clf_comm_cart_01",
        difference_id="diff_comm_cart_01",
        rule_id="RULE-COMMERCE-CART-ADD-DISABLED",
        category="FUNCTIONAL",
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="path_repro_01",
            trajectory_id=uuid4(),
            classification_id="clf_comm_cart_01",
            difference_id="diff_comm_cart_01",
            seed_url="http://127.0.0.1:3000/",
            steps=[
                ReproductionStep(step_index=0, action_type=ActionType.NAVIGATE, value="/", raw_target="/"),
                ReproductionStep(step_index=1, action_type=ActionType.CLICK, stable_target_identity="#product-1", target_role="link", accessible_name="Product 1"),
                ReproductionStep(step_index=2, action_type=ActionType.CLICK, stable_target_identity="#add-to-cart-btn", target_role="button", accessible_name="Add to Cart"),
            ],
            path_signature="nav->click_prod->click_cart",
            observation_ids=[uuid4(), uuid4()],
        ),
        final_verification=ReproductionVerification(
            expected_difference_id="diff_comm_cart_01",
            expected_classification_id="clf_comm_cart_01",
            expected_rule_id="RULE-COMMERCE-CART-ADD-DISABLED",
            expected_category="FUNCTIONAL",
            match_status=MatchStatus.FULL_MATCH,
            observed_match=True,
            notes="Button disabled state reproduced identically across 2 attempts.",
        ),
        total_duration_ms=420.5,
    )
    loc1 = SourceLocation(
        file_path="lab/applications/commerce/v2/routes/cart.py",
        start_line=24,
        end_line=32,
        symbol_name="handle_add_to_cart",
    )
    hunk1 = DiffHunk(
        old_start=24,
        old_lines=5,
        new_start=24,
        new_lines=6,
        header="@@ -24,5 +24,6 @@ def handle_add_to_cart()",
        lines=[
            DiffLine(old_line_number=24, change_type=LineChangeType.LINE_DELETED, content="    if item.stock > 0:"),
            DiffLine(new_line_number=24, change_type=LineChangeType.LINE_ADDED, content="    if item.stock < 0:  # Inverted stock condition"),
        ],
        added_lines=[24],
        deleted_lines=[24],
    )
    commit1 = CommitMetadata(
        commit_hash="c0ffee123456",
        author_name="Backend Team",
        author_email="dev@example.com",
        message="Refactor stock validation logic in cart handler",
    )
    attr1 = RootCauseAttribution(
        attribution_id="attr_comm_cart_01",
        source_location=loc1,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=commit1,
        commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
        diff_hunk=hunk1,
        explanation="Inverted stock comparison condition (item.stock < 0) prevents adding items to cart.",
    )
    rc1 = RootCauseResult(
        root_cause_id="rc_comm_cart_01",
        classification_id="clf_comm_cart_01",
        difference_id="diff_comm_cart_01",
        category="FUNCTIONAL",
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr1,
        attributions=[attr1],
        provenance=RootCauseProvenance(classification_id="clf_comm_cart_01", difference_id="diff_comm_cart_01"),
    )
    test1 = GeneratedTest(
        test_id="test_comm_cart_01",
        regression_id="clf_comm_cart_01",
        framework=TestFramework.PLAYWRIGHT,
        language=TestLanguage.TYPESCRIPT,
        title="Commerce Cart Button Regression Test",
        description="Verifies add to cart button remains interactive for stocked products",
        steps=[
            TestStep(step_index=0, action_type=ActionType.NAVIGATE, raw_target="/", resolved_selector="page.goto(`${BASE_URL}/`)", description="Navigate to homepage"),
            TestStep(step_index=1, action_type=ActionType.CLICK, raw_target="#product-1", resolved_selector="page.getByRole('link', { name: 'Product 1' })", description="Select product 1"),
            TestStep(step_index=2, action_type=ActionType.CLICK, raw_target="#add-to-cart-btn", resolved_selector="page.getByRole('button', { name: 'Add to Cart' })", description="Click Add to Cart button"),
        ],
        assertions=[
            TestAssertion(
                assertion_id="ast_1",
                category="UI_STATE",
                assertion_type="toBeVisible",
                subject="page.locator('#cart-item-count')",
                expected_value="1",
                evidence_id="diff_comm_cart_01",
                reasoning="Cart counter expected to increment upon adding in-stock product.",
            )
        ],
        provenance=TestProvenance(classification_id="clf_comm_cart_01", difference_id="diff_comm_cart_01", source_locations=["lab/applications/commerce/v2/routes/cart.py:24-32"], commit_hashes=["c0ffee12"]),
        status=SynthesisStatus.SYNTHESIZED,
        validation_status=ValidationStatus.STRUCTURALLY_VALIDATED,
        generated_source="""import { test, expect } from '@playwright/test';

const BASE_URL = process.env.RETRACE_TARGET_URL || process.env.RETRACE_BASE_URL || 'http://127.0.0.1:3000';

test.describe('Commerce Cart Button Regression Test', () => {
  test('reproduce and assert against regression', async ({ page }) => {
    // 1. Navigate and select item
    await page.goto(`${BASE_URL}/`);
    await page.getByRole('link', { name: 'Product 1' }).click();

    // 2. Attempt to add to cart
    const addBtn = page.getByRole('button', { name: 'Add to Cart' });
    await expect(addBtn).toBeEnabled();
    await addBtn.click();

    // 3. Verify cart badge increments
    await expect(page.locator('#cart-item-count')).toContainText('1');
  });
});
""",
        validation_notes=["Syntax and AST structure verified.", "Zero synthetic ground truth references."],
    )
    chain1 = EvidenceChain(
        chain_id="chain_cart_01",
        nodes=[
            EvidenceChainNode(node_id="n1", node_type=EvidenceNodeType.OBSERVED_DIFFERENCE, title="Observed Difference", phase_origin="Phase 6: Difference Engine", status="OBSERVED", evidence_ids=["diff_comm_cart_01"], summary="Button #add-to-cart rendered as Out of Stock."),
            EvidenceChainNode(node_id="n2", node_type=EvidenceNodeType.REGRESSION_CLASSIFICATION, title="Regression Classification", phase_origin="Phase 7: Classifier", status="REGRESSION_CANDIDATE", evidence_ids=["clf_comm_cart_01"], summary="Classified as FUNCTIONAL regression under rule RULE-COMMERCE-CART-ADD-DISABLED."),
            EvidenceChainNode(node_id="n3", node_type=EvidenceNodeType.REPRODUCTION_REPLAY, title="Autonomous Reproduction", phase_origin="Phase 8: Reproduction", status="REPRODUCED", evidence_ids=["repro_comm_cart_01"], summary="Successfully reproduced defect across 2 attempts in fresh browser context."),
            EvidenceChainNode(node_id="n4", node_type=EvidenceNodeType.ROOT_CAUSE_LOCALIZATION, title="Root Cause Localization", phase_origin="Phase 9: Localization", status="LOCATED", evidence_ids=["rc_comm_cart_01"], summary="Defect localized to handle_add_to_cart in lab/applications/commerce/v2/routes/cart.py (lines 24-32)."),
            EvidenceChainNode(node_id="n5", node_type=EvidenceNodeType.COMMIT_ATTRIBUTION, title="Commit Attribution", phase_origin="Phase 9: Commit Attributor", status="CAUSAL_COMMIT", evidence_ids=["c0ffee123456"], summary="Attributed to commit c0ffee123456 (Refactor stock validation logic in cart handler)."),
            EvidenceChainNode(node_id="n6", node_type=EvidenceNodeType.SYNTHESIZED_TEST, title="Synthesized Regression Test", phase_origin="Phase 10: Synthesis", status="SYNTHESIZED", evidence_ids=["test_comm_cart_01"], summary="Synthesized Playwright TypeScript test verifying cart button enablement."),
        ],
    )
    sections1 = [
        ReportSection(section_id="s1", section_number=1, title="1. Executive Summary", content_markdown="RETRACE discovered a functional regression preventing customers from adding in-stock items to cart. Root cause localized to cart handler stock check logic in commit c0ffee123456.", evidence_ids=["clf_comm_cart_01"]),
        ReportSection(section_id="s2", section_number=2, title="2. Regression Classification", content_markdown="- Category: FUNCTIONAL\n- Rule: RULE-COMMERCE-CART-ADD-DISABLED\n- Reason: Add to Cart button became disabled.", evidence_ids=["clf_comm_cart_01"]),
        ReportSection(section_id="s3", section_number=3, title="3. Reproduction Result", content_markdown="- Status: REPRODUCED (2 attempts, 420.5ms)\n- Replay verified causal path.", evidence_ids=["repro_comm_cart_01"]),
        ReportSection(section_id="s4", section_number=4, title="4. Behavioral Difference", content_markdown="- Expected: Button enabled with text 'Add to Cart'\n- Actual: Button disabled with text 'Out of Stock'", evidence_ids=["diff_comm_cart_01"]),
        ReportSection(section_id="s5", section_number=5, title="5. Reproduction Path", content_markdown="| Step | Action | Target |\n|---|---|---|\n| 1 | Navigate | / |\n| 2 | Click | Product 1 |\n| 3 | Click | Add to Cart |", evidence_ids=["repro_comm_cart_01"]),
        ReportSection(section_id="s6", section_number=6, title="6. Expected vs Actual Behavior", content_markdown="| Version A | Version B |\n|---|---|\n| Button Enabled | Button Disabled |", evidence_ids=["clf_comm_cart_01"]),
        ReportSection(section_id="s7", section_number=7, title="7. Source Localization", content_markdown="### Status: `CONFIRMED SOURCE LOCALIZATION`\n- File: `lab/applications/commerce/v2/routes/cart.py`\n- Lines: 24-32\n- Enclosing Symbol: `handle_add_to_cart`", evidence_ids=["rc_comm_cart_01"]),
        ReportSection(section_id="s8", section_number=8, title="8. Commit Attribution", content_markdown="### Classification: `CAUSAL_COMMIT`\n- Commit: `c0ffee123456`\n- Summary: Refactor stock validation logic in cart handler", evidence_ids=["c0ffee123456"]),
        ReportSection(section_id="s9", section_number=9, title="9. Evidence Chain", content_markdown="Difference -> Classification -> Reproduction -> Localization -> Commit -> Test", evidence_ids=["chain_cart_01"]),
        ReportSection(section_id="s10", section_number=10, title="10. Generated Regression Test", content_markdown="```typescript\nimport { test, expect } from '@playwright/test';\n```", evidence_ids=["test_comm_cart_01"]),
        ReportSection(section_id="s11", section_number=11, title="11. Limitations & Scope Boundaries", content_markdown="- Read-only analysis\n- Zero benchmark oracle leakage", evidence_ids=[]),
    ]
    report1 = EvidenceReport(
        report_id="rep_comm_cart_01",
        investigation_id="inv_comm_cart_01",
        regression_id="clf_comm_cart_01",
        title="Commerce Cart Button Disabled Regression",
        status=ReportStatus.COMPLETE,
        summary="Customer unable to add items to cart due to inverted stock check.",
        sections=sections1,
        evidence_chain=chain1,
        markdown_content="# Commerce Cart Button Disabled Regression\n\nExecutive Summary\nRETRACE identified a functional regression in the checkout workflow...",
        json_content={"investigation_id": "inv_comm_cart_01", "status": "COMPLETE", "category": "FUNCTIONAL"},
        provenance=ReportProvenance(classification_id="clf_comm_cart_01", difference_id="diff_comm_cart_01"),
    )
    art1 = ArtifactReference(
        id=uuid4(),
        kind=ArtifactKind.GENERATED_TEST,
        storage_uri="file:///storage/analyses/1111/investigations/inv_comm_cart_01/test.spec.ts",
        mime_type="text/typescript",
        size_bytes=850,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    inv1 = InvestigationResult(
        investigation_id="inv_comm_cart_01",
        analysis_id=analysis_id,
        regression_id="clf_comm_cart_01",
        classification=clf1,
        reproduction=repro1,
        root_cause=rc1,
        generated_test=test1,
        report=report1,
        artifacts=[art1],
        provenance=InvestigationProvenance(analysis_id=analysis_id, classification_id="clf_comm_cart_01", difference_id="diff_comm_cart_01"),
        status="COMPLETED",
    )
    _INVESTIGATION_REGISTRY["inv_comm_cart_01"] = inv1

    # 2. Investigation 2: Promo Discount Modal Regression
    clf2 = RegressionClassification(
        classification_id="clf_comm_modal_02",
        difference_id="diff_comm_modal_02",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-COMMERCE-PROMO-MODAL-UNRESPONSIVE",
        reason="Promo discount modal submit button throws unhandled exception on click.",
        evidence=ClassificationEvidence(
            difference_id="diff_comm_modal_02",
            canonical_subject="button#apply-promo",
            details={"selector": "#apply-promo", "error": "TypeError: promo.apply is not a function"},
        ),
    )
    repro2 = ReproductionResult(
        reproduction_id="repro_comm_modal_02",
        classification_id="clf_comm_modal_02",
        difference_id="diff_comm_modal_02",
        rule_id="RULE-COMMERCE-PROMO-MODAL-UNRESPONSIVE",
        category="FUNCTIONAL",
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="path_repro_02",
            trajectory_id=uuid4(),
            classification_id="clf_comm_modal_02",
            difference_id="diff_comm_modal_02",
            seed_url="http://127.0.0.1:3000/cart",
            path_signature="step=0|type=NAVIGATE->step=1|type=CLICK",
        ),
    )

    loc2 = SourceLocation(
        file_path="lab/applications/commerce/v2/static/js/promo.js",
        start_line=55,
        end_line=62,
        symbol_name="applyPromoCode",
    )
    cmt2 = CommitMetadata(
        commit_hash="deadbeef99",
        author_name="Frontend Team",
        author_email="frontend@retrace.local",
        message="Refactor promo application handler",
    )
    attr2 = RootCauseAttribution(
        attribution_id="attr_comm_modal_02",
        source_location=loc2,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=cmt2,
        explanation="Promo discount handler signature modified improperly",
    )
    rc2 = RootCauseResult(
        root_cause_id="rc_comm_modal_02",
        classification_id="clf_comm_modal_02",
        difference_id="diff_comm_modal_02",
        category="FUNCTIONAL",
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr2,
        attributions=[attr2],
        provenance=RootCauseProvenance(classification_id="clf_comm_modal_02", difference_id="diff_comm_modal_02"),
    )
    report2 = EvidenceReport(
        report_id="rep_comm_modal_02",
        investigation_id="inv_comm_modal_02",
        regression_id="clf_comm_modal_02",
        title="Promo Discount Modal Regression",
        status=ReportStatus.COMPLETE,
        summary="Promo modal throws unhandled exception on click.",
        sections=[],
        evidence_chain=EvidenceChain(chain_id="chain_modal_02", nodes=[]),

        markdown_content="# Promo Discount Modal Regression",
        json_content={"investigation_id": "inv_comm_modal_02", "status": "COMPLETE", "category": "FUNCTIONAL"},
        provenance=ReportProvenance(classification_id="clf_comm_modal_02", difference_id="diff_comm_modal_02"),
    )
    inv2 = InvestigationResult(
        investigation_id="inv_comm_modal_02",
        analysis_id=analysis_id,
        regression_id="clf_comm_modal_02",
        classification=clf2,
        reproduction=repro2,
        root_cause=rc2,
        report=report2,
        status="COMPLETED",
        provenance=InvestigationProvenance(analysis_id=analysis_id, classification_id="clf_comm_modal_02", difference_id="diff_comm_modal_02"),
    )
    _INVESTIGATION_REGISTRY["inv_comm_modal_02"] = inv2




@router.get("", response_model=list[InvestigationSummaryResponse])
async def list_investigations(
    analysis_id: UUID | None = Query(default=None, description="Filter by analysis session ID"),
) -> list[InvestigationSummaryResponse]:
    """List all assembled investigation packages, optionally filtered by analysis session."""
    seed_sample_investigations()
    results: list[InvestigationSummaryResponse] = []
    for inv in _INVESTIGATION_REGISTRY.values():
        if analysis_id is not None and inv.analysis_id != analysis_id:
            continue

        cat_val = (
            inv.classification.category.value
            if hasattr(inv.classification.category, "value")
            else str(inv.classification.category)
        )
        src_loc = None
        cmt = None
        if inv.root_cause and inv.root_cause.primary_attribution:
            loc = inv.root_cause.primary_attribution.source_location
            src_loc = f"{loc.file_path}:{loc.start_line}-{loc.end_line}"
            if inv.root_cause.primary_attribution.commit:
                cmt = inv.root_cause.primary_attribution.commit.commit_hash[:8]

        results.append(
            InvestigationSummaryResponse(
                investigation_id=inv.investigation_id,
                analysis_id=inv.analysis_id,
                regression_id=inv.regression_id,
                category=cat_val,
                status=inv.status.value,
                title=inv.report.title,
                has_generated_test=inv.generated_test is not None,
                source_location=src_loc,
                commit_hash=cmt,
            )
        )
    return results


def _get_investigation_entity(investigation_id: str) -> InvestigationResult | None:
    if investigation_id not in _INVESTIGATION_REGISTRY and investigation_id in ("inv_comm_cart_01", "inv_comm_modal_02"):
        seed_sample_investigations(force=True)
    return _INVESTIGATION_REGISTRY.get(investigation_id)


@router.get("/{investigation_id}", response_model=dict[str, Any])
async def get_investigation(investigation_id: str) -> dict[str, Any]:
    """Get complete investigation package details by ID."""
    inv = _get_investigation_entity(investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID '{investigation_id}' not found",
        )
    return inv.model_dump(mode="json")



@router.get("/{investigation_id}/test")
async def get_investigation_test(investigation_id: str) -> Response:
    """Retrieve the synthesized Playwright TypeScript test file for an investigation."""
    inv = _get_investigation_entity(investigation_id)
    if not inv or not inv.generated_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesized regression test for investigation '{investigation_id}' not found",
        )
    return Response(
        content=inv.generated_test.generated_source,
        media_type="text/typescript",
        headers={"Content-Disposition": f'attachment; filename="regression_{investigation_id}.spec.ts"'},
    )


@router.get("/{investigation_id}/report")
async def get_investigation_report(
    investigation_id: str,
    format: str = Query(default="markdown", pattern="^(markdown|json)$"),
) -> Response:
    """Retrieve the evidence investigation report in Markdown or JSON format."""
    inv = _get_investigation_entity(investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation report with ID '{investigation_id}' not found",
        )
    if format == "json":
        import json

        return Response(
            content=json.dumps(inv.report.json_content, indent=2, sort_keys=True),
            media_type="application/json",
        )
    else:
        return Response(
            content=inv.report.markdown_content,
            media_type="text/markdown",
        )


@router.get("/{investigation_id}/evidence-graph", response_model=EvidenceGraph)
async def get_investigation_evidence_graph(investigation_id: str) -> EvidenceGraph:
    """Retrieve the deterministic Forensic Evidence Graph (DAG) for an investigation."""
    inv = _get_investigation_entity(investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID '{investigation_id}' not found",
        )
    explanation = ForensicIntelligenceEngine.explain_investigation(inv)
    return explanation.evidence_graph


@router.get("/{investigation_id}/explanation", response_model=ForensicInvestigationExplanation)
async def get_investigation_explanation(investigation_id: str) -> ForensicInvestigationExplanation:
    """Retrieve the complete Forensic Investigation Explanation package with hypotheses and falsification."""
    inv = _get_investigation_entity(investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID '{investigation_id}' not found",
        )
    return ForensicIntelligenceEngine.explain_investigation(inv)


@router.post("/{investigation_id}/replay", response_model=ReplayResult)
async def replay_investigation(
    investigation_id: str,
    analysis_version: str = Query("forensics-v1", description="Forensics engine version for replay verification"),
) -> ReplayResult:
    """Execute deterministic offline replay against captured investigation evidence without browser execution."""
    inv = _get_investigation_entity(investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID '{investigation_id}' not found",
        )
    return InvestigationReplayEngine.replay_investigation(inv, analysis_version=analysis_version)


@router.get("/{investigation_id}/compare/{other_id}", response_model=InvestigationComparisonResult)
async def compare_investigations(investigation_id: str, other_id: str) -> InvestigationComparisonResult:
    """Compare two investigations across shared/unique evidence, graph diffs, and root-cause conclusions."""
    inv_a = _get_investigation_entity(investigation_id)
    if not inv_a:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation with ID '{investigation_id}' not found",
        )
    inv_b = _get_investigation_entity(other_id)
    if not inv_b:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comparison target investigation with ID '{other_id}' not found",
        )
    return InvestigationReplayEngine.compare_investigations(inv_a, inv_b)


@router.post("/start", response_model=dict[str, Any], status_code=status.HTTP_202_ACCEPTED)

async def start_investigation_workflow(request: InvestigationRequest) -> dict[str, Any]:
    """Start an asynchronous autonomous investigation workflow using LangGraph orchestration."""
    workflow_id = default_workflow_runner.start_background(request)
    return {
        "workflow_id": workflow_id,
        "analysis_id": request.analysis_id,
        "status": "PENDING",
        "message": "Investigation workflow started in background.",
    }


@router.get("/workflow/{workflow_id}/status", response_model=dict[str, Any])
async def get_workflow_status(workflow_id: str) -> dict[str, Any]:
    """Get current execution status, phase, and history for an orchestrated workflow."""
    state = default_workflow_runner.get_state(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found",
        )
    events = default_workflow_runner.get_events(workflow_id)
    return {
        "workflow_id": workflow_id,
        "analysis_id": state.get("analysis_id"),
        "status": state.get("status"),
        "current_phase": state.get("current_phase"),
        "history": state.get("history", []),
        "events_count": len(events),
        "error_message": state.get("error_message"),
        "failure_type": state.get("failure_type"),
    }


@router.post("/workflow/{workflow_id}/cancel", response_model=dict[str, Any])
async def cancel_workflow(workflow_id: str) -> dict[str, Any]:
    """Cancel an active investigation workflow cooperatively."""
    state = default_workflow_runner.get_state(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found",
        )
    await default_workflow_runner.cancel(workflow_id)
    return {
        "workflow_id": workflow_id,
        "status": "CANCELLED",
        "message": "Workflow cancellation requested.",
    }


@router.post("/workflow/{workflow_id}/resume", response_model=dict[str, Any])
async def resume_workflow(workflow_id: str) -> dict[str, Any]:
    """Resume an interrupted or checkpointed workflow from its last valid node."""
    state = default_workflow_runner.get_state(workflow_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with ID '{workflow_id}' not found",
        )
    res = await default_workflow_runner.resume(workflow_id)
    return {
        "workflow_id": workflow_id,
        "status": res.get("status"),
        "current_phase": res.get("current_phase"),
    }

