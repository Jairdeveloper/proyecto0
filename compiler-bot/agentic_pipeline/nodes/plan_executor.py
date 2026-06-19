"""PlanExecutor — Template Method with PlanObserver for task execution."""

from __future__ import annotations

import logging
from abc import ABC
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from agentic_pipeline.nodes.planner import Task, TaskState
from agentic_pipeline.nodes.task_command import TaskCommand

logger = logging.getLogger(__name__)


# ============================================================================
# PlanObserver — logging and tracking state changes
# ============================================================================


class PlanObserver:
    """Observer that logs task state changes."""

    def __init__(self) -> None:
        self._log: list[dict[str, Any]] = []

    def on_state_change(
        self,
        task: Task,
        old_state: TaskState,
        new_state: TaskState,
    ) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": task.id,
            "old_state": old_state.value,
            "new_state": new_state.value,
        }
        self._log.append(entry)
        logger.info("Task %s: %s -> %s", task.id, old_state.value, new_state.value)

    def on_error(self, task: Task, error: str) -> None:
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": task.id,
            "error": error,
        }
        self._log.append(entry)
        logger.error("Task %s failed: %s", task.id, error)

    def get_log(self) -> list[dict[str, Any]]:
        return list(self._log)

    def clear(self) -> None:
        self._log.clear()


# ============================================================================
# PlanExecutor — Template Method
# ============================================================================


class PlanExecutor(ABC):
    """Abstract executor with Template Method pattern."""

    def __init__(self, observer: PlanObserver | None = None) -> None:
        self._observer = observer or PlanObserver()
        self._commands: dict[str, TaskCommand] = {}
        self._done: set[str] = set()
        self._failed: list[tuple[str, str]] = []

    def register_command(self, task_id: str, command: TaskCommand) -> None:
        self._commands[task_id] = command

    # --- Template Method hooks ---

    def pre_execute(self, task: Task) -> None: ...

    def post_execute(self, task: Task) -> None: ...

    def on_error(self, task: Task, error: Exception) -> None:
        self._observer.on_error(task, str(error))
        self._failed.append((task.id, str(error)))

    # --- Template Method ---

    def execute_all(
        self,
        tasks: list[Task],
        base_dir: Path | None = None,
    ) -> list[Task]:
        """Execute tasks in order, respecting dependencies."""
        results: list[Task] = []
        for task in tasks:
            if task.id in self._done:
                continue
            old_state = task.state
            task.state = TaskState.READY
            self._observer.on_state_change(task, old_state, task.state)

            self.pre_execute(task)

            old_state = task.state
            task.state = TaskState.RUNNING
            self._observer.on_state_change(task, old_state, task.state)

            try:
                cmd = self._commands.get(task.id)
                if cmd is not None:
                    cmd.execute(base_dir)
                task.state = TaskState.DONE
                self._done.add(task.id)
                self._observer.on_state_change(task, TaskState.RUNNING, TaskState.DONE)
            except Exception as e:
                task.state = TaskState.FAILED
                self.on_error(task, e)

            self.post_execute(task)
            results.append(task)
        return results

    def rollback(self, tasks: list[Task]) -> list[str]:
        """Undo commands in reverse order."""
        undone: list[str] = []
        for task in reversed(tasks):
            cmd = self._commands.get(task.id)
            if cmd is not None and cmd.undo():
                undone.append(task.id)
                task.state = TaskState.PENDING
        return undone

    @property
    def observer(self) -> PlanObserver:
        return self._observer

    @property
    def done_ids(self) -> set[str]:
        return self._done

    @property
    def failed_tasks(self) -> list[tuple[str, str]]:
        return self._failed


class HeuristicExecutor(PlanExecutor):
    """Concrete executor using heuristic ordering."""

    def pre_execute(self, task: Task) -> None:
        logger.debug("Pre-executing: %s", task.id)

    def post_execute(self, task: Task) -> None:
        logger.debug("Post-executing: %s", task.id)

    def on_error(self, task: Task, error: Exception) -> None:
        super().on_error(task, error)
        logger.warning("HeuristicExecutor: task %s failed, continuing", task.id)
