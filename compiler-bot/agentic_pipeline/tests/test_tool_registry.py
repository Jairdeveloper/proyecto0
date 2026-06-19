"""Tests for ToolRegistry and ported tools."""

from __future__ import annotations

import os
import tempfile

import pytest

from agentic_pipeline.tool_registry import ToolRegistry
from agentic_pipeline.tools.explain import ExplainTool
from agentic_pipeline.tools.read_file import ReadFileTool
from agentic_pipeline.tools.run_command import RunCommandTool
from agentic_pipeline.tools.search_code import SearchCodeTool
from agentic_pipeline.tools.write_file import WriteFileTool


@pytest.fixture
def registry() -> ToolRegistry:
    r = ToolRegistry()
    r.register(ReadFileTool())
    r.register(WriteFileTool())
    r.register(RunCommandTool())
    r.register(SearchCodeTool())
    r.register(ExplainTool())
    return r


class TestToolRegistry:
    def test_register_and_list(self, registry: ToolRegistry):
        tools = registry.list_available()
        names = [t["name"] for t in tools]
        assert "read_file" in names
        assert "write_file" in names
        assert "run_command" in names
        assert len(tools) >= 4

    def test_has_tool(self, registry: ToolRegistry):
        assert registry.has_tool("read_file")
        assert registry.has_tool("explain")
        assert not registry.has_tool("nonexistent")

    def test_get_tool(self, registry: ToolRegistry):
        tool = registry.get_tool("read_file")
        assert tool is not None
        assert tool.name == "read_file"
        assert registry.get_tool("nope") is None

    def test_execute_unknown(self, registry: ToolRegistry):
        import asyncio

        result = asyncio.run(registry.execute("nope", {}))
        assert not result.success
        assert "not found" in result.error


class TestReadFileTool:
    @pytest.mark.asyncio
    async def test_read_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("hello world")
            tmp = f.name
        try:
            tool = ReadFileTool()
            result = await tool.execute({"path": tmp})
            assert result.success
            assert result.data["content"] == "hello world"
            assert result.data["size"] == 11
        finally:
            os.unlink(tmp)

    @pytest.mark.asyncio
    async def test_read_nonexistent(self):
        tool = ReadFileTool()
        result = await tool.execute({"path": "/tmp/nonexistent_file_xyz"})
        assert not result.success
        assert "no encontrado" in result.error

    @pytest.mark.asyncio
    async def test_read_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            tool = ReadFileTool()
            result = await tool.execute({"path": tmp})
            assert not result.success
            assert "No es un archivo" in result.error


class TestWriteFileTool:
    @pytest.mark.asyncio
    async def test_write_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.txt")
            tool = WriteFileTool()
            result = await tool.execute({"path": path, "content": "hello"})
            assert result.success
            assert result.data["bytes"] == 5
            with open(path) as f:
                assert f.read() == "hello"

    @pytest.mark.asyncio
    async def test_write_creates_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a", "b", "c", "test.txt")
            tool = WriteFileTool()
            result = await tool.execute({"path": path, "content": "nested"})
            assert result.success
            assert os.path.exists(path)

    @pytest.mark.asyncio
    async def test_write_path_traversal_blocked(self):
        tool = WriteFileTool()
        result = await tool.execute({"path": "../escape.txt", "content": "x"})
        assert not result.success
        assert "Path traversal" in result.error


class TestRunCommandTool:
    @pytest.mark.asyncio
    async def test_run_echo(self):
        tool = RunCommandTool()
        result = await tool.execute({"command": "echo hello"})
        assert result.success
        assert result.data["stdout"].strip() == "hello"

    @pytest.mark.asyncio
    async def test_run_failure(self):
        tool = RunCommandTool()
        result = await tool.execute({"command": "false"})
        assert not result.success
        assert result.data["returncode"] == 1

    @pytest.mark.asyncio
    async def test_run_timeout(self):
        tool = RunCommandTool()
        result = await tool.execute({"command": "sleep 30"})
        assert not result.success


class TestExplainTool:
    @pytest.mark.asyncio
    async def test_explain_message(self):
        tool = ExplainTool()
        result = await tool.execute({"message": "hello"})
        assert result.success
        assert result.data["message"] == "hello"
