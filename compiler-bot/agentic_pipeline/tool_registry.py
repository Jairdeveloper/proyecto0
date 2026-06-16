"""Tool — abstract base for agent tools.  ToolRegistry — central registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class Parameter:
    name: str
    type: str
    description: str = ""
    required: bool = True


class Tool(ABC):
    name: str = ""
    description: str = ""
    parameters: list[Parameter] = field(default_factory=list)

    @abstractmethod
    async def execute(self, params: dict) -> ToolResult: ...


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def list_available(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": [
                    {"name": p.name, "type": p.type, "description": p.description}
                    for p in t.parameters
                ],
            }
            for t in self._tools.values()
        ]

    @classmethod
    def build_default(cls) -> ToolRegistry:
        """Crea un ToolRegistry con todas las herramientas por defecto.

        Equivalente a _build_default_tool_registry() en agent_loop.py.
        """
        from .tools.read_file import ReadFileTool
        from .tools.write_file import WriteFileTool
        from .tools.run_command import RunCommandTool
        from .tools.search_code import SearchCodeTool
        from .tools.generate_code import GenerateCodeTool
        from .tools.ask_user import AskUserTool
        from .tools.explain import ExplainTool

        registry = cls()
        registry.register(ReadFileTool())
        registry.register(WriteFileTool())
        registry.register(RunCommandTool())
        registry.register(SearchCodeTool())
        registry.register(GenerateCodeTool())
        registry.register(AskUserTool())
        registry.register(ExplainTool())
        return registry

    async def execute(self, name: str, params: dict) -> ToolResult:
        tool = self.get_tool(name)
        if tool is None:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        return await tool.execute(params)
