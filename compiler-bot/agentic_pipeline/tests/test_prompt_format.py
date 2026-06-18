"""Tests for FORMAT prompt."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.handler_base import PromptRequest
from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry


class TestFormatPrompt:
    def setup_method(self) -> None:
        import agentic_pipeline.prompt_chain.prompts as _pkg

        _ = _pkg
        PromptRegistry.clear()
        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.format",
        )
        importlib.reload(_mod)

    def _make_ctx(
        self,
        plan: dict,
        files: list[dict],
        validation: dict,
    ) -> ChainContext:
        ctx = ChainContext()
        ctx.set_output("preprocess", {"normalized": "", "domain": "backend"})
        ctx.set_output("intent", {"intent": "CREATE"})
        ctx.set_output("plan", plan)
        ctx.set_output("generate", {"files": files, "errors": []})
        ctx.set_output("verify", validation)
        return ctx

    @pytest.mark.asyncio
    async def test_format_summary_mentions_files(self):
        from agentic_pipeline.prompt_chain.prompts.format import FormatHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"summary": "Modulo pagos creado con 2 archivos.",'
            '"files_created": ["modules/pagos/pagos.module.ts",'
            '"modules/pagos/pagos.controller.ts"],'
            '"warnings": [], "next_steps": ["Revisa los archivos"],'
            '"success": true}',
            structured={
                "summary": "Modulo pagos creado con 2 archivos.",
                "files_created": [
                    "modules/pagos/pagos.module.ts",
                    "modules/pagos/pagos.controller.ts",
                ],
                "warnings": [],
                "next_steps": ["Revisa los archivos"],
                "success": True,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = FormatHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea modulo pagos")
        ctx = self._make_ctx(
            plan={"tasks": [], "execution_order": []},
            files=[{"path": "modules/pagos/pagos.module.ts", "type": "module"}],
            validation={
                "valid": True,
                "checks": [],
                "should_retry": False,
                "suggestions": [],
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert "pagos" in result["summary"]
        assert len(result["files_created"]) == 2

    @pytest.mark.asyncio
    async def test_format_success_true(self):
        from agentic_pipeline.prompt_chain.prompts.format import FormatHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"summary": "Todo correcto.", "files_created": [],'
            '"warnings": [], "next_steps": [], "success": true}',
            structured={
                "summary": "Todo correcto.",
                "files_created": [],
                "warnings": [],
                "next_steps": [],
                "success": True,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = FormatHandler(llm=mock_llm)
        request = PromptRequest(raw_input="test")
        ctx = self._make_ctx(
            plan={},
            files=[],
            validation={
                "valid": True,
                "checks": [],
                "should_retry": False,
                "suggestions": [],
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_format_warnings_from_verify(self):
        from agentic_pipeline.prompt_chain.prompts.format import FormatHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"summary": "Creado con advertencias.",'
            '"files_created": ["test.ts"],'
            '"warnings": ["Falta validacion de input"],'
            '"next_steps": ["Anade validacion"],'
            '"success": true}',
            structured={
                "summary": "Creado con advertencias.",
                "files_created": ["test.ts"],
                "warnings": ["Falta validacion de input"],
                "next_steps": ["Anade validacion"],
                "success": True,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = FormatHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea modulo")
        ctx = self._make_ctx(
            plan={},
            files=[{"path": "test.ts", "type": "test"}],
            validation={
                "valid": True,
                "checks": [],
                "should_retry": False,
                "suggestions": ["Falta validacion"],
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert len(result["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_format_llm_fails_fallback(self):
        from agentic_pipeline.prompt_chain.prompts.format import FormatHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            success=False,
            error="LLM unavailable",
        )

        with patch(
            "agentic_pipeline.prompt_chain.handler_base.execute_fallback",
        ) as mock_fb:
            mock_fb.return_value = {
                "summary": "Procesado.",
                "files_created": [],
                "warnings": [],
                "next_steps": ["Revisa los archivos generados"],
                "success": True,
            }
            handler = FormatHandler(llm=mock_llm)
            request = PromptRequest(raw_input="test")
            ctx = self._make_ctx(
                plan={},
                files=[],
                validation={
                    "valid": True,
                    "checks": [],
                    "should_retry": False,
                    "suggestions": [],
                },
            )
            response = await handler.handle(request, ctx)

        result = response.output
        assert result["success"] is True
        mock_fb.assert_called_once()
