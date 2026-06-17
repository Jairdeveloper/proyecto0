"""Tests for LLMCache (F5.3)."""

from __future__ import annotations

import pytest

from agentic_pipeline.prompt_chain.llm_cache import LLMCache


class TestLLMCache:
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        cache = LLMCache(backend="memory")
        prompt = "crea un modulo de pagos en nestjs"
        schema = "PreprocessorContract"
        response = {"normalized": "crea modulo pagos nestjs", "domain": "backend"}

        await cache.set(prompt, schema, response)
        cached = await cache.get(prompt, schema)

        assert cached is not None
        assert cached["normalized"] == "crea modulo pagos nestjs"

    @pytest.mark.asyncio
    async def test_get_miss_returns_none(self):
        cache = LLMCache(backend="memory")
        result = await cache.get("some prompt", "SomeSchema")
        assert result is None

    @pytest.mark.asyncio
    async def test_make_key_deterministic(self):
        key1 = LLMCache._make_key("Crea  Modulo  Pagos", "Test")
        key2 = LLMCache._make_key("crea modulo pagos", "Test")
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_different_schemas_different_keys(self):
        key1 = LLMCache._make_key("crea modulo pagos", "ContractA")
        key2 = LLMCache._make_key("crea modulo pagos", "ContractB")
        assert key1 != key2

    @pytest.mark.asyncio
    async def test_stats(self):
        cache = LLMCache(backend="memory")
        await cache.get("prompt1", "Schema1")
        await cache.get("prompt1", "Schema1")
        await cache.set("prompt1", "Schema1", {"result": "ok"})
        await cache.get("prompt1", "Schema1")

        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["hit_rate"] == pytest.approx(33.3, rel=0.1)

    @pytest.mark.asyncio
    async def test_clear(self):
        cache = LLMCache(backend="memory")
        await cache.set("p", "S", {"data": 1})
        await cache.get("p", "S")
        assert cache.stats()["hits"] == 1
        cache.clear()
        assert cache.stats()["hits"] == 0
        assert cache.stats()["misses"] == 0

    @pytest.mark.asyncio
    async def test_case_insensitive_key(self):
        """El hash normaliza a lowercase, variaciones de mayusculas son mismas."""
        key1 = LLMCache._make_key("CREA MODULO", "Test")
        key2 = LLMCache._make_key("crea modulo", "Test")
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_whitespace_normalization(self):
        """Multiples espacios se colapsan en uno."""
        key1 = LLMCache._make_key("crea   modulo   pagos", "Test")
        key2 = LLMCache._make_key("crea modulo pagos", "Test")
        assert key1 == key2
