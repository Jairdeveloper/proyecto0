"""Parser GLR stage — Lark-based parsing with AST generation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from lark import Lark, Token, Tree

from ..base_stage import PipelineStage
from ..state_models import ActionPlan, AnalysisResult, StageContext, StageOutput
from .ast_nodes import (
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

STOP_WORDS_RE = re.compile(
    r"\b(de|en|para|del|un|una|por|el|la|los|las|al)\b", re.IGNORECASE
)

GRAMMAR_DIR = Path(__file__).parent.parent / "grammars"


# ============================================================================
# GRAMMAR LOADING
# ============================================================================


def _load_grammar(name: str) -> str:
    return (GRAMMAR_DIR / name).read_text()


PARSERS: dict[str, Lark] = {
    "project": Lark(_load_grammar("project_grammar.lark"), parser="earley"),
    "ui": Lark(_load_grammar("ui_grammar.lark"), parser="earley"),
    "data": Lark(_load_grammar("data_grammar.lark"), parser="earley"),
    "infra": Lark(_load_grammar("infra_grammar.lark"), parser="earley"),
}

AST_BUILDERS: dict[str, callable] = {}


def _clean_text(text: str) -> str:
    return STOP_WORDS_RE.sub("", text).strip()


# ============================================================================
# PROJECT GRAMMAR AST BUILDER
# ============================================================================


def _build_project_ast(tree: Tree) -> ProjectNode:
    root = ProjectNode("project")
    for child in tree.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "section":
            for sub in child.children:
                if not isinstance(sub, Tree):
                    continue
                if sub.data == "page_def":
                    page = _build_page_def(sub)
                    if page is not None:
                        root.add(page)
                elif sub.data == "module_def":
                    page = _build_module_def(sub)
                    if page is not None:
                        root.add(page)
    return root


def _build_page_def(tree: Tree) -> PageNode | None:
    name = ""
    comps: list[ComponentNode] = []
    for child in tree.children:
        if isinstance(child, Tree) and child.data in ("component_list",):
            for sub in child.children:
                if isinstance(sub, Tree):
                    c = _build_component_from_tree(sub)
                    if c is not None:
                        comps.append(c)
        elif isinstance(child, Token) and child.type == "CNAME":
            name = str(child)
    page = PageNode(name)
    for c in comps:
        page.add(c)
    return page


def _build_module_def(tree: Tree) -> PageNode | None:
    name = ""
    for child in tree.children:
        if isinstance(child, Token) and child.type == "CNAME":
            name = str(child)
    return PageNode(name)


def _build_component_from_tree(tree: Tree) -> ComponentNode | None:
    if tree.data == "CNAME":
        return ComponentNode(
            str(tree.children[0]) if tree.children else "", "component"
        )
    return None


AST_BUILDERS["project"] = _build_project_ast


# ============================================================================
# UI GRAMMAR AST BUILDER
# ============================================================================


def _build_ui_ast(tree: Tree) -> ProjectNode:
    root = ProjectNode("ui_layout")
    for child in tree.children:
        if not isinstance(child, Tree):
            continue
        if child.data == "layout":
            page = _build_layout(child)
            if page is not None:
                root.add(page)
    return root


def _build_layout(tree: Tree) -> PageNode | None:
    name = ""
    for child in tree.children:
        if isinstance(child, Tree) and child.data == "CNAME":
            name = str(child.children[0]) if child.children else ""
    return PageNode(name)


AST_BUILDERS["ui"] = _build_ui_ast


# ============================================================================
# DATA GRAMMAR AST BUILDER
# ============================================================================


def _build_data_ast(tree: Tree) -> ProjectNode:
    root = ProjectNode("data_model")
    for child in tree.children:
        if not isinstance(child, Tree) or child.data != "entity_def":
            continue
        entity = _build_entity_def(child)
        if entity is not None:
            root.add(entity)
    return root


def _build_entity_def(tree: Tree) -> EntityNode | None:
    name = ""
    for child in tree.children:
        if isinstance(child, Token) and child.type == "CNAME":
            name = str(child)
            break
    entity = EntityNode(name)
    for child in tree.children:
        if isinstance(child, Tree) and child.data == "attribute_list":
            for attr_tree in child.children:
                if isinstance(attr_tree, Tree) and attr_tree.data == "attribute":
                    parts = [str(c) for c in attr_tree.children if c is not None]
                    if len(parts) >= 2:
                        cname_part = parts[0]
                        type_part = parts[2] if len(parts) > 2 else parts[-1]
                        entity.add_attribute(cname_part, type_part)
    return entity


AST_BUILDERS["data"] = _build_data_ast


# ============================================================================
# INFRA GRAMMAR AST BUILDER
# ============================================================================


def _build_infra_ast(tree: Tree) -> ProjectNode:
    root = ProjectNode("infrastructure")
    for child in tree.children:
        if not isinstance(child, Tree) or child.data != "infrastructure":
            continue
        name = ""
        for sub in child.children:
            if isinstance(sub, Tree) and sub.data == "CNAME":
                name = str(sub.children[0]) if sub.children else ""
        infra_type = "infra"
        for token in child.scan_values(lambda t: True):
            if token.type in ("INFRA_KEYWORD",):
                val = str(token).lower()
                if val == "basededatos":
                    val = "base de datos"
                infra_type = val
                break
        node = InfraNode(name, infra_type)
        root.add(node)
    return root


AST_BUILDERS["infra"] = _build_infra_ast


# ============================================================================
# GRAMMAR SELECTOR
# ============================================================================


def _select_grammar(text: str) -> str:
    text_lower = text.lower()
    if any(kw in text_lower for kw in ("entidad", "modelo", "entity", "atributo")):
        return "data"
    if any(
        kw in text_lower
        for kw in (
            "basededatos",
            "base de datos",
            "servicio",
            "despliegue",
            "cpu",
            "memoria",
            "database",
            "deploy",
        )
    ):
        return "infra"
    if any(
        kw in text_lower
        for kw in ("navbar", "sidebar", "footer", "header", "layout", "seccion")
    ):
        return "ui"
    return "project"


# ============================================================================
# PARSER GLR STAGE
# ============================================================================


class ParserGLR(PipelineStage):
    """Stage 4: parses token text into an AST using Lark GLR parser."""

    name = "parser"

    def __init__(self, context: StageContext, grammar: str = ""):
        super().__init__(context)
        self.grammar_name = grammar
        self._input_text = ""

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            tokens = input_data.get("tokens", [])
            self._input_text = " ".join(t.get("value", "") for t in tokens)
        else:
            raw = str(input_data)
            tokens_from_lexer = raw.split()
            self._input_text = " ".join(tokens_from_lexer)
        self._input_text = _clean_text(self._input_text)
        logger.debug("Parser cleaned text: %.100s", self._input_text)

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Input: {len(self._input_text)} chars"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.3,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        grammar = self.grammar_name or _select_grammar(self._input_text)
        logger.info("Selected grammar: %s", grammar)
        return ActionPlan(
            steps=[{"action": "parse", "grammar": grammar}],
            strategy="deterministic",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        grammar = self.grammar_name
        if plan.steps:
            grammar = plan.steps[0].get("grammar", grammar)

        if grammar not in PARSERS:
            return StageOutput(
                stage=self.context.stage,
                output_data={},
                success=False,
                error=f"Unknown grammar: {grammar}",
            )

        parser = PARSERS[grammar]
        builder = AST_BUILDERS[grammar]
        try:
            tree = parser.parse(self._input_text)
            ast = builder(tree)
            ir = ast.to_ir()
            errors = [e for e in ast.validate() if e]
            logger.info("Parsed %s grammar: %d nodes", grammar, len(ast.children))
            return StageOutput(
                stage=self.context.stage,
                output_data={
                    "ast": ir,
                    "errors": errors,
                    "grammar": grammar,
                    "node_count": len(ast.children),
                },
                metrics={
                    "node_count": len(ast.children),
                    "error_count": len(errors),
                },
            )
        except Exception as e:
            logger.error("Parse error: %s", e)
            return StageOutput(
                stage=self.context.stage,
                output_data={},
                success=False,
                error=str(e),
            )

    def learn_and_improve(self, feedback: object) -> None:
        pass
