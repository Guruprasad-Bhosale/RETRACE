"""Evidence Reporting Configuration and Formatting Policies."""

from pydantic import BaseModel, ConfigDict, Field


class ReportingConfig(BaseModel):
    """Configuration options for evidence investigation report generation."""

    model_config = ConfigDict(extra="forbid")

    include_full_diff_hunks: bool = True
    max_diff_lines_per_hunk: int = Field(default=50, ge=5, le=500)
    include_generated_test_code: bool = True
    include_full_evidence_chain: bool = True
    canonicalize_newlines: bool = True
    include_reproduction_step_table: bool = True
