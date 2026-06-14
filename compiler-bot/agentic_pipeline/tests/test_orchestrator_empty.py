import pytest

from agentic_pipeline.orchestrator import PipelineOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_compile():
    orch = PipelineOrchestrator()
    assert orch.compiled is not None


@pytest.mark.asyncio
async def test_orchestrator_run():
    orch = PipelineOrchestrator()
    result = await orch.run("test prompt")
    assert result is not None
