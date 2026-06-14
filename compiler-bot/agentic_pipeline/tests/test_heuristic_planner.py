"""Tests for Task model, TaskGraph, and HeuristicPlanner."""


from agentic_pipeline.nodes.planner import (
    HeuristicPlanner,
    Task,
    TaskGraph,
    TaskState,
)


class TestTask:
    def test_default_state(self):
        t = Task(id="t1", description="test")
        assert t.state == TaskState.PENDING

    def test_can_run_no_deps(self):
        t = Task(id="t1", description="test")
        assert t.can_run(set())

    def test_can_run_with_deps(self):
        t = Task(id="t1", description="test", dependencies=["dep1"])
        assert not t.can_run(set())
        assert t.can_run({"dep1"})

    def test_model_dump(self):
        t = Task(id="t1", description="test", target="react")
        data = t.model_dump()
        assert data["id"] == "t1"
        assert data["target"] == "react"


class TestTaskGraph:
    def test_empty(self):
        g = TaskGraph()
        assert g.all_tasks() == []
        assert not g.has_cycle()

    def test_add_and_get(self):
        g = TaskGraph()
        t = Task(id="a", description="task a")
        g.add_task(t)
        assert g.get_task("a") is t
        assert g.get_task("nonexistent") is None

    def test_topological_order_simple(self):
        g = TaskGraph()
        g.add_task(Task(id="a", description="a"))
        g.add_task(Task(id="b", description="b", dependencies=["a"]))
        order = g.topological_order()
        assert order.index("a") < order.index("b")

    def test_cycle_detection(self):
        g = TaskGraph()
        g.add_task(Task(id="a", description="a", dependencies=["b"]))
        g.add_task(Task(id="b", description="b", dependencies=["a"]))
        assert g.has_cycle()

    def test_cycle_returns_empty(self):
        g = TaskGraph()
        g.add_task(Task(id="a", description="a", dependencies=["b"]))
        g.add_task(Task(id="b", description="b", dependencies=["a"]))
        assert g.topological_order() == []

    def test_ready_tasks(self):
        g = TaskGraph()
        g.add_task(Task(id="a", description="a"))
        g.add_task(Task(id="b", description="b", dependencies=["a"]))
        ready = g.ready_tasks(set())
        assert len(ready) == 1
        assert ready[0].id == "a"

    def test_ready_tasks_after_done(self):
        g = TaskGraph()
        g.add_task(Task(id="a", description="a"))
        g.add_task(Task(id="b", description="b", dependencies=["a"]))
        ready = g.ready_tasks({"a"})
        assert len(ready) == 1
        assert ready[0].id == "b"

    def test_independent_tasks_all_ready(self):
        g = TaskGraph()
        g.add_task(Task(id="a", description="a"))
        g.add_task(Task(id="b", description="b"))
        ready = g.ready_tasks(set())
        assert len(ready) == 2


class TestHeuristicPlanner:
    def test_plan_empty(self):
        hp = HeuristicPlanner()
        g = TaskGraph()
        assert hp.plan(g) == []

    def test_plan_single(self):
        hp = HeuristicPlanner()
        g = TaskGraph()
        g.add_task(Task(id="task", description="test"))
        planned = hp.plan(g)
        assert len(planned) == 1
        assert planned[0].id == "task"

    def test_group_by_layer(self):
        hp = HeuristicPlanner()
        tasks = [
            Task(id="entity User", description="entidad"),
            Task(id="page login", description="pagina"),
            Task(id="db postgres", description="database"),
        ]
        groups = hp.group_by_layer(tasks)
        assert "data" in groups
        assert "ui" in groups
        assert "infra" in groups

    def test_estimate_simple(self):
        hp = HeuristicPlanner()
        g = TaskGraph()
        g.add_task(Task(id="a", description="a"))
        assert hp.estimate_complexity(g) == "simple"

    def test_estimate_moderate(self):
        hp = HeuristicPlanner()
        g = TaskGraph()
        for i in range(4):
            g.add_task(Task(id=f"t{i}", description=f"task {i}"))
        assert hp.estimate_complexity(g) == "moderate"

    def test_estimate_complex(self):
        hp = HeuristicPlanner()
        g = TaskGraph()
        for i in range(6):
            g.add_task(Task(id=f"t{i}", description=f"task {i}"))
        assert hp.estimate_complexity(g) == "complex"

    def test_detect_layer(self):
        assert HeuristicPlanner._detect_layer(Task(id="config_app", description="c")) == "config"
        assert HeuristicPlanner._detect_layer(Task(id="entity_user", description="e")) == "data"
        assert HeuristicPlanner._detect_layer(Task(id="api_auth", description="a")) == "api"
        assert HeuristicPlanner._detect_layer(Task(id="page_home", description="p")) == "ui"
        assert HeuristicPlanner._detect_layer(Task(id="db_postgres", description="d")) == "infra"
        assert HeuristicPlanner._detect_layer(Task(id="generic_thing", description="g")) == "domain"
