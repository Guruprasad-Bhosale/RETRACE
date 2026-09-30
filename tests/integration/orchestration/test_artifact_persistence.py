"""Integration test verifying artifact reference preservation throughout the workflow."""

from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import MemorySaver

from apps.worker.orchestration.graph import create_investigation_graph
from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)
from apps.worker.reproduction.models import (
    MatchStatus,
    ReproductionAttemptResult,
    ReproductionEvidence,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
    ReproductionSuiteResult,
    ReproductionVerification,
)
from apps.worker.rootcause.models import (
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    RootCauseSuiteResult,
)
from packages.domain.models import ArtifactKind, ArtifactReference


@pytest.mark.asyncio
async def test_artifact_persistence_in_workflow():
    checkpointer = MemorySaver()
    adapters = InvestigationNodeAdapters()
    graph = create_investigation_graph(adapters, checkpointer=checkpointer)

    analysis_id = uuid4()
    run_a_id = uuid4()
    run_b_id = uuid4()
    traj_a_id = uuid4()
    traj_b_id = uuid4()

    mock_artifact = ArtifactReference(
        id=uuid4(),
        kind=ArtifactKind.SCREENSHOT,
        storage_uri="file:///test/screenshot.png",
        mime_type="image/png",
        size_bytes=1024,
        sha256_hash="abcdef123456",
    )

    mock_classification = RegressionClassificationResult(
        run_a_id=run_a_id,
        run_b_id=run_b_id,
        trajectory_a_id=traj_a_id,
        trajectory_b_id=traj_b_id,
        classifications=[
            RegressionClassification(
                classification_id="clf-art-1",
                difference_id="diff-art-1",
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                category=RegressionCategory.FUNCTIONAL,
                rule_id="RULE_TEST",
                reason="Missing CTA button on checkout.",
                evidence=ClassificationEvidence(
                    difference_id="diff-art-1",
                    artifact_references=[mock_artifact],
                ),
            )
        ],
    )

    mock_reproduction_suite = ReproductionSuiteResult(
        run_a_id=run_a_id,
        run_b_id=run_b_id,
        trajectory_a_id=traj_a_id,
        trajectory_b_id=traj_b_id,
        results=[
            ReproductionResult(
                reproduction_id="repro-art-1",
                classification_id="clf-art-1",
                difference_id="diff-art-1",
                rule_id="RULE_TEST",
                category="FUNCTIONAL",
                status=ReproductionStatus.REPRODUCED,
                strategy=ReproductionStrategy.DIRECT_REPLAY,
                path=ReproductionPath(
                    path_id="path-art-1",
                    trajectory_id=traj_a_id,
                    classification_id="clf-art-1",
                    difference_id="diff-art-1",
                    seed_url="http://localhost:3000",
                    path_signature="sig-art-1",
                ),
                attempts=[
                    ReproductionAttemptResult(
                        attempt_number=1,
                        strategy=ReproductionStrategy.DIRECT_REPLAY,
                        status=ReproductionStatus.REPRODUCED,
                        evidence=ReproductionEvidence(
                            artifact_references=[mock_artifact],
                        ),
                    )
                ],
                final_verification=ReproductionVerification(
                    expected_difference_id="diff-art-1",
                    expected_classification_id="clf-art-1",
                    expected_rule_id="RULE_TEST",
                    expected_category="FUNCTIONAL",
                    match_status=MatchStatus.FULL_MATCH,
                    observed_match=True,
                ),
            )
        ],
    )

    mock_root_cause_suite = RootCauseSuiteResult(
        run_a_id=run_a_id,
        run_b_id=run_b_id,
        results=[
            RootCauseResult(
                root_cause_id="rc-art-1",
                classification_id="clf-art-1",
                difference_id="diff-art-1",
                reproduction_id="repro-art-1",
                category="FUNCTIONAL",
                status=RootCauseStatus.LOCATED,
                provenance=RootCauseProvenance(
                    classification_id="clf-art-1",
                    difference_id="diff-art-1",
                    reproduction_id="repro-art-1",
                ),
            )
        ],
    )

    initial_state: InvestigationWorkflowState = {
        "workflow_id": "wf-art-1",
        "analysis_id": str(analysis_id),
        "status": WorkflowStatus.RUNNING.value,
        "current_phase": "start",
        "version_a": {"base_url": "http://localhost:3000", "version_id": str(run_a_id)},
        "version_b": {"base_url": "http://localhost:3001", "version_id": str(run_b_id)},
        "history": [],
        "artifacts": [mock_artifact.model_dump(mode="json")],
        "cancellation_requested": False,
        "exploration_result_a": {"states_discovered": 5},
        "exploration_result_b": {"states_discovered": 5},
        "alignment_result": {"aligned_pairs": []},
        "semantic_diff_result": {"differences": []},
        "classification_result": mock_classification,
        "reproduction_suite": mock_reproduction_suite,
        "root_cause_suite": mock_root_cause_suite,
    }

    config = {"configurable": {"thread_id": "wf-art-1"}}
    final_state = await graph.ainvoke(initial_state, config=config)

    assert final_state["status"] == WorkflowStatus.COMPLETED.value
    assert final_state["investigation_suite"] is not None
    inv = final_state["investigation_suite"].investigations[0]
    # Verify that reproduction evidence artifacts are preserved in the final assembled investigation
    assert len(inv.reproduction.attempts[0].evidence.artifact_references) == 1
    assert inv.reproduction.attempts[0].evidence.artifact_references[0].storage_uri == "file:///test/screenshot.png"
