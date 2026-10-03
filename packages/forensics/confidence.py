"""Transparent Forensic Confidence Model.

Computes non-arbitrary, defensible confidence levels grounded in verifiable evidence weights,
contradiction counts, and reproduction status without artificial probability fabrication.
"""

from packages.forensics.models import (
    ConfidenceAssessment,
    ConfidenceLevel,
    ForensicEvidenceItem,
    ForensicEvidenceType,
    ForensicHypothesis,
    HypothesisStatus,
)


class ConfidenceCalculator:
    """Calculates transparent confidence metrics for forensic root-cause conclusions."""

    # Explicit evidence weights reflecting investigative authority
    WEIGHT_REPRODUCTION_CONFIRMED: float = 0.40
    WEIGHT_AST_SOURCE_MATCH: float = 0.35
    WEIGHT_DOM_NETWORK_OBSERVATION: float = 0.20
    WEIGHT_CONTRADICTING_PENALTY: float = 0.50
    WEIGHT_UNRESOLVED_PENALTY: float = 0.10

    @classmethod
    def evaluate(
        cls,
        primary_hypothesis: ForensicHypothesis,
        evidence_catalog: dict[str, ForensicEvidenceItem] | list[ForensicEvidenceItem],
        has_reproduction: bool = False,
        has_source_match: bool = False,
    ) -> ConfidenceAssessment:
        """Evaluate confidence based on evidence weights and contradiction counts."""
        if isinstance(evidence_catalog, list):
            catalog = {e.id: e for e in evidence_catalog}
        else:
            catalog = evidence_catalog

        supporting_ids = set(primary_hypothesis.supporting_evidence_ids)
        contradicting_ids = set(primary_hypothesis.contradicting_evidence_ids)

        supporting_count = len(supporting_ids)
        contradicting_count = len(contradicting_ids)

        score = 0.0

        # 1. Evaluate reproduction authority
        if has_reproduction:
            score += cls.WEIGHT_REPRODUCTION_CONFIRMED
        else:
            for ev_id in supporting_ids:
                item = catalog.get(ev_id)
                if item and item.evidence_type in (
                    ForensicEvidenceType.REPRODUCTION,
                    ForensicEvidenceType.TEST_RESULT,
                ):
                    score += cls.WEIGHT_REPRODUCTION_CONFIRMED
                    break

        # 2. Evaluate AST / Git source attribution authority
        if has_source_match:
            score += cls.WEIGHT_AST_SOURCE_MATCH
        else:
            for ev_id in supporting_ids:
                item = catalog.get(ev_id)
                if item and item.evidence_type in (
                    ForensicEvidenceType.AST_DIFF,
                    ForensicEvidenceType.GIT_DIFF,
                    ForensicEvidenceType.SOURCE_REFERENCE,
                ):
                    score += cls.WEIGHT_AST_SOURCE_MATCH
                    break

        # 3. Evaluate DOM and Network observation support
        for ev_id in supporting_ids:
            item = catalog.get(ev_id)
            if item and item.evidence_type in (
                ForensicEvidenceType.DOM_OBSERVATION,
                ForensicEvidenceType.NETWORK_OBSERVATION,
                ForensicEvidenceType.STATE_DIFF,
            ):
                score += cls.WEIGHT_DOM_NETWORK_OBSERVATION
                break

        # 4. Apply penalties for contradictions
        score -= contradicting_count * cls.WEIGHT_CONTRADICTING_PENALTY

        # Unresolved count
        unresolved_count = 1 if primary_hypothesis.status == HypothesisStatus.UNRESOLVED else 0
        score -= unresolved_count * cls.WEIGHT_UNRESOLVED_PENALTY

        # Clamp score between 0.0 and 1.0
        final_score = max(0.0, min(1.0, round(score, 2)))

        # Determine qualitative confidence level
        if final_score >= 0.75 and supporting_count >= 2 and contradicting_count == 0:
            level = ConfidenceLevel.HIGH
            rationale = (
                f"High confidence: {supporting_count} supporting evidence sources verified, "
                "including deterministic reproduction and AST source attribution with 0 contradictions."
            )
        elif final_score >= 0.45 and contradicting_count == 0:
            level = ConfidenceLevel.MEDIUM
            rationale = (
                f"Medium confidence: {supporting_count} supporting evidence sources verified. "
                "Behavioral difference localized but requires secondary verification."
            )
        elif final_score >= 0.25:
            level = ConfidenceLevel.LOW
            rationale = (
                f"Low confidence: Score {final_score:.2f} with {contradicting_count} contradicting "
                "or inconclusive observations."
            )
        else:
            level = ConfidenceLevel.INSUFFICIENT
            rationale = "Insufficient confidence: Available evidence does not satisfy deterministic verification."

        return ConfidenceAssessment(
            level=level,
            score=final_score,
            supporting_count=supporting_count,
            contradicting_count=contradicting_count,
            unresolved_count=unresolved_count,
            rationale=rationale,
        )
