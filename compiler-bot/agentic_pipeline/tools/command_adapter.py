"""ToolCommand — adaptador Command para tools existentes."""

from __future__ import annotations

import logging
import time
from typing import Any

from agentic_pipeline.prompt_chain.command_base import Command, CommandResult
from agentic_pipeline.tool_registry import ToolRegistry, ToolResult

logger = logging.getLogger(__name__)


class ToolCommand(Command):
    """Wrapper Command que ejecuta una tool via ToolRegistry.

    Convierte cualquier tool registrada en un objeto Command usable
    por CommandHistory, MacroCommand, etc.
    """

    name = "tool"

    def __init__(
        self,
        registry: ToolRegistry,
        tool_name: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        self._registry = registry
        self._tool_name = tool_name
        self._params = params or {}
        self.name = f"tool:{tool_name}"

    async def execute(self) -> CommandResult:
        t0 = time.time()
        try:
            result: ToolResult = await self._registry.execute(
                self._tool_name,
                self._params,
            )
            duration = time.time() - t0
            if result.success:
                return CommandResult(
                    success=True,
                    data=result.data
                    if isinstance(result.data, dict)
                    else {"value": result.data},
                    duration=duration,
                    command_name=self.name,
                )
            return CommandResult(
                success=False,
                data={},
                error=result.error,
                duration=duration,
                command_name=self.name,
            )
        except Exception as exc:
            duration = time.time() - t0
            return CommandResult(
                success=False,
                error=str(exc),
                duration=duration,
                command_name=self.name,
            )
