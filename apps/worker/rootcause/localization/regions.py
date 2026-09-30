"""Source Region Matching and Location Normalization Layer.

Translates diff hunks and modified line ranges into canonical SourceLocation entities.
"""

from apps.worker.rootcause.ast.locator import ASTSymbolLocator
from apps.worker.rootcause.ast.models import ASTFileIndex
from apps.worker.rootcause.models import ASTSymbol, DiffHunk, FileDiff, SourceLocation


class SourceRegionMatcher:
    """Deterministic matcher from file diffs to canonical source locations."""

    @classmethod
    def match_hunk_locations(
        cls,
        file_diff: FileDiff,
        file_index: ASTFileIndex | None = None,
        repo_path: str = "",
    ) -> list[tuple[SourceLocation, ASTSymbol | None, DiffHunk]]:
        """Extract canonical SourceLocations and associated AST symbols for all hunks in a FileDiff."""
        results: list[tuple[SourceLocation, ASTSymbol | None, DiffHunk]] = []
        path = file_diff.primary_path()

        for hunk in file_diff.hunks:
            start_ln = hunk.new_start if hunk.new_start > 0 else hunk.old_start
            count = hunk.new_lines if hunk.new_lines > 0 else hunk.old_lines
            end_ln = max(start_ln, start_ln + count - 1)

            symbol: ASTSymbol | None = None
            if file_index and file_index.is_valid:
                symbol = ASTSymbolLocator.locate_symbol_for_line(
                    file_index=file_index,
                    line_number=start_ln,
                    repo_path=repo_path,
                )

            snippet_lines = [dl.content for dl in hunk.lines if dl.content]
            snippet_str = "\n".join(snippet_lines[:5]) if snippet_lines else None

            loc = SourceLocation(
                repository_path=repo_path,
                file_path=path,
                symbol_name=symbol.name if symbol else None,
                symbol_kind=symbol.kind if symbol else None,
                start_line=max(1, start_ln),
                start_column=0,
                end_line=max(1, end_ln),
                end_column=0,
                snippet=snippet_str,
            )
            results.append((loc, symbol, hunk))

        return results
