"""Unit tests for the SecurityAuditor static scanner."""

import tempfile
from pathlib import Path

from packages.security.audit import FindingSeverity, SecurityAuditor


def test_security_auditor_detects_aws_key():
    """Verify scanner detects embedded AWS access keys."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "leaked_secret.py"
        test_file.write_text("AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'", encoding="utf-8")

        auditor = SecurityAuditor(root_dir=tmp_dir)
        findings = auditor.scan_secrets()

        assert len(findings) >= 1
        assert findings[0].rule_id == "SEC-001"
        assert findings[0].severity == FindingSeverity.CRITICAL


def test_security_auditor_detects_private_key():
    """Verify scanner detects embedded private keys."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "cert.pem"
        test_file.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...", encoding="utf-8")

        auditor = SecurityAuditor(root_dir=tmp_dir)
        findings = auditor.scan_secrets()

        assert len(findings) >= 1
        assert findings[0].rule_id == "SEC-003"


def test_security_auditor_detects_unsafe_subprocess():
    """Verify scanner detects unsafe subprocess with shell=True."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "runner.py"
        test_file.write_text("import subprocess\nsubprocess.run('ls ' + user_input, shell=True)\n", encoding="utf-8")

        auditor = SecurityAuditor(root_dir=tmp_dir)
        findings = auditor.scan_subprocess_safety()

        assert len(findings) >= 1
        assert findings[0].rule_id == "SEC-010"
        assert findings[0].severity == FindingSeverity.HIGH
