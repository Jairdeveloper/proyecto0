"""ConversationalMemory — Memoria persistente del agente. Port de memory.sh."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ConversationalMemory:
    """Memoria persistente del agente.
    
    Almacena historial de conversaciones, contexto y sesiones en archivos JSON.
    Port del patron utilizado en agent-robot/memory.sh.
    """

    def __init__(self, storage_dir: str = ".recpl_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._mem_file = self.storage_dir / "agent_memory.json"
        self.current_session = self._load_or_create()

    def _load_or_create(self) -> dict:
        if self._mem_file.exists():
            return json.loads(self._mem_file.read_text(encoding="utf-8"))
        return {"historial": [], "contexto": {}, "sesiones": []}

    def _save(self) -> None:
        self._mem_file.write_text(
            json.dumps(self.current_session, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def save_context(self, key: str, value: Any) -> None:
        """Guarda un valor en el contexto de la sesion actual."""
        self.current_session["contexto"][key] = value
        self._save()

    def get_context(self, key: str) -> Any:
        """Recupera un valor del contexto de la sesion actual."""
        return self.current_session["contexto"].get(key)

    def add_history(self, instruction: str, response: str) -> None:
        """Agrega una entrada al historial."""
        self.current_session["historial"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instruction": instruction,
            "response": response,
        })
        self._save()

    def get_recent(self, limit: int = 5) -> list[dict]:
        """Retorna las ultimas N entradas del historial."""
        return self.current_session["historial"][-limit:]

    def list_sessions(self) -> list[str]:
        """Lista las sesiones disponibles en el directorio de memoria."""
        pattern = self.storage_dir.glob("agent_memory_*.json")
        return sorted(p.name for p in pattern)

    def set_session(self, name: str) -> None:
        """Cambia a una sesion especifica."""
        self._mem_file = self.storage_dir / f"agent_memory_{name}.json"
        self.current_session = self._load_or_create()

    def export(self) -> str:
        """Exporta toda la memoria como JSON legible."""
        return json.dumps(self.current_session, indent=2, ensure_ascii=False)
