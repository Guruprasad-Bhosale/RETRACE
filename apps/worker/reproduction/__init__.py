"""RETRACE Autonomous Regression Reproduction Engine Package.

Provides deterministic causal path planning, dual-version browser replay, expected vs actual
evidence verification, bounded precondition recovery, safety enforcement, and reproduction persistence.
"""

from apps.worker.reproduction.config import (
    PerformanceSamplingPolicy,
    RecoveryPolicy,
    ReplayPolicy,
    ReproductionConfig,
    SafetyPolicy,
    VerificationPolicy,
)
from apps.worker.reproduction.diagnostics import ReproductionDiagnosticsFormatter
from apps.worker.reproduction.engine import ReproductionEngine
from apps.worker.reproduction.errors import (
    ActionResolutionError,
    PathPlanningError,
    PathValidationError,
    RecoveryExhaustedError,
    ReplayExecutionError,
    ReproductionConfigError,
    ReproductionEngineError,
    ReproductionTimeoutError,
    SafetyViolationError,
    VerificationError,
)
from apps.worker.reproduction.models import (
    MatchStatus,
    OriginalEvidence,
    ReproductionAttemptResult,
    ReproductionEvidence,
    ReproductionObservation,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStep,
    ReproductionStrategy,
    ReproductionSuiteResult,
    ReproductionSummary,
    compute_deterministic_reproduction_id,
)
from apps.worker.reproduction.path import (
    compute_reproduction_path_signature,
    validate_reproduction_path,
)
from apps.worker.reproduction.persistence import ReproductionPersistenceMapper
from apps.worker.reproduction.planner import ReproductionPathPlanner
from apps.worker.reproduction.replay import ReproductionReplayEngine
from apps.worker.reproduction.safety import ReproductionSafetyGuard
from apps.worker.reproduction.verification import ReproductionVerifier

__all__ = [
    "ActionResolutionError",
    "MatchStatus",
    "OriginalEvidence",
    "PathPlanningError",
    "PathValidationError",
    "PerformanceSamplingPolicy",
    "RecoveryExhaustedError",
    "RecoveryPolicy",
    "ReplayExecutionError",
    "ReplayPolicy",
    "ReproductionAttemptResult",
    "ReproductionConfig",
    "ReproductionConfigError",
    "ReproductionDiagnosticsFormatter",
    "ReproductionEngine",
    "ReproductionEngineError",
    "ReproductionEvidence",
    "ReproductionObservation",
    "ReproductionPath",
    "ReproductionPathPlanner",
    "ReproductionPersistenceMapper",
    "ReproductionReplayEngine",
    "ReproductionResult",
    "ReproductionSafetyGuard",
    "ReproductionStatus",
    "ReproductionStep",
    "ReproductionStrategy",
    "ReproductionSuiteResult",
    "ReproductionSummary",
    "ReproductionTimeoutError",
    "ReproductionVerifier",
    "SafetyPolicy",
    "SafetyViolationError",
    "VerificationError",
    "VerificationPolicy",
    "compute_deterministic_reproduction_id",
    "compute_reproduction_path_signature",
    "validate_reproduction_path",
]
