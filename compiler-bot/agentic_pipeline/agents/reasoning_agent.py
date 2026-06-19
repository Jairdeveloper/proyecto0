"""ReasoningAgent — descompone objetivos con plan_handler (F4) + fallback GoalTreePlanner (N3.2b)."""

from __future__ import annotations

from agentic_pipeline.agents.agent_mediator import AgentMessage, PerceptionResult, ReasoningResult
from agentic_pipeline.agents.base_agent import Agent, SharedContext, Task, TaskResult
from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend
from agentic_pipeline.world_model import WorldModel


class ReasoningAgent(Agent):
    """Agente especializado en razonamiento y planificacion."""

    name = "reasoning_agent"
    role = "descomponer objetivos en planes ejecutables"
    subscriptions = ["perception.completed"]

    def __init__(
        self,
        context: SharedContext,
        world: WorldModel | None = None,
        llm: LLMBackend | None = None,
    ):
        super().__init__(context)
        self.world = world or WorldModel()
        self._llm = llm
        self.planner = GoalTreePlanner()
        self._last_perception: PerceptionResult | None = None

    def on_message(self, msg: AgentMessage) -> None:
        if isinstance(msg.payload, PerceptionResult):
            self._last_perception = msg.payload
            if self.mediator:
                self.mediator.send(
                    AgentMessage(
                        sender=self.name,
                        topic="reasoning.completed",
                        payload=ReasoningResult(
                            goal_id=msg.correlation_id,
                            goal_description=msg.payload.raw,
                            subtasks=[],
                            verification_criteria=[],
                        ),
                        correlation_id=msg.correlation_id,
                    )
                )

    async def process(self, task: Task) -> TaskResult:
        perception = self.context.subscribe("perception_result") or {}
        text = perception.get("raw", task.description)
        intent_data = perception.get("intent", {})
        intent_name = intent_data.get("intent", "CREATE") if intent_data else "CREATE"

        if self._llm is not None:
            result_data = await self._process_with_prompt(
                text,
                perception,
                intent_name,
            )
            if result_data is not None:
                if self.mediator:
                    self.mediator.send(
                        AgentMessage(
                            sender=self.name,
                            topic="reasoning.completed",
                            payload=ReasoningResult(
                                goal_id=result_data.get("goal_id", task.id),
                                goal_description=result_data.get("goal_description", ""),
                                subtasks=result_data.get("subtasks", []),
                                verification_criteria=result_data.get("verification_criteria", []),
                            ),
                            correlation_id=task.id,
                        )
                    )
                else:
                    self.context.publish("reasoning_result", result_data)
                return TaskResult(task.id, True, data=result_data)

        return await self._process_rule_based(
            task,
            text,
            intent_name,
        )

    async def _process_with_prompt(
        self,
        text: str,
        perception: dict,
        intent_name: str,
    ) -> dict | None:
        try:
            self._ensure_prompts()
            from agentic_pipeline.prompt_chain.prompts.plan import (
                plan_handler,
            )

            output = await plan_handler(
                intent=intent_name,
                module=perception.get("module"),
                entity=perception.get("entity"),
                tech=perception.get("tech", []),
                features=perception.get("features", []),
                llm=self._llm,
            )
            return {
                "goal_id": "prompt_plan",
                "goal_description": (
                    f"Plan for {intent_name}: "
                    f"{perception.get('module') or perception.get('entity') or text}"
                ),
                "subtasks": [
                    {
                        "id": t.get("id", ""),
                        "description": t.get("type", ""),
                        "status": "pending",
                    }
                    for t in output.get("tasks", [])
                ],
                "verification_criteria": [
                    f"Verify {t.get('type', '')}" for t in output.get("tasks", [])
                ],
            }
        except Exception:
            return None

    def _ensure_prompts(self) -> None:
        from agentic_pipeline.prompt_chain.orchestrator import (
            _ensure_prompts_registered,
        )

        _ensure_prompts_registered()

    async def _process_rule_based(
        self,
        task: Task,
        text: str,
        intent_name: str,
    ) -> TaskResult:
        entities = task.params.get("entities", [])
        goal = self.planner.decompose(text, intent_name, entities, self.world)

        result = {
            "goal_id": goal.id,
            "goal_description": goal.description,
            "subtasks": [
                {"id": s.id, "description": s.description, "status": s.status}
                for s in goal.subtasks
            ],
            "verification_criteria": goal.verification_criteria,
        }

        if self.mediator:
            self.mediator.send(
                AgentMessage(
                    sender=self.name,
                    topic="reasoning.completed",
                    payload=ReasoningResult(
                        goal_id=goal.id,
                        goal_description=goal.description,
                        subtasks=result["subtasks"],
                        verification_criteria=result["verification_criteria"],
                    ),
                    correlation_id=task.id,
                )
            )
        else:
            self.context.publish("reasoning_result", result)
        return TaskResult(task.id, True, data=result)
