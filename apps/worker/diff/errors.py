"""Semantic Difference Engine Error Hierarchy.

Defines deterministic exceptions for invalid alignments, missing evidence,
and diff execution anomalies.
"""


class DiffEngineError(Exception):
    """Base exception for all semantic difference engine errors."""


class IncompatibleAlignmentError(DiffEngineError):
    """Raised when an AlignmentResult cannot be compared due to missing or corrupt structural metadata."""


class InvalidEvidenceError(DiffEngineError):
    """Raised when evidence references are structurally invalid or unverifiable."""
