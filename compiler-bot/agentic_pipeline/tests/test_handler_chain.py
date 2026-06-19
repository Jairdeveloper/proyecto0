"""Tests for Chain of Responsibility base (PromptHandler)."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.handler_base import (
    PromptHandler,
    PromptRequest,
    PromptResponse,
)


class _TestHandler(PromptHandler):
    name = "test"
    output_contract = None
    input_fields: list[str] = []

    def _build_prompt_kwargs(self, request, ctx_data):
        return {"raw_text": request.raw_input}

    async def handle(self, request, ctx):
        return PromptResponse(success=True, output={"handled": True})


class _ChainHandler(PromptHandler):
    name = "chain"
    output_contract = None
    input_fields: list[str] = []

    def __init__(self, marker: str, llm=None, debug_callback=None):
        super().__init__(llm, debug_callback)
        self.marker = marker

    def _build_prompt_kwargs(self, request, ctx_data):
        return {"raw_text": request.raw_input}

    async def handle(self, request, ctx):
        if self._next_handler:
            return await self._next_handler.handle(request, ctx)
        return PromptResponse(success=True, output={"marker": self.marker})


class TestHandlerBase:
    def test_set_next_returns_handler(self):
        h1 = _TestHandler()
        h2 = _TestHandler()
        returned = h1.set_next(h2)
        assert returned is h2

    def test_set_next_chains(self):
        h1 = _TestHandler()
        h2 = _TestHandler()
        h3 = _TestHandler()
        h1.set_next(h2).set_next(h3)
        assert h1._next_handler is h2
        assert h2._next_handler is h3
        assert h3._next_handler is None

    @pytest.mark.asyncio
    async def test_handler_delegates_to_next(self):
        h1 = _ChainHandler("first")
        h2 = _ChainHandler("second")
        h1.set_next(h2)
        request = PromptRequest(raw_input="test")
        ctx = ChainContext()
        response = await h1.handle(request, ctx)
        # Last handler in chain returns its response
        assert response.success is True

    @pytest.mark.asyncio
    async def test_handler_no_next_returns_own_response(self):
        handler = _TestHandler()
        request = PromptRequest(raw_input="test")
        ctx = ChainContext()
        response = await handler.handle(request, ctx)
        assert response.success is True
        assert response.output["handled"] is True

    def test_prompt_request_defaults(self):
        request = PromptRequest(raw_input="hola")
        assert request.raw_input == "hola"
        assert request.debug_callback is None

    def test_prompt_response_defaults(self):
        response = PromptResponse()
        assert response.success is True
        assert response.output == {}
        assert response.error is None


class TestHandlerChainBuild:
    """Test the chain building pattern used by ChainOrchestrator."""

    def test_build_handler_chain(self):
        h1 = _ChainHandler("pre")
        h2 = _ChainHandler("intent")
        h3 = _ChainHandler("plan")
        h1.set_next(h2).set_next(h3)
        assert h1._next_handler is h2
        assert h2._next_handler is h3
        assert h3._next_handler is None

    @pytest.mark.asyncio
    async def test_chain_all_handlers_invoked(self):
        results: list[str] = []

        class _TrackingHandler(PromptHandler):
            name = "track"
            output_contract = None
            input_fields: list[str] = []

            def __init__(self, marker: str, llm=None, debug_callback=None):
                super().__init__(llm, debug_callback)
                self.marker = marker

            def _build_prompt_kwargs(self, request, ctx_data):
                return {"raw_text": request.raw_input}

            async def handle(self, request, ctx):
                results.append(self.marker)
                if self._next_handler:
                    return await self._next_handler.handle(request, ctx)
                return PromptResponse(success=True, output={"marker": self.marker})

        h1 = _TrackingHandler("a")
        h2 = _TrackingHandler("b")
        h3 = _TrackingHandler("c")
        h1.set_next(h2).set_next(h3)

        request = PromptRequest(raw_input="test")
        ctx = ChainContext()
        response = await h1.handle(request, ctx)

        assert results == ["a", "b", "c"]
        assert response.success is True
        assert response.output["marker"] == "c"

    @pytest.mark.asyncio
    async def test_chain_empty_chain(self):
        h1 = _TestHandler()
        request = PromptRequest(raw_input="test")
        ctx = ChainContext()
        response = await h1.handle(request, ctx)
        assert response.success is True

    @pytest.mark.asyncio
    async def test_handler_llm_failure_fallback(self):
        import agentic_pipeline.prompt_chain.prompts as _pkg
        from agentic_pipeline.prompt_chain.prompt_template import (
            PromptRegistry,
        )
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            PreprocessHandler,
        )

        _ = _pkg
        PromptRegistry.clear()

        import importlib

        _mod = importlib.import_module(
            "agentic_pipeline.prompt_chain.prompts.preprocess",
        )
        importlib.reload(_mod)

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = AsyncMock(
            success=False,
            error="LLM unavailable",
        )

        handler = PreprocessHandler(llm=mock_llm)
        request = PromptRequest(raw_input="crea modulo")
        ctx = ChainContext()
        response = await handler.handle(request, ctx)
        assert response.success is True
        assert "normalized" in response.output
