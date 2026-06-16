"""Tests for multi-agent system (N3.5)."""

from __future__ import annotations

import pytest


class TestBaseAgent:
    def test_task_dataclass(self):
        from agentic_pipeline.agents.base_agent import Task
        t = Task(id="t1", description="test", agent="perception_agent")
        assert t.id == "t1"
        assert t.agent == "perception_agent"
        assert t.status == "pending"
        assert t.params == {}
        assert t.dependencies == []

    def test_task_result_dataclass(self):
        from agentic_pipeline.agents.base_agent import TaskResult
        r = TaskResult(task_id="t1", success=True, data={"key": "val"})
        assert r.task_id == "t1"
        assert r.success is True
        assert r.data["key"] == "val"
        assert r.error is None

    def test_shared_context_publish_subscribe(self):
        from agentic_pipeline.agents.base_agent import SharedContext
        ctx = SharedContext()
        ctx.publish("topic1", "data1")
        result = ctx.subscribe("topic1")
        assert result == "data1"

    def test_shared_context_get_snapshot(self):
        from agentic_pipeline.agents.base_agent import SharedContext
        ctx = SharedContext()
        ctx.publish("a", 1)
        ctx.publish("b", 2)
        snap = ctx.get_snapshot()
        assert snap == {"a": 1, "b": 2}

    def test_agent_abstract_cannot_instantiate(self):
        from agentic_pipeline.agents.base_agent import Agent, SharedContext
        with pytest.raises(TypeError):
            Agent(SharedContext())  # type: ignore

    def test_async_shared_context_inherits(self):
        from agentic_pipeline.agents.base_agent import AsyncSharedContext
        ctx = AsyncSharedContext()
        assert hasattr(ctx, "publish")
        assert hasattr(ctx, "subscribe")
        assert hasattr(ctx, "get_snapshot")


class TestPerceptionAgent:
    @pytest.mark.asyncio
    async def test_process_returns_task_result(self):
        from agentic_pipeline.agents.base_agent import SharedContext, Task
        from agentic_pipeline.agents.perception_agent import PerceptionAgent
        ctx = SharedContext()
        agent = PerceptionAgent(ctx)
        task = Task(id="p1", description="crea un modulo de pagos", agent="perception_agent",
                    params={"text": "crea un modulo de pagos"})
        result = await agent.process(task)
        assert result.success is True
        assert result.task_id == "p1"

    @pytest.mark.asyncio
    async def test_publishes_perception_result(self):
        from agentic_pipeline.agents.base_agent import SharedContext, Task
        from agentic_pipeline.agents.perception_agent import PerceptionAgent
        ctx = SharedContext()
        agent = PerceptionAgent(ctx)
        task = Task(id="p2", description="test", agent="perception_agent",
                    params={"text": "test"})
        await agent.process(task)
        result = ctx.subscribe("perception_result")
        assert result is not None
        assert "raw" in result


class TestReasoningAgent:
    @pytest.mark.asyncio
    async def test_process_returns_goal(self):
        from agentic_pipeline.agents.base_agent import SharedContext, Task
        from agentic_pipeline.agents.reasoning_agent import ReasoningAgent
        from agentic_pipeline.world_model import WorldModel
        ctx = SharedContext()
        ctx.publish("perception_result", {"raw": "crea modulo pagos", "intent": {"intent": "CREATE"}})
        agent = ReasoningAgent(ctx, WorldModel())
        task = Task(id="r1", description="crea modulo pagos", agent="reasoning_agent")
        result = await agent.process(task)
        assert result.success is True
        assert "goal_id" in result.data
        assert "subtasks" in result.data

    @pytest.mark.asyncio
    async def test_publishes_reasoning_result(self):
        from agentic_pipeline.agents.base_agent import SharedContext, Task
        from agentic_pipeline.agents.reasoning_agent import ReasoningAgent
        from agentic_pipeline.world_model import WorldModel
        ctx = SharedContext()
        ctx.publish("perception_result", {"raw": "crea modulo", "intent": {"intent": "CREATE"}})
        agent = ReasoningAgent(ctx, WorldModel())
        task = Task(id="r2", description="crea modulo", agent="reasoning_agent")
        await agent.process(task)
        result = ctx.subscribe("reasoning_result")
        assert result is not None
        assert "subtasks" in result


