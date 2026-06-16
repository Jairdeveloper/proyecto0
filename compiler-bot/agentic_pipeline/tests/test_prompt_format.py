"""Tests for FORMAT prompt."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest

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

    @pytest.mark.asyncio
    async def test_format_summary_mentions_files(self):
        from agentic_pipeline.prompt_chain.prompts.format import format_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"summary": "Modulo pagos creado con 2 archivos.",'
                     '"files_created": ["modules/pagos/pagos.module.ts",'
                     '"modules/pagos/pagos.controller.ts"],'
                     '"warnings": [], "next_steps": ["Revisa los archivos"],'
                     '"success": true}',
            structured={
                "summary": "Modulo pagos creado con 2 archivos.",
                "files_created": ["modules/pagos/pagos.module.ts",
                                  "modules/pagos/pagos.controller.ts"],
                "warnings": [],
                "next_steps": ["Revisa los archivos"],
                "success": True,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await format_handler(
            original_request="crea modulo pagos",
            plan={"tasks": []},
            generated_files=[{"path": "modules/pagos/pagos.module.ts",
                              "type": "module"}],
            validation={"valid": True, "checks": []},
            llm=mock_llm,
        )
        assert "pagos" in result["summary"]
        assert len(result["files_created"]) == 2

    @pytest.mark.asyncio
    async def test_format_success_true(self):
        from agentic_pipeline.prompt_chain.prompts.format import format_handler

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
        result = await format_handler(
            original_request="test",
            plan={},
            generated_files=[],
            validation={"valid": True},
            llm=mock_llm,
        )
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_format_warnings_from_verify(self):
        from agentic_pipeline.prompt_chain.prompts.format import format_handler

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
        result = await format_handler(
            original_request="crea modulo",
            plan={},
            generated_files=[{"path": "test.ts", "type": "test"}],
            validation={"valid": True, "suggestions": ["Falta validacion"]},
            llm=mock_llm,
        )
        assert len(result["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_format_llm_fails_fallback(self):
        from agentic_pipeline.prompt_chain.prompts.format import format_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            success=False, error="LLM unavailable",
        )

        with patch(
            "agentic_pipeline.prompt_chain.prompts.format.execute_fallback",
        ) as mock_fb:
            mock_fb.return_value = {
                "summary": "Procesado.",
                "files_created": [],
                "warnings": [],
                "next_steps": ["Revisa los archivos generados"],
                "success": True,
            }
            result = await format_handler(
                original_request="test",
                plan={},
                generated_files=[],
                validation={},
                llm=mock_llm,
            )

        assert result["success"] is True
        mock_fb.assert_called_once()
