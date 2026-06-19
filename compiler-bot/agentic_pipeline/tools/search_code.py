"""Tool: search_code — Busca texto en el codigo fuente."""

from __future__ import annotations

import subprocess

from agentic_pipeline.tool_registry import Parameter, Tool, ToolResult


class SearchCodeTool(Tool):
    name = "search_code"
    description = "Busca un patron de texto en los archivos del proyecto"
    parameters = [
        Parameter("pattern", "string", "Patron de busqueda (regex)"),
        Parameter("path", "string", "Ruta donde buscar (opcional)", required=False),
    ]

    async def execute(self, params: dict) -> ToolResult:
        pattern = params["pattern"]
        search_path = params.get("path", ".")
        try:
            result = subprocess.run(
                ["rg", "-n", pattern, search_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except FileNotFoundError:
            try:
                result = subprocess.run(
                    ["grep", "-rn", pattern, search_path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except FileNotFoundError:
                return ToolResult(success=False, error="ni rg ni grep estan instalados")
        except Exception as e:
            return ToolResult(success=False, error=f"Error en busqueda: {e}")

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
            return ToolResult(
                success=True,
                data={"matches": lines, "count": len(lines)},
            )
        return ToolResult(
            success=True,
            data={"matches": [], "count": 0},
        )