class TestExecutionAgent:
    @pytest.mark.asyncio
    async def test_process_explain_action(self):
        from agentic_pipeline.agents.base_agent import SharedContext, Task
        from agentic_pipeline.agents.execution_agent import ExecutionAgent
        from agentic_pipeline.world_model import WorldModel
        ctx = SharedContext()
        agent = ExecutionAgent(ctx, WorldModel())
        task = Task(id="e1", description="explica algo", agent="execution_agent",
                    params={"action": "explain"})
        result = await agent.process(task)
        assert result.success is True


class TestValidatorAgent:
    @pytest.mark.asyncio
    async def test_process_validates_criteria(self):
        from agentic_pipeline.agents.base_agent import SharedContext, Task
        from agentic_pipeline.agents.validator_agent import ValidatorAgent
        from agentic_pipeline.world_model import WorldModel
        ctx = SharedContext()
        ctx.publish("reasoning_result", {
            "verification_criteria": [],
        })
        ctx.publish("execution_result", {})
        agent = ValidatorAgent(ctx, WorldModel())
        task = Task(id="v1", description="validar", agent="validator_agent",
                    params={"verification_criteria": []})
        result = await agent.process(task)
        assert result.success is True
        assert "criteria_checks" in result.data


class TestSupervisorAgent:
    @pytest.mark.asyncio
    async def test_decomposes_into_subtasks(self):
        from agentic_pipeline.agents.base_agent import SharedContext, Task
        from agentic_pipeline.agents.supervisor_agent import SupervisorAgent
        ctx = SharedContext()
        agent = SupervisorAgent(ctx, {})
        subtasks = agent._decompose(Task("t", "test", "supervisor"))
        assert len(subtasks) >= 3
        names = [s.agent for s in subtasks]
        assert "perception_agent" in names
        assert "reasoning_agent" in names
        assert "execution_agent" in names
        assert "validator_agent" in names

    @pytest.mark.asyncio
    async def test_full_flow_with_mock_agents(self):
        from agentic_pipeline.agents.base_agent import (
            Agent, SharedContext, Task, TaskResult,
        )
        from agentic_pipeline.agents.supervisor_agent import SupervisorAgent

        class MockSuccessAgent(Agent):
            name = "mock"
            role = "test"

            async def process(self, task: Task) -> TaskResult:
                return TaskResult(task_id=task.id, success=True, data={})

        ctx = SharedContext()
        agents = {
            "perception_agent": MockSuccessAgent(ctx),
            "reasoning_agent": MockSuccessAgent(ctx),
            "execution_agent": MockSuccessAgent(ctx),
            "validator_agent": MockSuccessAgent(ctx),
        }
        supervisor = SupervisorAgent(ctx, agents)
        result = await supervisor.process(Task("t", "test", "supervisor"))
        assert result.success is True
        assert "perceive" in result.data
        assert "reason" in result.data
        assert "execute" in result.data
        assert "validate" in result.data

    @pytest.mark.asyncio
    async def test_replan_on_failure(self):
        from agentic_pipeline.agents.base_agent import (
            Agent, SharedContext, Task, TaskResult,
        )
        from agentic_pipeline.agents.supervisor_agent import SupervisorAgent

        class FailOnceAgent(Agent):
            name = "fail_once"
            role = "test"
            call_count = 0

            async def process(self, task: Task) -> TaskResult:
                self.call_count += 1
                if self.call_count == 1:
                    return TaskResult(task_id=task.id, success=False, error="fail")
                return TaskResult(task_id=task.id, success=True, data={})

        class AlwaysSuccessAgent(Agent):
            name = "always_ok"
            role = "test"

            async def process(self, task: Task) -> TaskResult:
                return TaskResult(task_id=task.id, success=True, data={})

        ctx = SharedContext()
        fail_agent = FailOnceAgent(ctx)
        agents = {
            "perception_agent": fail_agent,
            "reasoning_agent": AlwaysSuccessAgent(ctx),
            "execution_agent": AlwaysSuccessAgent(ctx),
            "validator_agent": AlwaysSuccessAgent(ctx),
        }
        supervisor = SupervisorAgent(ctx, agents)
        result = await supervisor.process(
            Task("t", "test", "supervisor", params={"max_retries": 2}),
        )
        assert result.success is True
