"""Top-Level Root Cause Localization & Code/Commit Attribution Engine.

Coordinates Git repository inspection, unified diff normalization, multi-language AST parsing,
behavioral localization, and deterministic commit attribution.
"""

from pathlib import Path

from apps.worker.regression.models import RegressionClassification, RegressionClassificationResult
from apps.worker.reproduction.models import ReproductionResult, ReproductionSuiteResult
from apps.worker.rootcause.ast.models import ASTFileIndex
from apps.worker.rootcause.ast.parser import MultiLanguageASTParser
from apps.worker.rootcause.attribution.engine import AttributionEngine
from apps.worker.rootcause.config import RootCauseConfig
from apps.worker.rootcause.git.diff import DiffParser
from apps.worker.rootcause.git.repository import GitRepository
from apps.worker.rootcause.models import (
    FileDiff,
    RepositoryContext,
    RootCauseResult,
    RootCauseStatus,
    RootCauseSuiteResult,
    RootCauseSummary,
)


class RootCauseEngine:
    """Master engine for deterministic root-cause localization and code/commit attribution."""

    def __init__(
        self,
        config: RootCauseConfig | None = None,
        git_repo: GitRepository | None = None,
        attribution_engine: AttributionEngine | None = None,
    ):
        self.config = config or RootCauseConfig()
        self.git_repo = git_repo or GitRepository(config=self.config.git)
        self.attribution_engine = attribution_engine or AttributionEngine(
            config=self.config.attribution
        )

    def analyze(
        self,
        classification_result: RegressionClassificationResult,
        reproduction_suite_result: ReproductionSuiteResult | None = None,
        repository_context: RepositoryContext | None = None,
    ) -> RootCauseSuiteResult:
        """Execute comprehensive root-cause analysis for an entire suite of classified regressions."""
        repo_ctx = repository_context or RepositoryContext()

        # 1. Extract and normalize diffs
        diffs = self._extract_diffs(repo_ctx)

        # 2. Build AST indices for all target files
        ast_indices = self._build_ast_indices(repo_ctx, diffs)

        # 3. Map reproductions by classification_id
        repro_map: dict[str, ReproductionResult] = {}
        if reproduction_suite_result:
            for r in reproduction_suite_result.results:
                repro_map[r.classification_id] = r
                repro_map[r.difference_id] = r

        # 4. Attribute each classification
        results: list[RootCauseResult] = []
        for classification in classification_result.classifications:
            repro = repro_map.get(classification.classification_id) or repro_map.get(
                classification.difference_id
            )
            res = self.attribution_engine.attribute(
                classification=classification,
                reproduction=repro,
                diffs=diffs,
                ast_indices=ast_indices,
                repo_ctx=repo_ctx,
            )
            results.append(res)

        # 5. Sort results deterministically
        results.sort(key=lambda r: r.deterministic_sort_key())

        # 6. Compute summary
        summary = self._compute_summary(results)

        return RootCauseSuiteResult(
            run_a_id=classification_result.run_a_id,
            run_b_id=classification_result.run_b_id,
            results=results,
            summary=summary,
            metadata={
                "total_classifications": len(classification_result.classifications),
                "total_diff_files": len(diffs),
                "repository_context": repo_ctx.model_dump(mode="json"),
            },
        )

    def analyze_regression(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        repository_context: RepositoryContext | None = None,
    ) -> RootCauseResult:
        """Execute root-cause analysis for a single classified regression."""
        repo_ctx = repository_context or RepositoryContext()
        diffs = self._extract_diffs(repo_ctx)
        ast_indices = self._build_ast_indices(repo_ctx, diffs)

        return self.attribution_engine.attribute(
            classification=classification,
            reproduction=reproduction,
            diffs=diffs,
            ast_indices=ast_indices,
            repo_ctx=repo_ctx,
        )

    # --------------------------------------------------------------------------
    # Internal Extraction Helpers
    # --------------------------------------------------------------------------

    def _extract_diffs(self, repo_ctx: RepositoryContext) -> list[FileDiff]:
        """Extract normalized file diffs from Git repository or filesystem directories."""
        # 1. Dual directory comparison (e.g. Commerce Lab v1 vs v2)
        if repo_ctx.version_a_path and repo_ctx.version_b_path:
            p_a = Path(repo_ctx.version_a_path)
            p_b = Path(repo_ctx.version_b_path)
            if p_a.is_dir() and p_b.is_dir():
                return DiffParser.compare_directories(p_a, p_b)

        # 2. Git ref comparison
        if repo_ctx.is_git_repository and repo_ctx.repository_path and repo_ctx.baseline_ref and repo_ctx.target_ref:
            try:
                diff_text = self.git_repo.get_diff(
                    repo_path=repo_ctx.repository_path,
                    baseline_ref=repo_ctx.baseline_ref,
                    target_ref=repo_ctx.target_ref,
                )
                return DiffParser.parse_unified_diff(diff_text)
            except Exception:
                pass

        return []

    def _build_ast_indices(
        self, repo_ctx: RepositoryContext, diffs: list[FileDiff]
    ) -> dict[str, ASTFileIndex]:
        """Build AST symbol indices for all modified files."""
        indices: dict[str, ASTFileIndex] = {}

        for fd in diffs:
            p = fd.primary_path()
            content: str | None = None

            # Attempt loading content from version_b_path
            if repo_ctx.version_b_path:
                target_file = Path(repo_ctx.version_b_path) / p
                if target_file.is_file():
                    try:
                        content = target_file.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        pass

            # Attempt loading content from Git target_ref
            if content is None and repo_ctx.is_git_repository and repo_ctx.repository_path:
                try:
                    ref = repo_ctx.target_ref or "HEAD"
                    content = self.git_repo.get_file_at_ref(
                        repo_path=repo_ctx.repository_path,
                        ref=ref,
                        relative_path=p,
                    )
                except Exception:
                    pass

            if content is not None:
                indices[p] = MultiLanguageASTParser.parse_file_content(
                    file_path=p,
                    content=content,
                    language=fd.language,
                )
            else:
                # Fallback empty index
                indices[p] = ASTFileIndex(
                    file_path=p,
                    language=fd.language,
                    nodes=[],
                    is_valid=True,
                )

        return indices

    def _compute_summary(self, results: list[RootCauseResult]) -> RootCauseSummary:
        """Compute statistical summary counts."""
        located = 0
        partially = 0
        candidate = 0
        inconclusive = 0
        unsupported = 0

        for r in results:
            if r.status == RootCauseStatus.LOCATED:
                located += 1
            elif r.status == RootCauseStatus.PARTIALLY_LOCATED:
                partially += 1
            elif r.status == RootCauseStatus.CANDIDATE_ONLY:
                candidate += 1
            elif r.status == RootCauseStatus.INCONCLUSIVE:
                inconclusive += 1
            elif r.status == RootCauseStatus.UNSUPPORTED:
                unsupported += 1

        return RootCauseSummary(
            total_regressions_analyzed=len(results),
            located_count=located,
            partially_located_count=partially,
            candidate_only_count=candidate,
            inconclusive_count=inconclusive,
            unsupported_count=unsupported,
        )
