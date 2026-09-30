"""RETRACE Semantic Difference Engine Package.

Provides deterministic, evidence-backed semantic difference analysis across
Version A and Version B web application executions.
"""

from apps.worker.diff.config import DiffConfig
from apps.worker.diff.diagnostics import DiffDiagnosticsFormatter
from apps.worker.diff.engine import SemanticDiffEngine
from apps.worker.diff.errors import (
    DiffEngineError,
    IncompatibleAlignmentError,
    InvalidEvidenceError,
)
from apps.worker.diff.models import (
    AccessibilityDifference,
    ActionDifference,
    ComparisonStatus,
    ConsoleDifference,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    InteractionDifference,
    NetworkDifference,
    PerformanceDifference,
    RouteDifference,
    SemanticDifference,
    SemanticDiffResult,
    SemanticDiffSummary,
    StateDifference,
    TransitionDifference,
)

__all__ = [
    "AccessibilityDifference",
    "ActionDifference",
    "ComparisonStatus",
    "ConsoleDifference",
    "DiffConfig",
    "DiffDiagnosticsFormatter",
    "DiffEngineError",
    "DifferenceCategory",
    "DifferenceEvidence",
    "DifferenceKind",
    "IncompatibleAlignmentError",
    "InteractionDifference",
    "InvalidEvidenceError",
    "NetworkDifference",
    "PerformanceDifference",
    "RouteDifference",
    "SemanticDifference",
    "SemanticDiffEngine",
    "SemanticDiffResult",
    "SemanticDiffSummary",
    "StateDifference",
    "TransitionDifference",
]
