"""Tests for IR Builder and DependencyGraph."""

import pytest

from agentic_pipeline.nodes.ir_builder import DependencyGraph, IRBuilder
from agentic_pipeline.nodes.ir_nodes import (
    IRAPI,
    IREntity,
    IRInfra,
    IRPage,
)


class TestDependencyGraph:
    def test_empty_graph(self):
        g = DependencyGraph()
        assert g.resolve() == []
        assert g.has_cycle() is False

    def test_single_node(self):
        g = DependencyGraph()
        node = IRPage("home")
        g.add_node(node)
        order = g.resolve()
        assert "home" in order

    def test_simple_chain(self):
        g = DependencyGraph()
        g.add_node(IRPage("a"))
        g.add_node(IRPage("b"))
        g.add_dependency("b", "a")
        order = g.resolve()
        assert order.index("a") < order.index("b")

    def test_cycle_detection(self):
        g = DependencyGraph()
        g.add_node(IRPage("a"))
        g.add_node(IRPage("b"))
        g.add_dependency("a", "b")
        g.add_dependency("b", "a")
        assert g.has_cycle() is True

    def test_cycle_returns_empty_order(self):
        g = DependencyGraph()
        g.add_node(IRPage("a"))
        g.add_node(IRPage("b"))
        g.add_dependency("a", "b")
        g.add_dependency("b", "a")
        assert g.resolve() == []

    def test_validate_unknown_dependency(self):
        g = DependencyGraph()
        node = IRPage("a")
        g.add_node(node)
        g.add_dependency("a", "nonexistent")
        errors = g.validate()
        assert any("unknown" in e for e in errors)

    def test_validate_cycle(self):
        g = DependencyGraph()
        g.add_node(IRPage("a"))
        g.add_node(IRPage("b"))
        g.add_dependency("a", "b")
        g.add_dependency("b", "a")
        errors = g.validate()
        assert any("cycle" in e for e in errors)

    def test_add_dependency_auto_creates_entry(self):
        g = DependencyGraph()
        g.add_dependency("new_node", "dep")
        assert "new_node" in g._edges


class TestIRBuilder:
    @pytest.fixture
    def builder(self):
        return IRBuilder()

    def test_build_empty(self, builder):
        root = builder.build({"node_type": "project", "children": []})
        assert root.name == "project"
        assert len(root.children) == 0

    def test_build_page_with_component(self, builder):
        ir_dict = {
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
        root = builder.build(ir_dict)
        assert len(root.children) == 1
        page = root.children[0]
        assert page.name == "login"
        assert len(page.children) == 1
        assert page.children[0].name == "form"

    def test_build_entity(self, builder):
        ir_dict = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "entity",
                    "name": "User",
                    "attributes": [{"name": "email", "type": "string"}],
                },
            ],
        }
        root = builder.build(ir_dict)
        assert len(root.children) == 1
        entity = root.children[0]
        assert entity.name == "User"
        assert isinstance(entity, IREntity)

    def test_build_infra(self, builder):
        ir_dict = {
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
        root = builder.build(ir_dict)
        assert len(root.children) == 1
        infra = root.children[0]
        assert infra.name == "postgres"
        assert isinstance(infra, IRInfra)

    def test_build_api(self, builder):
        ir_dict = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "api",
                    "name": "Auth",
                    "methods": ["POST", "GET"],
                },
            ],
        }
        root = builder.build(ir_dict)
        assert len(root.children) == 1
        api = root.children[0]
        assert api.name == "Auth"
        assert isinstance(api, IRAPI)

    def test_build_config(self, builder):
        ir_dict = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "config",
                    "name": "app",
                    "settings": {"port": 3000},
                },
            ],
        }
        root = builder.build(ir_dict)
        assert len(root.children) == 1

    def test_build_with_config(self, builder):
        ir_dict = {"node_type": "project", "children": []}
        root = builder.build_with_config(ir_dict, {"debug": True})
        assert len(root.children) == 1

    def test_validate_valid(self, builder):
        ir_dict = {
            "node_type": "project",
            "children": [
                {
                    "node_type": "page",
                    "name": "home",
                    "children": [
                        {
                            "node_type": "component",
                            "name": "nav",
                            "component_type": "navbar",
                        },
                    ],
                },
            ],
        }
        builder.build(ir_dict)
        errors = builder.validate()
        assert errors == []

    def test_validate_empty_page(self, builder):
        ir_dict = {
            "node_type": "project",
            "children": [
                {"node_type": "page", "name": "empty", "children": []},
            ],
        }
        builder.build(ir_dict)
        errors = builder.validate()
        assert any("no components" in e for e in errors)

    def test_dep_graph_populated(self, builder):
        ir_dict = {
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
                        },
                    ],
                },
            ],
        }
        builder.build(ir_dict)
        assert not builder.dep_graph.has_cycle()
        assert len(builder.dep_graph.resolve()) >= 1

    def test_unknown_node_type(self, builder):
        ir_dict = {
            "node_type": "project",
            "children": [
                {"node_type": "unknown_type", "name": "x"},
            ],
        }
        root = builder.build(ir_dict)
        assert len(root.children) == 0  # unknown nodes skipped
