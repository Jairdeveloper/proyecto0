"""Tests for TypeRegistry and domain validators."""

from agentic_pipeline.nodes.type_systems import (
    TypeRegistry,
    data_entity_validator,
    get_default_registry,
    infra_resource_validator,
    page_validator,
    ui_component_validator,
)


class TestTypeRegistry:
    def test_register_and_validate(self):
        reg = TypeRegistry()
        reg.register("test", "foo", lambda v: [] if v.get("ok") else ["not ok"])
        assert reg.validate("test", "foo", {"ok": True}) == []
        assert reg.validate("test", "foo", {"ok": False}) == ["not ok"]

    def test_validate_unknown_type(self):
        reg = TypeRegistry()
        errors = reg.validate("unknown", "type", {})
        assert any("Unknown type" in e for e in errors)

    def test_list_types(self):
        reg = TypeRegistry()
        reg.register("ui", "button", lambda v: [])
        reg.register("ui", "form", lambda v: [])
        types = reg.list_types("ui")
        assert "button" in types
        assert "form" in types

    def test_has_type(self):
        reg = TypeRegistry()
        reg.register("data", "entity", lambda v: [])
        assert reg.has_type("data", "entity") is True
        assert reg.has_type("data", "nonexistent") is False

    def test_domains(self):
        reg = TypeRegistry()
        reg.register("a", "x", lambda v: [])
        reg.register("b", "y", lambda v: [])
        assert "a" in reg.domains()
        assert "b" in reg.domains()


class TestUIComponentValidator:
    def test_valid_component(self):
        errors = ui_component_validator({"name": "form", "component_type": "formulario"})
        assert errors == []

    def test_missing_name(self):
        errors = ui_component_validator({"component_type": "form"})
        assert any("name" in e for e in errors)

    def test_missing_type(self):
        errors = ui_component_validator({"name": "form"})
        assert any("type is required" in e for e in errors)

    def test_empty_name(self):
        errors = ui_component_validator({"name": "", "component_type": "form"})
        assert any("empty" in e for e in errors)


class TestPageValidator:
    def test_valid_page(self):
        errors = page_validator(
            {
                "name": "login",
                "children": [{"node_type": "component"}],
            }
        )
        assert errors == []

    def test_page_no_children(self):
        errors = page_validator({"name": "empty", "children": []})
        assert any("no components" in e for e in errors)

    def test_page_empty_name(self):
        errors = page_validator({"name": "", "children": []})
        assert any("empty" in e for e in errors)


class TestDataEntityValidator:
    def test_valid_entity(self):
        errors = data_entity_validator(
            {
                "name": "User",
                "attributes": [
                    {"name": "email", "type": "string"},
                ],
            }
        )
        assert errors == []

    def test_no_attributes(self):
        errors = data_entity_validator({"name": "Empty", "attributes": []})
        assert any("at least one" in e for e in errors)

    def test_invalid_attr_type(self):
        errors = data_entity_validator(
            {
                "name": "Bad",
                "attributes": [{"name": "foo", "type": "invalid_type"}],
            }
        )
        assert any("Invalid attribute type" in e for e in errors)

    def test_empty_name(self):
        errors = data_entity_validator({"name": "", "attributes": []})
        assert any("empty" in e for e in errors)


class TestInfraResourceValidator:
    def test_valid_resource(self):
        errors = infra_resource_validator(
            {
                "name": "postgres",
                "infra_type": "database",
            }
        )
        assert errors == []

    def test_empty_name(self):
        errors = infra_resource_validator({"name": "", "infra_type": "db"})
        assert any("empty" in e for e in errors)

    def test_empty_type(self):
        errors = infra_resource_validator({"name": "db", "infra_type": ""})
        assert any("empty" in e for e in errors)


class TestDefaultRegistry:
    def test_get_default_registry(self):
        reg = get_default_registry()
        assert reg.has_type("ui", "component")
        assert reg.has_type("ui", "page")
        assert reg.has_type("data", "entity")
        assert reg.has_type("infra", "resource")
        assert reg.has_type("infra", "database")
        assert reg.has_type("infra", "service")

    def test_default_registry_singleton(self):
        reg1 = get_default_registry()
        reg2 = get_default_registry()
        assert reg1 is reg2
