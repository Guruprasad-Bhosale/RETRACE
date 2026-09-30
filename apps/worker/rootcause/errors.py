"""Root Cause Localization & Code/Commit Attribution Exception Hierarchy.

Provides distinct, strongly typed exceptions for Git operations, diff parsing,
AST analysis, behavioral localization, and causal attribution.
"""


class RootCauseError(Exception):
    """Base exception for all root-cause localization and attribution errors."""


class RepositoryAnalysisError(RootCauseError):
    """Raised when repository inspection or git analysis fails."""


class UnsafePathError(RepositoryAnalysisError):
    """Raised when a repository path or ref violates safety boundaries."""


class GitExecutionError(RepositoryAnalysisError):
    """Raised when a git command fails or times out."""


class DiffParsingError(RootCauseError):
    """Raised when a unified diff or patch cannot be parsed deterministically."""


class ASTParsingError(RootCauseError):
    """Raised when source code AST parsing fails."""


class UnsupportedLanguageError(ASTParsingError):
    """Raised when source file language is not supported for AST analysis."""


class LocalizationError(RootCauseError):
    """Raised when mapping behavioral evidence to source code regions fails."""


class AttributionError(RootCauseError):
    """Raised when constructing causal attribution or commit linkage fails."""


class ProvenanceError(RootCauseError):
    """Raised when provenance linkage is incomplete or corrupted."""
