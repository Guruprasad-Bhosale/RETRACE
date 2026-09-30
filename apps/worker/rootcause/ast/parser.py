"""Multi-Language Source Parser (Python AST, JS/TS Structural Block, HTML Structural Tree).

Provides deterministic, error-tolerant AST parsing for Python, lexical/structural block indexing
for JavaScript/TypeScript, and structural element tree indexing for HTML/CSS without external daemons.
"""

import ast
import re
from html.parser import HTMLParser

from apps.worker.rootcause.ast.models import ASTFileIndex, ASTNodeInfo
from apps.worker.rootcause.git.diff import DiffParser
from apps.worker.rootcause.models import ASTNodeType, LanguageType


class MultiLanguageASTParser:
    """Deterministic, resilient multi-language source structure parser."""

    @classmethod
    def parse_file_content(
        cls, file_path: str, content: str, language: LanguageType | None = None
    ) -> ASTFileIndex:
        """Parse source code string into a structured ASTFileIndex."""
        lang = language or DiffParser.detect_language(file_path)

        if lang == LanguageType.PYTHON:
            return cls._parse_python_ast(file_path, content)
        elif lang in (LanguageType.JAVASCRIPT, LanguageType.TYPESCRIPT):
            return cls._parse_javascript_structural_blocks(file_path, content, lang)
        elif lang == LanguageType.HTML:
            return cls._parse_html_structural_elements(file_path, content)
        elif lang == LanguageType.CSS:
            return cls._parse_css(file_path, content)
        elif lang == LanguageType.JSON:
            return cls._parse_json(file_path, content)
        else:
            return ASTFileIndex(
                file_path=file_path,
                language=LanguageType.UNSUPPORTED_LANGUAGE,
                nodes=[],
                is_valid=True,
            )

    # --------------------------------------------------------------------------
    # Python AST Parser (Standard Library ast)
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_python_ast(cls, file_path: str, content: str) -> ASTFileIndex:
        """Parse Python source code using standard library ast module."""
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError as exc:
            return ASTFileIndex(
                file_path=file_path,
                language=LanguageType.PYTHON,
                nodes=[],
                is_valid=False,
                error_message=f"Python syntax error at line {exc.lineno}: {exc.msg}",
            )
        except Exception as exc:
            return ASTFileIndex(
                file_path=file_path,
                language=LanguageType.PYTHON,
                nodes=[],
                is_valid=False,
                error_message=f"Failed to parse Python AST: {exc}",
            )

        nodes: list[ASTNodeInfo] = []
        lines = content.splitlines()

        class PythonVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_class: str | None = None

            def _get_snippet(self, start_line: int, end_line: int) -> str:
                s_idx = max(0, start_line - 1)
                e_idx = min(len(lines), end_line)
                return "\n".join(lines[s_idx:e_idx])

            def visit_ClassDef(self, node: ast.ClassDef):
                prev_class = self.current_class
                self.current_class = node.name

                end_ln = getattr(node, "end_lineno", node.lineno)
                nodes.append(
                    ASTNodeInfo(
                        name=node.name,
                        kind=ASTNodeType.CLASS,
                        start_line=node.lineno,
                        end_line=end_ln,
                        start_column=node.col_offset,
                        end_column=getattr(node, "end_col_offset", 0),
                        parent_name=prev_class,
                        parameters=[b.id for b in node.bases if isinstance(b, ast.Name)],
                        docstring=ast.get_docstring(node),
                        snippet=self._get_snippet(node.lineno, min(node.lineno + 3, end_ln)),
                    )
                )
                self.generic_visit(node)
                self.current_class = prev_class

            def _extract_route_info(self, decorator_list: list[ast.expr]) -> tuple[str | None, list[str]]:
                route_path: str | None = None
                http_methods: list[str] = []
                for dec in decorator_list:
                    if isinstance(dec, ast.Call):
                        func = dec.func
                        # Pattern: @app.get("/path") or @router.post("/path")
                        if isinstance(func, ast.Attribute):
                            method_name = func.attr.upper()
                            if method_name in ("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"):
                                http_methods.append(method_name)
                                if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                                    route_path = dec.args[0].value
                return route_path, http_methods

            def visit_FunctionDef(self, node: ast.FunctionDef):
                self._handle_function(node, is_async=False)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self._handle_function(node, is_async=True)

            def _handle_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool):
                end_ln = getattr(node, "end_lineno", node.lineno)
                params = [a.arg for a in node.args.args]
                route_path, http_methods = self._extract_route_info(node.decorator_list)

                kind = ASTNodeType.METHOD if self.current_class else ASTNodeType.FUNCTION
                if route_path or http_methods:
                    kind = ASTNodeType.ROUTE_HANDLER

                # Check for calculations or state mutations inside body
                state_keys: list[str] = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Subscript) and isinstance(child.slice, ast.Constant):
                        if isinstance(child.slice.value, str):
                            state_keys.append(child.slice.value)

                nodes.append(
                    ASTNodeInfo(
                        name=node.name,
                        kind=kind,
                        start_line=node.lineno,
                        end_line=end_ln,
                        start_column=node.col_offset,
                        end_column=getattr(node, "end_col_offset", 0),
                        parent_name=self.current_class,
                        parameters=params,
                        docstring=ast.get_docstring(node),
                        route_path=route_path,
                        http_methods=http_methods,
                        state_keys=list(set(state_keys)),
                        snippet=self._get_snippet(node.lineno, min(node.lineno + 3, end_ln)),
                    )
                )
                self.generic_visit(node)

        visitor = PythonVisitor()
        visitor.visit(tree)

        # Sort deterministically by line number
        nodes.sort(key=lambda n: (n.start_line, n.end_line, n.name))

        return ASTFileIndex(
            file_path=file_path,
            language=LanguageType.PYTHON,
            nodes=nodes,
            is_valid=True,
        )

    # --------------------------------------------------------------------------
    # JavaScript / TypeScript Structural Block Parser
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_javascript_structural_blocks(
        cls, file_path: str, content: str, language: LanguageType
    ) -> ASTFileIndex:
        """Parse JavaScript/TypeScript using regex-based structural block and symbol extraction."""
        nodes: list[ASTNodeInfo] = []
        lines = content.splitlines()

        def get_snippet(s_line: int, e_line: int) -> str:
            s_idx = max(0, s_line - 1)
            e_idx = min(len(lines), e_line)
            return "\n".join(lines[s_idx:e_idx])

        # Regex patterns for JS/TS structures
        fn_decl_re = re.compile(r"^\s*(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(([^)]*)\)")
        arrow_fn_re = re.compile(
            r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s+)?(?:\(([^)]*)\)|[a-zA-Z0-9_$]+)\s*=>"
        )
        method_re = re.compile(r"^\s*(?:async\s+)?([a-zA-Z0-9_$]+)\s*\(([^)]*)\)\s*\{")
        class_re = re.compile(r"^\s*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$]+))?")
        route_re = re.compile(r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]")
        fetch_re = re.compile(r"fetch\s*\(\s*['\"`]([^'\"`]+)['\"`]")
        storage_re = re.compile(r"(?:localStorage|sessionStorage)\.(?:setItem|getItem|removeItem)\s*\(\s*['\"]([^'\"]+)['\"]")

        # Track bracket depth to estimate end line
        total_lines = len(lines)
        for idx, line in enumerate(lines):
            line_num = idx + 1
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*"):
                continue

            # Class match
            c_match = class_re.match(line)
            if c_match:
                cls_name = c_match.group(1)
                nodes.append(
                    ASTNodeInfo(
                        name=cls_name,
                        kind=ASTNodeType.CLASS,
                        start_line=line_num,
                        end_line=min(total_lines, line_num + 20),
                        snippet=get_snippet(line_num, min(total_lines, line_num + 2)),
                    )
                )
                continue

            # Function declaration
            fn_match = fn_decl_re.match(line)
            if fn_match:
                fn_name = fn_match.group(1)
                params = [p.strip() for p in fn_match.group(2).split(",") if p.strip()]
                # Find matching close brace or estimate
                end_ln = cls._find_matching_brace_end(lines, idx)
                nodes.append(
                    ASTNodeInfo(
                        name=fn_name,
                        kind=ASTNodeType.FUNCTION,
                        start_line=line_num,
                        end_line=end_ln,
                        parameters=params,
                        snippet=get_snippet(line_num, min(total_lines, line_num + 2)),
                    )
                )
                continue

            # Arrow function assignment
            arrow_match = arrow_fn_re.match(line)
            if arrow_match:
                fn_name = arrow_match.group(1)
                raw_params = arrow_match.group(2) or ""
                params = [p.strip() for p in raw_params.split(",") if p.strip()]
                end_ln = cls._find_matching_brace_end(lines, idx)
                nodes.append(
                    ASTNodeInfo(
                        name=fn_name,
                        kind=ASTNodeType.FUNCTION,
                        start_line=line_num,
                        end_line=end_ln,
                        parameters=params,
                        snippet=get_snippet(line_num, min(total_lines, line_num + 2)),
                    )
                )
                continue

            # Method match
            m_match = method_re.match(line)
            if m_match and not m_match.group(1).startswith("if") and not m_match.group(1).startswith("for") and not m_match.group(1).startswith("while") and not m_match.group(1).startswith("switch"):
                m_name = m_match.group(1)
                params = [p.strip() for p in m_match.group(2).split(",") if p.strip()]
                end_ln = cls._find_matching_brace_end(lines, idx)
                nodes.append(
                    ASTNodeInfo(
                        name=m_name,
                        kind=ASTNodeType.METHOD,
                        start_line=line_num,
                        end_line=end_ln,
                        parameters=params,
                        snippet=get_snippet(line_num, min(total_lines, line_num + 2)),
                    )
                )
                continue

            # Route handlers
            r_match = route_re.search(line)
            if r_match:
                http_m = r_match.group(1).upper()
                r_path = r_match.group(2)
                end_ln = cls._find_matching_brace_end(lines, idx)
                nodes.append(
                    ASTNodeInfo(
                        name=f"{http_m} {r_path}",
                        kind=ASTNodeType.ROUTE_HANDLER,
                        start_line=line_num,
                        end_line=end_ln,
                        route_path=r_path,
                        http_methods=[http_m],
                        snippet=get_snippet(line_num, min(total_lines, line_num + 2)),
                    )
                )
                continue

            # API calls
            f_match = fetch_re.search(line)
            if f_match:
                ep = f_match.group(1)
                nodes.append(
                    ASTNodeInfo(
                        name=f"fetch({ep})",
                        kind=ASTNodeType.API_CALL,
                        start_line=line_num,
                        end_line=line_num,
                        route_path=ep,
                        snippet=line.strip(),
                    )
                )

            # Storage state keys
            st_match = storage_re.search(line)
            if st_match:
                st_key = st_match.group(1)
                nodes.append(
                    ASTNodeInfo(
                        name=f"storage:{st_key}",
                        kind=ASTNodeType.STATE_MUTATION,
                        start_line=line_num,
                        end_line=line_num,
                        state_keys=[st_key],
                        snippet=line.strip(),
                    )
                )

        nodes.sort(key=lambda n: (n.start_line, n.end_line, n.name))
        return ASTFileIndex(
            file_path=file_path,
            language=language,
            nodes=nodes,
            is_valid=True,
        )

    @classmethod
    def _find_matching_brace_end(cls, lines: list[str], start_idx: int) -> int:
        """Find ending line of a block by counting curly braces."""
        brace_count = 0
        found_first = False
        total = len(lines)

        for i in range(start_idx, total):
            line = lines[i]
            for ch in line:
                if ch == "{":
                    brace_count += 1
                    found_first = True
                elif ch == "}":
                    brace_count -= 1
                    if found_first and brace_count <= 0:
                        return i + 1
        return min(total, start_idx + 10)

    # --------------------------------------------------------------------------
    # HTML Structural Element Tree Parser
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_html_structural_elements(cls, file_path: str, content: str) -> ASTFileIndex:
        """Parse HTML source code extracting structural element tags and accessibility attributes."""
        nodes: list[ASTNodeInfo] = []
        lines = content.splitlines()

        class StructuredHTMLParser(HTMLParser):
            def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
                ln, col = self.getpos()
                attr_dict = {k.lower(): v for k, v in attrs}
                elem_id = attr_dict.get("id")
                elem_name = attr_dict.get("name")
                aria_labels = [k for k in attr_dict if k.startswith("aria-")]
                route_path: str | None = None

                if tag == "a" and "href" in attr_dict:
                    route_path = attr_dict.get("href")
                elif tag == "form" and "action" in attr_dict:
                    route_path = attr_dict.get("action")

                name_repr = f"<{tag}"
                if elem_id:
                    name_repr += f" id='{elem_id}'"
                elif elem_name:
                    name_repr += f" name='{elem_name}'"
                name_repr += ">"

                kind = ASTNodeType.DOM_BINDING
                if route_path:
                    kind = ASTNodeType.ROUTE_HANDLER

                state_keys: list[str] = []
                if elem_id:
                    state_keys.append(elem_id)
                if elem_name:
                    state_keys.append(elem_name)
                state_keys.extend(aria_labels)

                snippet = lines[ln - 1].strip() if 0 < ln <= len(lines) else ""

                nodes.append(
                    ASTNodeInfo(
                        name=name_repr,
                        kind=kind,
                        start_line=ln,
                        end_line=ln,
                        start_column=col,
                        route_path=route_path,
                        state_keys=state_keys,
                        snippet=snippet,
                    )
                )

        try:
            parser = StructuredHTMLParser()
            parser.feed(content)
        except Exception as exc:
            return ASTFileIndex(
                file_path=file_path,
                language=LanguageType.HTML,
                nodes=nodes,
                is_valid=False,
                error_message=str(exc),
            )

        nodes.sort(key=lambda n: (n.start_line, n.end_line, n.name))
        return ASTFileIndex(
            file_path=file_path,
            language=LanguageType.HTML,
            nodes=nodes,
            is_valid=True,
        )

    # --------------------------------------------------------------------------
    # CSS & JSON Parsers
    # --------------------------------------------------------------------------

    @classmethod
    def _parse_css(cls, file_path: str, content: str) -> ASTFileIndex:
        """Parse CSS stylesheet selectors and rule blocks."""
        nodes: list[ASTNodeInfo] = []
        rule_re = re.compile(r"([^{]+)\{")
        lines = content.splitlines()

        for idx, line in enumerate(lines):
            line_num = idx + 1
            m = rule_re.search(line)
            if m:
                selector = m.group(1).strip()
                if selector:
                    end_ln = cls._find_matching_brace_end(lines, idx)
                    nodes.append(
                        ASTNodeInfo(
                            name=selector,
                            kind=ASTNodeType.DOM_BINDING,
                            start_line=line_num,
                            end_line=end_ln,
                            snippet=line.strip(),
                        )
                    )

        nodes.sort(key=lambda n: (n.start_line, n.end_line, n.name))
        return ASTFileIndex(
            file_path=file_path,
            language=LanguageType.CSS,
            nodes=nodes,
            is_valid=True,
        )

    @classmethod
    def _parse_json(cls, file_path: str, content: str) -> ASTFileIndex:
        """Parse JSON keys and configurations."""
        nodes: list[ASTNodeInfo] = []
        key_re = re.compile(r'^\s*"([^"]+)"\s*:\s*(.*)$')
        lines = content.splitlines()

        for idx, line in enumerate(lines):
            line_num = idx + 1
            m = key_re.match(line)
            if m:
                k = m.group(1)
                nodes.append(
                    ASTNodeInfo(
                        name=f"json:{k}",
                        kind=ASTNodeType.CONFIGURATION,
                        start_line=line_num,
                        end_line=line_num,
                        state_keys=[k],
                        snippet=line.strip(),
                    )
                )

        nodes.sort(key=lambda n: (n.start_line, n.end_line, n.name))
        return ASTFileIndex(
            file_path=file_path,
            language=LanguageType.JSON,
            nodes=nodes,
            is_valid=True,
        )
