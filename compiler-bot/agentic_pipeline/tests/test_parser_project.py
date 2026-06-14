"""Tests for ParserGLR stage and AST nodes."""

import pytest

from agentic_pipeline.nodes.ast_nodes import (
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)
from agentic_pipeline.nodes.parser import ParserGLR, _select_grammar
from agentic_pipeline.state_models import Stage, StageContext


# ============================================================================
# AST Node unit tests
# ============================================================================


class TestProjectNode:
    def test_empty_project(self):
        p = ProjectNode("test")
        ir = p.to_ir()
        assert ir["node_type"] == "project"
        assert ir["children"] == []

    def test_project_with_page(self):
        p = ProjectNode("test")
        page = PageNode("home")
        p.add(page)
        ir = p.to_ir()
        assert len(ir["children"]) == 1
        assert ir["children"][0]["name"] == "home"

    def test_validate_no_errors(self):
        p = ProjectNode("test")
        assert p.validate() == []


class TestPageNode:
    def test_page_with_components(self):
        page = PageNode("login")
        comp = ComponentNode("form", "formulario")
        page.add(comp)
        ir = page.to_ir()
        assert ir["name"] == "login"
        assert len(ir["children"]) == 1
        assert ir["children"][0]["component_type"] == "formulario"

    def test_page_no_components_validation_error(self):
        page = PageNode("empty")
        errors = page.validate()
        assert any("no components" in e for e in errors)

    def test_page_evaluate(self):
        page = PageNode("home")
        comp = ComponentNode("table", "tabla")
        page.add(comp)
        ev = page.evaluate()
        assert ev["type"] == "page"
        assert ev["name"] == "home"
        assert len(ev["components"]) == 1


class TestComponentNode:
    def test_component_ir(self):
        c = ComponentNode("form", "formulario")
        ir = c.to_ir()
        assert ir["node_type"] == "component"
        assert ir["name"] == "form"
        assert ir["component_type"] == "formulario"

    def test_component_validate(self):
        c = ComponentNode("btn", "boton")
        assert c.validate() == []


class TestEntityNode:
    def test_entity_with_attributes(self):
        e = EntityNode("User")
        e.add_attribute("name", "string")
        e.add_attribute("age", "int")
        ir = e.to_ir()
        assert ir["name"] == "User"
        assert len(ir["attributes"]) == 2
        assert ir["attributes"][0] == {"name": "name", "type": "string"}

    def test_entity_no_attributes_validation_error(self):
        e = EntityNode("Empty")
        errors = e.validate()
        assert any("no attributes" in e for e in errors)


class TestInfraNode:
    def test_infra_with_resources(self):
        node = InfraNode("postgres", "basededatos")
        node.add_resource({"name": "cpu", "value": "4"})
        ir = node.to_ir()
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


class TestParserGLR:
    @pytest.fixture
    def parser(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        return ParserGLR(ctx)

    def test_receive_mission_from_dict(self, parser):
        parser.receive_mission({"tokens": [{"value": "pagina"}, {"value": "login"}]})
        assert "pagina" in parser._input_text
        assert "login" in parser._input_text

    def test_receive_mission_from_string(self, parser):
        parser.receive_mission("pagina login con formulario")
        assert "pagina" in parser._input_text

    def test_analyze(self, parser):
        parser.receive_mission("pagina login con formulario")
        result = parser.analyze()
        assert result.complexity_score == 0.3

    def test_act_returns_ast(self, parser):
        parser.receive_mission("pagina login con formulario")
        plan = parser.reflect_and_plan(parser.analyze())
        output = parser.act(plan)
        assert output.success is True
        assert "ast" in output.output_data
        assert output.output_data["ast"]["node_type"] == "project"

    def test_act_data_grammar(self, parser):
        parser.receive_mission("entidad Usuario nombre:string email:string")
        plan = parser.reflect_and_plan(parser.analyze())
        output = parser.act(plan)
        assert output.success is True
        assert output.output_data["grammar"] == "data"

    def test_act_infra_grammar(self, parser):
        parser.receive_mission("basededatos postgres")
        plan = parser.reflect_and_plan(parser.analyze())
        output = parser.act(plan)
        assert output.success is True

    def test_execute_full_flow(self, parser):
        result = parser.execute(
            {
                "tokens": [
                    {"value": "pagina"},
                    {"value": "login"},
                    {"value": "con"},
                    {"value": "formulario"},
                ]
            }
        )
        assert result.success is True
        assert result.stage == Stage.PARSER

    def test_unknown_grammar(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx, grammar="unknown")
        p.receive_mission("test")
        output = p.act(p.reflect_and_plan(p.analyze()))
        assert output.success is False
        assert "unknown" in (output.error or "")

    def test_learn_and_improve(self, parser):
        parser.receive_mission("test")
        output = parser.act(parser.reflect_and_plan(parser.analyze()))
        parser.learn_and_improve(output.feedback)
        assert True  # no exception


class TestParserGLREdgeCases:
    def test_empty_input(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        result = p.execute("")
        assert result.success is False  # lark can't parse empty

    def test_single_page(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        result = p.execute("modulo pagos")
        assert result.success is True

    def test_tokens_with_stop_words(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        p.receive_mission("pagina de login con formulario")
        assert "de" not in p._input_text.split()


class TestParserGLRMultiGrammar:
    def test_project_grammar(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx, grammar="project")
        result = p.execute("pagina login con formulario")
        assert result.success is True
        assert result.output_data["node_count"] >= 1

    def test_data_grammar(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx, grammar="data")
        result = p.execute("entidad Usuario nombre:string email:string")
        assert result.success is True
