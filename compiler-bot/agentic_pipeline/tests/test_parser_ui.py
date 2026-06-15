"""Tests for UI and Infra grammar parsing with token-based input."""

import pytest

from agentic_pipeline.nodes.parser import ParserGLR
from agentic_pipeline.state_models import Stage, StageContext

UI_TOKENS = [
    {"value": "pagina", "type": "WEB_APP", "category": "domain"},
    {"value": "login", "type": "CNAME", "category": "entity"},
    {"value": "con", "type": "CONNECTOR", "category": "connector"},
    {"value": "formulario", "type": "FORM", "category": "ui"},
    {"value": "y", "type": "CONNECTOR", "category": "connector"},
    {"value": "tabla", "type": "TABLE", "category": "ui"},
]

SECTION_TOKENS = [
    {"value": "seccion", "type": "CNAME", "category": "domain"},
    {"value": "navbar", "type": "CNAME", "category": "entity"},
    {"value": "con", "type": "CONNECTOR", "category": "connector"},
    {"value": "header", "type": "CNAME", "category": "entity"},
]

DB_TOKENS = [
    {"value": "basededatos", "type": "INFRA_KEYWORD", "category": "domain"},
    {"value": "postgres", "type": "CNAME", "category": "entity"},
]

SERVICE_TOKENS = [
    {"value": "servicio", "type": "INFRA_KEYWORD", "category": "domain"},
    {"value": "api", "type": "CNAME", "category": "entity"},
    {"value": "con", "type": "CONNECTOR", "category": "connector"},
    {"value": "cpu", "type": "RESOURCE", "category": "domain"},
    {"value": "4", "type": "NUMBER", "category": "value"},
]


class TestUIGrammar:
    @pytest.fixture
    def parser(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        return ParserGLR(ctx, grammar="ui")

    def test_parse_page_with_components(self, parser):
        result = parser.execute({"tokens": UI_TOKENS})
        assert result.success is True
        assert result.output_data["grammar"] == "ui"

    def test_parse_section(self, parser):
        result = parser.execute({"tokens": SECTION_TOKENS})
        assert result.success is True

    def test_parse_empty_fails(self, parser):
        result = parser.execute({"tokens": []})
        assert result.success is False


class TestInfraGrammar:
    @pytest.fixture
    def parser(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        return ParserGLR(ctx, grammar="infra")

    def test_parse_database(self, parser):
        result = parser.execute({"tokens": DB_TOKENS})
        assert result.success is True

    def test_parse_service(self, parser):
        result = parser.execute({"tokens": SERVICE_TOKENS})
        assert result.success is True

    def test_parse_empty_fails(self, parser):
        result = parser.execute({"tokens": []})
        assert result.success is False


class TestParserIntegration:
    def test_from_lexer_output(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        tokens = {"tokens": UI_TOKENS}
        result = p.execute(tokens)
        assert result.success is True
        ast = result.output_data["ast"]
        assert len(ast.get("nodes", [])) >= 1

    def test_realistic_scenario(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        tokens = {
            "tokens": UI_TOKENS + [
                {"value": "modulo", "type": "CNAME", "category": "entity"},
                {"value": "pagos", "type": "CNAME", "category": "entity"},
            ]
        }
        result = p.execute(tokens)
        assert result.success is True
