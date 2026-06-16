"""ExecutionAgent — ejecuta acciones usando ToolRegistry (N3.2c)."""

from __future__ import annotations

from ..tool_registry import ToolRegistry
from ..world_model import WorldModel
from .base_agent import Agent, SharedContext, Task, TaskResult


class ExecutionAgent(Agent):
    """Agente especializado en ejecutar acciones en el sistema."""

    name = "execution_agent"
    role = "ejecutar acciones de generacion, lectura, escritura"

    def __init__(self, context: SharedContext, world: WorldModel | None = None):
        super().__init__(context)
        self.world = world or WorldModel()
        self.tools = ToolRegistry.build_default()

    async def process(self, task: Task) -> TaskResult:
        action = task.params.get("action", "")
        path = task.params.get("path", "")
        content = task.params.get("content", "")

        if action == "generate":
            target = task.params.get("target", "nestjs")
            result = await self.tools.execute(
                "generate_code",
                {"target": target, "params": task.params},
            )
        elif action == "read_file":
            result = await self.tools.execute("read_file", {"path": path})
        elif action == "write_file":
            result = await self.tools.execute("write_file",
                                              {"path": path, "content": content})
        elif action == "run_command":
            cmd = task.params.get("command", "")
            result = await self.tools.execute("run_command", {"command": cmd})
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

        self.context.publish("execution_result", result.data if result.success else result.error)
        return TaskResult(
            task_id=task.id,
            success=result.success,
            data=result.data,
            error=result.error,
        )
