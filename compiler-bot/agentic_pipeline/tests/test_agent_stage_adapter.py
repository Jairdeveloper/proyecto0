"""Tests for AgentStageAdapter."""

from agentic_pipeline.agents.agent_stage_adapter import AgentStageAdapter
from agentic_pipeline.agents.base_agent import Agent, SharedContext, Task, TaskResult
from agentic_pipeline.state_models import ActionPlan, Stage, StageContext


class _MockAgent(Agent):
    name = "mock_agent"
    role = "test"

    def __init__(self, should_fail: bool = False):
        super().__init__(SharedContext())
        self.should_fail = should_fail
        self.processed_tasks: list[Task] = []

    async def process(self, task: Task) -> TaskResult:
        self.processed_tasks.append(task)
        if self.should_fail:
            return TaskResult(task.id, False, error="mock failure")
        return TaskResult(
            task.id, True, data={"handled": True, "input": task.description}
        )


class TestAgentStageAdapter:
    def test_receive_mission_creates_task(self):
        ctx = StageContext(stage=Stage.INTENT, input_data="test input")
        agent = _MockAgent()
        adapter = AgentStageAdapter(ctx, agent)
        adapter.receive_mission({"key": "value"})
        assert adapter._task is not None
        assert adapter._task.agent == "mock_agent"

    def test_act_success(self):
        ctx = StageContext(stage=Stage.INTENT, input_data="test")
        agent = _MockAgent()
        adapter = AgentStageAdapter(ctx, agent)
        adapter.receive_mission("create module")
        output = adapter.act(ActionPlan(steps=[], strategy="test"))
        assert output.success is True
        assert output.output_data.get("handled") is True

    def test_act_failure(self):
        ctx = StageContext(stage=Stage.INTENT, input_data="test")
        agent = _MockAgent(should_fail=True)
        adapter = AgentStageAdapter(ctx, agent)
        adapter.receive_mission("create module")
        output = adapter.act(ActionPlan(steps=[], strategy="test"))
        assert output.success is False
        assert "mock failure" in (output.error or "")

    def test_act_no_task(self):
        ctx = StageContext(stage=Stage.INTENT, input_data="test")
        agent = _MockAgent()
        adapter = AgentStageAdapter(ctx, agent)
        output = adapter.act(ActionPlan(steps=[], strategy="test"))
        assert output.success is False
        assert "No task created" in (output.error or "")

    def test_adapter_stage_output_metrics(self):
        ctx = StageContext(stage=Stage.INTENT, input_data="test")
        agent = _MockAgent()
        adapter = AgentStageAdapter(ctx, agent)
        adapter.receive_mission("create module")
        output = adapter.act(ActionPlan(steps=[], strategy="test"))
        assert output.metrics is not None
        assert output.metrics.get("agent") == "mock_agent"

    def test_adapter_with_agent_instance(self):
        ctx = StageContext(stage=Stage.INTENT, input_data="test")
        agent = _MockAgent()
        adapter = AgentStageAdapter(ctx, agent, agent_name="custom_name")
        adapter.receive_mission("test")
        assert adapter._agent_name == "custom_name"
