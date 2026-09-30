"""RETRACE Exploration Engine Exception Hierarchy."""

from typing import Any


class ExplorationError(Exception):
    """Base exception for all exploration engine errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ExplorationTimeoutError(ExplorationError):
    """Raised when exploration exceeds total time budget."""

    pass


class SafetyViolationError(ExplorationError):
    """Raised when an action violates safety boundary (destructive action, foreign origin)."""

    pass


class BacktrackingFailedError(ExplorationError):
    """Raised when path replay or navigation fails to return to parent state."""

    pass


class RecoveryMismatchError(BacktrackingFailedError):
    """Raised when recovered state identity diverges from expected target state identity."""

    pass


class ExcessiveFailuresError(ExplorationError):
    """Raised when action or navigation failures exceed configured threshold."""

    pass


class FrontierExhaustedError(ExplorationError):
    """Raised when exploration frontier has no remaining candidate transitions."""

    pass
