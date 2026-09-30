"""Evidence Reporting Domain Exceptions.

Structured exception hierarchy for evidence report generation, causal chain building,
and deterministic report formatting.
"""


class ReportingError(Exception):
    """Base exception for all reporting operations."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MissingEvidenceError(ReportingError):
    """Raised when critical evidence is missing for a mandatory report section."""

    pass


class ReportFormattingError(ReportingError):
    """Raised when report formatting fails."""

    pass


class ReportSerializationError(ReportingError):
    """Raised when report serialization fails."""

    pass


class ReportingConfigError(ReportingError):
    """Raised when reporting configuration parameters are invalid."""

    pass
