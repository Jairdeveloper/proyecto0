"""ExecutionAgent — ejecuta acciones con generate_handler (F4) + fallback ToolRegistry (N3.2c)."""

from __future__ import annotations

from agentic_pipeline.agents.agent_mediator import AgentMessage, ExecutionResult
from agentic_pipeline.agents.base_agent import Agent, SharedContext, Task, TaskResult
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend
from agentic_pipeline.tool_registry import ToolRegistry
from agentic_pipeline.world_model import WorldModel


class ExecutionAgent(Agent):
    """Agente especializado en ejecutar acciones en el sistema."""

    name = "execution_agent"
    role = "ejecutar acciones de generacion, lectura, escritura"
    subscriptions = ["reasoning.completed"]

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

    def on_message(self, msg: AgentMessage) -> None:
        if self.mediator:
            self.mediator.send(
                AgentMessage(
                    sender=self.name,
                    topic="execution.completed",
                    payload=ExecutionResult(files=[], errors=[]),
                    correlation_id=msg.correlation_id,
                )
            )

    async def process(self, task: Task) -> TaskResult:
        action = task.params.get("action", "")
        path = task.params.get("path", "")
        content = task.params.get("content", "")

        if action == "generate" and self._llm is not None:
            result_data = await self._process_generate_with_prompt(task)
            if result_data is not None:
                self.world.apply_action(
                    {
                        "type": "generate",
                        "path": "",
                        "goal_id": task.id,
                        "rationale": task.description,
                    }
                )
                if self.mediator:
                    self.mediator.send(
                        AgentMessage(
                            sender=self.name,
                            topic="execution.completed",
                            payload=ExecutionResult(
                                files=result_data.get("files", []),
                                errors=result_data.get("errors", []),
                            ),
                            correlation_id=task.id,
                        )
                    )
                else:
                    self.context.publish("execution_result", result_data)
                return TaskResult(task.id, True, data=result_data)

        return await self._process_with_tools(
            task,
            action,
            path,
            content,
        )

    async def _process_generate_with_prompt(
        self,
        task: Task,
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
                tasks=tasks_list,
                llm=self._llm,
            )
            return {
                "files": output.get("files", []),
                "errors": output.get("errors", []),
            }
        except Exception:
            return None

    async def _process_with_tools(
        self,
        task: Task,
        action: str,
        path: str,
        content: str,
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
                "write_file",
                {"path": path, "content": content},
            )
        elif action == "run_command":
            cmd = task.params.get("command", "")
            result = await self.tools.execute(
                "run_command",
                {"command": cmd},
            )
        else:
            result = await self.tools.execute(
                "explain",
                {"message": f"Ejecutando: {task.description}"},
            )

        if result.success:
            self.world.apply_action(
                {
                    "type": action or "execute",
                    "path": path,
                    "goal_id": task.id,
                    "rationale": task.description,
                }
            )

        result_data = result.data if result.success else result.error
        if self.mediator:
            files_data = result_data if isinstance(result_data, list) else []
            self.mediator.send(
                AgentMessage(
                    sender=self.name,
                    topic="execution.completed",
                    payload=ExecutionResult(
                        files=files_data
                        if isinstance(files_data, list)
                        else [{"data": str(files_data)}],
                        errors=[] if result.success else [str(result.error)],
                    ),
                    correlation_id=task.id,
                )
            )
        else:
            self.context.publish("execution_result", result_data)
        return TaskResult(
            task.id,
            success=result.success,
            data=result_data,
            error=result.error,
        )
