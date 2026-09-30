"""RETRACE Regression Classification Engine Package.

Provides deterministic, evidence-backed regression candidate classification
across Version A and Version B semantic differences.
"""

from apps.worker.regression.classifier import RegressionClassifier
from apps.worker.regression.config import (
    AccessibilityPolicy,
    ClassificationPolicy,
    PerformancePolicy,
    RegressionConfig,
    RuntimeErrorPolicy,
)
from apps.worker.regression.diagnostics import RegressionDiagnosticsFormatter
from apps.worker.regression.errors import (
    ClassificationConfigurationError,
    InvalidSemanticDiffError,
    RegressionEngineError,
    UnsupportedDifferenceError,
)
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    ClassificationSummary,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)

__all__ = [
    "AccessibilityPolicy",
    "ClassificationConfigurationError",
    "ClassificationEvidence",
    "ClassificationPolicy",
    "ClassificationStatus",
    "ClassificationSummary",
    "InvalidSemanticDiffError",
    "PerformancePolicy",
    "RegressionCategory",
    "RegressionClassification",
    "RegressionClassificationResult",
    "RegressionClassifier",
    "RegressionConfig",
    "RegressionDiagnosticsFormatter",
    "RegressionEngineError",
    "RuntimeErrorPolicy",
    "UnsupportedDifferenceError",
]
