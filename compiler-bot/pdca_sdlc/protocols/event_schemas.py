"""Pydantic event schemas for PDCA-sdlc inter-agent communication.

Each model corresponds to an event topic in the async event bus.
Schemas define the ``data`` payload structure for ``Event.data``.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProjectInitialized(BaseModel):
    """Emitted when a new project is submitted for processing."""

    description: str
    project_id: str


class AdaptationComplete(BaseModel):
    """Emitted after AdaptationAgent classifies the project."""

    complexity: Literal["simple", "moderate", "complex"]
    lifecycle: Literal["fast_track", "iterative", "incremental", "agile", "spiral"]
    processes: list[str]
    activities: list[str]
    effort_estimate: dict[str, Any]


class RequirementCreated(BaseModel):
    """Emitted after RequirementsAnalyst processes a description."""

    requirement_ids: list[str]
    count: int


class ArchitectureProposed(BaseModel):
    """Emitted after ArchitectAgent designs system architecture."""

    component_ids: list[str]
    components: list[dict[str, Any]]
    requirement_ids: list[str]


class CodeCommitted(BaseModel):
    """Emitted when CoderAgent generates code successfully."""

    module_id: str
    component: str
    files: list[str]
    tests_passed: bool


class CodeFailed(BaseModel):
    """Emitted when CoderAgent fails to generate code."""

    module_id: str
    component: str
    error: str


class QualityGateResult(BaseModel):
    """Emitted by quality gates during verification."""

    module_id: str | None = None
    gate: str
    result: Literal["passed", "failed"]
    details: str | None = None


class RiskIdentified(BaseModel):
    """Emitted when an agent encounters a non-recoverable error."""

    description: str
    severity: Literal["low", "medium", "high", "critical"]
    source_event: str = Field(default="", description="Topic of the event that caused this risk")
