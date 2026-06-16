"""Tool: ask_user — Pregunta al usuario para obtener clarificacion."""

from __future__ import annotations

import asyncio

from ..tool_registry import Tool, ToolResult, Parameter


async def _get_input(prompt: str) -> str:
    """Lee input del usuario de forma asincrona."""
    return await asyncio.get_event_loop().run_in_executor(
        None, lambda: input(f"\n[AGENTE] {prompt}\n> "),
    )


class AskUserTool(Tool):
    name = "ask_user"
    description = "Pregunta al usuario para obtener clarificacion sobre una instruccion"
    parameters = [
        Parameter("question", "string", "Pregunta para el usuario"),
    ]

    async def execute(self, params: dict) -> ToolResult:
        question = params["question"]
        response = await _get_input(question)
        return ToolResult(
            success=True,
            data={"response": response, "question": question},
        )
