"""SdlcDashboardService — read-only facade over KnowledgeGraph, EventBus, Registry.

Provides the data model for the dashboard API. All methods are read-only.
"""

from __future__ import annotations

import time

from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph, NodeType


class SdlcDashboardService:
    """Read model for the SDLC dashboard.

    Wraps KG, EventBus, and Registry queries into dashboard-friendly
    JSON-serializable dicts.
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        event_bus: AsyncEventBus,
        registry: CapabilityRegistry,
    ) -> None:
        self._kg = knowledge_graph
        self._bus = event_bus
        self._registry = registry

    def get_health(self) -> dict[str, object]:
        """Return server health status."""
        return {"status": "ok", "timestamp": time.time()}

    def get_projects(self) -> dict[str, list[dict[str, object]]]:
        """List all projects (one per goal node) with summary counts."""
        goals = self._kg.query(node_type=NodeType.goal)
        projects: list[dict[str, object]] = []
        for goal in goals:
            pid = goal.properties.get("project_id", goal.id.replace("goal-", ""))
            reqs = self._kg.query(node_type=NodeType.requirement)
            req_count = len(reqs)
            artifacts = self._kg.query(
                node_type=NodeType.artifact,
                project_id=pid,
            )
            events = self._bus.replay(str(pid))
            projects.append(
                {
                    "project_id": pid,
                    "complexity": goal.properties.get("complexity", ""),
                    "lifecycle": goal.properties.get("lifecycle", ""),
                    "description": str(goal.properties.get("description", ""))[:120],
                    "requirement_count": req_count,
                    "artifact_count": len(artifacts),
                    "event_count": len(events),
                },
            )
        return {"projects": projects}

    def get_project(self, project_id: str) -> dict[str, object] | None:
        """Return full detail for a single project or None."""
        goal = self._kg.get_node(f"goal-{project_id}")
        if goal is None:
            return None

        reqs = self._kg.query(node_type=NodeType.requirement)
        artifacts = self._kg.query(
            node_type=NodeType.artifact,
            project_id=project_id,
        )
        events = self._bus.replay(project_id)

        return {
            "project_id": project_id,
            "goal": {
                "description": str(goal.properties.get("description", "")),
                "complexity": goal.properties.get("complexity", ""),
                "lifecycle": goal.properties.get("lifecycle", ""),
                "processes": goal.properties.get("processes", []),
                "activities": goal.properties.get("activities", []),
                "effort_estimate": goal.properties.get("effort_estimate", {}),
            },
            "requirements": [
                {
                    "id": r.id,
                    "text": r.properties.get("text", ""),
                    "type": r.properties.get("type", ""),
                    "priority": r.properties.get("priority", ""),
                }
                for r in reqs
            ],
            "artifacts": [
                {
                    "target": a.properties.get("target", ""),
                    "status": a.properties.get("status", ""),
                    "error": a.properties.get("error", ""),
                    "files": a.properties.get("paths", []),
                }
                for a in artifacts
            ],
            "event_count": len(events),
        }

    def get_trace(self, project_id: str) -> dict[str, list[dict[str, object]]] | None:
        """Return BFS trace from the goal node."""
        goal = self._kg.get_node(f"goal-{project_id}")
        if goal is None:
            return None
        nodes = self._kg.get_trace(f"goal-{project_id}")
        return {
            "trace": [
                {
                    "id": n.id,
                    "type": n.node_type.value,
                    "properties": dict(n.properties),
                }
                for n in nodes
            ],
        }

    def get_agents(self) -> dict[str, object]:
        """Return all registered agents with status."""
        manifests = self._registry.get_all()
        return {
            "agents": [
                {
                    "agent_id": m.agent_id,
                    "agent_name": m.agent_name,
                    "description": m.description,
                    "status": m.status,
                    "triggers": m.triggers,
                }
                for m in manifests
            ],
            "total": len(manifests),
        }

    def get_events(
        self,
        project_id: str,
        limit: int = 20,
    ) -> dict[str, object]:
        """Return recent events for a project."""
        all_events = self._bus.replay(project_id)
        limited = all_events[-limit:]
        return {
            "project_id": project_id,
            "count": len(limited),
            "events": [
                {
                    "sequence": e.sequence,
                    "topic": e.topic,
                    "source": e.source,
                    "timestamp": e.timestamp,
                    "data": e.data,
                }
                for e in limited
            ],
        }
