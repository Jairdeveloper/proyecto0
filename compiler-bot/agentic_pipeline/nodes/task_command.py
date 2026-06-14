"""TaskCommand — Command pattern with execute/undo for file operations."""

from __future__ import annotations

import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TaskCommand(ABC):
    """Abstract command with execute() and undo()."""

    @abstractmethod
    def execute(self, base_dir: Path | None = None) -> Path | None: ...

    @abstractmethod
    def undo(self) -> bool: ...


class FileCreateCommand(TaskCommand):
    """Creates a file with content on execute, removes on undo."""

    def __init__(
        self,
        task_id: str,
        relative_path: str,
        content: str = "",
    ) -> None:
        self._task_id = task_id
        self._relative_path = relative_path
        self._content = content
        self._created_path: Path | None = None

    def execute(self, base_dir: Path | None = None) -> Path | None:
        base = base_dir or Path.cwd()
        target = base / self._relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self._content)
        self._created_path = target
        logger.info("Created file: %s", target)
        return target

    def undo(self) -> bool:
        if self._created_path is not None and self._created_path.exists():
            self._created_path.unlink()
            logger.info("Removed file: %s", self._created_path)
            self._created_path = None
            return True
        return False


class ScaffoldCommand(TaskCommand):
    """Creates a directory scaffold with sub-items on execute, removes on undo."""

    def __init__(
        self,
        task_id: str,
        relative_path: str,
        items: list[dict[str, Any]] | None = None,
    ) -> None:
        self._task_id = task_id
        self._relative_path = relative_path
        self._items: list[dict[str, Any]] = items or []
        self._created_dirs: list[Path] = []

    def execute(self, base_dir: Path | None = None) -> Path | None:
        base = base_dir or Path.cwd()
        root = base / self._relative_path
        root.mkdir(parents=True, exist_ok=True)
        self._created_dirs.append(root)
        for item in self._items:
            name = item.get("name", "")
            kind = item.get("kind", "file")
            path = root / name
            if kind == "dir":
                path.mkdir(parents=True, exist_ok=True)
                self._created_dirs.append(path)
            else:
                content = item.get("content", "")
                path.write_text(content)
        logger.info("Created scaffold: %s (%d items)", root, len(self._items))
        return root

    def undo(self) -> bool:
        removed = False
        for d in reversed(self._created_dirs):
            if d.exists():
                if d.is_dir():
                    shutil.rmtree(d)
                else:
                    d.unlink()
                removed = True
        self._created_dirs.clear()
        return removed
