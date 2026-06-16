"""Tests for VERIFY prompt."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest

from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry


class TestVerifyPrompt:
    def setup_method(self) -> None:
        import agentic_pipeline.prompt_chain.prompts as _pkg
        _ = _pkg
        PromptRegistry.clear()
        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.verify",
        )
        importlib.reload(_mod)

    @pytest.mark.asyncio
    async def test_verify_valid_files(self):
        from agentic_pipeline.prompt_chain.prompts.verify import verify_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"valid": true, "checks": [{"check": "estructura",'
                     '"passed": true, "detail": ""}],'
                     '"should_retry": false, "suggestions": []}',
            structured={
                "valid": True,
                "checks": [{"check": "estructura", "passed": True, "detail": ""}],
                "should_retry": False,
                "suggestions": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await verify_handler(
            requirements={"intent": "CREATE", "module": "pagos"},
            files=[{"path": "test.ts", "content": "// ok"}],
            llm=mock_llm,
        )
        assert result["valid"] is True
        assert result["should_retry"] is False

    @pytest.mark.asyncio
    async def test_verify_missing_imports(self):
        from agentic_pipeline.prompt_chain.prompts.verify import verify_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"valid": false, "checks": [{"check": "imports",'
                     '"passed": false, "detail": "Falta import Injectable"}],'
                     '"should_retry": true, "suggestions": ["Anade Injectable"]}',
            structured={
                "valid": False,
                "checks": [{"check": "imports", "passed": False,
                            "detail": "Falta import Injectable"}],
                "should_retry": True,
                "suggestions": ["Anade Injectable"],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await verify_handler(
            requirements={"intent": "CREATE"},
            files=[{"path": "test.ts", "content": "// no import"}],
            llm=mock_llm,
        )
        assert result["valid"] is False
        assert result["should_retry"] is True

    @pytest.mark.asyncio
    async def test_verify_should_retry(self):
        from agentic_pipeline.prompt_chain.prompts.verify import verify_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"valid": false, "checks": [{"check": "estructura",'
                     '"passed": false, "detail": "Archivo no existe"}],'
                     '"should_retry": true, "suggestions": ["Regenerar archivo"]}',
            structured={
                "valid": False,
                "checks": [{"check": "estructura", "passed": False,
                            "detail": "Archivo no existe"}],
                "should_retry": True,
                "suggestions": ["Regenerar archivo"],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await verify_handler(
            requirements={"intent": "CREATE"},
            files=[{"path": "missing.ts", "content": ""}],
            llm=mock_llm,
        )
        assert result["should_retry"] is True

    @pytest.mark.asyncio
    async def test_verify_suggestions(self):
        from agentic_pipeline.prompt_chain.prompts.verify import verify_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"valid": true, "checks": [{"check": "naming",'
                     '"passed": true, "detail": ""}],'
                     '"should_retry": false,'
                     '"suggestions": ["Considera usar DTOs"]}',
            structured={
                "valid": True,
                "checks": [{"check": "naming", "passed": True, "detail": ""}],
                "should_retry": False,
                "suggestions": ["Considera usar DTOs"],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await verify_handler(
            requirements={"intent": "CREATE"},
            files=[{"path": "ok.ts", "content": "// ok"}],
            llm=mock_llm,
        )
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_verify_llm_fails_fallback(self):
        from agentic_pipeline.prompt_chain.prompts.verify import verify_handler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            success=False, error="LLM unavailable",
        )

        with patch(
            "agentic_pipeline.prompt_chain.prompts.verify.execute_fallback",
        ) as mock_fb:
            mock_fb.return_value = {
                "valid": True,
                "checks": [],
                "should_retry": False,
                "suggestions": [],
            }
            result = await verify_handler(
                requirements={},
                files=[],
                llm=mock_llm,
            )

        assert result["valid"] is True
        mock_fb.assert_called_once()
