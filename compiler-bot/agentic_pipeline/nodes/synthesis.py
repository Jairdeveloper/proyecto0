"""Backward compat: re-export ActionExecutor as SynthesisOrchestrator."""

from agentic_pipeline.nodes.action_executor import (
    ActionExecutor as SynthesisOrchestrator,  # noqa: F401
)
