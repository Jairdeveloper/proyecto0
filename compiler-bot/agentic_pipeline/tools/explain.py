"""Tool: explain — Explica un concepto o responde textualmente al usuario."""

from __future__ import annotations

from agentic_pipeline.tool_registry import Parameter, Tool, ToolResult


class ExplainTool(Tool):
    name = "explain"
    description = "Responde textualmente al usuario con una explicacion"
    parameters = [
        Parameter("message", "string", "Mensaje a mostrar al usuario"),
    ]

    async def execute(self, params: dict) -> ToolResult:
        return ToolResult(
            success=True,
            data={"message": params["message"]},
        )
