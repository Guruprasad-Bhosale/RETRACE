"""Structured Exception Hierarchy for Phase 8 Autonomous Regression Reproduction Engine."""


class ReproductionEngineError(Exception):
    """Base exception for all reproduction engine errors."""


class PathPlanningError(ReproductionEngineError):
    """Raised when causal reproduction path cannot be planned from source evidence."""


class PathValidationError(ReproductionEngineError):
    """Raised when a candidate reproduction path fails topological or structural validation."""


class ActionResolutionError(ReproductionEngineError):
    """Raised when an action's stable semantic identity cannot be resolved on a target state."""


class ReplayExecutionError(ReproductionEngineError):
    """Raised when browser replay execution fails unexpectedly during session progression."""


class SafetyViolationError(ReproductionEngineError):
    """Raised when an action or navigation violates reproductive safety policies."""


class VerificationError(ReproductionEngineError):
    """Raised when reproduction verification encounters invalid or incomparable evidence."""


class RecoveryExhaustedError(ReproductionEngineError):
    """Raised when bounded recovery fails to restore expected preconditions within configured limits."""


class ReproductionTimeoutError(ReproductionEngineError):
    """Raised when overall reproduction attempt exceeds max duration timeout."""


class ReproductionConfigError(ReproductionEngineError):
    """Raised when reproduction configuration parameters are invalid."""
