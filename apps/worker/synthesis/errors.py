"""Test Synthesis Domain Exceptions.

Structured exception hierarchy for Playwright test synthesis, selector resolution,
evidence-derived assertion generation, and generated test validation.
"""


class SynthesisError(Exception):
    """Base exception for all test synthesis operations."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MissingReproductionPathError(SynthesisError):
    """Raised when a reproduction result lacks a causal reproduction path."""

    pass


class UnresolvedSelectorError(SynthesisError):
    """Raised when a stable selector cannot be deterministically resolved."""

    pass


class InvalidAssertionError(SynthesisError):
    """Raised when an assertion is malformed or lacks evidence grounding."""

    pass


class TestSerializationError(SynthesisError):
    """Raised when generated test model cannot be serialized into source code."""

    __test__ = False


class TestValidationError(SynthesisError):
    """Raised when a generated test fails structural or evidence validation."""

    __test__ = False


class SynthesisConfigError(SynthesisError):
    """Raised when synthesis configuration parameters are invalid."""

    pass
