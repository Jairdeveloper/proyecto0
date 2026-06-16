"""Snapshot tests for AST output from parser and full pipeline.

Requires: syrupy
Usage: python -m pytest tests/test_ast_snapshots.py --snapshot-update
"""

from __future__ import annotations

from typing import Any


from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.nodes.parser import ParserGLR
from agentic_pipeline.nodes.preprocessor import Preprocessor
from agentic_pipeline.state_models import Stage, StageContext

def _run_parser(text: str) -> dict[str, Any]:
    """Run preprocessor → lexer → parser and return the AST dict."""
    pre_ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
    pre = Preprocessor(pre_ctx, domain="web")
    pre.receive_mission({"raw": text, "intent": {"domain": "web"}})
    pre_output = pre.act(pre.reflect_and_plan(pre.analyze()))

    lex_ctx = StageContext(stage=Stage.LEXER, input_data="")
    lex = Lexer(lex_ctx)
    lex.receive_mission(pre_output.output_data)
    lex_output = lex.act(lex.reflect_and_plan(lex.analyze()))

    par_ctx = StageContext(stage=Stage.PARSER, input_data="")
    par = ParserGLR(par_ctx)
    par.receive_mission(lex_output.output_data)
    par_output = par.act(par.reflect_and_plan(par.analyze()))

    return par_output.output_data.get("ast", {})


# ===========================================================================
# Snapshot 1: page AST
# ===========================================================================


def test_ast_page_snapshot(snapshot):
    """AST for: 'pagina login con formulario' (UI grammar)."""
    ast = _run_parser("pagina login con formulario")
    snapshot.assert_match(ast)


# ===========================================================================
# Snapshot 2: entity AST
# ===========================================================================


def test_ast_entity_snapshot(snapshot):
    """AST for: 'entidad Usuario nombre:string email:string' (data grammar)."""
    ast = _run_parser("entidad Usuario nombre:string email:string edad:int")
    snapshot.assert_match(ast)


# ===========================================================================
# Snapshot 3: full project AST
# ===========================================================================


def test_ast_project_snapshot(snapshot):
    """AST for: 'crea un modulo de pagos con NestJS y Prisma' (project grammar)."""
    ast = _run_parser("crea un modulo de pagos con NestJS y Prisma")
    snapshot.assert_match(ast)
