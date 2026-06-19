"""Tool: read_file — Lee el contenido de un archivo del sistema."""

from __future__ import annotations

from pathlib import Path

from agentic_pipeline.tool_registry import Parameter, Tool, ToolResult


class ReadFileTool(Tool):
    name = "read_file"
    description = "Lee el contenido de un archivo del sistema de archivos"
    parameters = [
        Parameter("path", "string", "Ruta del archivo a leer"),
    ]

    async def execute(self, params: dict) -> ToolResult:
        path = Path(params["path"])
        if not path.exists():
            return ToolResult(success=False, error=f"Archivo no encontrado: {path}")
        if not path.is_file():
            return ToolResult(success=False, error=f"No es un archivo: {path}")
        try:
            content = path.read_text(encoding="utf-8")
            return ToolResult(
                success=True,
                data={"content": content, "size": len(content), "path": str(path)},
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Error al leer: {e}")
