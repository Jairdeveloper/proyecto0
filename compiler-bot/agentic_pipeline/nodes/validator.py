"""Validator stage — Chain of Responsibility for code validation."""

from __future__ import annotations

import logging
import re
import subprocess
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from ..base_stage import PipelineStage
from ..state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


class ValidationResult:
    def __init__(
        self,
        level: ValidationLevel,
        message: str = "",
        details: list[str] | None = None,
    ) -> None:
        self.level = level
        self.message = message
        self.details = details or []


class Validator(ABC):
    def __init__(self) -> None:
        self.next_validator: Validator | None = None

    def set_next(self, validator: Validator) -> Validator:
        self.next_validator = validator
        return validator

    @abstractmethod
    def validate(self, output_dir: Path) -> ValidationResult: ...

    def check(self, output_dir: Path) -> ValidationResult:
        result = self.validate(output_dir)
        if result.level == ValidationLevel.ERROR:
            return result
        if self.next_validator is not None:
            return self.next_validator.check(output_dir)
        return result


# ============================================================================
# Concrete validators
# ============================================================================


class SyntaxValidator(Validator):
    """Checks syntax with prettier."""

    def validate(self, output_dir: Path) -> ValidationResult:
        try:
            result = subprocess.run(
                ["npx", "prettier", "--check", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                lines = result.stdout.split("\n")[:5]
                return ValidationResult(
                    ValidationLevel.ERROR,
                    "Syntax errors found",
                    lines,
                )
            return ValidationResult(ValidationLevel.PASS, "Syntax OK")
        except FileNotFoundError:
            return ValidationResult(
                ValidationLevel.WARNING,
                "prettier not installed, skipping syntax check",
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                ValidationLevel.WARNING,
                "prettier timed out",
                [],
            )


class TypeChecker(Validator):
    """Checks TypeScript types with tsc."""

    def validate(self, output_dir: Path) -> ValidationResult:
        tsconfig = output_dir / "tsconfig.json"
        if not tsconfig.exists():
            return ValidationResult(
                ValidationLevel.WARNING,
                "No tsconfig.json found, skipping type check",
            )
        try:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--project", str(tsconfig)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                lines = result.stdout.split("\n")[:10]
                return ValidationResult(
                    ValidationLevel.ERROR,
                    "Type errors found",
                    lines,
                )
            return ValidationResult(ValidationLevel.PASS, "Types OK")
        except FileNotFoundError:
            return ValidationResult(
                ValidationLevel.WARNING,
                "tsc not installed, skipping type check",
            )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                ValidationLevel.WARNING,
                "tsc timed out",
                [],
            )


# ---------------------------------------------------------------------------
# Security patterns
# ---------------------------------------------------------------------------

SECRET_PATTERNS: list[tuple[str, str]] = [
    (r"(?i)password\s*[=:]\s*[\"'].+[\"']", "Hardcoded password"),
    (r"(?i)api[_-]?key\s*[=:]\s*[\"'].+[\"']", "Hardcoded API key"),
    (r"(?i)secret\s*[=:]\s*[\"'].+[\"']", "Hardcoded secret"),
    (r"(?i)token\s*[=:]\s*[\"'].{8,}[\"']", "Hardcoded token"),
    (r"(?i)sk-[A-Za-z0-9]{20,}", "OpenAI API key"),
    (r"(?i)AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"-----BEGIN (RSA |EC )?PRIVATE KEY-----", "Private key"),
]


class SecurityScanner(Validator):
    """Scans for hardcoded secrets using regex patterns + trufflehog."""

    def __init__(
        self,
        patterns: list[tuple[str, str]] | None = None,
    ) -> None:
        super().__init__()
        self.patterns = patterns or SECRET_PATTERNS

    def validate(self, output_dir: Path) -> ValidationResult:
        findings: list[str] = []
        for filepath in output_dir.rglob("*"):
            if not filepath.is_file():
                continue
            try:
                content = filepath.read_text()
                for pattern, desc in self.patterns:
                    if re.search(pattern, content):
                        rel = filepath.relative_to(output_dir)
                        findings.append(f"{desc} in {rel}")
            except (UnicodeDecodeError, PermissionError):
                continue
        try:
            tr_result = subprocess.run(
                ["trufflehog", "filesystem", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if tr_result.returncode == 0 and tr_result.stdout.strip():
                findings.append(f"trufflehog: {tr_result.stdout[:500]}")
        except FileNotFoundError:
            pass
        if findings:
            return ValidationResult(
                ValidationLevel.ERROR,
                "Security issues detected",
                findings,
            )
        return ValidationResult(ValidationLevel.PASS, "Security OK")


# ============================================================================
# PipelineStage
# ============================================================================


class ValidatorPipeline(PipelineStage):
    """Stage 9: validates generated code via Chain of Responsibility."""

    name = "validator"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_data: dict[str, Any] | None = None
        self._chain = self._build_chain()
        self._all_results: list[ValidationResult] = []

    @staticmethod
    def _build_chain() -> Validator:
        syntax = SyntaxValidator()
        types = TypeChecker()
        security = SecurityScanner()
        syntax.set_next(types).set_next(security)
        return syntax

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            self._input_data = input_data
        else:
            self._input_data = {}

    def analyze(self) -> AnalysisResult:
        files = self._input_data.get("generated_files", []) if self._input_data else []
        return AnalysisResult(
            observations=[f"Files to validate: {len(files)}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.3,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(
            steps=[
                {"action": "run_syntax_check"},
                {"action": "run_type_check"},
                {"action": "run_security_scan"},
            ],
            strategy="deterministic",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        self._all_results = []
        files = self._input_data.get("generated_files", []) if self._input_data else []
        if not files:
            return StageOutput(
                stage=self.context.stage,
                output_data={"results": [], "should_retry": False},
                metrics={"validations": 0, "errors": 0, "warnings": 0},
                success=True,
            )
        output_dirs: set[Path] = set()
        for fp in files:
            p = Path(fp)
            parent = p.parent
            if parent.exists():
                output_dirs.add(parent)
        for output_dir in output_dirs:
            result = self._chain.check(output_dir)
            self._all_results.append(result)
        errors = sum(1 for r in self._all_results if r.level == ValidationLevel.ERROR)
        warnings = sum(
            1 for r in self._all_results if r.level == ValidationLevel.WARNING
        )
        should_retry = errors > 0
        return StageOutput(
            stage=self.context.stage,
            output_data={
                "results": [
                    {
                        "level": r.level.value,
                        "message": r.message,
                        "details": r.details,
                    }
                    for r in self._all_results
                ],
                "should_retry": should_retry,
                "generated_files": files,
            },
            metrics={
                "validations": len(self._all_results),
                "errors": errors,
                "warnings": warnings,
            },
            success=not should_retry,
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
