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

    async def execute(self, name: str, params: dict) -> ToolResult:
        tool = self.get_tool(name)
        if tool is None:
            return ToolResult(success=False, error=f"Tool not found: {name}")
        return await tool.execute(params)
