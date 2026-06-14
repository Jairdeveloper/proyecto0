"""IR nodes with 5 layers: Config, Domain, UI, API, Infra."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List


class IRNode(ABC):
    """Abstract IR node with Composite pattern."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.children: List[IRNode] = []

    def add(self, child: IRNode) -> None:
        self.children.append(child)

    @abstractmethod
    def to_code(self, target: str) -> str: ...

    @abstractmethod
    def validate(self) -> List[str]: ...

    @abstractmethod
    def dependencies(self) -> List[str]: ...


# ============================================================================
# Layer 1: Config
# ============================================================================


class IRConfig(IRNode):
    """Configuration layer — project settings, design tokens, env vars."""

    def __init__(
        self,
        name: str,
        settings: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name)
        self.settings: dict[str, Any] = settings or {}

    def to_code(self, target: str) -> str:
        if target == "json":
            import json

            return json.dumps(self.settings, indent=2)
        lines = [f"# Config: {self.name}"]
        for k, v in self.settings.items():
            lines.append(f"{k}={v}")
        return "\n".join(lines)

    def validate(self) -> List[str]:
        return []

    def dependencies(self) -> List[str]:
        return []


# ============================================================================
# Layer 2: Domain / Project
# ============================================================================


class IRProject(IRNode):
    """Domain layer — root project node."""

    def to_code(self, target: str) -> str:
        return "\n".join(c.to_code(target) for c in self.children)

    def validate(self) -> List[str]:
        errors: List[str] = []
        for c in self.children:
            errors.extend(c.validate())
        return [e for e in errors if e]

    def dependencies(self) -> List[str]:
        deps: List[str] = []
        for c in self.children:
            deps.extend(c.dependencies())
        return deps


# ============================================================================
# Layer 3: UI
# ============================================================================


class IRPage(IRNode):
    """UI layer — a page/section with components."""

    def to_code(self, target: str) -> str:
        if target == "react":
            comps = "\n      ".join(c.to_code(target) for c in self.children)
            return (
                f"export default function {self.name}() {{\n"
                f"  return (\n"
                f"    <div>\n"
                f"      {comps}\n"
                f"    </div>\n"
                f"  )\n"
                f"}}"
            )
        return f"<!-- page: {self.name} -->"

    def validate(self) -> List[str]:
        if not self.children:
            return [f"Page '{self.name}' has no components"]
        errors: List[str] = []
        for c in self.children:
            errors.extend(c.validate())
        return [e for e in errors if e]

    def dependencies(self) -> List[str]:
        return [c.name for c in self.children if isinstance(c, IRComponent)]


class IRComponent(IRNode):
    """UI layer — a reusable component."""

    def __init__(
        self,
        name: str,
        component_type: str = "component",
    ) -> None:
        super().__init__(name)
        self.component_type = component_type

    def to_code(self, target: str) -> str:
        if target == "react":
            return f"<{self.name} />"
        return f"<!-- component: {self.name} ({self.component_type}) -->"

    def validate(self) -> List[str]:
        if not self.name:
            return ["Component name cannot be empty"]
        return []

    def dependencies(self) -> List[str]:
        return []


# ============================================================================
# Layer 4: API / Data
# ============================================================================


class IREntity(IRNode):
    """Data layer — a data entity with attributes."""

    def __init__(
        self,
        name: str,
        attributes: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(name)
        self.attributes: list[dict[str, str]] = attributes or []

    def to_code(self, target: str) -> str:
        if target == "prisma":
            if not self.attributes:
                return f"model {self.name} {{}}"
            attrs = "\n  ".join(f"{a['name']} {a['type']}" for a in self.attributes)
            return f"model {self.name} {{\n  {attrs}\n}}"
        if target == "nestjs":
            lines = [f"// entity: {self.name}"]
            for a in self.attributes:
                lines.append(f"  {a['name']}: {a['type']}")
            return "\n".join(lines)
        return f"// entity {self.name}"

    def validate(self) -> List[str]:
        if not self.name:
            return ["Entity name cannot be empty"]
        if not self.attributes:
            return [f"Entity '{self.name}' has no attributes"]
        return []

    def dependencies(self) -> List[str]:
        return []


class IRAPI(IRNode):
    """API layer — an API endpoint or module."""

    def __init__(
        self,
        name: str,
        methods: list[str] | None = None,
    ) -> None:
        super().__init__(name)
        self.methods: list[str] = methods or ["GET"]

    def to_code(self, target: str) -> str:
        if target == "nestjs":
            methods = ", ".join(self.methods)
            return (
                f"@Controller('{self.name.lower()}')\n"
                f"export class {self.name}Controller {{\n"
                f"  // methods: {methods}\n"
                f"}}"
            )
        return f"// api: {self.name} [{', '.join(self.methods)}]"

    def validate(self) -> List[str]:
        if not self.name:
            return ["API name cannot be empty"]
        return []

    def dependencies(self) -> List[str]:
        return []


# ============================================================================
# Layer 5: Infra
# ============================================================================


class IRInfra(IRNode):
    """Infrastructure layer — databases, services, deployments."""

    def __init__(
        self,
        name: str,
        infra_type: str = "resource",
        resources: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(name)
        self.infra_type = infra_type
        self.resources: list[dict[str, Any]] = resources or []

    def to_code(self, target: str) -> str:
        if target == "docker":
            if self.infra_type == "database":
                return (
                    f"{self.name}:\n"
                    f"  image: postgres:15\n"
                    f"  environment:\n"
                    f"    POSTGRES_DB: {self.name}\n"
                )
            if self.infra_type == "service":
                return f"{self.name}:\n  build: .\n  ports:\n    - '3000:3000'\n"
        if target == "yaml":
            import yaml  # type: ignore[import-untyped]

            return yaml.dump(
                {self.name: {"type": self.infra_type, "resources": self.resources}},
                default_flow_style=False,
            )
        return f"# infra: {self.name} ({self.infra_type})"

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.name:
            errors.append("Infra resource name cannot be empty")
        if not self.infra_type:
            errors.append("Infra resource type cannot be empty")
        return errors

    def dependencies(self) -> List[str]:
        return []
