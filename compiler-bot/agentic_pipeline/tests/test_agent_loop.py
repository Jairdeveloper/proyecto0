"""Tests for AgentLoop."""

from __future__ import annotations

import tempfile

import pytest

from agentic_pipeline.agent_loop import AgentLoop, AgentOutput
from agentic_pipeline.orchestrator import AgentOrchestrator
from agentic_pipeline.memory import ConversationalMemory


class TestAgentOutput:
    def test_agent_output_dataclass(self):
        output = AgentOutput(status="completed", data={"key": "val"}, iterations=2)
        assert output.status == "completed"
        assert output.data["key"] == "val"
        assert output.iterations == 2

    def test_agent_output_defaults(self):
        output = AgentOutput(status="error")
        assert output.data == {}
        assert output.message == ""
        assert output.iterations == 0


class TestAgentLoopInit:
    def test_default_initialization(self):
        loop = AgentLoop(max_iterations=3)
        assert loop.max_iterations == 3
        assert not loop.interactive
        # Default tools are registered
        tools = loop.list_tools()
        names = [t["name"] for t in tools]
        assert "read_file" in names
        assert "write_file" in names
        assert "run_command" in names
        assert "search_code" in names
        assert "explain" in names

    def test_custom_orchestrator_and_memory(self):
        tmp = tempfile.mkdtemp()
        mem = ConversationalMemory(storage_dir=tmp)
        loop = AgentLoop(
            orchestrator=AgentOrchestrator(),
            memory=mem,
            max_iterations=1,
        )
        assert loop.max_iterations == 1

    @pytest.mark.asyncio
    async def test_run_completes(self):
        loop = AgentLoop(max_iterations=3)
        result = await loop.run("crea un modulo de pagos")
        assert result.status in ("completed", "max_iterations_reached")
        assert result.iterations >= 1
        assert result.iterations <= 3

    @pytest.mark.asyncio
    async def test_run_records_in_memory(self):
        tmp = tempfile.mkdtemp()
        mem = ConversationalMemory(storage_dir=tmp)
        loop = AgentLoop(memory=mem, max_iterations=3)
        await loop.run("test prompt")
        recent = mem.get_recent(1)
        assert len(recent) >= 1

    @pytest.mark.asyncio
    async def test_run_max_iterations(self):
        loop = AgentLoop(max_iterations=1)
        result = await loop.run("some prompt")
        assert result.iterations <= 1

    def test_list_tools(self):
        loop = AgentLoop()
        tools = loop.list_tools()
        assert isinstance(tools, list)
        assert len(tools) >= 5
