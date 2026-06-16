"""ExecutionAgent — ejecuta acciones con generate_handler (F4) + fallback ToolRegistry (N3.2c)."""

from __future__ import annotations

from agentic_pipeline.prompt_chain.llm_backend import LLMBackend

from ..tool_registry import ToolRegistry
from ..world_model import WorldModel
from .base_agent import Agent, SharedContext, Task, TaskResult


class ExecutionAgent(Agent):
    """Agente especializado en ejecutar acciones en el sistema.

    Si se provee ``llm``, usa ``generate_handler`` para acciones de
    generacion. Para acciones de archivo/comando usa ToolRegistry.
    """

    name = "execution_agent"
    role = "ejecutar acciones de generacion, lectura, escritura"

    def __init__(
        self,
        context: SharedContext,
        world: WorldModel | None = None,
        llm: LLMBackend | None = None,
    ):
        super().__init__(context)
        self.world = world or WorldModel()
        self._llm = llm
        self.tools = ToolRegistry.build_default()

    async def process(self, task: Task) -> TaskResult:
        action = task.params.get("action", "")
        path = task.params.get("path", "")
        content = task.params.get("content", "")

        if action == "generate" and self._llm is not None:
            result_data = await self._process_generate_with_prompt(task)
            if result_data is not None:
                self.world.apply_action({
                    "type": "generate",
                    "path": "",
                    "goal_id": task.id,
                    "rationale": task.description,
                })
                self.context.publish("execution_result", result_data)
                return TaskResult(task.id, True, data=result_data)

        return await self._process_with_tools(
            task, action, path, content,
        )

    async def _process_generate_with_prompt(
        self, task: Task,
    ) -> dict | None:
        try:
            from agentic_pipeline.prompt_chain.orchestrator import (
                _ensure_prompts_registered,
            )
            _ensure_prompts_registered()

            from agentic_pipeline.prompt_chain.prompts.generate import (
                generate_handler,
            )
            tasks_list = task.params.get("tasks", [])
            output = await generate_handler(
                tasks=tasks_list, llm=self._llm,
            )
            return {
                "files": output.get("files", []),
                "errors": output.get("errors", []),
            }
        except Exception:
            return None

    async def _process_with_tools(
        self, task: Task, action: str, path: str, content: str,
    ) -> TaskResult:
        if action == "generate":
            target = task.params.get("target", "nestjs")
            result = await self.tools.execute(
                "generate_code",
                {"target": target, "params": task.params},
            )
        elif action == "read_file":
            result = await self.tools.execute("read_file", {"path": path})
        elif action == "write_file":
            result = await self.tools.execute(
                "write_file", {"path": path, "content": content},
            )
        elif action == "run_command":
            cmd = task.params.get("command", "")
            result = await self.tools.execute(
                "run_command", {"command": cmd},
            )
        else:
            result = await self.tools.execute(
                "explain",
                {"message": f"Ejecutando: {task.description}"},
            )

        if result.success:
            self.world.apply_action({
                "type": action or "execute",
                "path": path,
                "goal_id": task.id,
                "rationale": task.description,
            })

        self.context.publish(
            "execution_result",
            result.data if result.success else result.error,
        )
        return TaskResult(
            task.id,
            success=result.success,
            data=result.data,
            error=result.error,
        )
