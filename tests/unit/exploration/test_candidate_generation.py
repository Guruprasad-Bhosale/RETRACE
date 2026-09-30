"""Unit tests for deterministic candidate generation and ordering."""

from uuid import uuid4

from apps.worker.browser.inventory import ActionableElement, ElementInventory
from apps.worker.exploration.candidate import CandidateGenerator
from apps.worker.exploration.config import ExplorationConfig
from packages.domain.models import ActionType


def test_candidate_generation_deterministic_ordering_with_document_order():
    config = ExplorationConfig(seed_url="http://localhost:3001")
    generator = CandidateGenerator(config)

    el_1 = ActionableElement(
        tag="button",
        accessible_name="Submit",
        dom_id="submit-btn",
        stable_identity="id:submit-btn",
    )
    el_2 = ActionableElement(
        tag="input",
        element_type="text",
        name_attr="query",
        placeholder="Search...",
        stable_identity="input:query",
    )
    el_3 = ActionableElement(
        tag="a",
        accessible_name="Catalog",
        href="/catalog.html",
        stable_identity="link:catalog",
    )

    inventory = ElementInventory(
        elements=[el_1, el_2, el_3],
        total_count=3,
        by_tag={"button": 1, "input": 1, "a": 1},
    )

    state_id = "state_123"
    obs_id = uuid4()

    candidates = generator.generate_candidates(
        inventory=inventory,
        source_state_id=state_id,
        source_observation_id=obs_id,
        current_url="http://localhost:3001/",
    )

    assert len(candidates) == 3
    # Check that ordering keys are strictly sorted
    keys = [c.compute_ordering_key() for c in candidates]
    assert keys == sorted(keys)

    # Check synthetic input values
    input_cand = next(c for c in candidates if c.action_type == ActionType.TYPE)
    assert input_cand.value == "test"
