"""Tests for AST Visitor pattern — IASTVisitor and concrete visitors."""

import pytest

from agentic_pipeline.nodes.ast_nodes import (
    ComponentNode,
    EntityNode,
    InfraNode,
    PageNode,
    ProjectNode,
)
from agentic_pipeline.nodes.ast_visitor import IASTVisitor, TreeWalkingVisitor
from agentic_pipeline.nodes.evaluation_visitor import EvaluationVisitor
from agentic_pipeline.nodes.validation_visitor import ValidationVisitor


class TestIASTVisitor:
    def test_interface_cannot_instantiate(self):
        with pytest.raises(TypeError):
            IASTVisitor()  # type: ignore[abstract]

    def test_tree_walking_can_instantiate(self):
        v = TreeWalkingVisitor()
        assert isinstance(v, IASTVisitor)


class TestAcceptDispatch:
    def test_accept_project(self):
        node = ProjectNode("test")
        visited: list[str] = []

        class SpyVisitor(IASTVisitor):
            def visit_project(self, n):
                visited.append("project")
            def visit_page(self, n):
                visited.append("page")
            def visit_component(self, n):
                visited.append("component")
            def visit_entity(self, n):
                visited.append("entity")
            def visit_infra(self, n):
                visited.append("infra")

        node.accept(SpyVisitor())
        assert visited == ["project"]

    def test_accept_page(self):
        node = PageNode("test")
        visited: list[str] = []

        class SpyVisitor(IASTVisitor):
            def visit_project(self, n):
                visited.append("project")
            def visit_page(self, n):
                visited.append("page")
            def visit_component(self, n):
                visited.append("component")
            def visit_entity(self, n):
                visited.append("entity")
            def visit_infra(self, n):
                visited.append("infra")

        node.accept(SpyVisitor())
        assert visited == ["page"]

    def test_accept_component(self):
        node = ComponentNode("btn", "boton")
        visited: list[str] = []

        class SpyVisitor(IASTVisitor):
            def visit_project(self, n):
                visited.append("project")
            def visit_page(self, n):
                visited.append("page")
            def visit_component(self, n):
                visited.append("component")
            def visit_entity(self, n):
                visited.append("entity")
            def visit_infra(self, n):
                visited.append("infra")

        node.accept(SpyVisitor())
        assert visited == ["component"]

    def test_accept_entity(self):
        node = EntityNode("User")
        visited: list[str] = []

        class SpyVisitor(IASTVisitor):
            def visit_project(self, n):
                visited.append("project")
            def visit_page(self, n):
                visited.append("page")
            def visit_component(self, n):
                visited.append("component")
            def visit_entity(self, n):
                visited.append("entity")
            def visit_infra(self, n):
                visited.append("infra")

        node.accept(SpyVisitor())
        assert visited == ["entity"]

    def test_accept_infra(self):
        node = InfraNode("db", "database")
        visited: list[str] = []

        class SpyVisitor(IASTVisitor):
            def visit_project(self, n):
                visited.append("project")
            def visit_page(self, n):
                visited.append("page")
            def visit_component(self, n):
                visited.append("component")
            def visit_entity(self, n):
                visited.append("entity")
            def visit_infra(self, n):
                visited.append("infra")

        node.accept(SpyVisitor())
        assert visited == ["infra"]


class TestTreeWalkingVisitor:
    def test_walk_project_children(self):
        root = ProjectNode("root")
        page1 = PageNode("home")
        page2 = PageNode("about")
        root.add(page1)
        root.add(page2)
        visited: list[str] = []

        class WalkSpy(TreeWalkingVisitor):
            def visit_page(self, node):
                visited.append(node.name)
                super().visit_page(node)

        root.accept(WalkSpy())
        assert visited == ["home", "about"]

    def test_walk_nested_structure(self):
        root = ProjectNode("root")
        page = PageNode("dashboard")
        comp = ComponentNode("chart", "grafico")
        page.add(comp)
        root.add(page)
        visited: list[str] = []

        class WalkSpy(TreeWalkingVisitor):
            def visit_page(self, node):
                visited.append(f"page:{node.name}")
                super().visit_page(node)
            def visit_component(self, node):
                visited.append(f"comp:{node.name}")
                super().visit_component(node)

        root.accept(WalkSpy())
        assert visited == ["page:dashboard", "comp:chart"]

    def test_leaf_nodes_do_nothing(self):
        comp = ComponentNode("btn", "boton")
        entity = EntityNode("User")
        infra = InfraNode("db", "database")

        tw = TreeWalkingVisitor()
        result_comp = comp.accept(tw)
        result_entity = entity.accept(tw)
        result_infra = infra.accept(tw)

        assert result_comp is tw
        assert result_entity is tw
        assert result_infra is tw


