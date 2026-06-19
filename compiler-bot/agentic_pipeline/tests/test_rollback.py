"""Tests for TaskCommand execute/undo (rollback)."""

import tempfile
from pathlib import Path

from agentic_pipeline.nodes.task_command import (
    FileCreateCommand,
    ScaffoldCommand,
)


class TestFileCreateCommand:
    def test_execute_creates_file(self):
        cmd = FileCreateCommand("t1", "test.txt", "hello world")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = cmd.execute(base)
            assert result is not None
            assert result.exists()
            assert result.read_text() == "hello world"

    def test_execute_default_dir(self):
        cmd = FileCreateCommand("t1", "test.txt", "content")
        result = cmd.execute()
        assert result is not None
        assert result.exists()
        result.unlink()

    def test_undo_removes_file(self):
        cmd = FileCreateCommand("t1", "test_undo.txt", "content")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cmd.execute(base)
            assert (base / "test_undo.txt").exists()
            assert cmd.undo() is True
            assert not (base / "test_undo.txt").exists()

    def test_undo_noop_when_not_executed(self):
        cmd = FileCreateCommand("t1", "never_created.txt", "")
        assert cmd.undo() is False


class TestScaffoldCommand:
    def test_execute_creates_scaffold(self):
        cmd = ScaffoldCommand(
            "t1",
            "mymod",
            items=[
                {"name": "main.py", "kind": "file", "content": "# hello"},
                {"name": "utils", "kind": "dir"},
            ],
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            result = cmd.execute(base)
            assert result is not None
            assert (base / "mymod" / "main.py").exists()
            assert (base / "mymod" / "main.py").read_text() == "# hello"
            assert (base / "mymod" / "utils").is_dir()

    def test_undo_removes_scaffold(self):
        cmd = ScaffoldCommand(
            "t1",
            "undo_mod",
            items=[{"name": "file.txt", "kind": "file", "content": "data"}],
        )
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            cmd.execute(base)
            assert (base / "undo_mod" / "file.txt").exists()
            assert cmd.undo() is True
            assert not (base / "undo_mod").exists()

    def test_undo_noop_when_not_executed(self):
        cmd = ScaffoldCommand("t1", "never_created")
        assert cmd.undo() is False
