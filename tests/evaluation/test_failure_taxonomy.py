"""Unit tests for failure taxonomy categorization."""

from apps.worker.evaluation.models import FailureTaxonomy


def test_failure_taxonomy_values():
    assert len(FailureTaxonomy) == 12
    assert FailureTaxonomy.INPUT_FAILURE.value == "INPUT_FAILURE"
    assert FailureTaxonomy.CLASSIFICATION_FAILURE.value == "CLASSIFICATION_FAILURE"
    assert FailureTaxonomy.REPRODUCTION_FAILURE.value == "REPRODUCTION_FAILURE"
    assert FailureTaxonomy.ROOT_CAUSE_FAILURE.value == "ROOT_CAUSE_FAILURE"
    assert FailureTaxonomy.SYNTHESIS_FAILURE.value == "SYNTHESIS_FAILURE"
    assert FailureTaxonomy.ORCHESTRATION_FAILURE.value == "ORCHESTRATION_FAILURE"
