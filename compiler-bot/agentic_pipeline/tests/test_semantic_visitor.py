"""Tests for SemanticVisitor and SemanticAnalyzer stage."""

import pytest

from agentic_pipeline.nodes.semantic_analyzer import (
    SemanticAnalyzer,
    SemanticVisitor,
)
from agentic_pipeline.nodes.symbol_table import SymbolTable
from agentic_pipeline.nodes.type_systems import TypeRegistry
from agentic_pipeline.state_models import Stage, StageContext

# ============================================================================
# SemanticVisitor tests
# ============================================================================


class TestSemanticVisitor:
    def test_visitor_project(self):
        st = SymbolTable()
        visitor = SemanticVisitor(st)
        ir = {"node_type": "project", "children": []}
        visitor.visit(ir)
        assert "$project" in st.current_scope()

    def test_visitor_page_creates_scope(self):
        st = SymbolTable()
        visitor = SemanticVisitor(st)
        ir = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "page",
                    "name": "login",
                    "children": [
                        {
                            "node_type": "component",
                            "name": "form",
                            "component_type": "formulario",
                        },
                    ],
                }
            ],
        }
        visitor.visit(ir)
        assert st.has_symbol("$project")
        assert not st.has_symbol("login")
        assert not st.has_symbol("form")

    def test_visitor_detects_empty_page(self):
        st = SymbolTable()
        visitor = SemanticVisitor(st)
        ir = {
            "node_type": "project",
            "children": [
                {"node_type": "page", "name": "empty", "children": []},
            ],
        }
        visitor.visit(ir)
        assert any("no components" in e for e in visitor.errors)

    def test_visitor_entity(self):
        st = SymbolTable()
        visitor = SemanticVisitor(st)
        ir = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "entity",
                    "name": "User",
                    "attributes": [{"name": "email", "type": "string"}],
                },
            ],
        }
        visitor.visit(ir)
        assert st.has_symbol("User")

    def test_visitor_entity_no_attributes(self):
        st = SymbolTable()
        visitor = SemanticVisitor(st)
        ir = {
            "node_type": "project",
            "children": [
                {"node_type": "entity", "name": "Empty", "attributes": []},
            ],
        }
        visitor.visit(ir)
        assert any("at least one" in e for e in visitor.errors)

    def test_visitor_infra(self):
        st = SymbolTable()
        visitor = SemanticVisitor(st)
        ir = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "infra",
                    "name": "postgres",
                    "infra_type": "database",
                    "resources": [],
                },
            ],
        }
        visitor.visit(ir)
        assert st.has_symbol("postgres")

    def test_visitor_unknown_node_warning(self):
        st = SymbolTable()
        visitor = SemanticVisitor(st)
        ir = {"node_type": "unknown_thing", "children": []}
        visitor.visit(ir)
        assert any("Unknown" in w for w in visitor.warnings)

    def test_visitor_page_exit_restores_scope(self):
        st = SymbolTable()
        st.define("outer", {"type": "global"})
        visitor = SemanticVisitor(st)
        ir = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "page",
                    "name": "inside",
                    "children": [
                        {
                            "node_type": "component",
                            "name": "btn",
                            "component_type": "button",
                        },
                    ],
                },
            ],
        }
        visitor.visit(ir)
        # After exit_page, the page's scope should be popped
        # but components defined inside shouldn't be in global scope
        scope_keys = st.current_scope().keys()
        assert "outer" in scope_keys
        assert "btn" not in scope_keys

    def test_visitor_registry_injection(self):
        reg = TypeRegistry()
        reg.register("ui", "page", lambda v: ["custom error"])
        st = SymbolTable()
        visitor = SemanticVisitor(st, registry=reg)
        ir = {
            "node_type": "project",
            "children": [
                {"node_type": "page", "name": "p", "children": []},
            ],
        }
        visitor.visit(ir)
        assert any("custom error" in e for e in visitor.errors)


# ============================================================================
# SemanticAnalyzer stage tests
# ============================================================================


