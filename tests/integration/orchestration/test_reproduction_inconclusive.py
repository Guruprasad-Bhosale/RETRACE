"""Integration test for workflow handling reproduction NO_MATCH resulting in INCONCLUSIVE."""

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


@pytest.mark.asyncio
async def test_reproduction_inconclusive_workflow():
    checkpointer = MemorySaver()
    adapters = InvestigationNodeAdapters()
    graph = create_investigation_graph(adapters, checkpointer=checkpointer)

    analysis_id = uuid4()
    run_a_id = uuid4()
    run_b_id = uuid4()
    traj_a_id = uuid4()
    traj_b_id = uuid4()

    mock_classification = RegressionClassificationResult(
        run_a_id=run_a_id,
        run_b_id=run_b_id,
        trajectory_a_id=traj_a_id,
        trajectory_b_id=traj_b_id,
        classifications=[
            RegressionClassification(
                classification_id="clf-inconc-1",
                difference_id="diff-1",
                status=ClassificationStatus.REGRESSION_CANDIDATE,
                category=RegressionCategory.FUNCTIONAL,
                rule_id="RULE_TEST",
                reason="Element missing on v2",
                evidence=ClassificationEvidence(
                    difference_id="diff-1",
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
                reproduction_id="repro-inconc-1",
                classification_id="clf-inconc-1",
                difference_id="diff-1",
                rule_id="RULE_TEST",
                category="FUNCTIONAL",
                status=ReproductionStatus.NOT_REPRODUCED,
                strategy=ReproductionStrategy.DIRECT_REPLAY,
                path=ReproductionPath(
                    path_id="path-1",
                    trajectory_id=traj_a_id,
                    classification_id="clf-inconc-1",
                    difference_id="diff-1",
                    seed_url="http://localhost:3000",
                    path_signature="sig-1",
                ),
                attempts=[
                    ReproductionAttemptResult(
                        attempt_number=1,
                        strategy=ReproductionStrategy.DIRECT_REPLAY,
                        status=ReproductionStatus.NOT_REPRODUCED,
                        evidence=ReproductionEvidence(),
                    )
                ],
                final_verification=ReproductionVerification(
                    expected_difference_id="diff-1",
                    expected_classification_id="clf-inconc-1",
                    expected_rule_id="RULE_TEST",
                    expected_category="FUNCTIONAL",
                    match_status=MatchStatus.NO_MATCH,
                    observed_match=False,
                ),
            )
        ],
    )

    mock_root_cause_suite = RootCauseSuiteResult(
        run_a_id=run_a_id,
        run_b_id=run_b_id,
        results=[
            RootCauseResult(
                root_cause_id="rc-inconc-1",
                classification_id="clf-inconc-1",
                difference_id="diff-1",
                reproduction_id="repro-inconc-1",
                category="FUNCTIONAL",
                status=RootCauseStatus.INCONCLUSIVE,
                provenance=RootCauseProvenance(
                    classification_id="clf-inconc-1",
                    difference_id="diff-1",
                    reproduction_id="repro-inconc-1",
                ),
            )
        ],
    )

    initial_state: InvestigationWorkflowState = {
        "workflow_id": "wf-inconclusive-1",
        "analysis_id": str(analysis_id),
        "status": WorkflowStatus.RUNNING.value,
        "current_phase": "start",
        "version_a": {"base_url": "http://localhost:3000", "version_id": str(run_a_id)},
        "version_b": {"base_url": "http://localhost:3001", "version_id": str(run_b_id)},
        "history": [],
        "artifacts": [],
        "cancellation_requested": False,
        "exploration_result_a": {"states_discovered": 5},
        "exploration_result_b": {"states_discovered": 5},
        "alignment_result": {"aligned_pairs": []},
        "semantic_diff_result": {"differences": []},
        "classification_result": mock_classification,
        "reproduction_suite": mock_reproduction_suite,
        "root_cause_suite": mock_root_cause_suite,
    }

    config = {"configurable": {"thread_id": "wf-inconclusive-1"}}
    final_state = await graph.ainvoke(initial_state, config=config)

    assert final_state["status"] == WorkflowStatus.INCONCLUSIVE.value
    assert final_state["investigation_suite"] is not None
    assert final_state["investigation_suite"].summary.inconclusive_count == 1
    assert final_state["investigation_suite"].summary.completed_count == 0
