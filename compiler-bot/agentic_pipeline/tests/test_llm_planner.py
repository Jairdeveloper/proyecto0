"""Tests for HybridPlanner PipelineStage and LLM delegation."""

import pytest

from agentic_pipeline.nodes.ir_nodes import IRPage, IRProject
from agentic_pipeline.nodes.planner import HybridPlanner
from agentic_pipeline.state_models import Stage, StageContext


class TestHybridPlanner:
    @pytest.fixture
    def planner(self):
        ctx = StageContext(stage=Stage.PLANNER, input_data="")
        return HybridPlanner(ctx)

    def test_receive_mission(self, planner):
        planner.receive_mission({"dependency_order": ["a", "b"]})
        assert planner._input_data is not None

    def test_receive_mission_fallback(self, planner):
        planner.receive_mission("invalid")
        assert planner._input_data == {}

    def test_analyze(self, planner):
        planner.receive_mission({"dependency_order": ["a", "b"]})
        result = planner.analyze()
        assert result.complexity_score == 0.3
        assert "a" in result.observations[0]

    def test_reflect_and_plan(self, planner):
        result = planner.reflect_and_plan(planner.analyze())
        assert len(result.steps) == 3

    def test_act_empty(self, planner):
        planner.receive_mission({})
        plan = planner.reflect_and_plan(planner.analyze())
        output = planner.act(plan)
        assert output.success is True
        assert output.metrics["task_count"] == 0

    def test_act_with_ir_tree(self, planner):
        proj = IRProject("test")
        page = IRPage("login")
        proj.add(page)
        planner.receive_mission({"ir_tree": proj})
        plan = planner.reflect_and_plan(planner.analyze())
        output = planner.act(plan)
        assert output.metrics["task_count"] >= 1

    def test_execute_full_flow(self, planner):
        proj = IRProject("app")
        page = IRPage("home")
        proj.add(page)
        result = planner.execute({"ir_tree": proj})
        assert result.stage == Stage.PLANNER
        assert result.success is True

    def test_act_returns_layers(self, planner):
        proj = IRProject("app")
        proj.add(IRPage("login"))
        planner.receive_mission({"ir_tree": proj})
        plan = planner.reflect_and_plan(planner.analyze())
        output = planner.act(plan)
        assert "layers" in output.output_data
        assert "execution_order" in output.output_data

    def test_complexity_simple(self, planner):
        planner.receive_mission({})
        plan = planner.reflect_and_plan(planner.analyze())
        output = planner.act(plan)
        assert output.output_data["complexity"] in ("simple", "moderate", "complex")

    def test_learn_and_improve(self, planner):
        planner.receive_mission({})
        planner.learn_and_improve({})
        assert True

    def test_commands_in_output(self, planner):
        proj = IRProject("test")
        proj.add(IRPage("dashboard"))
        planner.receive_mission({"ir_tree": proj})
        plan = planner.reflect_and_plan(planner.analyze())
        output = planner.act(plan)
        assert len(output.output_data["commands"]) >= 1
        assert output.output_data["commands"][0]["task_id"] == "dashboard"