class TestSemanticAnalyzer:
    @pytest.fixture
    def analyzer(self):
        ctx = StageContext(stage=Stage.SEMANTIC_ANALYZER, input_data="")
        return SemanticAnalyzer(ctx)

    def test_receive_mission_from_dict(self, analyzer):
        analyzer.receive_mission({"ast": {"node_type": "project", "children": []}})
        assert analyzer._input_ir == {"node_type": "project", "children": []}

    def test_receive_mission_from_ir_direct(self, analyzer):
        analyzer.receive_mission({"node_type": "project", "children": []})
        assert analyzer._input_ir == {"node_type": "project", "children": []}

    def test_receive_mission_fallback(self, analyzer):
        analyzer.receive_mission("invalid")
        assert analyzer._input_ir == {"node_type": "project", "children": []}

    def test_analyze(self, analyzer):
        analyzer.receive_mission({"node_type": "project", "children": []})
        result = analyzer.analyze()
        assert result.complexity_score == 0.4

    def test_reflect_and_plan(self, analyzer):
        result = analyzer.reflect_and_plan(analyzer.analyze())
        assert len(result.steps) == 3

    def test_act_returns_success_on_valid(self, analyzer):
        analyzer.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {
                            "node_type": "page",
                            "name": "login",
                            "children": [
                                {
                                    "node_type": "component",
                                    "name": "form",
                                    "component_type": "formulario",
                                },
                            ],
                        },
                    ],
                }
            }
        )
        plan = analyzer.reflect_and_plan(analyzer.analyze())
        output = analyzer.act(plan)
        assert output.success is True
        assert "semantic_errors" in output.output_data
        assert output.output_data["semantic_errors"] == []

    def test_act_returns_errors_on_empty_page(self, analyzer):
        analyzer.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {"node_type": "page", "name": "empty", "children": []},
                    ],
                }
            }
        )
        plan = analyzer.reflect_and_plan(analyzer.analyze())
        output = analyzer.act(plan)
        assert output.success is False
        assert len(output.output_data["semantic_errors"]) > 0

    def test_execute_full_flow(self, analyzer):
        result = analyzer.execute(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {
                            "node_type": "page",
                            "name": "login",
                            "children": [
                                {
                                    "node_type": "component",
                                    "name": "form",
                                    "component_type": "formulario",
                                },
                            ],
                        },
                    ],
                }
            }
        )
        assert result.stage == Stage.SEMANTIC_ANALYZER
        assert result.success is True

    def test_learn_and_improve(self, analyzer):
        analyzer.receive_mission({"node_type": "project", "children": []})
        analyzer.learn_and_improve({})
        assert True

    def test_symbol_table_in_output(self, analyzer):
        analyzer.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {
                            "node_type": "page",
                            "name": "home",
                            "children": [
                                {
                                    "node_type": "component",
                                    "name": "navbar",
                                    "component_type": "navigation",
                                },
                            ],
                        },
                    ],
                }
            }
        )
        plan = analyzer.reflect_and_plan(analyzer.analyze())
        output = analyzer.act(plan)
        snapshot = output.output_data["symbol_table_snapshot"]
        assert isinstance(snapshot, list)
        assert len(snapshot) >= 1

    def test_warnings_on_unknown_node(self, analyzer):
        analyzer.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {"node_type": "weird_node", "name": "x"},
                    ],
                }
            }
        )
        plan = analyzer.reflect_and_plan(analyzer.analyze())
        output = analyzer.act(plan)
        assert len(output.output_data["warnings"]) > 0


class TestSemanticAnalyzerEdgeCases:
    def test_empty_ir(self):
        ctx = StageContext(stage=Stage.SEMANTIC_ANALYZER, input_data="")
        a = SemanticAnalyzer(ctx)
        result = a.execute({"ast": {"node_type": "project", "children": []}})
        assert result.success is True  # empty is valid

    def test_deeply_nested(self):
        ctx = StageContext(stage=Stage.SEMANTIC_ANALYZER, input_data="")
        a = SemanticAnalyzer(ctx)
        ir = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "page",
                    "name": "dashboard",
                    "children": [
                        {
                            "node_type": "component",
                            "name": "chart",
                            "component_type": "grafico",
                            "children": [],
                        },
                    ],
                },
                {
                    "node_type": "entity",
                    "name": "Metric",
                    "attributes": [
                        {"name": "value", "type": "int"},
                        {"name": "date", "type": "date"},
                    ],
                },
                {
                    "node_type": "infra",
                    "name": "redis",
                    "infra_type": "service",
                    "resources": [],
                },
            ],
        }
        result = a.execute({"ast": ir})
        assert result.success is True

    def test_multiple_errors(self):
        ctx = StageContext(stage=Stage.SEMANTIC_ANALYZER, input_data="")
        a = SemanticAnalyzer(ctx)
        ir = {
            "node_type": "project",
            "children": [
                {"node_type": "page", "name": "", "children": []},
                {
                    "node_type": "entity",
                    "name": "Bad",
                    "attributes": [{"name": "x", "type": "invalid"}],
                },
            ],
        }
        result = a.execute({"ast": ir})
        assert result.success is False
        assert len(result.output_data["semantic_errors"]) >= 2
