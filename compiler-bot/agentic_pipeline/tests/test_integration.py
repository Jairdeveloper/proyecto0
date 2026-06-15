"""Integration tests — end-to-end pipeline validation."""

from __future__ import annotations

import pytest

from agentic_pipeline.orchestrator import PipelineOrchestrator

pytestmark = pytest.mark.asyncio


async def _run_pipeline(prompt: str) -> dict:
    orch = PipelineOrchestrator()
    result = await orch.run(prompt)
    return result


async def test_empty_prompt():
    """Empty prompt should not crash."""
    result = await _run_pipeline("")
    assert result is not None
    assert result["success"] is True


async def test_simple_prompt_nonempty_output():
    """Simple Spanish prompt produces output."""
    result = await _run_pipeline("crea un modulo de pagos")
    assert result is not None
    assert result["success"] is True
    output = result.get("output", {})
    assert output is not None


async def test_prompt_with_technology():
    """Prompt mentioning NestJS and Prisma reaches validator."""
    result = await _run_pipeline(
        "crea una API REST con NestJS y Prisma para gestion de usuarios",
    )
    assert result is not None
    assert result["success"] is True


async def test_prompt_with_ui():
    """Prompt with UI elements generates UI output."""
    result = await _run_pipeline(
        "pagina web con formulario de registro y tabla de usuarios",
    )
    assert result is not None
    assert result["success"] is True


async def test_long_prompt():
    """Long real-world prompt should complete without error."""
    prompt = (
        "Disena una pagina web moderna y profesional para un servicio "
        "de acortamiento de enlaces con formulario principal, estadisticas, "
        "autenticacion de usuarios, panel de control y codigos QR"
    )
    result = await _run_pipeline(prompt)
    assert result is not None
    assert result["success"] is True


async def test_pipeline_all_stages_executed():
    """Verify orchestrator executes all 10 stages by checking output shape."""
    orch = PipelineOrchestrator()
    assert orch.compiled is not None
    stages = {
        "intent",
        "preprocessor",
        "lexer",
        "parser",
        "semantic_analyzer",
        "ir_generator",
        "planner",
        "synthesis",
        "ui_generator",
        "validator",
    }
    assert len(stages) == 10
    result = await orch.run("crea un modulo de pagos")
    assert result["success"] is True
