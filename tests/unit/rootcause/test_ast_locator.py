"""Unit tests for AST symbol locator and hunk-to-symbol mapping."""

from apps.worker.rootcause.ast.locator import ASTSymbolLocator
from apps.worker.rootcause.ast.parser import MultiLanguageASTParser
from apps.worker.rootcause.models import (
    ASTNodeType,
    DiffHunk,
    DiffLine,
    LanguageType,
    LineChangeType,
)

SOURCE = """
def first_func():
    return 1

def target_func(x: int):
    # Line 6
    val = x * 2
    return val

def third_func():
    return 3
"""


def test_ast_symbol_locator_enclosing_line():
    """Verify finding the innermost symbol enclosing a specific line number."""
    index = MultiLanguageASTParser.parse_file_content("example.py", SOURCE, LanguageType.PYTHON)
    sym = ASTSymbolLocator.locate_symbol_for_line(index, line_number=7)

    assert sym is not None
    assert sym.name == "target_func"
    assert sym.kind == ASTNodeType.FUNCTION
    assert sym.location.start_line == 5
    assert sym.location.end_line == 8


def test_ast_symbol_locator_diff_hunk():
    """Verify locating symbols modified by a diff hunk."""
    index = MultiLanguageASTParser.parse_file_content("example.py", SOURCE, LanguageType.PYTHON)
    hunk = DiffHunk(
        old_start=6,
        old_lines=2,
        new_start=6,
        new_lines=3,
        lines=[
            DiffLine(change_type=LineChangeType.LINE_ADDED, content="    val = x * 3", new_line_number=7)
        ],
        added_lines=[7],
    )

    symbols = ASTSymbolLocator.locate_symbols_for_hunk(index, hunk)
    assert len(symbols) == 1
    assert symbols[0].name == "target_func"
