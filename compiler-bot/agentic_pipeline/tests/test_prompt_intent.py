"""Tests for INTENT prompt."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.handler_base import PromptRequest
from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry


class TestIntentPrompt:
    def setup_method(self) -> None:
        import agentic_pipeline.prompt_chain.prompts as _pkg

        _ = _pkg
        PromptRegistry.clear()
        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.intent",
        )
        importlib.reload(_mod)

    @pytest.mark.asyncio
    async def test_intent_create_module(self):
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"intent": "CREATE", "confidence": 0.98,'
            '"module": "pagos", "entity": null,'
            '"tech": ["nestjs"], "features": [],'
            '"is_ambiguous": false, "missing_info": []}',
            structured={
                "intent": "CREATE",
                "confidence": 0.98,
                "module": "pagos",
                "entity": None,
                "tech": ["nestjs"],
                "features": [],
                "is_ambiguous": False,
                "missing_info": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = IntentHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea un modulo de pagos")
        ctx = ChainContext()
        ctx.set_output(
            "preprocess",
            {
                "normalized": "crea un modulo de pagos",
                "domain": "backend",
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["intent"] == "CREATE"
        assert result["module"] == "pagos"
        assert "nestjs" in result["tech"]

    @pytest.mark.asyncio
    async def test_intent_delete(self):
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"intent": "DELETE", "confidence": 0.95,'
            '"module": "auth", "entity": null,'
            '"tech": [], "features": [],'
            '"is_ambiguous": false, "missing_info": []}',
            structured={
                "intent": "DELETE",
                "confidence": 0.95,
                "module": "auth",
                "entity": None,
                "tech": [],
                "features": [],
                "is_ambiguous": False,
                "missing_info": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = IntentHandler(llm=mock_llm)
        request = PromptRequest(raw_input="elimina el modulo auth")
        ctx = ChainContext()
        ctx.set_output(
            "preprocess",
            {
                "normalized": "elimina el modulo auth",
                "domain": "backend",
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["intent"] == "DELETE"
        assert result["module"] == "auth"

    @pytest.mark.asyncio
    async def test_intent_read(self):
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"intent": "READ", "confidence": 0.92,'
            '"module": null, "entity": null,'
            '"tech": [], "features": [],'
            '"is_ambiguous": false, "missing_info": []}',
            structured={
                "intent": "READ",
                "confidence": 0.92,
                "module": None,
                "entity": None,
                "tech": [],
                "features": [],
                "is_ambiguous": False,
                "missing_info": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = IntentHandler(llm=mock_llm)
        request = PromptRequest(raw_input="muestra el contenido del archivo")
        ctx = ChainContext()
        ctx.set_output(
            "preprocess",
            {
                "normalized": "muestra el contenido del archivo",
                "domain": "backend",
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["intent"] == "READ"

    @pytest.mark.asyncio
    async def test_intent_ambiguous_no_module(self):
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"intent": "CREATE", "confidence": 0.6,'
            '"module": null, "entity": null,'
            '"tech": [], "features": [],'
            '"is_ambiguous": true,'
            '"missing_info": ["modulo", "tecnologia"]}',
            structured={
                "intent": "CREATE",
                "confidence": 0.6,
                "module": None,
                "entity": None,
                "tech": [],
                "features": [],
                "is_ambiguous": True,
                "missing_info": ["modulo", "tecnologia"],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = IntentHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea algo")
        ctx = ChainContext()
        ctx.set_output(
            "preprocess",
            {
                "normalized": "crea algo",
                "domain": "backend",
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["is_ambiguous"] is True
        assert len(result["missing_info"]) > 0

    @pytest.mark.asyncio
    async def test_intent_extracts_tech(self):
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"intent": "CREATE", "confidence": 0.97,'
            '"module": "api", "entity": null,'
            '"tech": ["nestjs", "prisma"], "features": ["crud"],'
            '"is_ambiguous": false, "missing_info": []}',
            structured={
                "intent": "CREATE",
                "confidence": 0.97,
                "module": "api",
                "entity": None,
                "tech": ["nestjs", "prisma"],
                "features": ["crud"],
                "is_ambiguous": False,
                "missing_info": [],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = IntentHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea modulo api con nestjs y prisma")
        ctx = ChainContext()
        ctx.set_output(
            "preprocess",
            {
                "normalized": "crea modulo api con nestjs y prisma",
                "domain": "backend",
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert "nestjs" in result["tech"]
        assert "prisma" in result["tech"]

    @pytest.mark.asyncio
    async def test_intent_llm_fails_fallback(self):
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            success=False,
            error="LLM unavailable",
        )

        with patch(
            "agentic_pipeline.prompt_chain.handler_base.execute_fallback",
        ) as mock_fb:
            mock_fb.return_value = {
                "intent": "CREATE",
                "confidence": 0.5,
                "module": None,
                "entity": None,
                "tech": [],
                "features": [],
                "is_ambiguous": False,
                "missing_info": [],
            }
            handler = IntentHandler(llm=mock_llm)
            request = PromptRequest(raw_input="crea modulo")
            ctx = ChainContext()
            ctx.set_output(
                "preprocess",
                {
                    "normalized": "crea modulo",
                    "domain": "backend",
                },
            )
            response = await handler.handle(request, ctx)

        result = response.output
        assert result["intent"] == "CREATE"
        mock_fb.assert_called_once()

    @pytest.mark.asyncio
    async def test_intent_low_confidence(self):
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = LLMResult(
            content='{"intent": "EXPLAIN", "confidence": 0.25,'
            '"module": null, "entity": null,'
            '"tech": [], "features": [],'
            '"is_ambiguous": true,'
            '"missing_info": ["accion clara"]}',
            structured={
                "intent": "EXPLAIN",
                "confidence": 0.25,
                "module": None,
                "entity": None,
                "tech": [],
                "features": [],
                "is_ambiguous": True,
                "missing_info": ["accion clara"],
            },
            success=True,
            provider="test",
            model="test",
            duration=0.1,
        )
        handler = IntentHandler(llm=mock_llm)
        request = PromptRequest(raw_input="que es esto")
        ctx = ChainContext()
        ctx.set_output(
            "preprocess",
            {
                "normalized": "que es esto",
                "domain": "backend",
            },
        )
        response = await handler.handle(request, ctx)
        result = response.output
        assert result["confidence"] < 0.5
        assert result["is_ambiguous"] is True
