"""Tests for SecurityScanner."""

from pathlib import Path

from agentic_pipeline.nodes.validator import (
    SecurityScanner,
    ValidationLevel,
)


class TestSecurityScanner:
    def test_ok_on_clean_dir(self, tmp_path: Path):
        (tmp_path / "safe.txt").write_text("hello world\n")
        scanner = SecurityScanner()
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.PASS

    def test_detects_hardcoded_password(self, tmp_path: Path):
        (tmp_path / "config.js").write_text('const password = "supersecret";\n')
        scanner = SecurityScanner()
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.ERROR
        assert len(result.details) >= 1

    def test_detects_api_key(self, tmp_path: Path):
        (tmp_path / ".env").write_text('API_KEY = "sk-12345678901234567890"\n')
        scanner = SecurityScanner()
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.ERROR

    def test_detects_private_key(self, tmp_path: Path):
        (tmp_path / "key.pem").write_text("-----BEGIN PRIVATE KEY-----\nABCDEF\n")
        scanner = SecurityScanner()
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.ERROR

    def test_skips_binary_files(self, tmp_path: Path):
        (tmp_path / "image.bin").write_bytes(b"\x00\x01\x02\xff")
        scanner = SecurityScanner()
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.PASS

    def test_detects_aws_key(self, tmp_path: Path):
        (tmp_path / "config").write_text("aws_key = AKIA1234567890123456\n")
        scanner = SecurityScanner()
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.ERROR

    def test_scan_subdirectories(self, tmp_path: Path):
        sub = tmp_path / "src"
        sub.mkdir()
        (sub / "secret.txt").write_text('token = "ghp_abcdefghijklmnop"\n')
        scanner = SecurityScanner()
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.ERROR

    def test_custom_patterns(self, tmp_path: Path):
        (tmp_path / "db.py").write_text("host = localhost\n")
        scanner = SecurityScanner(patterns=[("localhost", "Hardcoded host")])
        result = scanner.validate(tmp_path)
        assert result.level == ValidationLevel.ERROR
        assert "Hardcoded host" in result.details[0]

    def test_set_next_chain(self, tmp_path: Path):
        v1 = SecurityScanner()
        v2 = SecurityScanner()
        v1.set_next(v2)
        result = v1.check(tmp_path)
        assert result.level == ValidationLevel.PASS
