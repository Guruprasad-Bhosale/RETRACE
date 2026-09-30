"""Direct Symbol and Route Resolution Layer.

Resolves symbol definitions and route handlers matching behavioral evidence across analyzed files.
"""

from apps.worker.rootcause.ast.models import ASTFileIndex
from apps.worker.rootcause.models import ASTSymbol, SourceLocation


class SymbolResolver:
    """Deterministic symbol resolver across analyzed AST indices."""

    @classmethod
    def find_symbols_by_name(
        cls, name: str, indices: dict[str, ASTFileIndex]
    ) -> list[ASTSymbol]:
        """Find all symbols across files matching the given name."""
        results: list[ASTSymbol] = []
        for file_path, index in sorted(indices.items()):
            for node in index.nodes:
                if node.name == name or node.name.endswith(f".{name}"):
                    loc = SourceLocation(
                        file_path=file_path,
                        symbol_name=node.name,
                        symbol_kind=node.kind,
                        start_line=node.start_line,
                        start_column=node.start_column,
                        end_line=node.end_line,
                        end_column=node.end_column,
                        snippet=node.snippet,
                    )
                    results.append(
                        ASTSymbol(
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
                    )
        return results

    @classmethod
    def find_symbols_by_route(
        cls, route_path: str, indices: dict[str, ASTFileIndex]
    ) -> list[ASTSymbol]:
        """Find route handler symbols matching a specific URL route path."""
        norm_target = route_path.strip().rstrip("/").lower()
        results: list[ASTSymbol] = []

        for file_path, index in sorted(indices.items()):
            for node in index.nodes:
                if node.route_path:
                    norm_node = node.route_path.strip().rstrip("/").lower()
                    if norm_node == norm_target or norm_target.endswith(norm_node) or norm_node.endswith(norm_target):
                        loc = SourceLocation(
                            file_path=file_path,
                            symbol_name=node.name,
                            symbol_kind=node.kind,
                            start_line=node.start_line,
                            start_column=node.start_column,
                            end_line=node.end_line,
                            end_column=node.end_column,
                            snippet=node.snippet,
                        )
                        results.append(
                            ASTSymbol(
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
                        )
        return results