class TestValidationVisitor:
    def test_empty_page_has_error(self):
        page = PageNode("empty")
        errors = page.accept(ValidationVisitor()).errors
        assert any("no components" in e.lower() for e in errors)

    def test_page_with_components_no_error(self):
        page = PageNode("home")
        page.add(ComponentNode("btn", "boton"))
        errors = page.accept(ValidationVisitor()).errors
        page_errors = [e for e in errors if "page" in e.lower()]
        assert all("no components" not in e.lower() for e in page_errors)

    def test_empty_entity_has_error(self):
        entity = EntityNode("Empty")
        errors = entity.accept(ValidationVisitor()).errors
        assert any("no attributes" in e.lower() for e in errors)

    def test_entity_with_attributes_no_error(self):
        entity = EntityNode("User")
        entity.add_attribute("name", "string")
        errors = entity.accept(ValidationVisitor()).errors
        entity_errors = [e for e in errors if "entity" in e.lower()]
        assert all("no attributes" not in e.lower() for e in entity_errors)

    def test_valid_ast_no_errors(self):
        root = ProjectNode("app")
        page = PageNode("home")
        page.add(ComponentNode("btn", "boton"))
        root.add(page)
        entity = EntityNode("User")
        entity.add_attribute("name", "string")
        root.add(entity)
        errors = root.accept(ValidationVisitor()).errors
        assert errors == []

    def test_multiple_errors_collected(self):
        root = ProjectNode("app")
        root.add(PageNode("empty1"))
        root.add(PageNode("empty2"))
        errors = root.accept(ValidationVisitor()).errors
        page_errors = [e for e in errors if "page" in e.lower()]
        assert len(page_errors) == 2


class TestEvaluationVisitor:
    def test_evaluate_empty_project(self):
        p = ProjectNode("test")
        result = p.accept(EvaluationVisitor())
        assert result["type"] == "project"
        assert result["pages"] == []

    def test_evaluate_project_with_pages(self):
        p = ProjectNode("app")
        p.add(PageNode("home"))
        p.add(PageNode("about"))
        result = p.accept(EvaluationVisitor())
        assert len(result["pages"]) == 2
        assert result["pages"][0]["name"] == "home"
        assert result["pages"][1]["name"] == "about"

    def test_evaluate_page_with_components(self):
        page = PageNode("dashboard")
        page.add(ComponentNode("chart", "grafico"))
        page.add(ComponentNode("table", "tabla"))
        result = page.accept(EvaluationVisitor())
        assert result["type"] == "page"
        assert len(result["components"]) == 2
        assert result["components"][0]["component_type"] == "grafico"

    def test_evaluate_component(self):
        comp = ComponentNode("form", "formulario")
        result = comp.accept(EvaluationVisitor())
        assert result["type"] == "component"
        assert result["name"] == "form"
        assert result["component_type"] == "formulario"

    def test_evaluate_entity(self):
        entity = EntityNode("User")
        entity.add_attribute("name", "string")
        result = entity.accept(EvaluationVisitor())
        assert result["type"] == "entity"
        assert len(result["attributes"]) == 1

    def test_evaluate_infra(self):
        infra = InfraNode("db", "postgres")
        result = infra.accept(EvaluationVisitor())
        assert result["type"] == "infra"
        assert result["infra_type"] == "postgres"
