"""Capability Registry — central registry of agent capabilities.

Each agent registers its capabilities (ISO 12207 process/activities/tasks,
triggers, output events) so the system can route events to the right agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CapabilityManifest:
    agent_id: str
    agent_name: str
    description: str
    iso_12207: dict[str, Any]
    triggers: list[str]
    output_events: list[str]
    llm_profile: str = "flash"
    version: str = "0.1.0"
    status: str = "active"


class CapabilityRegistry:
    """Registry of agent capabilities.

    Agents register themselves with a CapabilityManifest describing
    what they do, which events they respond to, and which ISO 12207
    activities they cover.
    """

    def __init__(self) -> None:
        self._manifests: dict[str, CapabilityManifest] = {}

    def register(self, manifest: CapabilityManifest) -> None:
        self._manifests[manifest.agent_id] = manifest

    def unregister(self, agent_id: str) -> bool:
        if agent_id not in self._manifests:
            return False
        del self._manifests[agent_id]
        return True

    def get(self, agent_id: str) -> CapabilityManifest | None:
        return self._manifests.get(agent_id)

    def find_by_event(self, topic: str) -> list[CapabilityManifest]:
        """Find agents whose triggers match an event topic."""
        from pdca_sdlc.core.event_bus import TopicMatcher

        return [
            m
            for m in self._manifests.values()
            if m.status == "active" and any(TopicMatcher.matches(t, topic) for t in m.triggers)
        ]

    def find_by_iso_activity(self, activity: str) -> list[CapabilityManifest]:
        """Find agents that cover a specific ISO 12207 activity."""
        return [
            m
            for m in self._manifests.values()
            if m.status == "active" and any(activity in str(v) for v in m.iso_12207.values())
        ]

    def get_all(self) -> list[CapabilityManifest]:
        return list(self._manifests.values())

    def update_status(self, agent_id: str, status: str) -> bool:
        if agent_id not in self._manifests:
            return False
        self._manifests[agent_id].status = status
        return True

    def count(self) -> int:
        return len(self._manifests)
