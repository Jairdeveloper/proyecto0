"""Tests for RequirementDecomposer pipeline stage."""

import pytest

from agentic_pipeline.nodes.requirement_decomposer import RequirementDecomposer
from agentic_pipeline.state_models import RequirementGraph, Stage, StageContext


@pytest.fixture
def decomposer():
    ctx = StageContext(
        stage=Stage.REQUIREMENT_DECOMPOSER,
        input_data="",
    )
    return RequirementDecomposer(ctx, llm=None)


class TestRequirementDecomposer:
    def test_receive_mission(self, decomposer):
        decomposer.receive_mission("Crea una pagina web")
        assert decomposer._raw_text == "Crea una pagina web"

    def test_analyze_returns_analysis(self, decomposer):
        decomposer.receive_mission("Crea una pagina web con auth")
        result = decomposer.analyze()
        assert result.observations is not None
        assert result.complexity_score == 0.3

    def test_reflect_and_plan_returns_plan(self, decomposer):
        analysis = decomposer.analyze()
        plan = decomposer.reflect_and_plan(analysis)
        assert len(plan.steps) == 4
        assert plan.strategy == "llm_assisted"

    def test_act_returns_graph_with_domain(self, decomposer):
        decomposer.receive_mission("Crea una pagina web para acortar enlaces")
        plan = decomposer.reflect_and_plan(decomposer.analyze())
        output = decomposer.act(plan)
        graph = RequirementGraph(**output.output_data)
        assert graph.domain == "web"

    def test_act_detects_features(self, decomposer):
        decomposer.receive_mission("Sistema con auth y QR para enlaces")
        plan = decomposer.reflect_and_plan(decomposer.analyze())
        output = decomposer.act(plan)
        graph = RequirementGraph(**output.output_data)
        assert len(graph.features) > 0
        assert any("JWT" in f for f in graph.features)

    def test_execute_full_flow(self, decomposer):
        prompt = "Diseña una pagina web para acortar enlaces con auth y QR"
        result = decomposer.execute(prompt)
        assert result.success is True
        graph = RequirementGraph(**result.output_data)
        assert graph.domain == "web"
        assert len(graph.entities) >= 1
        assert len(graph.features) >= 1
        assert result.metrics["entities"] >= 1
        assert result.metrics["features"] >= 1

    def test_learn_and_improve(self, decomposer):
        decomposer.receive_mission("test")
        output = decomposer.act(decomposer.reflect_and_plan(decomposer.analyze()))
        decomposer.learn_and_improve(output.feedback)
        assert True  # no exception


class TestRequirementDecomposerEdgeCases:
    def test_empty_input(self):
        ctx = StageContext(stage=Stage.REQUIREMENT_DECOMPOSER, input_data="")
        rd = RequirementDecomposer(ctx, llm=None)
        result = rd.execute("")
        assert result.success is True

    def test_very_long_input(self):
        ctx = StageContext(stage=Stage.REQUIREMENT_DECOMPOSER, input_data="")
        rd = RequirementDecomposer(ctx, llm=None)
        long_text = "web " * 500
        result = rd.execute(long_text)
        assert result.success is True

    def test_output_has_all_fields(self):
        ctx = StageContext(stage=Stage.REQUIREMENT_DECOMPOSER, input_data="")
        rd = RequirementDecomposer(ctx, llm=None)
        rd.receive_mission("Crea una pagina web")
        plan = rd.reflect_and_plan(rd.analyze())
        output = rd.act(plan)
        graph = RequirementGraph(**output.output_data)
        assert graph.raw_text == "Crea una pagina web"
        assert isinstance(graph.entities, list)
        assert isinstance(graph.features, list)
        assert isinstance(graph.constraints, list)
        assert isinstance(graph.user_stories, list)
