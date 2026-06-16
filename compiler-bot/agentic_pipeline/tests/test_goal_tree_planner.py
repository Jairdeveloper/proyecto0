"""Tests for GoalTreePlanner (N2.2b)."""

from __future__ import annotations


class TestGoalTreePlanner:
    def test_decompose_create_module(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
        planner = GoalTreePlanner()
        goal = planner.decompose(
            "crea un modulo de pagos",
            "CREATE",
            [{"name": "pagos", "type": "module"}],
        )
        assert goal.id == "create_module"
        assert len(goal.subtasks) >= 2
        assert "pagos" in goal.description.lower()

    def test_decompose_create_entity(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
        planner = GoalTreePlanner()
        goal = planner.decompose(
            "crea una entidad usuario",
            "CREATE",
            [{"name": "usuario", "type": "entity"}],
        )
        assert goal.id == "create_entity"
        assert "usuario" in goal.description.lower()

    def test_decompose_explain(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
        planner = GoalTreePlanner()
        goal = planner.decompose(
            "explica como funciona el pipeline",
            "EXPLAIN",
            [],
        )
        assert goal.id == "explain"

    def test_decompose_crud(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
        planner = GoalTreePlanner()
        goal = planner.decompose(
            "crea un crud de productos",
            "CREATE",
            [{"name": "productos", "type": "crud"}],
        )
        assert goal.id == "create_crud"
        assert "CRUD" in goal.description.upper() or "crud" in goal.description.lower()

    def test_verify_success(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner, Goal
        from agentic_pipeline.world_model import WorldModel
        planner = GoalTreePlanner()
        world = WorldModel()
        world.apply_action({"type": "create", "path": "test.txt"})
        goal = Goal(id="test", description="test", status="pending",
                    verification_criteria=["existe test.txt?"])
        assert planner.verify(goal, world) is True

    def test_verify_failure(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner, Goal
        from agentic_pipeline.world_model import WorldModel
        planner = GoalTreePlanner()
        world = WorldModel()
        goal = Goal(id="test", description="test", status="pending",
                    verification_criteria=["existe inexistente.txt?"])
        assert planner.verify(goal, world) is False

    def test_replan(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner, Goal
        planner = GoalTreePlanner()
        goal = Goal(id="fail", description="algo", status="in_progress")
        result = planner.replan(goal, None, "error de prueba")
        assert result.status == "failed"
        assert result.error == "error de prueba"
        assert len(result.subtasks) == 1
        assert "corregir" in result.subtasks[0].description

    def test_subtasks_have_dependencies(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
        planner = GoalTreePlanner()
        goal = planner.decompose(
            "crea un modulo de pagos",
            "CREATE",
            [{"name": "pagos", "type": "module"}],
        )
        for sub in goal.subtasks:
            if sub.id != "create_dir":
                assert len(sub.dependencies) >= 1

    def test_goal_dataclass_defaults(self):
        from agentic_pipeline.nodes.reasoning_engine import Goal
        goal = Goal(id="g1", description="test", status="pending")
        assert goal.dependencies == []
        assert goal.subtasks == []
        assert goal.verification_criteria == []
        assert goal.result is None
        assert goal.error is None

    def test_goal_tree_size(self):
        from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
        planner = GoalTreePlanner()
        goal = planner.decompose(
            "crea un modulo de pagos",
            "CREATE",
            [{"name": "pagos", "type": "module"}],
        )
        assert len(goal.subtasks) >= 3
