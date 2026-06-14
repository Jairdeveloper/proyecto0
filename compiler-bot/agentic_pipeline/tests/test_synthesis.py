"""Tests for SynthesisOrchestrator stage."""

from pathlib import Path

import pytest

from agentic_pipeline.nodes.ir_nodes import IRPage, IRProject
from agentic_pipeline.nodes.synthesis import SynthesisOrchestrator
from agentic_pipeline.state_models import Stage, StageContext


@pytest.fixture
def orchestrator():
    ctx = StageContext(stage=Stage.SYNTHESIS, input_data="")
    return SynthesisOrchestrator(ctx)


class TestSynthesisOrchestrator:
    def test_receive_mission(self, orchestrator):
        orchestrator.receive_mission({"tasks": [], "commands": []})
        assert orchestrator._input_data is not None

    def test_receive_mission_fallback(self, orchestrator):
        orchestrator.receive_mission("invalid")
        assert orchestrator._input_data == {}

    def test_analyze(self, orchestrator):
        orchestrator.receive_mission({"tasks": [{"id": "a"}, {"id": "b"}]})
        result = orchestrator.analyze()
        assert "2" in result.observations[0]

    def test_reflect_and_plan(self, orchestrator):
        result = orchestrator.reflect_and_plan(orchestrator.analyze())
        assert len(result.steps) == 3

    def test_act_empty(self, orchestrator):
        orchestrator.receive_mission({})
        plan = orchestrator.reflect_and_plan(orchestrator.analyze())
        output = orchestrator.act(plan)
        assert output.success is True
        assert output.metrics["files_generated"] == 0

    def test_act_with_ir_tree(self, orchestrator):
        proj = IRProject("app")
        proj.add(IRPage("Home"))
        data = {
            "ir_tree": proj,
            "tasks": [{"id": "Home", "target": "react"}],
            "commands": [
                {"task_id": "Home", "path": str(Path.cwd() / "tmp_modules" / "home")}
            ],
        }
        orchestrator.receive_mission(data)
        plan = orchestrator.reflect_and_plan(orchestrator.analyze())
        output = orchestrator.act(plan)
        assert output.success is True
        assert output.metrics["files_generated"] >= 1

    def test_execute_full_flow(self, orchestrator):
        proj = IRProject("app")
        proj.add(IRPage("Dashboard"))
        data = {
            "ir_tree": proj,
            "tasks": [{"id": "Dashboard", "target": "react"}],
            "commands": [
                {
                    "task_id": "Dashboard",
                    "path": str(Path.cwd() / "tmp_modules" / "dashboard"),
                }
            ],
        }
        result = orchestrator.execute(data)
        assert result.stage == Stage.SYNTHESIS
        assert result.success is True

    def test_errors_listed(self, orchestrator):
        data = {
            "tasks": [{"id": "ghost", "target": "nonexistent"}],
            "commands": [{"task_id": "ghost", "path": "/tmp/ghost"}],
        }
        orchestrator.receive_mission(data)
        plan = orchestrator.reflect_and_plan(orchestrator.analyze())
        output = orchestrator.act(plan)
        assert output.success is False
        assert len(output.output_data["errors"]) > 0

    def test_learn_and_improve(self, orchestrator):
        orchestrator.learn_and_improve({})
        assert True

    def test_find_ir_node(self, orchestrator):
        proj = IRProject("app")
        page = IRPage("Login")
        proj.add(page)
        found = orchestrator._find_ir_node(proj, "Login")
        assert found is page
        assert orchestrator._find_ir_node(proj, "Ghost") is None

    def test_detect_target(self, orchestrator):
        from agentic_pipeline.nodes.ir_nodes import (
            IRAPI,
            IRComponent,
            IRConfig,
            IREntity,
            IRInfra,
        )

        assert orchestrator._detect_target(IRPage("x")) == "react"
        assert orchestrator._detect_target(IRComponent("x")) == "react"
        assert orchestrator._detect_target(IREntity("x")) == "prisma"
        assert orchestrator._detect_target(IRAPI("x")) == "nestjs"
        assert orchestrator._detect_target(IRInfra("x")) == "docker"
        assert orchestrator._detect_target(IRConfig("x")) == "tailwind"
