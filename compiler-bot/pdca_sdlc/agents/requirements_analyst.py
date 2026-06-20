"""RequirementsAnalystAgent — decomposes project description into requirements.

Trigger: ``adaptation.complete``
Output: ``requirement.created``
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from typing import Any, Literal

from pydantic import BaseModel, Field

from pdca_sdlc.core.base_agent import AgentContext, BaseAgent
from pdca_sdlc.core.capability_registry import CapabilityManifest
from pdca_sdlc.core.event_bus import Event
from pdca_sdlc.core.knowledge_graph import Node, NodeType
from pdca_sdlc.core.llm_client import LLMClient

logger = logging.getLogger(__name__)

_REQUIREMENT_TYPES: list[str] = ["functional", "business", "user", "non_functional"]
_PRIORITIES: list[str] = ["high", "medium", "low"]
_REQUIREMENT_KEYWORDS: dict[str, list[str]] = {
    "functional": [
        "login",
        "registro",
        "autenticacion",
        "crud",
        "crear",
        "listar",
        "actualizar",
        "eliminar",
        "buscar",
        "filtrar",
        "exportar",
        "importar",
        "notificar",
        "enviar",
        "recibir",
        "pago",
        "checkout",
        "carrito",
        "checkout",
    ],
    "non_functional": [
        "rendimiento",
        "seguridad",
        "seguro",
        "escalable",
        "disponible",
        "respuesta",
        "concurrencia",
        "latencia",
        "ssl",
        "https",
        "cifrado",
        "auth",
    ],
}


class RequirementSchema(BaseModel):
    """A single requirement with metadata."""

    id: str
    text: str
    type: Literal["functional", "business", "user", "non_functional"]
    priority: Literal["high", "medium", "low"]
    acceptance_criteria: list[str] = Field(default_factory=list)


class RequirementsAnalystAgent(BaseAgent):
    """Decomposes a project description into structured requirements.

    Uses LLM for decomposition with deterministic fallback.
    Writes each requirement as a ``requirement`` node in the KG.
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
            agent_name="RequirementsAnalystAgent",
            description="Decomposes project descriptions into structured requirements",
            iso_12207={"process": "6.1", "activities": ["6.1.1", "6.1.2"]},
            triggers=["adaptation.complete"],
            output_events=["requirement.created"],
        )

    async def handle_event(self, event: Event) -> None:
        """Process an ``adaptation.complete`` event."""
        project_id: str = event.project_id
        description = self._read_project_description(project_id)
        if not description:
            logger.warning("No project description found for %s", project_id)
            return

        requirements = await self._decompose(description)
        if not requirements:
            logger.warning("No requirements generated for %s", project_id)
            return

        for req in requirements:
            node = Node(
                id=req.id,
                node_type=NodeType.requirement,
                properties=req.model_dump(),
            )
            self.write_graph(node)

        await self.emit(
            "requirement.created",
            project_id,
            {
                "requirement_ids": [r.id for r in requirements],
                "count": len(requirements),
            },
        )

    def _read_project_description(self, project_id: str) -> str:
        """Read the project description from the goal node in the KG."""
        goal = self.read_graph(f"goal-{project_id}")
        if goal is not None:
            return str(goal.properties.get("description", ""))
        return ""

    async def _decompose(self, description: str) -> list[RequirementSchema]:
        """Decompose a description into requirements via LLM with fallback."""
        try:
            prompt = (
                "You are a requirements analyst. Decompose the following "
                "project description into a list of requirements. "
                "Each requirement must have: id, text, type "
                "(functional/business/user/non_functional), priority "
                "(high/medium/low), and acceptance_criteria (list of strings).\n\n"
                f"Project: {description}\n\n"
                'Respond with JSON: {"requirements": [...]}'
            )
            response = self._llm.complete(prompt, response_format="json")
            parsed: dict[str, Any] = json.loads(response)
            raw_list = parsed.get("requirements", [])
            if isinstance(raw_list, list) and raw_list:
                result = []
                for item in raw_list:
                    if isinstance(item, dict) and item.get("text"):
                        req_type = str(item.get("type", "functional"))
                        if req_type not in _REQUIREMENT_TYPES:
                            req_type = "functional"
                        priority = str(item.get("priority", "medium"))
                        if priority not in _PRIORITIES:
                            priority = "medium"
                        result.append(
                            RequirementSchema(
                                id=str(item.get("id", f"r-{len(result) + 1:03d}")),
                                text=str(item["text"]),
                                type=req_type,  # type: ignore[arg-type]
                                priority=priority,  # type: ignore[arg-type]
                                acceptance_criteria=list(
                                    item.get("acceptance_criteria", []),
                                ),
                            ),
                        )
                if result:
                    return result
        except Exception as exc:
            logger.debug("LLM decomposition failed, falling back: %s", exc)
        return self._fallback_decompose(description)

    def _fallback_decompose(self, description: str) -> list[RequirementSchema]:
        """Heuristic decomposition based on sentence splitting and keywords."""
        sentences = re.split(r"[.\n]+", description)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if not sentences:
            sentences = [description]
        result: list[RequirementSchema] = []
        for i, sentence in enumerate(sentences):
            req_type = self._guess_type(sentence)
            priority = self._guess_priority(sentence)
            result.append(
                RequirementSchema(
                    id=f"r-{i + 1:03d}",
                    text=sentence,
                    type=req_type,
                    priority=priority,
                    acceptance_criteria=[f"{sentence} — verificado"],
                ),
            )
        return result

    @staticmethod
    def _normalize(text: str) -> str:
        """Remove accents and lowercase."""
        nfkd = unicodedata.normalize("NFKD", text)
        return nfkd.encode("ascii", "ignore").decode("ascii").lower()

    @staticmethod
    def _guess_type(text: str) -> Literal["functional", "business", "user", "non_functional"]:
        """Guess requirement type from text keywords."""
        normalized = RequirementsAnalystAgent._normalize(text)
        for kw in _REQUIREMENT_KEYWORDS["non_functional"]:
            if kw in normalized:
                return "non_functional"
        for kw in _REQUIREMENT_KEYWORDS["functional"]:
            if kw in normalized:
                return "functional"
        return "functional"

    @staticmethod
    def _guess_priority(text: str) -> Literal["high", "medium", "low"]:
        """Guess priority from text keywords."""
        normalized = RequirementsAnalystAgent._normalize(text)
        high_keywords = ["seguridad", "autenticacion", "pago", "login", "auth", "critico"]
        low_keywords = ["cosmetic", "menor", "opcional", "nice to have", "futuro", "estetic"]
        for kw in high_keywords:
            if kw in normalized:
                return "high"
        for kw in low_keywords:
            if kw in normalized:
                return "low"
        return "medium"
