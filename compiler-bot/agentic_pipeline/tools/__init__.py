"""Tool registry and ToolCommand adapter for Command pattern."""

from __future__ import annotations

from ..tool_registry import ToolResult
from .command_adapter import ToolCommand

__all__ = [
    "ToolCommand",
    "ToolResult",
]
