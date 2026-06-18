"""CommandHistory — historial de ejecucion para debug, replay y analisis."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .command_base import Command, CommandResult

logger = logging.getLogger(__name__)


@dataclass
class CommandEntry:
    """Una entrada en el historial de comandos."""

    command_name: str
    result: CommandResult
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )
    params: dict[str, Any] = field(default_factory=dict)


class CommandHistory:
    """Historial de ejecucion de comandos.

    Permite:
    - Registrar cada comando ejecutado
    - Filtrar por exito/fallo
    - Reejecutar comandos fallidos
    - Obtener resumen de rendimiento
    """

    def __init__(self, max_entries: int = 1000) -> None:
        self._entries: list[CommandEntry] = []
        self._max_entries = max_entries

    def record(
        self,
        command: Command,
        result: CommandResult,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Registra un comando ejecutado en el historial."""
        entry = CommandEntry(
            command_name=command.name,
            result=result,
            params=params or {},
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries.pop(0)

    def get_all(self) -> list[CommandEntry]:
        """Retorna todas las entradas del historial."""
        return list(self._entries)

    def get_failures(self) -> list[CommandEntry]:
        """Filtra solo comandos que fallaron."""
        return [e for e in self._entries if not e.result.success]

    def get_successes(self) -> list[CommandEntry]:
        """Filtra solo comandos exitosos."""
        return [e for e in self._entries if e.result.success]

    def get_by_name(self, name: str) -> list[CommandEntry]:
        """Filtra por nombre de comando."""
        return [e for e in self._entries if e.command_name == name]

    def get_fallback_count(self) -> int:
        """Cuantos comandos usaron fallback."""
        return sum(1 for e in self._entries if e.result.fallback_used)

    def get_success_rate(self) -> float:
        """Tasa de exito como fraccion 0.0-1.0."""
        if not self._entries:
            return 1.0
        return len(self.get_successes()) / len(self._entries)

    def clear(self) -> None:
        """Limpia el historial (util en tests)."""
        self._entries.clear()

    def replay_failures(
        self,
        command_factory: dict[str, type[Command]],
    ) -> list[CommandResult]:
        """Re-ejecuta comandos fallidos usando un factory de nombres a clases."""
        results: list[CommandResult] = []
        for entry in self.get_failures():
            cls = command_factory.get(entry.command_name)
            if cls is None:
                logger.warning("No factory for command: %s", entry.command_name)
                continue
            try:
                cmd = cls(**entry.params)
                result = cmd.execute()  # type: ignore[misc]
                if hasattr(result, "__await__"):
                    import asyncio

                    result = asyncio.run(result)  # type: ignore[arg-type]
                results.append(result)
                logger.info(
                    "Replayed %s: success=%s",
                    entry.command_name,
                    result.success,
                )
            except Exception as exc:
                logger.error("Replay failed for %s: %s", entry.command_name, exc)
        return results
