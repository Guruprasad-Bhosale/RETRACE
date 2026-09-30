"""Transition Sequence and Gap Utility Module.

Provides deterministic sequence ordering and gap representation for ordered child transitions.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.alignment.models import AlignmentRelation, TransitionAlignment


class SequenceGap(BaseModel):
    """Represents an unaligned transition gap in Version A or Version B."""

    model_config = ConfigDict(extra="forbid")

    side: str = Field(description="'A' or 'B'")
    transition_id: str
    from_state_id: str
    to_state_id: str
    action_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransitionSequenceAnalyzer:
    """Helper for analyzing ordered transition paths and identifying transition gaps."""

    @staticmethod
    def extract_gaps(
        transition_alignments: list[TransitionAlignment],
    ) -> tuple[list[SequenceGap], list[SequenceGap]]:
        """Separate aligned transitions into gaps on side A and gaps on side B."""
        gaps_a: list[SequenceGap] = []
        gaps_b: list[SequenceGap] = []

        for ta in transition_alignments:
            if ta.relation == AlignmentRelation.UNMATCHED:
                if ta.transition_a_id and not ta.transition_b_id:
                    gaps_a.append(
                        SequenceGap(
                            side="A",
                            transition_id=ta.transition_a_id,
                            from_state_id=ta.from_state_a_id or "",
                            to_state_id=ta.to_state_a_id or "",
                            action_type=ta.action_alignment.signature_a.action_type.value
                            if ta.action_alignment and ta.action_alignment.signature_a
                            else "UNKNOWN",
                        )
                    )
                elif ta.transition_b_id and not ta.transition_a_id:
                    gaps_b.append(
                        SequenceGap(
                            side="B",
                            transition_id=ta.transition_b_id,
                            from_state_id=ta.from_state_b_id or "",
                            to_state_id=ta.to_state_b_id or "",
                            action_type=ta.action_alignment.signature_b.action_type.value
                            if ta.action_alignment and ta.action_alignment.signature_b
                            else "UNKNOWN",
                        )
                    )

        return gaps_a, gaps_b
