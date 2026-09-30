"""RETRACE Benchmark Schema & Domain Models.

Provides formal data models for benchmark cases, separating public benchmark
inputs (provided to RETRACE) from private benchmark oracles (used exclusively
by the evaluation harness).
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.orchestration.models import ExecutionPolicy, ResourceBudget, VersionConfig


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(UTC)


class ExpectedOutcome(StrEnum):
    """Authoritative expected outcome for a benchmark case."""

    REGRESSION = "REGRESSION"
    NON_REGRESSION = "NON_REGRESSION"
    INCONCLUSIVE = "INCONCLUSIVE"


class BenchmarkCategory(StrEnum):
    """Semantic category of defect or variation."""

    FUNCTIONAL = "FUNCTIONAL"
    NAVIGATION = "NAVIGATION"
    API_CONTRACT = "API_CONTRACT"
    STATE = "STATE"
    CALCULATION = "CALCULATION"
    ACCESSIBILITY = "ACCESSIBILITY"
    PERFORMANCE = "PERFORMANCE"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    NON_REGRESSION = "NON_REGRESSION"
    UNKNOWN = "UNKNOWN"


class ExpectedSourceRegion(BaseModel):
    """Expected source code location for root cause validation."""

    model_config = ConfigDict(extra="forbid")

    file_path: str
    symbol_name: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    hunk_keywords: list[str] = Field(default_factory=list)


class BenchmarkInput(BaseModel):
    """Isolated input payload passed to the RETRACE investigation runner.

    CRITICAL: Contains NO ground truth, defect IDs, or expected answers.
    """

    model_config = ConfigDict(extra="forbid")

    project_id: str = "benchmark-project"
    analysis_id: UUID = Field(default_factory=uuid4)
    version_a: VersionConfig
    version_b: VersionConfig
    budget: ResourceBudget = Field(default_factory=ResourceBudget)
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkOracle(BaseModel):
    """Private benchmark ground-truth expectations.

    CRITICAL: Held exclusively by the evaluation harness.
    Must NEVER be provided to production worker runtime.
    """

    model_config = ConfigDict(extra="forbid")

    expected_outcome: ExpectedOutcome
    expected_category: BenchmarkCategory
    expected_severity: str = "MEDIUM"
    expected_behavior_a: str = ""
    expected_behavior_b: str = ""
    expected_reproducible: bool = True
    expected_source_regions: list[ExpectedSourceRegion] = Field(default_factory=list)
    expected_commits: list[str] = Field(default_factory=list)
    expected_test_synthesized: bool = True
    ground_truth_root_cause: str = ""
    canonical_reproduction_steps: list[str] = Field(default_factory=list)
    oracle_metadata: dict[str, Any] = Field(default_factory=dict)


class BenchmarkCase(BaseModel):
    """Formal definition of a reproducible benchmark case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    name: str
    description: str
    input_config: BenchmarkInput
    oracle: BenchmarkOracle
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class BenchmarkSuite(BaseModel):
    """Container holding a curated collection of benchmark cases."""

    model_config = ConfigDict(extra="forbid")

    suite_id: str
    name: str
    description: str
    cases: list[BenchmarkCase] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
