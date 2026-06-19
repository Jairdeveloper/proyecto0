"""AgentLoop — Bucle principal del agente. Port de recpl.sh y agent.sh."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from agentic_pipeline.memory import ConversationalMemory
from agentic_pipeline.orchestrator import AgentOrchestrator
from agentic_pipeline.tool_registry import ToolRegistry
from agentic_pipeline.tools.ask_user import AskUserTool
from agentic_pipeline.tools.explain import ExplainTool
from agentic_pipeline.tools.generate_code import GenerateCodeTool
from agentic_pipeline.tools.read_file import ReadFileTool
from agentic_pipeline.tools.run_command import RunCommandTool
from agentic_pipeline.tools.search_code import SearchCodeTool
from agentic_pipeline.tools.write_file import WriteFileTool


@dataclass
class AgentOutput:
    status: Literal[
        "completed",
        "needs_clarification",
        "action_executed",
        "max_iterations_reached",
        "error",
    ]
    data: dict = field(default_factory=dict)
    message: str = ""
    iterations: int = 0


def _build_default_tool_registry() -> ToolRegistry:
    """Construye un ToolRegistry con todas las herramientas por defecto."""
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(RunCommandTool())
    registry.register(SearchCodeTool())
    registry.register(GenerateCodeTool())
    registry.register(AskUserTool())
    registry.register(ExplainTool())
    return registry


class AgentLoop:
    """Bucle principal del agente: percibe → razona → ejecuta → observa.

    Port del patron utilizado en:
    - compiler-bot/recpl.sh (interactive_mode, command_mode, batch_mode)
    - compiler-bot/agent-robot/agent.sh (classify → execute → respond)
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        tools: ToolRegistry | None = None,
        memory: ConversationalMemory | None = None,
        max_iterations: int = 5,
        interactive: bool = False,
    ):
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.tools = tools or _build_default_tool_registry()
        self.memory = memory or ConversationalMemory()
        self.max_iterations = max_iterations
        self.interactive = interactive

    async def run(self, prompt: str) -> AgentOutput:
        """Ejecuta el prompt a traves del pipeline con loop agente."""
        iteration = 0

        while iteration < self.max_iterations:
            output = await self.orchestrator.run(prompt)

            if output.get("success", False):
                self.memory.add_history(prompt, json.dumps(output, default=str))
                return AgentOutput(
                    status="completed",
                    data=output,
                    iterations=iteration + 1,
                )

            error = output.get("output", {}).get("error")
            if error:
                if self.interactive:
                    result = await self.tools.execute(
                        "ask_user",
                        {"question": f"Encontre un problema: {error}. Como procedo?"},
                    )
                    if result.success:
                        prompt = result.data["response"]
                    iteration += 1
                    continue

                return AgentOutput(
                    status="needs_clarification",
                    message=error,
                    iterations=iteration + 1,
                )

            if not output.get("success", True):
                observation = self._observe(output)
                if observation.get("success"):
                    self.memory.add_history(prompt, json.dumps(output, default=str))
                    return AgentOutput(
                        status="completed",
                        data=output,
                        iterations=iteration + 1,
                    )
                prompt = f"corrige: {observation.get('error', 'error desconocido')}"
                iteration += 1

        return AgentOutput(
            status="max_iterations_reached",
            message=f"No se completo en {self.max_iterations} iteraciones",
            iterations=self.max_iterations,
        )

    def _observe(self, output: dict) -> dict:
        """Observa el resultado de una accion ejecutada y retorna evaluacion."""
        out_data = output.get("output", {})
        if isinstance(out_data, dict):
            files = out_data.get("generated_files", [])
            errors = out_data.get("errors", [])
            return {
                "success": len(errors) == 0,
                "files_created": files,
                "error": "; ".join(errors) if errors else None,
            }
        return {"success": True, "files_created": [], "error": None}

    async def run_interactive(self) -> None:
        """Modo interactivo: loop REPL como recpl.sh interactive_mode()."""
        print("RECPL Agent v2.0 — Escribe 'quit' para salir.")
        while True:
            try:
                inp = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if inp.lower() in ("quit", "salir", "exit", "q"):
                break
            if not inp.strip():
                continue

            result = await self.run(inp)
            if result.status == "completed":
                print(json.dumps(result.data, indent=2, default=str))
            else:
                print(f"[{result.status}] {result.message}")

    def list_tools(self) -> list[dict]:
        """Lista las herramientas disponibles en el registro."""
        return self.tools.list_available()
