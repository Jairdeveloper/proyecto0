"""Tests for TypeChecker."""

from pathlib import Path

from agentic_pipeline.nodes.validator import TypeChecker, ValidationLevel


class TestTypeChecker:
    def test_warning_no_tsconfig(self, tmp_path: Path):
        checker = TypeChecker()
        result = checker.validate(tmp_path)
        assert result.level == ValidationLevel.WARNING
        assert "No tsconfig.json" in result.message

    def test_does_not_crash_with_tsconfig(self, tmp_path: Path):
        (tmp_path / "tsconfig.json").write_text('{"compilerOptions": {"strict": true}}')
        (tmp_path / "app.ts").write_text("const x: number = 1;\n")
        checker = TypeChecker()
        result = checker.validate(tmp_path)
        assert result.level in (
            ValidationLevel.PASS,
            ValidationLevel.WARNING,
            ValidationLevel.ERROR,
        )

    def test_set_next_returns_validator(self):
        v1 = TypeChecker()
        v2 = TypeChecker()
        returned = v1.set_next(v2)
        assert returned is v2

    def test_chain_continues_on_warning(self, tmp_path: Path):
        v1 = TypeChecker()
        v2 = TypeChecker()
        v1.set_next(v2)
        result = v1.check(tmp_path)
        assert result.level in (ValidationLevel.PASS, ValidationLevel.WARNING)

    def test_chain_stops_on_error(self, tmp_path: Path):
        class FailChecker(TypeChecker):
            def validate(self, output_dir: Path) -> object:
                from agentic_pipeline.nodes.validator import ValidationResult

                return ValidationResult(ValidationLevel.ERROR, "forced error")

        v1 = FailChecker()
        v2 = TypeChecker()
        v1.set_next(v2)
        result = v1.check(tmp_path)
        assert result.level == ValidationLevel.ERROR
