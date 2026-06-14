"""Tests for the full Chain of Responsibility in ValidatorPipeline."""

from pathlib import Path

from agentic_pipeline.nodes.validator import (
    SecurityScanner,
    SyntaxValidator,
    TypeChecker,
    ValidationLevel,
    Validator,
    ValidatorPipeline,
)
from agentic_pipeline.state_models import Stage, StageContext


class TestValidatorChain:
    def test_empty_chain_stops_immediately(self):
        class NoopValidator(Validator):
            def validate(self, output_dir: Path) -> object:
                from agentic_pipeline.nodes.validator import ValidationResult

                return ValidationResult(ValidationLevel.PASS, "noop")

        v = NoopValidator()
        result = v.check(Path("/nonexistent"))
        assert result.level == ValidationLevel.PASS
        assert result.message == "noop"

    def test_chain_stops_on_error(self, tmp_path: Path):
        class ErrorValidator(Validator):
            def validate(self, output_dir: Path) -> object:
                from agentic_pipeline.nodes.validator import ValidationResult

                return ValidationResult(ValidationLevel.ERROR, "fatal")

        class PassValidator(Validator):
            def validate(self, output_dir: Path) -> object:
                from agentic_pipeline.nodes.validator import ValidationResult

                return ValidationResult(ValidationLevel.PASS, "ok")

        v1 = ErrorValidator()
        v2 = PassValidator()
        v1.set_next(v2)
        result = v1.check(tmp_path)
        assert result.level == ValidationLevel.ERROR
        assert result.message == "fatal"

    def test_full_chain_syntax_type_security(self, tmp_path: Path):
        (tmp_path / "safe.js").write_text("const x = 1;\n")
        syntax = SyntaxValidator()
        types = TypeChecker()
        security = SecurityScanner()
        syntax.set_next(types).set_next(security)
        result = syntax.check(tmp_path)
        assert result.level in (ValidationLevel.PASS, ValidationLevel.WARNING)

    def test_validator_pipeline_empty_files(self):
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        pipe.receive_mission({})
        plan = pipe.reflect_and_plan(pipe.analyze())
        output = pipe.act(plan)
        assert output.success is True
        assert output.metrics["validations"] == 0

    def test_validator_pipeline_with_generated_files(self, tmp_path: Path):
        (tmp_path / "app.js").write_text("const a = 1;\n")
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        pipe.receive_mission({"generated_files": [str(tmp_path / "app.js")]})
        plan = pipe.reflect_and_plan(pipe.analyze())
        output = pipe.act(plan)
        assert output.metrics["validations"] >= 1

    def test_validator_pipeline_receive_mission_fallback(self):
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        pipe.receive_mission("invalid")
        assert pipe._input_data == {}

    def test_validator_pipeline_analyze(self):
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        pipe.receive_mission({"generated_files": ["a.ts", "b.ts"]})
        result = pipe.analyze()
        assert "2" in result.observations[0]

    def test_validator_pipeline_reflect_and_plan(self):
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        plan = pipe.reflect_and_plan(pipe.analyze())
        assert len(plan.steps) == 3

    def test_validator_pipeline_execute(self, tmp_path: Path):
        (tmp_path / "test.js").write_text("const x = 1;\n")
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        output = pipe.execute({"generated_files": [str(tmp_path / "test.js")]})
        assert output.stage == Stage.VALIDATOR

    def test_security_detected_in_validator_pipeline(self, tmp_path: Path):
        (tmp_path / "secret.env").write_text('PASSWORD = "hunter2"\n')
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        pipe.receive_mission({"generated_files": [str(tmp_path / "secret.env")]})
        plan = pipe.reflect_and_plan(pipe.analyze())
        output = pipe.act(plan)
        assert output.success is False
        assert output.metrics["errors"] >= 1

    def test_should_retry_on_error(self, tmp_path: Path):
        (tmp_path / "leak.txt").write_text("token = sk-abcdefghijklmnopqrst\n")
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        pipe.receive_mission({"generated_files": [str(tmp_path / "leak.txt")]})
        plan = pipe.reflect_and_plan(pipe.analyze())
        output = pipe.act(plan)
        assert output.output_data["should_retry"] is True

    def test_learn_and_improve(self):
        ctx = StageContext(stage=Stage.VALIDATOR, input_data="")
        pipe = ValidatorPipeline(ctx)
        pipe.learn_and_improve({})
        assert True

    def test_build_chain_order(self):
        pipe = ValidatorPipeline(StageContext(stage=Stage.VALIDATOR, input_data=""))
        chain = pipe._build_chain()
        assert isinstance(chain, SyntaxValidator)
        assert isinstance(chain.next_validator, TypeChecker)
        assert isinstance(chain.next_validator.next_validator, SecurityScanner)
