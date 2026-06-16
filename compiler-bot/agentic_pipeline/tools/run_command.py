"""Tool: run_command — Ejecuta un comando del sistema."""

from __future__ import annotations

import asyncio

from ..tool_registry import Tool, ToolResult, Parameter


class RunCommandTool(Tool):
    name = "run_command"
    description = "Ejecuta un comando del sistema y retorna stdout/stderr"
    parameters = [
        Parameter("command", "string", "Comando shell a ejecutar"),
    ]

    async def execute(self, params: dict) -> ToolResult:
        command = params["command"]
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30,
            )
            return ToolResult(
                success=proc.returncode == 0,
                data={
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                    "returncode": proc.returncode,
                },
            )
        except asyncio.TimeoutError:
            return ToolResult(success=False, error="Comando excedio el timeout de 30s")
        except FileNotFoundError:
            return ToolResult(success=False, error=f"Comando no encontrado: {command}")
        except Exception as e:
            return ToolResult(success=False, error=f"Error al ejecutar: {e}")
