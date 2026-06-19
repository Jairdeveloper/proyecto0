"""Tests for IRExportVisitor — AST to IR serialization."""

from agentic_pipeline.nodes.ast_nodes import (
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)
from agentic_pipeline.nodes.ir_export_visitor import IRExportVisitor


class TestIRExportProject:
    def test_empty_project(self):
        p = ProjectNode("test")
        result = p.accept(IRExportVisitor())
        assert result["node_type"] == "project"
        assert result["name"] == "test"
        assert result["children"] == []

    def test_project_with_pages(self):
        p = ProjectNode("app")
        p.add(PageNode("home"))
        p.add(PageNode("about"))
        result = p.accept(IRExportVisitor())
        assert len(result["children"]) == 2
        assert result["children"][0]["name"] == "home"
        assert result["children"][1]["name"] == "about"


class TestIRExportPage:
    def test_page_with_children(self):
        page = PageNode("login")
        comp = ComponentNode("form", "formulario")
        page.add(comp)
        result = page.accept(IRExportVisitor())
        assert result["node_type"] == "page"
        assert result["name"] == "login"
        assert len(result["children"]) == 1
        assert result["children"][0]["component_type"] == "formulario"

    def test_empty_page(self):
        page = PageNode("empty")
        result = page.accept(IRExportVisitor())
        assert result["children"] == []


class TestIRExportComponent:
    def test_component(self):
        comp = ComponentNode("btn", "boton")
        result = comp.accept(IRExportVisitor())
        assert result["node_type"] == "component"
        assert result["name"] == "btn"
        assert result["component_type"] == "boton"


class TestIRExportEntity:
    def test_entity_with_attributes(self):
        entity = EntityNode("User")
        entity.add_attribute("name", "string")
        entity.add_attribute("age", "int")
        result = entity.accept(IRExportVisitor())
        assert result["node_type"] == "entity"
        assert result["name"] == "User"
        assert len(result["attributes"]) == 2
        assert result["attributes"][0] == {"name": "name", "type": "string"}

    def test_empty_entity(self):
        entity = EntityNode("Empty")
        result = entity.accept(IRExportVisitor())
        assert result["attributes"] == []


class TestIRExportInfra:
    def test_infra_with_resources(self):
        infra = InfraNode("postgres", "basededatos")
        infra.add_resource({"name": "cpu", "value": "4"})
        result = infra.accept(IRExportVisitor())
        assert result["node_type"] == "infra"
        assert result["name"] == "postgres"
        assert result["infra_type"] == "basededatos"
        assert len(result["resources"]) == 1

    def test_infra_no_resources(self):
        infra = InfraNode("redis", "cache")
        result = infra.accept(IRExportVisitor())
        assert result["resources"] == []


class TestIRExportNested:
    def test_deep_nesting(self):
        root = ProjectNode("app")
        page = PageNode("dashboard")
        comp = ComponentNode("chart", "grafico")
        page.add(comp)
        root.add(page)
        result = root.accept(IRExportVisitor())
        assert result["node_type"] == "project"
        assert result["children"][0]["node_type"] == "page"
        assert result["children"][0]["children"][0]["node_type"] == "component"
        assert result["children"][0]["children"][0]["name"] == "chart"

    def test_multiple_entities(self):
        root = ProjectNode("data")
        e1 = EntityNode("User")
        e1.add_attribute("name", "string")
        e2 = EntityNode("Post")
        e2.add_attribute("title", "string")
        root.add(e1)
        root.add(e2)
        result = root.accept(IRExportVisitor())
        assert len(result["children"]) == 2
        assert result["children"][0]["name"] == "User"
        assert result["children"][1]["name"] == "Post"
