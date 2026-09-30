"""Unit tests for DivergenceExtractor."""

from uuid import uuid4

from apps.worker.alignment.divergence import DivergenceExtractor
from apps.worker.alignment.models import (
    AlignmentRelation,
    DivergenceType,
    EvidenceStrength,
    MatchEvidence,
    StateAlignment,
    StateObservationalFeatures,
    StateSignature,
)
from apps.worker.alignment.route_alignment import RouteAlignmentSummary


def test_extract_route_divergences() -> None:
    summary = RouteAlignmentSummary(
        unmatched_routes_a=["/legacy-cart"],
        unmatched_routes_b=["/express-checkout"],
    )
    divs = DivergenceExtractor.extract_route_divergences(summary)
    assert len(divs) == 2
    types = [d.divergence_type for d in divs]
    assert DivergenceType.ROUTE_DIVERGENCE in types


def test_extract_http_status_and_console_divergences() -> None:
    obs_a_id = uuid4()
    obs_b_id = uuid4()

    sig_a = StateSignature(
        state_id="s1",
        normalized_route="/checkout",
        inventory_signature="inv",
        a11y_signature="a11y",
        ui_state_signature="ui",
        observational=StateObservationalFeatures(
            http_status=200,
            console_errors_count=0,
            page_title="Checkout",
        ),
    )
    sig_b = StateSignature(
        state_id="s2",
        normalized_route="/checkout",
        inventory_signature="inv",
        a11y_signature="a11y",
        ui_state_signature="ui",
        observational=StateObservationalFeatures(
            http_status=404,
            console_errors_count=2,
            page_title="Checkout — Not Found",
        ),
    )

    sa = StateAlignment(
        state_a_id="s1",
        state_b_id="s2",
        observation_a_id=obs_a_id,
        observation_b_id=obs_b_id,
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.STRONG_MATCH,
        evidence=MatchEvidence(evidence_strength=EvidenceStrength.STRONG),
    )

    divs = DivergenceExtractor.extract_state_observational_divergences([sa])
    assert len(divs) == 3
    div_types = {d.divergence_type for d in divs}
    assert DivergenceType.HTTP_STATUS_DIVERGENCE in div_types
    assert DivergenceType.CONSOLE_ERROR_DIVERGENCE in div_types
    assert DivergenceType.OBSERVATIONAL_DIVERGENCE in div_types

    http_div = next(d for d in divs if d.divergence_type == DivergenceType.HTTP_STATUS_DIVERGENCE)
    assert http_div.observation_a_id == obs_a_id
    assert http_div.observation_b_id == obs_b_id
