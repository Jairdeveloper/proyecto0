"""SupervisorAgent — orquesta agentes especializados (N3.4) con ChainOrchestrator (F4)."""

from __future__ import annotations

from agentic_pipeline.prompt_chain.llm_backend import LLMBackend

from .agent_mediator import AgentMessage, ValidationResult
from .base_agent import Agent, SharedContext, Task, TaskResult


class SupervisorAgent(Agent):
    """Agente supervisor: coordina, delega y consolida."""

    name = "supervisor"
    role = "coordinar, delegar y consolidar"
    subscriptions = ["validation.completed", "task.failed"]

    def __init__(
        self,
        context: SharedContext,
        agents: dict[str, Agent],
        llm: LLMBackend | None = None,
    ):
        super().__init__(context)
        self.agents = agents
        self._llm = llm
        self._pending_results: dict[str, list[TaskResult]] = {}
        self._last_validation: ValidationResult | None = None

    def on_message(self, msg: AgentMessage) -> None:
        if isinstance(msg.payload, ValidationResult):
            self._last_validation = msg.payload

    async def process(self, task: Task) -> TaskResult:
        if self.mediator:
            return await self._process_with_mediator(task)
        if self._llm is not None:
            return await self._process_with_chain(task)
        return await self._process_with_agents(task)

    async def _process_with_mediator(self, task: Task) -> TaskResult:
        subtasks = self._decompose(task)
        results: dict[str, TaskResult] = {}

        for sub in subtasks:
            if sub.status == "skipped":
                continue
            agent = self.agents.get(sub.agent)
            if not agent:
                return TaskResult(task.id, False, error=f"Agent not found: {sub.agent}")
            self.mediator.send(
                AgentMessage(
                    sender=self.name,
                    topic=f"{sub.agent}.request",
                    payload={"description": sub.description, "params": sub.params},
                    correlation_id=sub.id,
                )
            )
            result = await agent.process(sub)
            results[sub.id] = result
            if not result.success:
                return TaskResult(task.id, False, error=result.error, data=results)

        return TaskResult(task.id, True, data=results)

    async def _process_with_chain(self, task: Task) -> TaskResult:
        try:
            from agentic_pipeline.prompt_chain.orchestrator import (
                ChainOrchestrator,
            )

            orch = ChainOrchestrator(llm=self._llm)
            result = await orch.run(task.description)
            success = result.get("success", False)
            return TaskResult(task.id, success, data=result)
        except Exception as exc:
            return TaskResult(task.id, False, error=f"Chain failed: {exc}")

    async def _process_with_agents(self, task: Task) -> TaskResult:
        subtasks = self._decompose(task)
        max_retries = task.params.get("max_retries", 1)

        for attempt in range(max_retries):
            results = {}
            for sub in subtasks:
                if sub.status == "skipped":
                    continue
                agent = self.agents.get(sub.agent)
                if not agent:
                    return TaskResult(
                        task.id, False, error=f"Agent not found: {sub.agent}"
                    )
                result = await agent.process(sub)
                results[sub.id] = result

                if not result.success:
                    if attempt < max_retries - 1:
                        subtasks = self._replan_failed(sub, subtasks)
                        break
                    return TaskResult(
                        task.id,
                        False,
                        error=result.error,
                        data=results,
                    )
            else:
                return TaskResult(task.id, True, data=results)

        return TaskResult(task.id, True, data={})

    def _decompose(self, task: Task) -> list[Task]:
        return [
            Task(
                "perceive",
                "Analizar entrada del usuario",
                "perception_agent",
                params={"text": task.description},
            ),
            Task(
                "reason",
                "Descomponer objetivo",
                "reasoning_agent",
                dependencies=["perceive"],
            ),
            Task(
                "execute",
                "Ejecutar acciones",
                "execution_agent",
                dependencies=["reason"],
            ),
            Task(
                "validate",
                "Verificar resultados",
                "validator_agent",
                dependencies=["execute"],
            ),
        ]

    def _replan_failed(
        self,
        failed_sub: Task,
        current_plan: list[Task],
    ) -> list[Task]:
        new_plan: list[Task] = []
        skip = False
        for sub in current_plan:
            if sub.id == failed_sub.id:
                new_plan.append(
                    Task(
                        f"{failed_sub.id}_retry",
                        f"Reintentar: {failed_sub.description}",
                        failed_sub.agent,
                        params=failed_sub.params,
                    )
                )
                skip = True
            elif skip and failed_sub.id in sub.dependencies:
                sub.status = "skipped"
                new_plan.append(sub)
            else:
                new_plan.append(sub)
        return new_plan
