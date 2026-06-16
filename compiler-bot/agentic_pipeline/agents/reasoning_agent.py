"""ReasoningAgent — descompone objetivos con GoalTreePlanner (N3.2b)."""

from __future__ import annotations

from ..nodes.reasoning_engine import GoalTreePlanner
from ..world_model import WorldModel
from .base_agent import Agent, SharedContext, Task, TaskResult


class ReasoningAgent(Agent):
    """Agente especializado en razonamiento y planificacion."""

    name = "reasoning_agent"
    role = "descomponer objetivos en planes ejecutables"

    def __init__(self, context: SharedContext, world: WorldModel | None = None):
        super().__init__(context)
        self.world = world or WorldModel()
        self.planner = GoalTreePlanner()

    async def process(self, task: Task) -> TaskResult:
        perception = self.context.subscribe("perception_result") or {}
        text = perception.get("raw", task.description)
        intent_data = perception.get("intent", {})
        intent_name = intent_data.get("intent", "CREATE") if intent_data else "CREATE"

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

        self.context.publish("reasoning_result", result)
        return TaskResult(task_id=task.id, success=True, data=result)
