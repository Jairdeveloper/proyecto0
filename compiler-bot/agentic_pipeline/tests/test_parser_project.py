"""Tests for ParserGLR stage and AST nodes."""

import pytest

from agentic_pipeline.nodes.ast_nodes import (
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)
from agentic_pipeline.nodes.evaluation_visitor import EvaluationVisitor
from agentic_pipeline.nodes.ir_export_visitor import IRExportVisitor
from agentic_pipeline.nodes.parser import ParserGLR, _select_grammar
from agentic_pipeline.nodes.validation_visitor import ValidationVisitor
from agentic_pipeline.state_models import Stage, StageContext


# ============================================================================
# AST Node unit tests
# ============================================================================


class TestProjectNode:
    def test_empty_project(self):
        p = ProjectNode("test")
        ir = p.accept(IRExportVisitor())
        assert ir["node_type"] == "project"
        assert ir["children"] == []

    def test_project_with_page(self):
        p = ProjectNode("test")
        page = PageNode("home")
        p.add(page)
        ir = p.accept(IRExportVisitor())
        assert len(ir["children"]) == 1
        assert ir["children"][0]["name"] == "home"

    def test_validate_no_errors(self):
        p = ProjectNode("test")
        errors = p.accept(ValidationVisitor()).errors
        assert errors == []


class TestPageNode:
    def test_page_with_components(self):
        page = PageNode("login")
        comp = ComponentNode("form", "formulario")
        page.add(comp)
        ir = page.accept(IRExportVisitor())
        assert ir["name"] == "login"
        assert len(ir["children"]) == 1
        assert ir["children"][0]["component_type"] == "formulario"

    def test_page_no_components_validation_error(self):
        page = PageNode("empty")
        errors = page.accept(ValidationVisitor()).errors
        assert any("no components" in e for e in errors)

    def test_page_evaluate(self):
        page = PageNode("home")
        comp = ComponentNode("table", "tabla")
        page.add(comp)
        ev = page.accept(EvaluationVisitor())
        assert ev["type"] == "page"
        assert ev["name"] == "home"
        assert len(ev["components"]) == 1


class TestComponentNode:
    def test_component_ir(self):
        c = ComponentNode("form", "formulario")
        ir = c.accept(IRExportVisitor())
        assert ir["node_type"] == "component"
        assert ir["name"] == "form"
        assert ir["component_type"] == "formulario"

    def test_component_validate(self):
        c = ComponentNode("btn", "boton")
        errors = c.accept(ValidationVisitor()).errors
        assert errors == []


class TestEntityNode:
    def test_entity_with_attributes(self):
        e = EntityNode("User")
        e.add_attribute("name", "string")
        e.add_attribute("age", "int")
        ir = e.accept(IRExportVisitor())
        assert ir["name"] == "User"
        assert len(ir["attributes"]) == 2
        assert ir["attributes"][0] == {"name": "name", "type": "string"}

    def test_entity_no_attributes_validation_error(self):
        e = EntityNode("Empty")
        errors = e.accept(ValidationVisitor()).errors
        assert any("no attributes" in e for e in errors)


class TestInfraNode:
    def test_infra_with_resources(self):
        node = InfraNode("postgres", "basededatos")
        node.add_resource({"name": "cpu", "value": "4"})
        ir = node.accept(IRExportVisitor())
        assert ir["name"] == "postgres"
        assert ir["infra_type"] == "basededatos"
        assert len(ir["resources"]) == 1


# ============================================================================
# Grammar selection
# ============================================================================


class TestGrammarSelection:
    def test_select_project(self):
        assert _select_grammar("pagina login con formulario") == "project"

    def test_select_data(self):
        assert _select_grammar("entidad Usuario") == "data"

    def test_select_infra(self):
        assert _select_grammar("base de datos postgres") == "infra"

    def test_select_ui(self):
        assert _select_grammar("seccion navbar con header") == "ui"


# ============================================================================
# ParserGLR Stage
# ============================================================================


