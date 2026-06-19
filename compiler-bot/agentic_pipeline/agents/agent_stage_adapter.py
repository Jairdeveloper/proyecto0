"""AgentStageAdapter — wraps an Agent as a PipelineStage.

Allows executing agents inside the StateGraph of AgentOrchestrator.
act() delegates to agent.process(task) and maps TaskResult -> StageOutput.
"""

import asyncio

from agentic_pipeline.agents.base_agent import Agent, Task
from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.state_models import ActionPlan, StageContext, StageOutput


class AgentStageAdapter(PipelineStage):
    """Adapter: wraps an Agent as a PipelineStage.

    Usage:
        adapter = AgentStageAdapter(ctx, perception_agent)
        output = await adapter.execute(input_data)
    """

    name = "agent_adapter"

    def __init__(
        self,
        context: StageContext,
        agent: Agent,
        agent_name: str = "",
    ):
        super().__init__(context)
        self._agent = agent
        self._agent_name = agent_name or agent.name
        self._task: Task | None = None

    def receive_mission(self, input_data: object) -> None:
        params = {"input_data": input_data}
        if isinstance(input_data, dict):
            params.update(input_data)
        self._task = Task(
            id=f"{self._agent_name}_{id(self)}",
            description=str(input_data)[:200],
            agent=self._agent_name,
            params=params,
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        if not self._task:
            return StageOutput(
                stage=self.context.stage,
                output_data={},
                success=False,
                error="No task created in receive_mission",
            )
        result = asyncio.run(self._agent.process(self._task))
        return StageOutput(
            stage=self.context.stage,
            output_data=result.data if isinstance(result.data, dict) else {"result": result.data},
            success=result.success,
            error=result.error,
            metrics={"agent": self._agent_name, "task_id": self._task.id},
        )
