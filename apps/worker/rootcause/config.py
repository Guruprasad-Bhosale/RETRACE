"""Root Cause Localization Configuration and Policy Objects.

Provides strongly typed configuration settings for safe Git inspection,
AST parsing bounds, behavioral localization heuristics, and causal attribution limits.
"""

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.rootcause.models import LanguageType


class GitAnalysisConfig(BaseModel):
    """Configuration policies for safe Git repository inspection."""

    model_config = ConfigDict(extra="forbid")

    git_timeout_seconds: float = Field(default=30.0, ge=1.0)
    max_diff_lines: int = Field(default=20000, ge=100)
    max_commits_to_walk: int = Field(default=100, ge=1)
    max_file_size_bytes: int = Field(default=5 * 1024 * 1024, ge=1024)  # 5MB
    allowed_schemes: list[str] = Field(default_factory=lambda: ["file"])


class ASTAnalysisConfig(BaseModel):
    """Configuration policies for multi-language AST parsing."""

    model_config = ConfigDict(extra="forbid")

    supported_languages: list[LanguageType] = Field(
        default_factory=lambda: [
            LanguageType.PYTHON,
            LanguageType.JAVASCRIPT,
            LanguageType.TYPESCRIPT,
            LanguageType.HTML,
            LanguageType.CSS,
            LanguageType.JSON,
        ]
    )
    max_tokens_or_lines: int = Field(default=10000, ge=100)
    extract_call_sites: bool = True
    extract_route_decorators: bool = True


class LocalizationConfig(BaseModel):
    """Configuration policies for behavioral localization matching."""

    model_config = ConfigDict(extra="forbid")

    enable_symbol_matching: bool = True
    enable_route_matching: bool = True
    enable_state_key_matching: bool = True
    enable_api_contract_matching: bool = True
    enable_dom_attribute_matching: bool = True
    max_candidate_locations: int = Field(default=20, ge=1)


class AttributionConfig(BaseModel):
    """Configuration policies for causal attribution decision."""

    model_config = ConfigDict(extra="forbid")

    min_causal_evidence_count: int = Field(default=1, ge=1)
    strict_provenance: bool = True
    allow_partial_localization: bool = True


class RootCauseConfig(BaseModel):
    """Master configuration container for the Root Cause Localization Engine."""

    model_config = ConfigDict(extra="forbid")

    git: GitAnalysisConfig = Field(default_factory=GitAnalysisConfig)
    ast: ASTAnalysisConfig = Field(default_factory=ASTAnalysisConfig)
    localization: LocalizationConfig = Field(default_factory=LocalizationConfig)
    attribution: AttributionConfig = Field(default_factory=AttributionConfig)
