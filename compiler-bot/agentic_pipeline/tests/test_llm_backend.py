"""Tests for LLMBackend, providers, and FailoverLLMBackend."""

from __future__ import annotations

import pytest
from pydantic import BaseModel


class _TestSchema(BaseModel):
    message: str
    count: int


class _MockLLMBase:
    """Base with proper signatures matching LLMBackend ABC."""

    async def generate(self, prompt, system="", temperature=0.3, max_tokens=4096):
        raise NotImplementedError

    async def generate_structured(
        self, prompt, system="", output_schema=None, temperature=0.3,
    ):
        raise NotImplementedError


class TestFailoverLLMBackend:
    @pytest.mark.asyncio
    async def test_failover_all_fail(self):
        from agentic_pipeline.prompt_chain.llm_backend import (
            FailoverLLMBackend,
            LLMResult,
        )

        class AlwaysFail(_MockLLMBase):
            async def generate(self, prompt="", system="", temperature=0.3, max_tokens=4096):
                return LLMResult(success=False, error="fail")
            async def generate_structured(self, prompt="", system="", output_schema=None, temperature=0.3):
                return LLMResult(success=False, error="fail")

        fb = FailoverLLMBackend([AlwaysFail(), AlwaysFail()])
        result = await fb.generate(prompt="test")
        assert not result.success
        assert result.error == "all backends failed"

    @pytest.mark.asyncio
    async def test_failover_first_succeeds(self):
        from agentic_pipeline.prompt_chain.llm_backend import (
            FailoverLLMBackend,
            LLMResult,
        )

        class FirstOK(_MockLLMBase):
            async def generate(self, prompt="", system="", temperature=0.3, max_tokens=4096):
                return LLMResult(content="ok", provider="first", model="m", success=True)
            async def generate_structured(self, prompt="", system="", output_schema=None, temperature=0.3):
                return LLMResult(content="ok", provider="first", model="m", success=True)

        class NeverReached(_MockLLMBase):
            async def generate(self, prompt="", system="", temperature=0.3, max_tokens=4096):
                raise RuntimeError("should not be called")
            async def generate_structured(self, prompt="", system="", output_schema=None, temperature=0.3):
                raise RuntimeError("should not be called")

        fb = FailoverLLMBackend([FirstOK(), NeverReached()])
        result = await fb.generate(prompt="test")
        assert result.success
        assert result.provider == "first"

    @pytest.mark.asyncio
    async def test_failover_structured_all_fail(self):
        from agentic_pipeline.prompt_chain.llm_backend import (
            FailoverLLMBackend,
            LLMResult,
        )

        class AlwaysFail(_MockLLMBase):
            async def generate(self, prompt="", system="", temperature=0.3, max_tokens=4096):
                return LLMResult(success=False, error="fail")
            async def generate_structured(self, prompt="", system="", output_schema=None, temperature=0.3):
                return LLMResult(success=False, error="fail")

        fb = FailoverLLMBackend([AlwaysFail()])
        result = await fb.generate_structured(
            prompt="test", output_schema=_TestSchema,
        )
        assert not result.success

    @pytest.mark.asyncio
    async def test_failover_empty_backends(self):
        from agentic_pipeline.prompt_chain.llm_backend import FailoverLLMBackend

        try:
            FailoverLLMBackend([])
            assert False, "should have raised"
        except ValueError:
            pass

    @pytest.mark.asyncio
    async def test_failover_structured_success(self):
        from agentic_pipeline.prompt_chain.llm_backend import (
            FailoverLLMBackend,
            LLMResult,
        )

        class StubLLM(_MockLLMBase):
            async def generate(self, prompt="", system="", temperature=0.3, max_tokens=4096):
                return LLMResult(
                    content='{"message": "hi", "count": 3}',
                    structured={"message": "hi", "count": 3},
                    provider="stub", model="s", success=True,
                )
            async def generate_structured(self, prompt="", system="", output_schema=None, temperature=0.3):
                return LLMResult(
                    content='{"message": "hi", "count": 3}',
                    structured={"message": "hi", "count": 3},
                    provider="stub", model="s", success=True,
                )

        fb = FailoverLLMBackend([StubLLM()])
        result = await fb.generate_structured(
            prompt="test", output_schema=_TestSchema,
        )
        assert result.success
        assert result.structured["message"] == "hi"


class TestOpenAIBackend:
    @pytest.mark.asyncio
    async def test_generate_no_api_key_returns_failure(self):
        from agentic_pipeline.prompt_chain.llm_backend import OpenAIBackend

        backend = OpenAIBackend(api_key="invalid-key")
        result = await backend.generate(prompt="test")
        # Should fail gracefully (not crash)
        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_generate_structured_no_api_key(self):
        from agentic_pipeline.prompt_chain.llm_backend import OpenAIBackend

        backend = OpenAIBackend(api_key="invalid-key")
        result = await backend.generate_structured(
            prompt="test", output_schema=_TestSchema,
        )
        assert not result.success


class TestBuildLLMBackend:
    def test_build_default_returns_failover(self):
        from agentic_pipeline.prompt_chain.llm_backend import (
            FailoverLLMBackend,
            build_llm_backend,
        )

        backend = build_llm_backend()
        assert isinstance(backend, FailoverLLMBackend)
