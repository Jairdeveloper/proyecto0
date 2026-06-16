"""Tests for PREPROCESS prompt."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest

from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry


class TestPreprocessPrompt:
    def setup_method(self) -> None:
        # Load __init__.py first (registers all 6 templates), then clear,
        # then reload just preprocess module to re-register it cleanly.
        import agentic_pipeline.prompt_chain.prompts as _pkg
        _ = _pkg
        PromptRegistry.clear()
        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.preprocess",
        )
        importlib.reload(_mod)

    @pytest.mark.asyncio
    async def test_preprocess_llm_success(self):
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            preprocess_handler,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"normalized": "crea modulo pagos en nestjs",'
                     '"domain": "backend", "language": "es",'
                     '"segments": ["crea modulo pagos en nestjs"],'
                     '"has_ambiguity": false, "confidence": 0.95}',
            structured={
                "normalized": "crea modulo pagos en nestjs",
                "domain": "backend",
                "language": "es",
                "segments": ["crea modulo pagos en nestjs"],
                "has_ambiguity": False,
                "confidence": 0.95,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await preprocess_handler(raw_text="crea modulo pagos en NestJS",
                                          llm=mock_llm)
        assert result["normalized"] == "crea modulo pagos en nestjs"
        assert result["domain"] == "backend"
        assert result["has_ambiguity"] is False

    @pytest.mark.asyncio
    async def test_preprocess_llm_fails_fallback(self):
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            preprocess_handler,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            success=False, error="LLM unavailable",
        )

        with patch(
            "agentic_pipeline.prompt_chain.prompts.preprocess.execute_fallback",
        ) as mock_fb:
            mock_fb.return_value = {
                "normalized": "crea modulo pagos en nestjs",
                "domain": "backend",
                "language": "es",
                "segments": ["crea modulo pagos en nestjs"],
                "has_ambiguity": False,
                "confidence": 0.5,
            }
            result = await preprocess_handler(raw_text="crea modulo pagos",
                                              llm=mock_llm)

        assert result["normalized"] == "crea modulo pagos en nestjs"
        assert result["confidence"] == 0.5
        mock_fb.assert_called_once_with(
            "preprocessor_filters", raw_text="crea modulo pagos",
        )

    @pytest.mark.asyncio
    async def test_preprocess_handles_empty_input(self):
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            preprocess_handler,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"normalized": "", "domain": "general",'
                     '"language": "es", "segments": [],'
                     '"has_ambiguity": true, "confidence": 0.1}',
            structured={
                "normalized": "",
                "domain": "general",
                "language": "es",
                "segments": [],
                "has_ambiguity": True,
                "confidence": 0.1,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await preprocess_handler(raw_text="", llm=mock_llm)
        assert result["normalized"] == ""
        assert result["confidence"] == 0.1
        assert result["has_ambiguity"] is True

    @pytest.mark.asyncio
    async def test_preprocess_extracts_domain(self):
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            preprocess_handler,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"normalized": "crea api rest", "domain": "backend",'
                     '"language": "es", "segments": ["crea api rest"],'
                     '"has_ambiguity": false, "confidence": 0.9}',
            structured={
                "normalized": "crea api rest",
                "domain": "backend",
                "language": "es",
                "segments": ["crea api rest"],
                "has_ambiguity": False,
                "confidence": 0.9,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await preprocess_handler(raw_text="crea api rest", llm=mock_llm)
        assert result["domain"] == "backend"

    @pytest.mark.asyncio
    async def test_preprocess_segments_sentences(self):
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            preprocess_handler,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"normalized": "crea modulo. anade auth.",'
                     '"domain": "backend", "language": "es",'
                     '"segments": ["crea modulo", "anade auth"],'
                     '"has_ambiguity": false, "confidence": 0.9}',
            structured={
                "normalized": "crea modulo. anade auth.",
                "domain": "backend",
                "language": "es",
                "segments": ["crea modulo", "anade auth"],
                "has_ambiguity": False,
                "confidence": 0.9,
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        result = await preprocess_handler(raw_text="crea modulo. anade auth.",
                                          llm=mock_llm)
        assert len(result["segments"]) == 2
        assert "crea modulo" in result["segments"]
