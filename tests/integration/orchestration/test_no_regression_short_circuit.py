"""Integration test for zero-regression short circuit in LangGraph workflow."""

from uuid import uuid4

import pytest

from apps.worker.orchestration.models import (
    InvestigationRequest,
    InvestigationWorkflowState,
    VersionConfig,
    WorkflowStatus,
    utc_now,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)


@pytest.mark.asyncio
async def test_workflow_zero_regression_short_circuit(tmp_path):
    """Verify workflow cleanly completes without running reproduction when no regressions exist."""
    runner = InvestigationWorkflowRunner()

    analysis_id = uuid4()
    req = InvestigationRequest(
        project_id="test-clean",
        analysis_id=analysis_id,
        version_a=VersionConfig(base_url="http://127.0.0.1:9000"),
        version_b=VersionConfig(base_url="http://127.0.0.1:9001"),
    )

    # Mock classify to return 0 regressions
    clf_non = RegressionClassification(
        classification_id="clf_clean_01",
        difference_id="diff_clean_01",
        status=ClassificationStatus.NON_REGRESSION,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-CLEAN",
        reason="Clean version",
        evidence=ClassificationEvidence(
            difference_id="diff_clean_01",
            canonical_subject="body",
            details={},
        ),
    )
    clf_res = RegressionClassificationResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[clf_non],
    )

    # Mock explore & diff in adapters to return clean results
    async def mock_explore(state: InvestigationWorkflowState):
        return {
            "exploration_result_a": {"visited_states": []},
            "exploration_result_b": {"visited_states": []},
            "current_phase": "explore",
            "history": runner.adapters._record_node(state, "explore", "COMPLETED", utc_now()),
        }

    async def mock_align(state: InvestigationWorkflowState):
        return {"alignment_result": {"pairs": []}, "current_phase": "align", "history": state.get("history", [])}

    async def mock_diff(state: InvestigationWorkflowState):
        return {"semantic_diff_result": {"differences": []}, "current_phase": "diff", "history": state.get("history", [])}

    async def mock_classify(state: InvestigationWorkflowState):
        return {"classification_result": clf_res, "current_phase": "classify", "history": state.get("history", [])}

    runner.adapters.explore = mock_explore
    runner.adapters.align = mock_align
    runner.adapters.diff = mock_diff
    runner.adapters.classify = mock_classify

    # Re-compile graph with patched node adapters
    from apps.worker.orchestration.graph import create_investigation_graph
    runner.graph = create_investigation_graph(adapters=runner.adapters, checkpointer=runner.checkpointer)

    result_state = await runner.run(req)

    assert result_state["status"] == WorkflowStatus.COMPLETED.value
    assert result_state["current_phase"] == "finalize_no_regression"
    assert result_state["investigation_suite"].summary.total_investigations == 0

    # Ensure reproduction and root cause nodes were NOT executed
    executed_nodes = [h["node_name"] for h in result_state.get("history", [])]
    assert "reproduce" not in executed_nodes
    assert "root_cause" not in executed_nodes
    assert "assemble" not in executed_nodes
