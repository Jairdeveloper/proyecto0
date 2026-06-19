"""Performance benchmarks for RECPL pipeline stages.

Requires: pytest-benchmark
Usage: python -m pytest tests/test_performance.py --benchmark-only
"""

from __future__ import annotations

import pytest

from agentic_pipeline.nodes.intent_stage import IntentStage
from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.nodes.parser import ParserGLR
from agentic_pipeline.nodes.planner import HybridPlanner
from agentic_pipeline.nodes.preprocessor import Preprocessor
from agentic_pipeline.nodes.synthesis import SynthesisOrchestrator
from agentic_pipeline.orchestrator import PipelineOrchestrator
from agentic_pipeline.state_models import Stage, StageContext

SHORT_PROMPT = "crea un modulo de pagos con NestJS y Prisma"
LONG_PROMPT = (
    "crea un sistema completo de gestion empresarial que incluya "
    + "modulo de usuarios con autenticacion JWT, modulo de pagos con "
    + "integracion de pasarela, modulo de facturacion con generacion de PDF, "
    + "modulo de inventario con control de stock, modulo de reportes con "
    + "graficos y dashboard, modulo de notificaciones con email y SMS, "
    + "modulo de auditoria con registro de actividades, "
    + "modulo de configuracion con parametros del sistema, "
    + "y modulo de respaldo con exportacion de datos. "
    + "Todo debe generarse con NestJS en el backend, React en el frontend, "
    + "Prisma como ORM, PostgreSQL como base de datos, "
    + "y Docker para el despliegue. "
    + "Incluir pruebas unitarias, pruebas de integracion, "
    + "documentacion de API con Swagger, "
    + "y configuracion de CI/CD con GitHub Actions. "
    + "El sistema debe ser escalable, seguro, "
    + "y seguir las mejores practicas de desarrollo." * 5
)


def _make_ctx(stage: Stage) -> StageContext:
    return StageContext(stage=stage, input_data="")


# ===========================================================================
# B1: Full pipeline — short prompt
# ===========================================================================


@pytest.mark.benchmark
def test_pipeline_short(benchmark):
    orch = PipelineOrchestrator(output_dir="/tmp/bench_pipeline_short")

    def run():
        import asyncio

        return asyncio.run(orch.run(SHORT_PROMPT))

    result = benchmark(run)
    assert result is not None


# ===========================================================================
# B2: Full pipeline — long prompt (500+ words)
# ===========================================================================


@pytest.mark.benchmark
def test_pipeline_long(benchmark):
    orch = PipelineOrchestrator(output_dir="/tmp/bench_pipeline_long")

    def run():
        import asyncio

        return asyncio.run(orch.run(LONG_PROMPT))

    result = benchmark(run)
    assert result is not None


# ===========================================================================
# B3: NLP only (IntentStage)
# ===========================================================================


@pytest.mark.benchmark
def test_nlp_only(benchmark):
    ctx = _make_ctx(Stage.INTENT)
    stage = IntentStage(ctx)

    def run():
        stage.receive_mission(SHORT_PROMPT)
        plan = stage.reflect_and_plan(stage.analyze())
        return stage.act(plan)

    result = benchmark(run)
    assert result is not None
    assert result.success is not None


# ===========================================================================
# B4: Parser throughput (lexer + parser)
# ===========================================================================


@pytest.mark.benchmark
def test_parser_throughput(benchmark):
    pre_ctx = _make_ctx(Stage.PREPROCESSOR)
    pre = Preprocessor(pre_ctx, domain="web")
    pre.receive_mission(SHORT_PROMPT)
    pre_output = pre.act(pre.reflect_and_plan(pre.analyze()))

    lex_ctx = _make_ctx(Stage.LEXER)
    lex = Lexer(lex_ctx)

    par_ctx = _make_ctx(Stage.PARSER)
    par = ParserGLR(par_ctx)

    def run():
        lex.receive_mission(pre_output.output_data)
        lex_output = lex.act(lex.reflect_and_plan(lex.analyze()))
        par.receive_mission(lex_output.output_data)
        return par.act(par.reflect_and_plan(par.analyze()))

    result = benchmark(run)
    assert result is not None
    assert "ast" in result.output_data


# ===========================================================================
# B5: Generators (planner + synthesis) with 10 targets
# ===========================================================================


@pytest.mark.benchmark
def test_generator_throughput(benchmark):
    ctx = _make_ctx(Stage.PLANNER)
    planner = HybridPlanner(ctx)

    planner.receive_mission(
        {
            "ir_tree": None,
            "dependency_order": [],
        },
    )
    plan = planner.reflect_and_plan(planner.analyze())
    plan_output = planner.act(plan)

    syn_ctx = _make_ctx(Stage.SYNTHESIS)
    syn = SynthesisOrchestrator(syn_ctx)

    def run():
        syn.receive_mission(plan_output.output_data)
        syn_plan = syn.reflect_and_plan(syn.analyze())
        return syn.act(syn_plan)

    result = benchmark(run)
    assert result is not None
