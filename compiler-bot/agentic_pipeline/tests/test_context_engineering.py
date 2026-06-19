"""Tests for Context Engineering (N2.2c)."""

from __future__ import annotations


class TestContextEngineering:
    def test_build_context_perception(self):
        from agentic_pipeline.orchestrator import build_context
        from agentic_pipeline.state_models import Stage

        ctx = build_context(
            Stage.INTENT,
            {
                "history": [{"role": "user", "content": "crea modulo"}],
            },
        )
        assert ctx.task_focus == "parse user intent and classify"
        assert len(ctx.relevant_history) <= 3

    def test_build_context_planner(self):
        from agentic_pipeline.orchestrator import build_context
        from agentic_pipeline.state_models import Stage

        ctx = build_context(
            Stage.PLANNER,
            {
                "history": [{"role": "user", "content": "crea modulo"}],
            },
        )
        assert ctx.task_focus == "decompose goal with current world state"
        assert len(ctx.relevant_history) == 0

    def test_build_context_synthesis(self):
        from agentic_pipeline.orchestrator import build_context
        from agentic_pipeline.state_models import Stage

        ctx = build_context(Stage.SYNTHESIS, {"history": []})
        assert ctx.task_focus == "generate code per plan, avoid overwrites"

    def test_build_context_preprocessor(self):
        from agentic_pipeline.orchestrator import build_context
        from agentic_pipeline.state_models import Stage

        ctx = build_context(Stage.PREPROCESSOR, {"history": []})
        assert ctx.task_focus == "syntactic analysis without context bias"

    def test_build_context_reasoning(self):
        from agentic_pipeline.orchestrator import build_context
        from agentic_pipeline.state_models import Stage

        ctx = build_context(Stage.REASONING, {"history": [{"a": "b"}] * 10})
        assert len(ctx.relevant_history) == 0

    def test_build_context_execution(self):
        from agentic_pipeline.orchestrator import build_context
        from agentic_pipeline.state_models import Stage

        ctx = build_context(Stage.EXECUTION, {"history": []})
        assert "generate code" in ctx.task_focus or "plan" in ctx.task_focus

    def test_context_window_dataclass(self):
        from agentic_pipeline.state_models import ContextWindow

        cw = ContextWindow(relevant_history=[], world_snapshot={}, task_focus="test")
        assert cw.task_focus == "test"
        assert cw.relevant_history == []
        assert cw.world_snapshot == {}

    def test_stage_focus_lexer(self):
        from agentic_pipeline.orchestrator import build_context
        from agentic_pipeline.state_models import Stage

        ctx = build_context(Stage.LEXER, {"history": []})
        assert "syntactic" in ctx.task_focus or "analysis" in ctx.task_focus

    def test_unknown_stage_default(self):
        from agentic_pipeline.orchestrator import build_context

        ctx = build_context("UNKNOWN", {"history": [{"x": "y"}]})
        assert ctx.task_focus == "general processing"
