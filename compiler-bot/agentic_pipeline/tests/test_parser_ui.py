"""Tests for UI and Infra grammar parsing."""

import pytest

from agentic_pipeline.nodes.parser import ParserGLR
from agentic_pipeline.state_models import Stage, StageContext


class TestUIGrammar:
    @pytest.fixture
    def parser(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        return ParserGLR(ctx, grammar="ui")

    def test_parse_page_with_components(self, parser):
        result = parser.execute("pagina login con formulario y tabla")
        assert result.success is True
        assert result.output_data["grammar"] == "ui"

    def test_parse_section(self, parser):
        result = parser.execute("seccion navbar con header")
        assert result.success is True

    def test_parse_empty_fails(self, parser):
        result = parser.execute("")
        assert result.success is False


class TestInfraGrammar:
    @pytest.fixture
    def parser(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        return ParserGLR(ctx, grammar="infra")

    def test_parse_database(self, parser):
        result = parser.execute("basededatos postgres")
        assert result.success is True

    def test_parse_service(self, parser):
        result = parser.execute("servicio api con cpu 4")
        assert result.success is True

    def test_parse_empty_fails(self, parser):
        result = parser.execute("")
        assert result.success is False


class TestParserIntegration:
    def test_from_lexer_output(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        tokens = {
            "tokens": [
                {"value": "pagina", "type": "WEB_APP", "category": "domain"},
                {"value": "login", "type": "CNAME", "category": "text"},
                {"value": "con", "type": "CONNECTOR", "category": "connector"},
                {"value": "formulario", "type": "FORM", "category": "ui"},
                {"value": "y", "type": "CONNECTOR", "category": "connector"},
                {"value": "tabla", "type": "TABLE", "category": "ui"},
            ]
        }
        result = p.execute(tokens)
        assert result.success is True
        assert result.output_data["node_count"] >= 1

    def test_realistic_scenario(self):
        ctx = StageContext(stage=Stage.PARSER, input_data="")
        p = ParserGLR(ctx)
        result = p.execute("pagina login con formulario y tabla modulo pagos")
        assert result.success is True
