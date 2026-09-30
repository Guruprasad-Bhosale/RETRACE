"""AST Domain Models and Indexed Structural Representations.

Defines fine-grained AST node structures and symbol index tables for multi-language source code.
"""

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.rootcause.models import ASTNodeType, LanguageType, SourceLocation


class ASTNodeInfo(BaseModel):
    """Normalized representation of a parsed AST node."""

    model_config = ConfigDict(extra="forbid")

    name: str
    kind: ASTNodeType
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    start_column: int = 0
    end_column: int = 0
    parent_name: str | None = None
    parameters: list[str] = Field(default_factory=list)
    docstring: str | None = None
    route_path: str | None = None
    http_methods: list[str] = Field(default_factory=list)
    state_keys: list[str] = Field(default_factory=list)
    snippet: str | None = None

    def to_source_location(self, file_path: str, repo_path: str = "") -> SourceLocation:
        """Convert ASTNodeInfo to a canonical SourceLocation."""
        return SourceLocation(
            repository_path=repo_path,
            file_path=file_path,
            symbol_name=self.name,
            symbol_kind=self.kind,
            start_line=self.start_line,
            start_column=self.start_column,
            end_line=self.end_line,
            end_column=self.end_column,
            snippet=self.snippet,
        )


class ASTFileIndex(BaseModel):
    """Symbol index table for a single parsed source file."""

    model_config = ConfigDict(extra="forbid")

    file_path: str
    language: LanguageType
    nodes: list[ASTNodeInfo] = Field(default_factory=list)
    is_valid: bool = True
    error_message: str | None = None

    def find_enclosing_node(self, line: int) -> ASTNodeInfo | None:
        """Find the innermost AST node enclosing the specified line."""
        matching = [
            node for node in self.nodes
            if node.start_line <= line <= node.end_line
        ]
        if not matching:
            return None
        # Return the most specific (innermost = smallest line span)
        matching.sort(key=lambda n: (n.end_line - n.start_line, n.start_line))
        return matching[0]

    def find_nodes_in_range(self, start_line: int, end_line: int) -> list[ASTNodeInfo]:
        """Find all AST nodes that intersect with the specified line range."""
        return [
            node for node in self.nodes
            if not (node.end_line < start_line or node.start_line > end_line)
        ]

    def find_by_name(self, name: str) -> list[ASTNodeInfo]:
        """Find nodes matching a symbol name."""
        return [node for node in self.nodes if node.name == name]

    def find_by_route(self, route_path: str) -> list[ASTNodeInfo]:
        """Find route handler nodes matching a route path."""
        norm = route_path.strip().rstrip("/")
        return [
            node for node in self.nodes
            if node.route_path and node.route_path.strip().rstrip("/") == norm
        ]
