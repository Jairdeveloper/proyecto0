"""Integration tests — NLP + pipeline end-to-end."""

from __future__ import annotations

import pytest

from agentic_pipeline.orchestrator import PipelineOrchestrator

pytestmark = pytest.mark.asyncio


async def _run_pipeline(prompt: str) -> dict:
    orch = PipelineOrchestrator()
    result = await orch.run(prompt)
    return result


async def test_pipeline_with_scaffold_intent():
    orch = PipelineOrchestrator()
    result = await orch.run("crea un modulo de pagos")
    assert result["success"] is True
    assert "output" in result


async def test_pipeline_with_query_intent():
    orch = PipelineOrchestrator()
    result = await orch.run("como se configura nestjs")
    assert result["success"] is True
    assert "output" in result


async def test_pipeline_with_explore_intent():
    orch = PipelineOrchestrator()
    result = await orch.run("que modulos tengo")
    assert result["success"] is True
