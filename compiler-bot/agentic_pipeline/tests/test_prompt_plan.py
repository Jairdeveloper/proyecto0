"""Tests for PLAN prompt."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest

from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry


class TestPlanPrompt:
    def setup_method(self) -> None:
        import agentic_pipeline.prompt_chain.prompts as _pkg
        _ = _pkg
        PromptRegistry.clear()
        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.plan",
        )
        importlib.reload(_mod)

    @pytest.mark.asyncio
    async def test_plan_create_module(self):
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"tasks": [{"id": "t1", "type": "scaffold_module",'
                     '"target": "pagos", "params": {"tech": "nestjs"},'
                     '"dependencies": []}],'
                     '"execution_order": ["t1"],'
                     '"complexity": "low", "estimated_files": 1}',
            structured={
                "tasks": [{"id": "t1", "type": "scaffold_module",
                           "target": "pagos", "params": {"tech": "nestjs"},
                           "dependencies": []}],
                "execution_order": ["t1"],
                "complexity": "low",
                "estimated_files": 1,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await plan_handler(
            intent="CREATE", module="pagos", tech=["nestjs"],
            llm=mock_llm,
        )
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["type"] == "scaffold_module"
        assert result["tasks"][0]["target"] == "pagos"

    @pytest.mark.asyncio
    async def test_plan_create_entity(self):
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"tasks": [{"id": "t1", "type": "create_entity",'
                     '"target": "User", "params": {},'
                     '"dependencies": []}],'
                     '"execution_order": ["t1"],'
                     '"complexity": "low", "estimated_files": 1}',
            structured={
                "tasks": [{"id": "t1", "type": "create_entity",
                           "target": "User", "params": {},
                           "dependencies": []}],
                "execution_order": ["t1"],
                "complexity": "low",
                "estimated_files": 1,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await plan_handler(
            intent="CREATE", entity="User", llm=mock_llm,
        )
        assert result["tasks"][0]["type"] == "create_entity"
        assert result["tasks"][0]["target"] == "User"

    @pytest.mark.asyncio
    async def test_plan_create_crud(self):
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"tasks": [{"id": "t1", "type": "scaffold_module",'
                     '"target": "productos", "params": {"tech": "nestjs"},'
                     '"dependencies": []},'
                     '{"id": "t2", "type": "generate_code",'
                     '"target": "productos", '
                     '"params": {"type": "controller"},'
                     '"dependencies": ["t1"]}],'
                     '"execution_order": ["t1", "t2"],'
                     '"complexity": "medium", "estimated_files": 2}',
            structured={
                "tasks": [
                    {"id": "t1", "type": "scaffold_module",
                     "target": "productos", "params": {"tech": "nestjs"},
                     "dependencies": []},
                    {"id": "t2", "type": "generate_code",
                     "target": "productos",
                     "params": {"type": "controller"},
                     "dependencies": ["t1"]},
                ],
                "execution_order": ["t1", "t2"],
                "complexity": "medium",
                "estimated_files": 2,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await plan_handler(
            intent="CREATE", module="productos",
            tech=["nestjs"], features=["crud"],
            llm=mock_llm,
        )
        assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_plan_no_tasks_read(self):
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"tasks": [], "execution_order": [],'
                     '"complexity": "low", "estimated_files": 0}',
            structured={
                "tasks": [],
                "execution_order": [],
                "complexity": "low",
                "estimated_files": 0,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await plan_handler(intent="READ", llm=mock_llm)
        assert result["tasks"] == []

    @pytest.mark.asyncio
    async def test_plan_dependencies_ordered(self):
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"tasks": [{"id": "t1", "type": "scaffold_module",'
                     '"target": "x", "params": {}, "dependencies": []},'
                     '{"id": "t2", "type": "generate_code",'
                     '"target": "x", "params": {}, "dependencies": ["t1"]}],'
                     '"execution_order": ["t1", "t2"],'
                     '"complexity": "low", "estimated_files": 2}',
            structured={
                "tasks": [
                    {"id": "t1", "type": "scaffold_module",
                     "target": "x", "params": {}, "dependencies": []},
                    {"id": "t2", "type": "generate_code",
                     "target": "x", "params": {}, "dependencies": ["t1"]},
                ],
                "execution_order": ["t1", "t2"],
                "complexity": "low",
                "estimated_files": 2,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await plan_handler(intent="CREATE", module="x", llm=mock_llm)
        order = result["execution_order"]
        assert order.index("t1") < order.index("t2")

    @pytest.mark.asyncio
    async def test_plan_llm_fails_fallback(self):
        from agentic_pipeline.prompt_chain.prompts.plan import plan_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            success=False, error="LLM unavailable",
        )

        with patch(
            "agentic_pipeline.prompt_chain.prompts.plan.execute_fallback",
        ) as mock_fb:
            mock_fb.return_value = {
                "tasks": [],
                "execution_order": [],
                "complexity": "low",
                "estimated_files": 0,
            }
            result = await plan_handler(
                intent="CREATE", module="test", llm=mock_llm,
            )

        assert result["execution_order"] == []
        mock_fb.assert_called_once()
