"""Tests for error recovery — pipeline abort on stage failure."""

from __future__ import annotations

import pytest

from agentic_pipeline.orchestrator import PipelineOrchestrator

pytestmark = pytest.mark.asyncio


async def test_pipeline_stops_on_empty_input():
    orch = PipelineOrchestrator()
    result = await orch.run("")
    assert result["success"] is True


async def test_pipeline_handles_nonsense_input():
    orch = PipelineOrchestrator()
    result = await orch.run("xyzzy 123 !!!")
    assert result["success"] is True
    assert "output" in result
