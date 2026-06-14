"""Tests for PlanExecutor and PlanObserver."""

import tempfile
from pathlib import Path

import pytest

from agentic_pipeline.nodes.plan_executor import (
    HeuristicExecutor,
    PlanObserver,
)
from agentic_pipeline.nodes.planner import Task, TaskState
from agentic_pipeline.nodes.task_command import (
    FileCreateCommand,
    ScaffoldCommand,
)


class TestPlanObserver:
    def test_on_state_change(self):
        obs = PlanObserver()
        t = Task(id="t1", description="test")
        obs.on_state_change(t, TaskState.PENDING, TaskState.READY)
        log = obs.get_log()
        assert len(log) == 1
        assert log[0]["task_id"] == "t1"
        assert log[0]["old_state"] == "pending"
        assert log[0]["new_state"] == "ready"

    def test_on_error(self):
        obs = PlanObserver()
        t = Task(id="t1", description="test")
        obs.on_error(t, "something went wrong")
        log = obs.get_log()
        assert len(log) == 1
        assert "error" in log[0]

    def test_clear(self):
        obs = PlanObserver()
        t = Task(id="t1", description="test")
        obs.on_state_change(t, TaskState.PENDING, TaskState.READY)
        obs.clear()
        assert obs.get_log() == []


class TestPlanExecutor:
    @pytest.fixture
    def executor(self):
        return HeuristicExecutor()

    def test_execute_all_empty(self, executor):
        results = executor.execute_all([])
        assert results == []

    def test_execute_single_task(self, executor):
        t = Task(id="t1", description="test")
        results = executor.execute_all([t])
        assert len(results) == 1
        assert results[0].state == TaskState.DONE
        assert "t1" in executor.done_ids

    def test_execute_with_file_command(self, executor):
        t = Task(id="write", description="write file")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cmd = FileCreateCommand("write", "test.txt", "hello")
            executor.register_command("write", cmd)
            results = executor.execute_all([t], base_dir=base)
            assert results[0].state == TaskState.DONE
            assert (base / "test.txt").exists()
            assert (base / "test.txt").read_text() == "hello"

    def test_execute_reuses_done(self, executor):
        t1 = Task(id="a", description="a")
        t2 = Task(id="a", description="a again")
        executor.execute_all([t1])
        executor.execute_all([t2])
        # t2 should be skipped since 'a' is already done
        assert len(executor.done_ids) == 1

    def test_observer_state_changes(self, executor):
        obs = executor.observer
        t = Task(id="t1", description="test")
        executor.execute_all([t])
        log = obs.get_log()
        # PENDING -> READY -> RUNNING -> DONE = 3 state changes
        assert len(log) >= 2


class TestRollback:
    def test_rollback_removes_file(self):
        executor = HeuristicExecutor()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            t = Task(id="del", description="deletable file")
            cmd = FileCreateCommand("del", "temp.txt", "content")
            executor.register_command("del", cmd)
            executor.execute_all([t], base_dir=base)
            assert (base / "temp.txt").exists()
            undone = executor.rollback([t])
            assert "del" in undone
            assert not (base / "temp.txt").exists()

    def test_rollback_reverse_order(self):
        executor = HeuristicExecutor()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            t1 = Task(id="first", description="first")
            t2 = Task(id="second", description="second")
            c1 = FileCreateCommand("first", "f1.txt", "1")
            c2 = FileCreateCommand("second", "f2.txt", "2")
            executor.register_command("first", c1)
            executor.register_command("second", c2)
            executor.execute_all([t1, t2], base_dir=base)
            undone = executor.rollback([t1, t2])
            # second should be undone before first
            assert undone == ["second", "first"]

    def test_rollback_scaffold(self):
        executor = HeuristicExecutor()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            t = Task(id="scaffold", description="scaffold")
            cmd = ScaffoldCommand(
                "scaffold",
                "mymodule",
                items=[{"name": "main.ts", "kind": "file", "content": "// code"}],
            )
            executor.register_command("scaffold", cmd)
            executor.execute_all([t], base_dir=base)
            assert (base / "mymodule" / "main.ts").exists()
            undone = executor.rollback([t])
            assert "scaffold" in undone
            assert not (base / "mymodule").exists()

    def test_rollback_no_command(self):
        executor = HeuristicExecutor()
        t = Task(id="nocmd", description="no command")
        t.state = TaskState.DONE
        undone = executor.rollback([t])
        assert undone == []
