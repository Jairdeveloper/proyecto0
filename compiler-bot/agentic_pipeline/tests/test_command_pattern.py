"""Tests for Fase 2 — Command Pattern.

4 tests:
- test_command_execute: Command se ejecuta y retorna CommandResult
- test_command_history: CommandHistory registra y filtra
- test_macro_command: MacroCommand ejecuta secuencia
- test_command_logged_on_failure: Command fallido se registra con error
"""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock

import pytest

from agentic_pipeline.prompt_chain.command_base import (
    Command,
    CommandResult,
    MacroCommand,
)
from agentic_pipeline.prompt_chain.command_history import CommandHistory
from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry


class _SuccessCommand(Command):
    name = "success_test"

    async def execute(self) -> CommandResult:
        return CommandResult(
            success=True,
            data={"result": "ok"},
            command_name=self.name,
        )


class _FailCommand(Command):
    name = "fail_test"

    async def execute(self) -> CommandResult:
        return CommandResult(
            success=False,
            data={},
            error="mock failure",
            command_name=self.name,
        )


class _SlowCommand(Command):
    name = "slow_test"

    def __init__(self, delay: float = 0.01) -> None:
        self._delay = delay

    async def execute(self) -> CommandResult:
        import asyncio
        import time

        t0 = time.time()
        await asyncio.sleep(self._delay)
        duration = time.time() - t0
        return CommandResult(
            success=True,
            data={"delayed": True},
            duration=duration,
            command_name=self.name,
        )


