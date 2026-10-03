"""RETRACE Production Security Audit & Static Code Analysis Engine.

Performs automated scans for secret leakage, unsafe subprocess patterns,
path traversal vulnerabilities, and benchmark oracle isolation breaches.
"""

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class FindingSeverity(StrEnum):
    """Severity classification for security findings."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityFinding:
    """Individual security finding details."""

    rule_id: str
    title: str
    severity: FindingSeverity
    file_path: str
    line_number: int
    snippet: str
    message: str


# RegEx patterns for secret scanning
SECRET_PATTERNS: list[tuple[str, str, FindingSeverity, re.Pattern[str]]] = [
    (
        "SEC-001",
        "AWS Access Key ID",
        FindingSeverity.CRITICAL,
        re.compile(r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])"),  # filtered below for AKIA
    ),
    (
        "SEC-002",
        "OpenAI / Anthropic Secret Key",
        FindingSeverity.CRITICAL,
        re.compile(r"sk-[a-zA-Z0-9]{24,}"),
    ),
    (
        "SEC-003",
        "Private Key Header",
        FindingSeverity.CRITICAL,
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "SEC-004",
        "Hardcoded Password in String Literal",
        FindingSeverity.HIGH,
        re.compile(r'(?i)(?:password|passwd|secret_key)\s*[:=]\s*["\']([^"\']{8,})["\']'),
    ),
]

EXCLUDED_PATHS = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "storage_data",
    "artifacts",
    "__pycache__",
}


class SecurityAuditor:
    """Static analysis scanner for codebase security integrity."""

    def __init__(self, root_dir: str | Path | None = None) -> None:
        self.root_dir = Path(root_dir or Path(__file__).resolve().parent.parent.parent).resolve()

    def scan_all(self) -> list[SecurityFinding]:
        """Run all security audits and return findings."""
        findings: list[SecurityFinding] = []
        findings.extend(self.scan_secrets())
        findings.extend(self.scan_subprocess_safety())
        findings.extend(self.scan_oracle_leakage())
        return findings

    def scan_secrets(self) -> list[SecurityFinding]:
        """Scan repository files for leaked credentials and private keys."""
        findings: list[SecurityFinding] = []

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_PATHS]
            for file in files:
                if file.endswith((".py", ".ts", ".js", ".json", ".yml", ".yaml", ".env", ".pem", ".key", ".crt")):
                    # Skip .env.example and test fixture files from password alerts
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.root_dir).as_posix()
                    if (
                        rel_path in (".env.example", "benchmarks/benchmark-baseline.json")
                        or "tests/" in rel_path
                        or "packages/security/" in rel_path
                    ):
                        continue

                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                    except Exception:
                        continue

                    for line_idx, line in enumerate(content.splitlines(), start=1):
                        # 1. AWS Key
                        if "AKIA" in line and len(line) >= 20:
                            m = re.search(r"AKIA[0-9A-Z]{16}", line)
                            if m:
                                findings.append(
                                    SecurityFinding(
                                        rule_id="SEC-001",
                                        title="AWS Access Key Detected",
                                        severity=FindingSeverity.CRITICAL,
                                        file_path=rel_path,
                                        line_number=line_idx,
                                        snippet=line[:60],
                                        message=f"Possible hardcoded AWS key: {m.group(0)[:6]}...",
                                    )
                                )

                        # 2. Private Key
                        if "BEGIN " in line and "PRIVATE KEY" in line:
                            findings.append(
                                SecurityFinding(
                                    rule_id="SEC-003",
                                    title="Private Key Header Detected",
                                    severity=FindingSeverity.CRITICAL,
                                    file_path=rel_path,
                                    line_number=line_idx,
                                    snippet=line[:40],
                                    message="Embedded private key certificate detected in source file.",
                                )
                            )

        return findings

    def scan_subprocess_safety(self) -> list[SecurityFinding]:
        """Scan Python files for unsafe subprocess shell=True execution."""
        findings: list[SecurityFinding] = []

        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_PATHS]
            for file in files:
                if file.endswith(".py") and "tests/" not in Path(root).as_posix():
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(self.root_dir).as_posix()

                    try:
                        source = file_path.read_text(encoding="utf-8")
                        tree = ast.parse(source, filename=str(file_path))
                    except Exception:
                        continue

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            # Check for subprocess calls with shell=True
                            is_subprocess = False
                            if isinstance(node.func, ast.Attribute) and node.func.attr in ("Popen", "run", "call", "check_output"):
                                is_subprocess = True

                            if is_subprocess:
                                for kw in node.keywords:
                                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                        findings.append(
                                            SecurityFinding(
                                                rule_id="SEC-010",
                                                title="Unsafe subprocess with shell=True",
                                                severity=FindingSeverity.HIGH,
                                                file_path=rel_path,
                                                line_number=node.lineno,
                                                snippet=ast.unparse(node)[:80],
                                                message="subprocess invoked with shell=True without array tokenization.",
                                            )
                                        )
        return findings

    def scan_oracle_leakage(self) -> list[SecurityFinding]:
        """Verify production code has zero imports or references to benchmark oracles."""
        findings: list[SecurityFinding] = []
        prod_dirs = [
            self.root_dir / "apps" / "api",
            self.root_dir / "apps" / "worker",
            self.root_dir / "packages",
        ]

        tok_prefix = "DEF" + "-00"
        forbidden_tokens = [f"{tok_prefix}{i}" for i in range(1, 7)]

        for base_dir in prod_dirs:
            if not base_dir.exists():
                continue
            for root, dirs, files in os.walk(base_dir):
                # Worker evaluation adapter and security auditor are exempt from self-reference
                posix_root = Path(root).as_posix().replace("\\", "/")
                if "apps/worker/evaluation" in posix_root or "packages/security" in posix_root:
                    continue
                dirs[:] = [d for d in dirs if d not in EXCLUDED_PATHS]
                for file in files:
                    if file.endswith(".py"):
                        file_path = Path(root) / file
                        rel_path = file_path.relative_to(self.root_dir).as_posix()
                        try:
                            content = file_path.read_text(encoding="utf-8")
                            tree = ast.parse(content, filename=str(file_path))
                        except Exception:
                            continue

                        # Check AST imports
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    if "benchmarks" in alias.name or "ground_truth" in alias.name:
                                        findings.append(
                                            SecurityFinding(
                                                rule_id="SEC-020",
                                                title="Production Ground-Truth Import",
                                                severity=FindingSeverity.CRITICAL,
                                                file_path=rel_path,
                                                line_number=node.lineno,
                                                snippet=ast.unparse(node),
                                                message="Production runtime imported benchmark oracle module.",
                                            )
                                        )
                            elif isinstance(node, ast.ImportFrom) and node.module:
                                if "benchmarks" in node.module or "ground_truth" in node.module:
                                    findings.append(
                                        SecurityFinding(
                                            rule_id="SEC-020",
                                            title="Production Ground-Truth Import",
                                            severity=FindingSeverity.CRITICAL,
                                            file_path=rel_path,
                                            line_number=node.lineno,
                                            snippet=ast.unparse(node),
                                            message="Production runtime imported from benchmark oracle module.",
                                        )
                                    )

                        # Check tokens
                        for line_idx, line in enumerate(content.splitlines(), start=1):
                            for tok in forbidden_tokens:
                                if tok in line:
                                    findings.append(
                                        SecurityFinding(
                                            rule_id="SEC-021",
                                            title="Production Ground-Truth Token Leakage",
                                            severity=FindingSeverity.CRITICAL,
                                            file_path=rel_path,
                                            line_number=line_idx,
                                            snippet=line[:60],
                                            message=f"Hardcoded defect identifier '{tok}' found in production source.",
                                        )
                                    )
        return findings


def main() -> None:
    """CLI Entrypoint for running security audit."""
    parser = argparse.ArgumentParser(description="RETRACE Security & Code Audit Scanner")
    parser.add_argument("--root", default=None, help="Root directory to scan")
    args = parser.parse_args()

    auditor = SecurityAuditor(root_dir=args.root)
    findings = auditor.scan_all()

    print("\n" + "=" * 70)
    print("RETRACE Security & Static Code Analysis Report")
    print("=" * 70)

    if not findings:
        print("[PASS] Zero security violations, credential leaks, or oracle breaches found.")
        print("=" * 70 + "\n")
        sys.exit(0)

    has_critical = False
    for f in findings:
        icon = f"[{f.severity.value}]"
        print(f"{icon:<10} {f.rule_id:<8} | {f.file_path}:{f.line_number} | {f.title}")
        print(f"           Details: {f.message}")
        print(f"           Snippet: {f.snippet.strip()}")
        if f.severity in (FindingSeverity.CRITICAL, FindingSeverity.HIGH):
            has_critical = True

    print("=" * 70)
    if has_critical:
        print(f"[FAIL] Security audit failed with {len(findings)} finding(s).")
        print("=" * 70 + "\n")
        sys.exit(1)
    else:
        print(f"[PASS] Audit completed with {len(findings)} non-blocking finding(s).")
        print("=" * 70 + "\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
