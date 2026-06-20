"""AdaptationAgent — classifies project complexity and selects ISO 12207 lifecycle.

Trigger: ``project.initialized``
Output: ``adaptation.complete``, ``complexity.classified``, ``lifecycle.proposed``
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pdca_sdlc.core.base_agent import AgentContext, BaseAgent
from pdca_sdlc.core.capability_registry import CapabilityManifest
from pdca_sdlc.core.event_bus import Event
from pdca_sdlc.core.knowledge_graph import Node, NodeType
from pdca_sdlc.core.llm_client import LLMClient
from pdca_sdlc.protocols.event_schemas import AdaptationComplete

logger = logging.getLogger(__name__)

_COMPLEXITY_KEYWORDS: dict[str, list[str]] = {
    "complex": [
        "multi-tenant",
        "oauth2",
        "microservicios",
        "seguridad",
        "arquitectura",
        "alta disponibilidad",
        "multi-modulo",
        "event sourcing",
        "cqrs",
        "ddd",
        "dominio",
    ],
    "moderate": [
        "autenticacion",
        "roles",
        "permisos",
        "integracion",
        "api",
        "webhook",
        "reportes",
        "dashboard",
        "workflow",
    ],
}

_ISO_TEMPLATES: dict[str, dict[str, Any]] = {
    "simple": {
        "lifecycle": "fast_track",
        "processes": ["6.1", "6.3"],
        "activities": [
            "Requirements Elicitation",
            "Software Implementation",
            "Unit Testing",
        ],
    },
    "moderate": {
        "lifecycle": "iterative",
        "processes": ["6.1", "6.2", "6.3", "6.4"],
        "activities": [
            "Requirements Elicitation",
            "Architecture Design",
            "Software Implementation",
            "Unit Testing",
            "Verification",
            "Configuration Management",
        ],
    },
    "complex": {
        "lifecycle": "agile",
        "processes": ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6"],
        "activities": [
            "Project Planning",
            "Requirements Elicitation",
            "Architecture Design",
            "Software Implementation",
            "Unit Testing",
            "Verification",
            "Risk Management",
            "Quality Assurance",
            "Configuration Management",
        ],
    },
}


class AdaptationAgent(BaseAgent):
    """Classifies project complexity, selects lifecycle, estimates effort.

    Uses LLM for classification with deterministic keyword fallback.
    """

    def __init__(
        self,
        context: AgentContext,
        llm_client: LLMClient | None = None,
    ) -> None:
        super().__init__(context)
        self._llm = llm_client or LLMClient()

    @property
    def manifest(self) -> CapabilityManifest:
        return CapabilityManifest(
            agent_id=self._ctx.agent_id,
            agent_name="AdaptationAgent",
            description=("Classifies project complexity and selects ISO 12207 lifecycle template"),
            iso_12207={"process": "6.1", "activities": ["6.1.1"]},
            triggers=["project.initialized"],
            output_events=[
                "adaptation.complete",
                "complexity.classified",
                "lifecycle.proposed",
            ],
        )

    async def handle_event(self, event: Event) -> None:
        """Process a ``project.initialized`` event."""
        description: str = event.data.get("description", "")
        project_id: str = event.project_id
        if not description:
            logger.warning("Empty description in project.initialized")
            return

        complexity = await self._classify_complexity(description)
        template = self._select_template(complexity)
        effort = self._estimate_effort(template)

        goal_node = Node(
            id=f"goal-{project_id}",
            node_type=NodeType.goal,
            properties={
                "project_id": project_id,
                "description": description,
                "complexity": complexity,
                "lifecycle": template["lifecycle"],
                "processes": template["processes"],
                "activities": template["activities"],
                "effort_estimate": effort,
            },
        )
        self.write_graph(goal_node)

        payload = AdaptationComplete(
            complexity=complexity,
            lifecycle=template["lifecycle"],
            processes=template["processes"],
            activities=template["activities"],
            effort_estimate=effort,
        )
        payload_dict = payload.model_dump()

        await self.emit("complexity.classified", project_id, {"complexity": complexity})
        await self.emit(
            "lifecycle.proposed",
            project_id,
            {"lifecycle": template["lifecycle"], "activities": template["activities"]},
        )
        await self.emit("adaptation.complete", project_id, payload_dict)

    async def _classify_complexity(self, description: str) -> str:
        """Classify project complexity via LLM, falling back to heuristics."""
        try:
            prompt = (
                "Classify the following project description into one of: "
                "simple, moderate, complex.\n\n"
                f"Description: {description}\n\n"
                'Respond with JSON: {"complexity": "...", "reason": "..."}'
            )
            response = self._llm.complete(prompt, response_format="json")
            parsed: dict[str, Any] = json.loads(response)
            result = parsed.get("complexity", "").lower().strip()
            if result in ("simple", "moderate", "complex"):
                return result
        except Exception as exc:
            logger.debug("LLM classification failed, falling back: %s", exc)
        return self._fallback_classify(description)

    def _fallback_classify(self, description: str) -> str:
        """Keyword-based deterministic classification."""
        desc_lower = description.lower()
        for keyword in _COMPLEXITY_KEYWORDS["complex"]:
            if keyword in desc_lower:
                return "complex"
        for keyword in _COMPLEXITY_KEYWORDS["moderate"]:
            if keyword in desc_lower:
                return "moderate"
        return "simple"

    def _select_template(self, complexity: str) -> dict[str, Any]:
        """Return ISO 12207 template for the given complexity."""
        return dict(_ISO_TEMPLATES.get(complexity, _ISO_TEMPLATES["simple"]))

    @staticmethod
    def _estimate_effort(template: dict[str, Any]) -> dict[str, Any]:
        """Estimate effort based on activities count."""
        count = len(template.get("activities", []))
        base_hours = count * 8
        return {
            "estimated_hours": base_hours,
            "estimated_days": base_hours // 6,
            "activity_count": count,
        }
