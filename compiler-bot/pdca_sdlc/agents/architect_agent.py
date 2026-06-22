"""ArchitectAgent — designs component architecture from requirements.

Trigger: ``requirement.created``
Output: ``architecture.proposed``
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pdca_sdlc.core.base_agent import AgentContext, BaseAgent
from pdca_sdlc.core.capability_registry import CapabilityManifest
from pdca_sdlc.core.event_bus import Event
from pdca_sdlc.core.knowledge_graph import Edge, EdgeType, Node, NodeType
from pdca_sdlc.core.llm_client import LLMClient

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT: str = (
    "You are a Software Architect following ISO 12207. "
    "Given these requirements, design a component architecture. "
    "Explore 2-3 architectural variants and select the best one.\n\n"
    "Return JSON: "
    "{components: [{name, tech_stack, interfaces, implements_requirements}], "
    "decisions: [{title, context, decision, consequences}]}"
)


class ArchitectAgent(BaseAgent):
    """Designs component architecture from requirements.

    For SIMPLE projects it skips (fast-path to CoderAgent).
    For MODERATE/COMPLEX it uses LLM with Tree-of-Thought exploration.
    Falls back to flat architecture (1 component per requirement)
    when the LLM is unavailable.
    """

    def __init__(
        self,
        context: AgentContext,
        llm_client: LLMClient | None = None,
    ) -> None:
        """Initialize the architect agent.

        Args:
            context: Agent context with event bus, KG, and registry.
            llm_client: Optional LLM client (defaults to mock).
        """
        super().__init__(context)
        self._llm = llm_client or LLMClient()
        self._custom_llm: bool = llm_client is not None

    @property
    def manifest(self) -> CapabilityManifest:
        """Return the capability manifest for this agent."""
        return CapabilityManifest(
            agent_id=self._ctx.agent_id,
            agent_name="ArchitectAgent",
            description=("Designs component architecture from requirements following ISO 12207"),
            iso_12207={"process": "6.2", "activities": ["6.2.1", "6.2.2", "6.2.3"]},
            triggers=["requirement.created"],
            output_events=["architecture.proposed"],
        )

    async def handle_event(self, event: Event) -> None:
        """Process a ``requirement.created`` event.

        Reads requirements from the KG, classifies project complexity,
        and generates component architecture with ADRs.
        Emits ``architecture.proposed`` on success.
        """
        project_id: str = event.project_id
        requirement_ids: list[str] = event.data.get("requirement_ids", [])

        if not requirement_ids:
            logger.warning("No requirement IDs in event for %s", project_id)
            return

        complexity = self._read_complexity(project_id)
        if complexity is None:
            logger.warning("No goal node found for %s", project_id)
            return

        # SIMPLE projects: fast-path skip, no architecture needed
        if complexity == "simple":
            logger.debug(
                "SIMPLE project %s — architect fast-path skip",
                project_id,
            )
            return

        requirements = self._read_requirements(requirement_ids)
        if not requirements:
            logger.warning("No requirements found in KG for %s", project_id)
            return

        components, decisions = await self._design_architecture(
            complexity=complexity,
            requirements=requirements,
        )

        component_ids = self._write_components(project_id, components)
        decision_ids = self._write_decisions(project_id, decisions)

        await self.emit(
            "architecture.proposed",
            project_id,
            {
                "component_ids": component_ids,
                "decision_ids": decision_ids,
                "components": components,
                "requirement_ids": requirement_ids,
            },
        )

    def _read_complexity(self, project_id: str) -> str | None:
        """Read project complexity from the goal node in the KG.

        Returns:
            Complexity string ("simple", "moderate", "complex")
            or None if the goal node does not exist.
        """
        goal = self.read_graph(f"goal-{project_id}")
        if goal is not None:
            return str(goal.properties.get("complexity", "simple"))
        return None

    def _read_requirements(
        self,
        requirement_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Read requirement nodes from the KG by their IDs.

        Args:
            requirement_ids: List of requirement node IDs.

        Returns:
            List of requirement property dicts.
        """
        result: list[dict[str, Any]] = []
        for rid in requirement_ids:
            node = self.read_graph(rid)
            if node is not None:
                result.append(node.properties)
        return result

    async def _design_architecture(
        self,
        complexity: str,
        requirements: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Design architecture using LLM with fallback.

        MODERATE projects use the flash model (temp 0.3).
        COMPLEX projects use the pro model (temp 0.2).

        Args:
            complexity: Project complexity ("moderate" or "complex").
            requirements: List of requirement property dicts.

        Returns:
            Tuple of (components, decisions).
        """
        try:
            llm = self._llm if self._custom_llm else self._llm_for_complexity(complexity)
            reqs_json: str = json.dumps(requirements, indent=2, ensure_ascii=False)
            prompt = f"{_SYSTEM_PROMPT}\n\nRequirements: {reqs_json}"
            response = llm.complete(prompt, response_format="json")
            parsed: dict[str, Any] = json.loads(response)
            components_raw = parsed.get("components", [])
            decisions_raw = parsed.get("decisions", [])

            if components_raw and isinstance(components_raw, list):
                validated_comps = self._validate_components(components_raw)
                validated_decisions = self._validate_decisions(decisions_raw)
                if validated_comps:
                    return validated_comps, validated_decisions
        except Exception as exc:
            logger.debug("LLM architecture design failed, falling back: %s", exc)

        return self._fallback_flat(requirements)

    def _llm_for_complexity(self, complexity: str) -> LLMClient:
        """Create an LLM client configured for the given complexity.

        Args:
            complexity: Project complexity ("moderate" or "complex").

        Returns:
            Configured LLMClient instance.
        """
        if complexity == "complex":
            return LLMClient(
                {
                    "model": "pro",
                    "temperature": 0.2,
                    "max_tokens": 8192,
                },
            )
        return LLMClient(
            {
                "model": "flash",
                "temperature": 0.3,
                "max_tokens": 4096,
            },
        )

    def _validate_components(
        self,
        components: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Validate and deduplicate component entries.

        Ensures each component has a name and implements_requirements list.

        Args:
            components: Raw component list from LLM.

        Returns:
            Validated component list.
        """
        seen_names: set[str] = set()
        result: list[dict[str, Any]] = []
        for comp in components:
            name = str(comp.get("name", "")).strip()
            if not name:
                continue
            if name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            result.append(
                {
                    "name": name,
                    "tech_stack": comp.get("tech_stack", []),
                    "interfaces": comp.get("interfaces", []),
                    "implements_requirements": list(
                        comp.get("implements_requirements", []),
                    ),
                },
            )
        return result

    def _validate_decisions(
        self,
        decisions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Validate ADR entries.

        Ensures each ADR has title, context, decision, and consequences.

        Args:
            decisions: Raw ADR list from LLM.

        Returns:
            Validated ADR list.
        """
        result: list[dict[str, Any]] = []
        for adr in decisions:
            title = str(adr.get("title", "")).strip()
            context = str(adr.get("context", "")).strip()
            decision = str(adr.get("decision", "")).strip()
            consequences = str(adr.get("consequences", "")).strip()
            if title and context and decision and consequences:
                result.append(
                    {
                        "title": title,
                        "context": context,
                        "decision": decision,
                        "consequences": consequences,
                    },
                )
        return result

    def _fallback_flat(
        self,
        requirements: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Generate flat architecture when LLM is unavailable.

        Creates one component per requirement.

        Args:
            requirements: List of requirement property dicts.

        Returns:
            Tuple of (components, decisions).
        """
        components: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for req in requirements:
            req_id: str = str(req.get("id", ""))
            req_text: str = str(req.get("text", f"requirement-{req_id}"))
            comp_name = self._derive_component_name(req_text, req_id)

            if comp_name.lower() in seen_names:
                idx = 2
                while f"{comp_name}{idx}" in seen_names:
                    idx += 1
                comp_name = f"{comp_name}{idx}"
            seen_names.add(comp_name.lower())

            components.append(
                {
                    "name": comp_name,
                    "tech_stack": ["generic"],
                    "interfaces": ["handle"],
                    "implements_requirements": [req_id] if req_id else [],
                },
            )

        decisions: list[dict[str, Any]] = [
            {
                "title": "Fallback Flat Architecture",
                "context": (
                    "LLM was unavailable during architecture design. "
                    "Using deterministic flat mapping."
                ),
                "decision": (
                    "Each requirement is mapped to exactly one component. "
                    "No cross-cutting concerns are extracted."
                ),
                "consequences": (
                    "Simpler structure but may miss shared abstractions. "
                    "Refactoring may be needed as the system grows."
                ),
            },
        ]

        return components, decisions

    @staticmethod
    def _derive_component_name(req_text: str, req_id: str) -> str:
        """Derive a component name from requirement text.

        Uses the first meaningful word or falls back to the requirement ID.

        Args:
            req_text: Requirement text.
            req_id: Requirement ID for fallback.

        Returns:
            A component name string.
        """
        clean = req_text.strip().lower()
        words = [w for w in clean.replace("-", " ").replace("_", " ").split() if w]
        # Skip very generic leading words
        skip_words = {"crear", "el", "la", "un", "una", "los", "las", "de", "del"}
        meaningful = [w for w in words if w not in skip_words]
        if meaningful:
            base = meaningful[0].capitalize()
            if len(meaningful) > 1:
                base += meaningful[1].capitalize()
            return base
        return f"Component{req_id.replace('-', '').capitalize()}"

    def _write_components(
        self,
        project_id: str,
        components: list[dict[str, Any]],
    ) -> list[str]:
        """Write component nodes and IMPLEMENTS edges to the KG.

        Args:
            project_id: The project ID.
            components: List of component property dicts.

        Returns:
            List of written component node IDs.
        """
        component_ids: list[str] = []
        for comp in components:
            comp_name: str = comp["name"]
            comp_id = f"comp-{comp_name.lower().replace(' ', '-')}-{project_id}"
            node = Node(
                id=comp_id,
                node_type=NodeType.component,
                properties=comp,
                created_by=self._ctx.agent_id,
            )
            self.write_graph(node)
            component_ids.append(comp_id)

            for req_id in comp.get("implements_requirements", []):
                self._ctx.knowledge_graph.add_edge(
                    Edge(
                        source_id=comp_id,
                        target_id=req_id,
                        edge_type=EdgeType.implements,
                        properties={},
                    ),
                )
        return component_ids

    def _write_decisions(
        self,
        project_id: str,
        decisions: list[dict[str, Any]],
    ) -> list[str]:
        """Write architecture decision nodes to the KG.

        Args:
            project_id: The project ID.
            decisions: List of ADR property dicts.

        Returns:
            List of written decision node IDs.
        """
        decision_ids: list[str] = []
        for i, adr in enumerate(decisions):
            adr_id = f"adr-{project_id}-{i + 1:03d}"
            node = Node(
                id=adr_id,
                node_type=NodeType.architecture_decision,
                properties=adr,
                created_by=self._ctx.agent_id,
            )
            self.write_graph(node)
            decision_ids.append(adr_id)
        return decision_ids
