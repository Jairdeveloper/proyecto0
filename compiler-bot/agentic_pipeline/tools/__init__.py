"""Tool registry and ToolCommand adapter for Command pattern."""

from __future__ import annotations

from agentic_pipeline.tool_registry import ToolResult
from agentic_pipeline.tools.command_adapter import ToolCommand

__all__ = [
    "ToolCommand",
    "ToolResult",
]