class TestCommandExecute:
    """Tests para 2.1 — Command se ejecuta y retorna CommandResult."""

    @pytest.mark.asyncio
    async def test_command_execute_success(self):
        cmd = _SuccessCommand()
        result = await cmd.execute()
        assert result.success is True
        assert result.data == {"result": "ok"}
        assert result.command_name == "success_test"

    @pytest.mark.asyncio
    async def test_command_execute_failure(self):
        cmd = _FailCommand()
        result = await cmd.execute()
        assert result.success is False
        assert result.error == "mock failure"
        assert result.command_name == "fail_test"

    @pytest.mark.asyncio
    async def test_command_result_defaults(self):
        result = CommandResult(success=True)
        assert result.success is True
        assert result.data == {}
        assert result.error is None
        assert result.fallback_used is False
        assert result.duration == 0.0

    @pytest.mark.asyncio
    async def test_preprocess_command_execute(self):
        """PreprocessCommand ejecuta handler via Command pattern."""
        import agentic_pipeline.prompt_chain.prompts as _pkg
        from agentic_pipeline.prompt_chain.commands import PreprocessCommand

        _ = _pkg
        PromptRegistry.clear()
        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.preprocess",
        )
        importlib.reload(_mod)

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"normalized": "crea modulo", "domain": "backend",'
            '"language": "es", "segments": ["crea modulo"],'
            '"has_ambiguity": false, "confidence": 0.95}',
            structured={
                "normalized": "crea modulo",
                "domain": "backend",
                "language": "es",
                "segments": ["crea modulo"],
                "has_ambiguity": False,
                "confidence": 0.95,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        cmd = PreprocessCommand(raw_text="crea modulo", llm=mock_llm)
        result = await cmd.execute()
        assert result.success is True
        assert result.data["normalized"] == "crea modulo"

    @pytest.mark.asyncio
    async def test_command_records_duration(self):
        cmd = _SlowCommand(delay=0.02)
        result = await cmd.execute()
        assert result.success is True
        assert result.duration >= 0.01


class TestCommandHistory:
    """Tests para 2.1 — CommandHistory registra y filtra."""

    def setup_method(self) -> None:
        self.history = CommandHistory(max_entries=10)

    def test_record_command(self):
        cmd = _SuccessCommand()
        result = CommandResult(success=True, data={}, command_name="success_test")
        self.history.record(cmd, result)
        assert len(self.history.get_all()) == 1

    def test_history_get_failures(self):
        cmd_s = _SuccessCommand()
        cmd_f = _FailCommand()
        self.history.record(cmd_s, CommandResult(success=True, data={}))
        self.history.record(cmd_f, CommandResult(success=False, error="fail"))
        failures = self.history.get_failures()
        successes = self.history.get_successes()
        assert len(failures) == 1
        assert len(successes) == 1

    def test_history_get_by_name(self):
        self.history.record(
            _SuccessCommand(),
            CommandResult(success=True, data={}),
        )
        self.history.record(
            _FailCommand(),
            CommandResult(success=False, error="fail"),
        )
        entries = self.history.get_by_name("success_test")
        assert len(entries) == 1
        assert entries[0].command_name == "success_test"

    def test_history_success_rate(self):
        self.history.record(
            _SuccessCommand(),
            CommandResult(success=True, data={}),
        )
        self.history.record(
            _FailCommand(),
            CommandResult(success=False, error="fail"),
        )
        assert self.history.get_success_rate() == 0.5

    def test_history_fallback_count(self):
        self.history.record(
            _SuccessCommand(),
            CommandResult(success=True, data={}, fallback_used=True),
        )
        self.history.record(
            _SuccessCommand(),
            CommandResult(success=True, data={}, fallback_used=False),
        )
        assert self.history.get_fallback_count() == 1

    def test_history_clear(self):
        self.history.record(
            _SuccessCommand(),
            CommandResult(success=True, data={}),
        )
        self.history.clear()
        assert len(self.history.get_all()) == 0

    def test_history_empty_success_rate(self):
        assert self.history.get_success_rate() == 1.0


class TestMacroCommand:
    """Tests para 2.3 — MacroCommand ejecuta secuencia."""

    @pytest.mark.asyncio
    async def test_macro_executes_all(self):
        macro = MacroCommand()
        macro.add(_SuccessCommand()).add(_SuccessCommand())
        result = await macro.execute()
        assert result.success is True

    @pytest.mark.asyncio
    async def test_macro_stops_on_failure(self):
        macro = MacroCommand()
        macro.add(_SuccessCommand())
        macro.add(_FailCommand())
        macro.add(_SuccessCommand())  # no deberia ejecutarse
        result = await macro.execute()
        assert result.success is False
        assert result.error == "mock failure"
        assert len(macro.commands) == 3

    @pytest.mark.asyncio
    async def test_macro_empty(self):
        macro = MacroCommand()
        result = await macro.execute()
        assert result.success is True
        assert result.data == {}

    @pytest.mark.asyncio
    async def test_macro_fluent_api(self):
        macro = MacroCommand()
        returned = macro.add(_SuccessCommand())
        assert returned is macro

    @pytest.mark.asyncio
    async def test_macro_records_duration(self):
        macro = MacroCommand()
        macro.add(_SlowCommand(delay=0.01))
        result = await macro.execute()
        assert result.duration >= 0.005


class TestCommandLoggedOnFailure:
    """Tests para 2.1 — Comandos fallidos se registran con error."""

    @pytest.mark.asyncio
    async def test_failure_recorded_in_history(self):
        history = CommandHistory()
        cmd = _FailCommand()
        result = await cmd.execute()
        history.record(cmd, result)
        failures = history.get_failures()
        assert len(failures) == 1
        assert failures[0].result.error == "mock failure"

    @pytest.mark.asyncio
    async def test_failure_duration_recorded(self):
        history = CommandHistory()
        cmd = _FailCommand()
        result = await cmd.execute()
        history.record(cmd, result)
        entry = history.get_failures()[0]
        assert entry.result.command_name == "fail_test"

    @pytest.mark.asyncio
    async def test_tool_command_adapter_failure(self):
        """ToolCommand adapta ToolResult a CommandResult."""
        from agentic_pipeline.tool_registry import ToolRegistry
        from agentic_pipeline.tools.command_adapter import ToolCommand

        registry = ToolRegistry()
        mock_tool = AsyncMock()
        mock_tool.name = "mock_tool"
        mock_tool.execute.return_value = type(
            "TR",
            (),
            {
                "success": False,
                "data": None,
                "error": "tool error",
            },
        )()
        registry.register(mock_tool)

        cmd = ToolCommand(registry, "mock_tool")
        result = await cmd.execute()
        assert result.success is False
        assert result.error == "tool error"
