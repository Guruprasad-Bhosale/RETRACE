"""RETRACE Browser Observation Engine Exception Hierarchy."""

from typing import Any


class BrowserEngineError(Exception):
    """Base exception for all browser observation engine errors."""

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


class BrowserLaunchError(BrowserEngineError):
    """Raised when browser process fails to launch safely."""

    pass


class BrowserContextError(BrowserEngineError):
    """Raised when context creation or sandboxing fails."""

    pass


class NavigationTimeoutError(BrowserEngineError):
    """Raised when page navigation exceeds configured timeout."""

    pass


class NavigationFailedError(BrowserEngineError):
    """Raised when page navigation fails due to network/DNS/protocol error."""

    pass


class ActionExecutionError(BrowserEngineError):
    """Raised when an explicit browser action fails to execute."""

    pass


class ElementNotFoundError(ActionExecutionError):
    """Raised when a requested action target cannot be resolved."""

    pass


class ElementNotInteractableError(ActionExecutionError):
    """Raised when target element exists but is disabled, obscured, or not actionable."""

    pass


class StabilizationTimeoutError(BrowserEngineError):
    """Raised when page state stabilization settles with an unresolved timeout."""

    pass


class ArtifactPersistenceError(BrowserEngineError):
    """Raised when writing an observation artifact to storage fails."""

    pass


class BrowserCrashedError(BrowserEngineError):
    """Raised when the browser context or page crashes unexpectedly."""

    pass
