"""Command interface and implementations for the Command pattern.

Formalizes prompt handlers and pipeline stages as Command objects
that can be executed, logged, composed, and replayed.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Resultado de la ejecucion de un Command."""

    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    fallback_used: bool = False
    duration: float = 0.0
    command_name: str = ""


class Command(ABC):
    """Command abstracto. Cada comando encapsula una operacion."""

    name: str = ""

    @abstractmethod
    async def execute(self) -> CommandResult: ...


class MacroCommand(Command):
    """Compone multiples Command en uno solo. Ejecuta secuencialmente."""

    name = "macro"

    def __init__(self, commands: list[Command] | None = None) -> None:
        self._commands: list[Command] = commands or []

    def add(self, command: Command) -> MacroCommand:
        """Anade un comando al macro. Retorna self para fluent API."""
        self._commands.append(command)
        return self

    async def execute(self) -> CommandResult:
        """Ejecuta todos los comandos secuencialmente. Retorna el ultimo resultado."""
        last_result = CommandResult(success=True, data={})
        for cmd in self._commands:
            t0 = time.time()
            try:
                result = await cmd.execute()
                duration = time.time() - t0
                result.duration = duration
                last_result = result
                logger.info(
                    "Macro sub-command %s: success=%s (%.3fs)",
                    cmd.name,
                    result.success,
                    duration,
                )
                if not result.success:
                    break
            except Exception as exc:
                duration = time.time() - t0
                logger.error("Macro sub-command %s failed: %s", cmd.name, exc)
                last_result = CommandResult(
                    success=False,
                    data={},
                    error=str(exc),
                    command_name=cmd.name,
                    duration=duration,
                )
                break
        return last_result

    @property
    def commands(self) -> list[Command]:
        return list(self._commands)
