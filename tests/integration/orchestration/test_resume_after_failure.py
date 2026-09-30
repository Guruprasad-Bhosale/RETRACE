"""Critical Failure-Recovery Integration Test.

Verifies that upon worker restart or failure during Phase 8 reproduction,
earlier completed phases (observe, explore, align, diff, classify) are NOT re-executed,
and reproduction resumes seamlessly from checkpointed state.
"""

from uuid import uuid4

import pytest

from apps.worker.investigation.models import (
    InvestigationProvenance,
    InvestigationResult,
    InvestigationStatus,
    InvestigationSuiteResult,
    InvestigationSummary,
)
from apps.worker.orchestration.graph import create_investigation_graph
from apps.worker.orchestration.models import (
    InvestigationRequest,
    InvestigationWorkflowState,
    VersionConfig,
    WorkflowStatus,
    utc_now,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters
from apps.worker.orchestration.runner import InvestigationWorkflowRunner
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)
from apps.worker.reporting.models import EvidenceChain, EvidenceReport
from apps.worker.reproduction.models import (
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionSuiteResult,
)
from apps.worker.rootcause.models import (
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    RootCauseSuiteResult,
)


@pytest.mark.asyncio
async def test_resume_after_failure_does_not_repeat_completed_phases():
    """Mandatory Phase 12 recovery test:

    1. Run phases 1-7 (validate, prepare, explore, align, diff, classify).
    2. Simulate failure / interruption at reproduction.
    3. Resume workflow with same thread_id.
    4. Verify explore/align/diff/classify are skipped/not re-executed,
       and reproduction/root_cause/assemble resume and complete cleanly.
    """
    adapters = InvestigationNodeAdapters()
    runner = InvestigationWorkflowRunner(adapters=adapters)

    analysis_id = uuid4()
    workflow_id = f"wf_resume_test_{analysis_id}"
    thread_id = workflow_id

    req = InvestigationRequest(
        project_id="commerce-failure-recovery",
        analysis_id=analysis_id,
        version_a=VersionConfig(base_url="http://127.0.0.1:9000"),
        version_b=VersionConfig(base_url="http://127.0.0.1:9001"),
    )

    clf = RegressionClassification(
        classification_id="clf_rec_01",
        difference_id="diff_rec_01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-RECOVERY-01",
        reason="Recovery candidate regression",
        evidence=ClassificationEvidence(
            difference_id="diff_rec_01",
            canonical_subject="button#cart",
            details={},
        ),
    )
    clf_res = RegressionClassificationResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[clf],
    )

    explore_call_count = 0
    align_call_count = 0
    diff_call_count = 0
    classify_call_count = 0
    reproduce_call_count = 0

    async def counting_explore(state: InvestigationWorkflowState):
        nonlocal explore_call_count
        if state.get("exploration_result_a") is not None:
            history = adapters._record_node(state, "explore", "SKIPPED", utc_now())
            return {"history": history}
        explore_call_count += 1
        return {
            "exploration_result_a": {"visited_states": []},
            "exploration_result_b": {"visited_states": []},
            "current_phase": "explore",
            "history": adapters._record_node(state, "explore", "COMPLETED", utc_now()),
        }

    async def counting_align(state: InvestigationWorkflowState):
        nonlocal align_call_count
        if state.get("alignment_result") is not None:
            history = adapters._record_node(state, "align", "SKIPPED", utc_now())
            return {"history": history}
        align_call_count += 1
        return {"alignment_result": {"pairs": []}, "current_phase": "align", "history": state.get("history", [])}

    async def counting_diff(state: InvestigationWorkflowState):
        nonlocal diff_call_count
        if state.get("semantic_diff_result") is not None:
            history = adapters._record_node(state, "diff", "SKIPPED", utc_now())
            return {"history": history}
        diff_call_count += 1
        return {"semantic_diff_result": {"differences": []}, "current_phase": "diff", "history": state.get("history", [])}

    async def counting_classify(state: InvestigationWorkflowState):
        nonlocal classify_call_count
        if state.get("classification_result") is not None:
            history = adapters._record_node(state, "classify", "SKIPPED", utc_now())
            return {"history": history}
        classify_call_count += 1
        return {"classification_result": clf_res, "current_phase": "classify", "history": state.get("history", [])}

    repro_should_fail = True

    async def counting_reproduce(state: InvestigationWorkflowState):
        nonlocal reproduce_call_count, repro_should_fail
        reproduce_call_count += 1
        if repro_should_fail:
            # Simulate worker crash or transient failure
            return {
                "status": WorkflowStatus.FAILED.value,
                "error_message": "Simulated reproduction network interruption",
                "current_phase": "reproduce",
                "history": adapters._record_node(state, "reproduce", "FAILED", utc_now()),
            }

        # Successful reproduction on resume
        rep = ReproductionResult(
            reproduction_id="repro_rec_01",
            classification_id="clf_rec_01",
            difference_id="diff_rec_01",
            rule_id="RULE-RECOVERY-01",
            category="FUNCTIONAL",
            status=ReproductionStatus.REPRODUCED,
            strategy="DIRECT_REPLAY",
            path=ReproductionPath(
                path_id="path_rec_01",
                trajectory_id=uuid4(),
                classification_id="clf_rec_01",
                difference_id="diff_rec_01",
                seed_url="http://127.0.0.1:9000",
                path_signature="sig_rec_01",
                steps=[],
            ),
        )
        return {
            "reproduction_suite": ReproductionSuiteResult(
                run_a_id=uuid4(),
                run_b_id=uuid4(),
                trajectory_a_id=uuid4(),
                trajectory_b_id=uuid4(),
                results=[rep],
            ),
            "current_phase": "reproduce",
            "history": adapters._record_node(state, "reproduce", "COMPLETED", utc_now()),
        }

    async def mock_root_cause(state: InvestigationWorkflowState):
        rc = RootCauseResult(
            root_cause_id="rc_rec_01",
            classification_id="clf_rec_01",
            difference_id="diff_rec_01",
            category="FUNCTIONAL",
            status=RootCauseStatus.LOCATED,
            attributions=[],
            provenance=RootCauseProvenance(
                classification_id="clf_rec_01",
                difference_id="diff_rec_01",
            ),
        )
        return {
            "root_cause_suite": RootCauseSuiteResult(
                run_a_id=uuid4(),
                run_b_id=uuid4(),
                results=[rc],
            ),
            "current_phase": "root_cause",
            "history": state.get("history", []),
        }

    async def mock_assemble(state: InvestigationWorkflowState):
        from apps.worker.reporting.models import ReportProvenance, ReportStatus

        inv = InvestigationResult(
            investigation_id="inv_rec_01",
            analysis_id=analysis_id,
            regression_id="clf_rec_01",
            classification=clf,
            report=EvidenceReport(
                report_id="rep_rec_01",
                regression_id="clf_rec_01",
                title="Recovery Report",
                status=ReportStatus.COMPLETE,
                summary="Recovery summary",
                markdown_content="# Recovery",
                json_content={},
                evidence_chain=EvidenceChain(chain_id="ch_01", nodes=[]),
                provenance=ReportProvenance(
                    classification_id="clf_rec_01",
                    difference_id="diff_rec_01",
                ),
            ),
            provenance=InvestigationProvenance(analysis_id=analysis_id, classification_id="clf_rec_01", difference_id="diff_rec_01"),
            status=InvestigationStatus.COMPLETED,
        )
        suite = InvestigationSuiteResult(
            analysis_id=analysis_id,
            run_a_id=uuid4(),
            run_b_id=uuid4(),
            investigations=[inv],
            summary=InvestigationSummary(total_investigations=1, completed_count=1),
        )
        return {"investigation_suite": suite, "current_phase": "assemble", "history": state.get("history", [])}

    adapters.explore = counting_explore
    adapters.align = counting_align
    adapters.diff = counting_diff
    adapters.classify = counting_classify
    adapters.reproduce = counting_reproduce
    adapters.root_cause = mock_root_cause
    adapters.assemble = mock_assemble

    runner.graph = create_investigation_graph(adapters=adapters, checkpointer=runner.checkpointer)

    # 1. First execution: should fail at reproduction
    first_res = await runner.run(req, workflow_id=workflow_id, thread_id=thread_id)
    assert first_res["status"] == WorkflowStatus.FAILED.value
    assert explore_call_count == 1
    assert align_call_count == 1
    assert diff_call_count == 1
    assert classify_call_count == 1
    assert reproduce_call_count == 1

    # 2. Fix reproduction failure and resume from checkpoint
    repro_should_fail = False
    first_res["status"] = WorkflowStatus.RUNNING.value  # Mark running for resume

    resumed_res = await runner.resume(workflow_id=workflow_id, thread_id=thread_id)

    # Assert that explore, align, diff, and classify were NOT re-called!
    assert explore_call_count == 1, "Explore must not be repeated on resume"
    assert align_call_count == 1, "Align must not be repeated on resume"
    assert diff_call_count == 1, "Diff must not be repeated on resume"
    assert classify_call_count == 1, "Classify must not be repeated on resume"
    assert reproduce_call_count == 2, "Reproduce should be retried on resume"

    # Assert workflow completed successfully
    assert resumed_res["status"] == WorkflowStatus.COMPLETED.value
    assert resumed_res["investigation_suite"].summary.completed_count == 1
