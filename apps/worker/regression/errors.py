"""Regression Classification Engine Error Hierarchy.

Defines deterministic exceptions for invalid semantic differences,
unsupported inputs, and classification engine configuration errors.
"""


class RegressionEngineError(Exception):
    """Base exception for all regression classification engine errors."""


class InvalidSemanticDiffError(RegressionEngineError):
    """Raised when a SemanticDiffResult cannot be classified due to missing or invalid structure."""


class UnsupportedDifferenceError(RegressionEngineError):
    """Raised when an unhandled or structurally malformed difference is encountered."""


class ClassificationConfigurationError(RegressionEngineError):
    """Raised when regression classification policies or thresholds are improperly configured."""
