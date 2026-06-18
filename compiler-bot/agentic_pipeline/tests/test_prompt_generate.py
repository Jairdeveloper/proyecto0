"""Tests for GENERATE prompt."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.handler_base import PromptRequest
from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry


class TestGeneratePrompt:
    def setup_method(self) -> None:
        import agentic_pipeline.prompt_chain.prompts as _pkg

        _ = _pkg
        PromptRegistry.clear()
        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.generate",
        )
        importlib.reload(_mod)

    def _make_ctx(self, plan_data: dict) -> ChainContext:
        ctx = ChainContext()
        ctx.set_output("preprocess", {"normalized": "", "domain": "backend"})
        ctx.set_output("intent", {"intent": "CREATE", "module": "test"})
        ctx.set_output("plan", plan_data)
        return ctx

    @pytest.mark.asyncio
    async def test_generate_module_files(self):
        from agentic_pipeline.prompt_chain.prompts.generate import (
            GenerateHandler,
        )

        tasks = [
            {
                "id": "t1",
                "type": "scaffold_module",
                "target": "pagos",
                "params": {"tech": "nestjs"},
            }
        ]
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"files": [{"path": "modules/pagos/pagos.module.ts",'
            '"content": "// module", "type": "module",'
            '"overwrite": false},'
            '{"path": "modules/pagos/pagos.controller.ts",'
            '"content": "// controller", "type": "controller",'
            '"overwrite": false}], "errors": []}',
            structured={
                "files": [
                    {
                        "path": "modules/pagos/pagos.module.ts",
                        "content": "// module",
                        "type": "module",
                        "overwrite": False,
                    },
                    {
                        "path": "modules/pagos/pagos.controller.ts",
                        "content": "// controller",
                        "type": "controller",
                        "overwrite": False,
                    },
                ],
                "errors": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = GenerateHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea modulo pagos")
        ctx = self._make_ctx({"tasks": tasks, "execution_order": ["t1"]})
        response = await handler.handle(request, ctx)
        result = response.output
        assert len(result["files"]) == 2
        paths = [f["path"] for f in result["files"]]
        assert any(".module.ts" in p for p in paths)
        assert any(".controller.ts" in p for p in paths)

    @pytest.mark.asyncio
    async def test_generate_entity_schema(self):
        from agentic_pipeline.prompt_chain.prompts.generate import (
            GenerateHandler,
        )

        tasks = [{"id": "t1", "type": "create_entity", "target": "User", "params": {}}]
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"files": [{"path": "prisma/schema.prisma",'
            '"content": "model User { id Int @id }",'
            '"type": "schema", "overwrite": false}],'
            '"errors": []}',
            structured={
                "files": [
                    {
                        "path": "prisma/schema.prisma",
                        "content": "model User { id Int @id }",
                        "type": "schema",
                        "overwrite": False,
                    }
                ],
                "errors": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = GenerateHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea entidad User")
        ctx = self._make_ctx({"tasks": tasks, "execution_order": ["t1"]})
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["files"][0]["type"] == "schema"
        assert "User" in result["files"][0]["content"]

    @pytest.mark.asyncio
    async def test_generate_parallel_tasks(self):
        from agentic_pipeline.prompt_chain.prompts.generate import (
            GenerateHandler,
        )

        tasks = [
            {"id": "t1", "type": "scaffold_module", "target": "a", "params": {}},
            {"id": "t2", "type": "scaffold_module", "target": "b", "params": {}},
        ]
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"files": [{"path": "modules/a/a.module.ts",'
            '"content": "// a", "type": "module",'
            '"overwrite": false},'
            '{"path": "modules/b/b.module.ts",'
            '"content": "// b", "type": "module",'
            '"overwrite": false}], "errors": []}',
            structured={
                "files": [
                    {
                        "path": "modules/a/a.module.ts",
                        "content": "// a",
                        "type": "module",
                        "overwrite": False,
                    },
                    {
                        "path": "modules/b/b.module.ts",
                        "content": "// b",
                        "type": "module",
                        "overwrite": False,
                    },
                ],
                "errors": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = GenerateHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea modulos a y b")
        ctx = self._make_ctx({"tasks": tasks, "execution_order": ["t1", "t2"]})
        response = await handler.handle(request, ctx)
        result = response.output
        assert len(result["files"]) == 2

    @pytest.mark.asyncio
    async def test_generate_no_overwrite(self):
        from agentic_pipeline.prompt_chain.prompts.generate import (
            GenerateHandler,
        )

        tasks = [
            {"id": "t1", "type": "scaffold_module", "target": "exists", "params": {}}
        ]
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"files": [{"path": "modules/exists/exists.module.ts",'
            '"content": "// existing", "type": "module",'
            '"overwrite": true}], "errors": []}',
            structured={
                "files": [
                    {
                        "path": "modules/exists/exists.module.ts",
                        "content": "// existing",
                        "type": "module",
                        "overwrite": True,
                    }
                ],
                "errors": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = GenerateHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea modulo exists")
        ctx = self._make_ctx({"tasks": tasks, "execution_order": ["t1"]})
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["files"][0]["overwrite"] is True

    @pytest.mark.asyncio
    async def test_generate_errors_reported(self):
        from agentic_pipeline.prompt_chain.prompts.generate import (
            GenerateHandler,
        )

        tasks = [{"id": "bad", "type": "unknown_type", "target": "x"}]
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"files": [], "errors": ["Unknown task type: unknown_type"]}',
            structured={
                "files": [],
                "errors": ["Unknown task type: unknown_type"],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = GenerateHandler(llm=mock_llm)
        request = PromptRequest(raw_input="tarea desconocida")
        ctx = self._make_ctx({"tasks": tasks, "execution_order": ["bad"]})
        response = await handler.handle(request, ctx)
        result = response.output
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_generate_llm_fails_fallback(self):
        from agentic_pipeline.prompt_chain.prompts.generate import (
            GenerateHandler,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            success=False,
            error="LLM unavailable",
        )

        with patch(
            "agentic_pipeline.prompt_chain.handler_base.execute_fallback",
        ) as mock_fb:
            mock_fb.return_value = {"files": [], "errors": []}
            handler = GenerateHandler(llm=mock_llm)
            request = PromptRequest(raw_input="genera algo")
            ctx = self._make_ctx({"tasks": [], "execution_order": []})
            response = await handler.handle(request, ctx)

        result = response.output
        assert result["files"] == []
        mock_fb.assert_called_once()
