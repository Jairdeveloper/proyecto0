"""WorldModel — Representacion interna del estado del entorno (N2.2a)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


@dataclass
class FileNode:
    path: str
    file_type: Literal["file", "directory"]
    hash: str | None = None
    created_by: str | None = None
    timestamp: str | None = None


@dataclass
class DecisionRecord:
    goal_id: str
    action: str
    rationale: str
    params: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


@dataclass
class WorldDelta:
    added: list[FileNode] = field(default_factory=list)
    modified: list[FileNode] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


class WorldModel:
    """Representacion interna del estado del entorno del agente."""

    def __init__(self):
        self.files: dict[str, FileNode] = {}
        self.decisions: list[DecisionRecord] = []
        self.goals: list[dict] = []
        self.constraints: list[dict] = []

    def initialize(self, scan_path: str = ".") -> None:
        """Escanea el directorio de trabajo y construye estado inicial."""
        base = Path(scan_path).resolve()
        for p in base.rglob("*"):
            if any(part.startswith(".") for part in p.parts):
                continue
            rel = str(p.relative_to(base))
            if p.is_dir():
                self.files[rel] = FileNode(path=rel, file_type="directory")
            else:
                content = p.read_bytes() if p.exists() else b""
                self.files[rel] = FileNode(
                    path=rel,
                    file_type="file",
                    hash=hashlib.md5(content).hexdigest(),
                )

    def apply_action(self, action: dict) -> WorldDelta:
        """Actualiza estado segun accion ejecutada. Retorna el cambio."""
        delta = WorldDelta()
        action_type = action.get("type", "")
        path = action.get("path", "")

        if action_type in ("create", "write"):
            node = FileNode(
                path=path,
                file_type="file",
                hash=action.get("hash"),
                created_by=action.get("goal_id"),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self.files[path] = node
            delta.added.append(node)

        elif action_type == "delete":
            if path in self.files:
                del self.files[path]
                delta.removed.append(path)

        elif action_type == "mkdir":
            node = FileNode(path=path, file_type="directory")
            self.files[path] = node
            delta.added.append(node)

        self.decisions.append(DecisionRecord(
            goal_id=action.get("goal_id", "unknown"),
            action=action_type,
            rationale=action.get("rationale", ""),
            params=action,
        ))
        return delta

    def query(self, question: str) -> str:
        """Responde preguntas sobre el estado."""
        q = question.lower()
        if "existe" in q or "exist" in q:
            for word in q.split():
                if word in self.files:
                    return f"Si, {word} existe"
                if word.endswith("?") and word[:-1] in self.files:
                    return f"Si, {word[:-1]} existe"
            return f"No encontrado: {question}"
        if "cuantos" in q or "list" in q:
            return f"Hay {len(self.files)} archivos/directorios conocidos"
        return f"No se como responder: {question}"

    def snapshot(self) -> dict:
        return {
            "files": list(self.files.keys()),
            "decisions": len(self.decisions),
            "goals": len(self.goals),
        }
