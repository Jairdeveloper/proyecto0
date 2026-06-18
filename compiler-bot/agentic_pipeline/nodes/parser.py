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
from .ir_export_visitor import IRExportVisitor

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

STOP_WORDS_RE = re.compile(
    r"\b(de|en|para|del|un|una|por|el|la|los|las|al)\b", re.IGNORECASE
)

GRAMMAR_DIR = Path(__file__).parent.parent / "grammars"

# ============================================================================
# WORDNET DISAMBIGUATION (N2.1c)
# ============================================================================

DOMAIN_MAP: dict[str, dict[str, str]] = {
    "software": {"grammar": "project", "description": "modulo de software"},
    "entity":   {"grammar": "data",    "description": "entidad de datos"},
    "ui":       {"grammar": "ui",      "description": "interfaz de usuario"},
    "infra":    {"grammar": "infra",   "description": "infraestructura"},
}


def ensure_nltk_data() -> None:
    """Descarga wordnet si no esta instalado."""
    try:
        from nltk.data import find as nltk_find
        nltk_find("wordnet")
    except LookupError:
        import nltk
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)


def infer_domain(synset) -> str:
    name = synset.name().lower()
    if any(k in name for k in ("computer", "software", "program")):
        return "software"
    if any(k in name for k in ("entity", "person", "object")):
        return "entity"
    if any(k in name for k in ("interface", "gui", "window")):
        return "ui"
    if any(k in name for k in ("infrastructure", "network", "database")):
        return "infra"
    return "entity"


def disambiguate_term(term: str, context: list[str]) -> dict:
    """Algoritmo de Lesk: synset mas probable segun contexto."""
    ensure_nltk_data()
    from nltk.wsd import lesk
    sentence = " ".join(context[-5:])
    synset = lesk(sentence, term, lang="spa")
    if synset:
        domain = infer_domain(synset)
        grammar_info = DOMAIN_MAP.get(domain, DOMAIN_MAP["entity"])
        return {
            "term": term,
            "synset": synset.name(),
            "definition": synset.definition(),
            "domain": domain,
            "grammar": grammar_info["grammar"],
        }
    return {"term": term, "synset": None, "domain": "unknown", "grammar": None}


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
                elif isinstance(sub, Token) and sub.type in ("CNAME", "COMP_KEYWORD"):
                    comps.append(ComponentNode(str(sub), str(sub)))
        elif isinstance(child, Token) and child.type in ("CNAME", "COMP_KEYWORD"):
            if not name:
                name = str(child)
    page = PageNode(name or "unnamed")
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
        if isinstance(child, Token) and child.type in ("CNAME", "COMP_KEYWORD"):
            if not name:
                name = str(child)
    return PageNode(name or "unnamed")


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


def _find_ambiguous_terms(tokens: list[dict]) -> list[str]:
    """Identifica terminos que aparecen en multiples gramaticas."""
    ambiguous = []
    text_lower = " ".join(t.get("value", "") for t in tokens).lower()
    for term in ("modulo", "entidad", "servicio", "pagina"):
        count = text_lower.count(term)
        if count > 0:
            ambiguous.append(term)
    return ambiguous


def _resolve_ambiguous_grammar(tokens: list[dict], context: list[str] | None = None) -> str | None:
    """Si los tokens sugieren multiples gramaticas, desambigua con WordNet."""
    ambiguous_terms = _find_ambiguous_terms(tokens)
    if not ambiguous_terms:
        return None

    ctx = context or []
    for term in ambiguous_terms:
        try:
            result = disambiguate_term(term, ctx)
            if result.get("grammar"):
                return result["grammar"]
        except Exception:
            continue
    return None


def _select_grammar(text: str, tokens: list[dict] | None = None,
                    context: list[str] | None = None) -> str:
    # Intentar desambiguacion por WordNet primero (N2.1c)
    if tokens and context:
        resolved = _resolve_ambiguous_grammar(tokens, context)
        if resolved:
            return resolved

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
        self._tokens: list[dict] = []
        self._enriched: dict = {}

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            tokens_raw = input_data.get("tokens", input_data)
            if isinstance(tokens_raw, list):
                self._tokens = tokens_raw
            else:
                self._tokens = []
            enriched_raw = input_data.get("enriched")
            self._enriched = enriched_raw if isinstance(enriched_raw, dict) else {}
        else:
            self._tokens = []
            self._enriched = {}

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Tokens: {len(self._tokens)}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.3,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        text = " ".join(t.get("value", "") for t in self._tokens)
        context_sentences = [s.strip() for s in self._enriched.get("history", [])]
        grammar = self.grammar_name or _select_grammar(text, self._tokens, context_sentences)
        logger.info("Selected grammar: %s", grammar)
        return ActionPlan(
            steps=[{"action": "parse", "grammar": grammar}],
            strategy="deterministic",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        if not self._tokens:
            return StageOutput(
                stage=self.context.stage,
                output_data={},
                success=False,
                error="No tokens received from lexer",
            )

        grammar = self.grammar_name
        if plan.steps:
            grammar = plan.steps[0].get("grammar", grammar)

        text = " ".join(t.get("value", "") for t in self._tokens)
        ast = self._try_lark_parse(text, grammar)
        if ast is None:
            ast = self._build_ast_from_tokens(self._tokens)

        nodes = ast.get("children", [])
        logger.info(
            "Built AST from %d tokens: %d nodes (grammar=%s)",
            len(self._tokens),
            len(nodes),
            grammar,
        )
        return StageOutput(
            stage=self.context.stage,
            output_data={
                "ast": ast,
                "grammar": grammar,
                "enriched": self._enriched or None,
            },
            metrics={
                "tokens": len(self._tokens),
                "ast_nodes": len(nodes),
            },
        )

    def _try_lark_parse(self, text: str, grammar: str) -> dict | None:
        if grammar not in PARSERS or grammar not in AST_BUILDERS:
            return None
        try:
            cleaned = _clean_text(text)
            if not cleaned.strip():
                return None
            tree = PARSERS[grammar].parse(cleaned)
            builder = AST_BUILDERS[grammar]
            project_node = builder(tree)
            return project_node.accept(IRExportVisitor())
        except Exception as e:
            logger.debug("Lark parse failed for grammar '%s': %s", grammar, e)
            return None

    def _build_ast_from_tokens(self, tokens: list[dict]) -> dict:
        actions = []
        entities = []
        for t in tokens:
            cat = t.get("category", "")
            if cat == "action":
                actions.append(t.get("value", ""))
            elif cat in ("entity", "domain"):
                entities.append(t.get("value", ""))
        return {
            "node_type": "project",
            "children": [{"node_type": "action", "value": a} for a in actions]
            + [{"node_type": "entity", "value": e} for e in entities],
        }

    def learn_and_improve(self, feedback: object) -> None:
        pass