PAGE_TOKENS = [
    {"value": "pagina", "type": "WEB_APP", "category": "domain"},
    {"value": "login", "type": "CNAME", "category": "entity"},
    {"value": "con", "type": "CONNECTOR", "category": "connector"},
    {"value": "formulario", "type": "FORM", "category": "ui"},
]

DATA_TOKENS = [
    {"value": "entidad", "type": "KEYWORD", "category": "domain"},
    {"value": "Usuario", "type": "CNAME", "category": "entity"},
    {"value": "nombre:string", "type": "CNAME", "category": "text"},
    {"value": "email:string", "type": "CNAME", "category": "text"},
]

INFRA_TOKENS = [
    {"value": "basededatos", "type": "INFRA_KEYWORD", "category": "domain"},
    {"value": "postgres", "type": "CNAME", "category": "entity"},
]


class TestParserGLR:
    @pytest.fixture
    def parser(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        return ParserGLR(ctx)

    def test_receive_mission_from_dict(self, parser):
        parser.receive_mission({"tokens": [{"value": "pagina"}, {"value": "login"}]})
        assert len(parser._tokens) == 2

    def test_receive_mission_from_tokens(self, parser):
        parser.receive_mission({"tokens": PAGE_TOKENS})
        assert len(parser._tokens) == 4

    def test_analyze(self, parser):
        parser.receive_mission({"tokens": PAGE_TOKENS})
        result = parser.analyze()
        assert result.complexity_score == 0.3

    def test_act_returns_ast(self, parser):
        parser.receive_mission({"tokens": PAGE_TOKENS})
        plan = parser.reflect_and_plan(parser.analyze())
        output = parser.act(plan)
        assert output.success is True
        assert "ast" in output.output_data

    def test_act_data_grammar(self, parser):
        parser.receive_mission({"tokens": DATA_TOKENS})
        plan = parser.reflect_and_plan(parser.analyze())
        output = parser.act(plan)
        assert output.success is True
        assert output.output_data["grammar"] == "data"

    def test_act_infra_grammar(self, parser):
        parser.receive_mission({"tokens": INFRA_TOKENS})
        plan = parser.reflect_and_plan(parser.analyze())
        output = parser.act(plan)
        assert output.success is True

    def test_execute_full_flow(self, parser):
        result = parser.execute({"tokens": PAGE_TOKENS})
        assert result.success is True
        assert result.stage == Stage.PARSER

    def test_unknown_grammar(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx, grammar="unknown")
        p.receive_mission({"tokens": PAGE_TOKENS})
        output = p.act(p.reflect_and_plan(p.analyze()))
        assert output.success is True
        assert output.output_data["grammar"] == "unknown"

    def test_learn_and_improve(self, parser):
        parser.receive_mission({"tokens": PAGE_TOKENS})
        output = parser.act(parser.reflect_and_plan(parser.analyze()))
        parser.learn_and_improve(output.feedback)
        assert True


class TestParserGLREdgeCases:
    def test_empty_input(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        result = p.execute({"tokens": []})
        assert result.success is False

    def test_single_page(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        result = p.execute({"tokens": PAGE_TOKENS})
        assert result.success is True

    def test_tokens_with_stop_words(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        p.receive_mission(
            {
                "tokens": [
                    {"value": "pagina", "type": "CNAME", "category": "domain"},
                    {"value": "de", "type": "STOP", "category": "stop"},
                    {"value": "login", "type": "CNAME", "category": "entity"},
                    {"value": "con", "type": "CONNECTOR", "category": "connector"},
                    {"value": "formulario", "type": "FORM", "category": "ui"},
                ]
            }
        )
        assert len(p._tokens) == 5


class TestParserGLRMultiGrammar:
    def test_project_grammar(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx, grammar="project")
        result = p.execute({"tokens": PAGE_TOKENS})
        assert result.success is True
        assert len(result.output_data["ast"].get("children", [])) >= 1

    def test_data_grammar(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx, grammar="data")
        result = p.execute({"tokens": DATA_TOKENS})
        assert result.success is True
