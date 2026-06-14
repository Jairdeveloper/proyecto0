from agentic_pipeline.state_models import (
    Stage,
    StageContext,
    AnalysisResult,
    ActionPlan,
    StageOutput,
    Token,
    DesignTokens,
)


def test_stage_enum_values():
    assert Stage.REQUIREMENT_DECOMPOSER.value == "requirement_decomposer"
    assert Stage.PREPROCESSOR.value == "preprocessor"
    assert Stage.LEXER.value == "lexer"
    assert Stage.PARSER.value == "parser"
    assert Stage.SEMANTIC_ANALYZER.value == "semantic_analyzer"
    assert Stage.IR_GENERATOR.value == "ir_generator"
    assert Stage.PLANNER.value == "planner"
    assert Stage.SYNTHESIS.value == "synthesis"
    assert Stage.UI_GENERATOR.value == "ui_generator"
    assert Stage.VALIDATOR.value == "validator"


def test_stage_context_defaults():
    ctx = StageContext(stage=Stage.LEXER, input_data="test")
    assert ctx.stage == Stage.LEXER
    assert ctx.input_data == "test"
    assert ctx.mission_id is not None
    assert ctx.previous_output is None
    assert ctx.config_overrides == {}


def test_analysis_result():
    r = AnalysisResult(
        observations=["obs1"],
        detected_patterns=["pat1"],
        risks=["risk1"],
        complexity_score=0.5,
    )
    assert r.observations == ["obs1"]
    assert r.detected_patterns == ["pat1"]
    assert r.risks == ["risk1"]
    assert r.complexity_score == 0.5


def test_action_plan():
    p = ActionPlan(steps=[{"action": "test"}], strategy="deterministic")
    assert p.steps == [{"action": "test"}]
    assert p.strategy == "deterministic"
    assert p.fallback_strategy == "deterministic"


def test_stage_output_defaults():
    o = StageOutput(stage=Stage.PARSER, output_data={"key": "val"})
    assert o.stage == Stage.PARSER
    assert o.output_data == {"key": "val"}
    assert o.metrics == {}
    assert o.feedback == {}
    assert o.success is True
    assert o.error is None


def test_token():
    t = Token(value="web_app", type="WEB_APP", category="domain", position=0)
    assert t.value == "web_app"
    assert t.type == "WEB_APP"
    assert t.category == "domain"
    assert t.position == 0
    assert t.confidence == 1.0


def test_design_tokens_defaults():
    dt = DesignTokens()
    assert dt.primary_color == "#6366F1"
    assert dt.secondary_color == "#10B981"
