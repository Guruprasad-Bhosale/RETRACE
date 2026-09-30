"""RETRACE Behavioral Trajectory Alignment Subsystem.

Provides deterministic structural alignment between Version A and Version B exploration trajectories.
"""

from apps.worker.alignment.action_signature import ActionSignatureCalculator
from apps.worker.alignment.aligner import BehavioralTrajectoryAligner
from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.diagnostics import AlignmentDiagnosticsFormatter
from apps.worker.alignment.divergence import DivergenceExtractor
from apps.worker.alignment.errors import (
    ActionAlignmentError,
    AlignmentError,
    AmbiguousAlignmentError,
    DivergenceExtractionError,
    StateAlignmentError,
)
from apps.worker.alignment.matcher import ActionMatcher, RouteMatcher, StateMatcher
from apps.worker.alignment.models import (
    ActionAlignment,
    ActionSignature,
    AlignmentRelation,
    AlignmentResult,
    Divergence,
    DivergenceType,
    EvidenceStrength,
    MatchEvidence,
    StateAlignment,
    StateObservationalFeatures,
    StateSignature,
    TrajectoryAlignment,
    TransitionAlignment,
)
from apps.worker.alignment.route_alignment import (
    RouteAligner,
    RouteAlignmentPair,
    RouteAlignmentSummary,
)
from apps.worker.alignment.runner import ABAnalysisRunner
from apps.worker.alignment.sequence import SequenceGap, TransitionSequenceAnalyzer
from apps.worker.alignment.state_signature import StateSignatureCalculator
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner

__all__ = [
    "ABAnalysisRunner",
    "ActionAlignment",
    "ActionAlignmentError",
    "ActionMatcher",
    "ActionSignature",
    "ActionSignatureCalculator",
    "AlignmentConfig",
    "AlignmentDiagnosticsFormatter",
    "AlignmentError",
    "AlignmentRelation",
    "AlignmentResult",
    "AmbiguousAlignmentError",
    "BehavioralTrajectoryAligner",
    "Divergence",
    "DivergenceExtractionError",
    "DivergenceExtractor",
    "DivergenceType",
    "EvidenceStrength",
    "MatchEvidence",
    "RouteAligner",
    "RouteAlignmentPair",
    "RouteAlignmentSummary",
    "RouteMatcher",
    "SequenceGap",
    "StateAlignment",
    "StateAlignmentError",
    "StateMatcher",
    "StateObservationalFeatures",
    "StateSignature",
    "StateSignatureCalculator",
    "TrajectoryAligner",
    "TrajectoryAlignment",
    "TransitionAlignment",
    "TransitionSequenceAnalyzer",
]
