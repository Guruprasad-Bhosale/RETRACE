"""AST Symbol Locator and Source Region Mapper.

Maps diff hunks, changed lines, and behavioral subjects to exact enclosing AST symbols.
"""

from apps.worker.rootcause.ast.models import ASTFileIndex, ASTNodeInfo
from apps.worker.rootcause.models import ASTSymbol, DiffHunk, SourceLocation


class ASTSymbolLocator:
    """Deterministic locator matching line spans to enclosing AST symbols."""

    @classmethod
    def locate_symbol_for_line(
        cls,
        file_index: ASTFileIndex,
        line_number: int,
        repo_path: str = "",
    ) -> ASTSymbol | None:
        """Find the innermost AST symbol enclosing a specific line number."""
        node = file_index.find_enclosing_node(line_number)
        if not node:
            return None
        return cls._node_to_symbol(node, file_index.file_path, repo_path)

    @classmethod
    def locate_symbols_for_hunk(
        cls,
        file_index: ASTFileIndex,
        hunk: DiffHunk,
        repo_path: str = "",
    ) -> list[ASTSymbol]:
        """Find all AST symbols modified or enclosed within a DiffHunk."""
        start_ln = hunk.new_start if hunk.new_start > 0 else hunk.old_start
        count = hunk.new_lines if hunk.new_lines > 0 else hunk.old_lines
        end_ln = max(start_ln, start_ln + count - 1)

        nodes = file_index.find_nodes_in_range(start_ln, end_ln)
        if not nodes:
            # Check if there is an outer enclosing node
            enclosing = file_index.find_enclosing_node(start_ln)
            if enclosing:
                nodes = [enclosing]

        # Convert to unique ASTSymbols
        symbols: list[ASTSymbol] = []
        seen = set()
        for n in nodes:
            sym = cls._node_to_symbol(n, file_index.file_path, repo_path)
            key = (sym.name, sym.location.start_line, sym.location.end_line)
            if key not in seen:
                seen.add(key)
                symbols.append(sym)
        return symbols

    @classmethod
    def _node_to_symbol(
        cls, node: ASTNodeInfo, file_path: str, repo_path: str = ""
    ) -> ASTSymbol:
        """Convert ASTNodeInfo to domain ASTSymbol."""
        loc = SourceLocation(
            repository_path=repo_path,
            file_path=file_path,
            symbol_name=node.name,
            symbol_kind=node.kind,
            start_line=node.start_line,
            start_column=node.start_column,
            end_line=node.end_line,
            end_column=node.end_column,
            snippet=node.snippet,
        )
        return ASTSymbol(
            name=node.name,
            kind=node.kind,
            location=loc,
            parent_symbol=node.parent_name,
            parameters=node.parameters,
            docstring=node.docstring,
            route_path=node.route_path,
            http_methods=node.http_methods,
            state_keys=node.state_keys,
        )
