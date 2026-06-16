"""Tool: write_file — Escribe contenido en un archivo del sistema."""

from __future__ import annotations

from pathlib import Path

from ..tool_registry import Tool, ToolResult, Parameter


class WriteFileTool(Tool):
    name = "write_file"
    description = "Escribe contenido en un archivo del sistema de archivos"
    parameters = [
        Parameter("path", "string", "Ruta del archivo a escribir"),
        Parameter("content", "string", "Contenido a escribir en el archivo"),
    ]

    async def execute(self, params: dict) -> ToolResult:
        path = Path(params["path"])
        resolved = path.resolve()
        if ".." in path.parts:
            return ToolResult(success=False, error="Path traversal bloqueado")
        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            content = params["content"]
            resolved.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                data={
                    "path": str(resolved),
                    "bytes": len(content),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Error al escribir: {e}")
