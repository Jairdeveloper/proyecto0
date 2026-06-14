"""Tests for SyntaxValidator."""

from pathlib import Path

from agentic_pipeline.nodes.validator import SyntaxValidator, ValidationLevel


class TestSyntaxValidator:
    def test_ok_on_valid_file(self, tmp_path: Path):
        (tmp_path / "valid.js").write_text("const x = 1;\n")
        validator = SyntaxValidator()
        result = validator.validate(tmp_path)
        assert result.level in (ValidationLevel.PASS, ValidationLevel.WARNING)

    def test_does_not_crash_on_empty_dir(self, tmp_path: Path):
        validator = SyntaxValidator()
        result = validator.validate(tmp_path)
        assert result.level in (
            ValidationLevel.PASS,
            ValidationLevel.WARNING,
            ValidationLevel.ERROR,
        )

    def test_set_next_returns_validator(self):
        v1 = SyntaxValidator()
        v2 = SyntaxValidator()
        returned = v1.set_next(v2)
        assert returned is v2

    def test_chain_passes_on_valid(self, tmp_path: Path):
        v1 = SyntaxValidator()
        v2 = SyntaxValidator()
        v1.set_next(v2)
        (tmp_path / "a.js").write_text("const x = 1;\n")
        result = v1.check(tmp_path)
        assert result.level in (ValidationLevel.PASS, ValidationLevel.WARNING)

    def test_chain_stops_on_syntax_error(self, tmp_path: Path):
        class FailValidator(SyntaxValidator):
            def validate(self, output_dir: Path) -> object:
                from agentic_pipeline.nodes.validator import ValidationResult

                return ValidationResult(ValidationLevel.ERROR, "syntax error")

        v1 = FailValidator()
        v2 = SyntaxValidator()
        v1.set_next(v2)
        result = v1.check(tmp_path)
        assert result.level == ValidationLevel.ERROR
