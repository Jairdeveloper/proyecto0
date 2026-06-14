"""Type registry with domain-specific type validators."""

from __future__ import annotations

from typing import Any, Callable

Validator = Callable[[dict[str, Any]], list[str]]


class TypeRegistry:
    """Registry of type validators organized by domain."""

    def __init__(self) -> None:
        self._types: dict[str, dict[str, Validator]] = {}

    def register(self, domain: str, type_name: str, validator: Validator) -> None:
        self._types.setdefault(domain, {})[type_name] = validator

    def validate(self, domain: str, type_name: str, value: dict[str, Any]) -> list[str]:
        validator = self._types.get(domain, {}).get(type_name)
        if validator is not None:
            return validator(value)
        return [f"Unknown type '{type_name}' in domain '{domain}'"]

    def list_types(self, domain: str) -> list[str]:
        return list(self._types.get(domain, {}).keys())

    def has_type(self, domain: str, type_name: str) -> bool:
        return type_name in self._types.get(domain, {})

    def domains(self) -> list[str]:
        return list(self._types.keys())


# ============================================================================
# Domain validators
# ============================================================================


def ui_component_validator(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not value.get("name"):
        errors.append("Component name cannot be empty")
    if not value.get("component_type") and not value.get("type"):
        errors.append("Component type is required (component_type or type)")
    return errors


def data_entity_validator(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not value.get("name"):
        errors.append("Entity name cannot be empty")
    attrs = value.get("attributes", [])
    if not attrs:
        errors.append("Entity must have at least one attribute")
    valid_types = {"string", "int", "boolean", "date", "relation"}
    for attr in attrs:
        if isinstance(attr, dict):
            attr_type = attr.get("type", "").lower()
            if attr_type not in valid_types:
                errors.append(
                    f"Invalid attribute type '{attr.get('type')}' "
                    f"in '{attr.get('name')}'"
                )
    return errors


def infra_resource_validator(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not value.get("name"):
        errors.append("Resource name cannot be empty")
    if not value.get("infra_type"):
        errors.append("Infrastructure type cannot be empty")
    return errors


def page_validator(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not value.get("name"):
        errors.append("Page name cannot be empty")
    children = value.get("children", [])
    if not children:
        errors.append("Page has no components")
    return errors


# ============================================================================
# Default registry singleton
# ============================================================================

_DEFAULT_REGISTRY: TypeRegistry | None = None


def get_default_registry() -> TypeRegistry:
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        reg = TypeRegistry()
        reg.register("ui", "component", ui_component_validator)
        reg.register("ui", "page", page_validator)
        reg.register("ui", "layout", page_validator)
        reg.register("data", "entity", data_entity_validator)
        reg.register("infra", "resource", infra_resource_validator)
        reg.register("infra", "database", infra_resource_validator)
        reg.register("infra", "service", infra_resource_validator)
        _DEFAULT_REGISTRY = reg
    return _DEFAULT_REGISTRY
