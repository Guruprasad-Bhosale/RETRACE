"""Alignment Exception Hierarchy.

Explicit exceptions raised during behavioral trajectory and state alignment.
"""


class AlignmentError(Exception):
    """Base exception for all alignment subsystem errors."""


class StateAlignmentError(AlignmentError):
    """Raised when state alignment invariants are violated."""


class ActionAlignmentError(AlignmentError):
    """Raised when action matching encounters an invalid state."""


class AmbiguousAlignmentError(AlignmentError):
    """Raised when an alignment operation requires an unambiguous match but ambiguity is detected."""


class DivergenceExtractionError(AlignmentError):
    """Raised when divergence extraction fails to map valid evidence."""
