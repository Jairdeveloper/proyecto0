"""VerificationAgent — verifica y valida el codigo generado contra requisitos.

Trigger: ``code.committed``
Outputs:
  - ``verification.complete`` — resultado de trazabilidad module->component->requirement
  - ``validation.complete`` — resultado de LLM-as-a-Judge
  - ``quality.gate.failed`` — cuando un quality gate no pasa
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pdca_sdlc.core.base_agent import AgentContext, BaseAgent
from pdca_sdlc.core.capability_registry import CapabilityManifest
from pdca_sdlc.core.event_bus import Event
from pdca_sdlc.core.knowledge_graph import EdgeType, Node, NodeType
from pdca_sdlc.core.llm_client import LLMClient
from pdca_sdlc.core.quality_gate import QualityGate

logger = logging.getLogger(__name__)

_VALIDATION_PROMPT: str = (
    "You are a QA Engineer evaluating if the generated code satisfies the requirement.\n"
    "\n"
    "Requirement: {req_text}\n"
    "Acceptance Criteria: {acceptance_criteria}\n"
    "Code: {code_snippet}\n"
    "\n"
    "Rate from 1 to 5:\n"
    "1 = Code does not address the requirement\n"
    "2 = Code partially addresses it but is incomplete\n"
    "3 = Code meets the basic requirement\n"
    "4 = Code fully meets the requirement with good quality\n"
    "5 = Code exceeds the requirement with excellent quality\n"
    "\n"
    "Respond with ONLY the number."
)


class VerificationAgent(BaseAgent):
    """Verifica y valida el codigo generado contra los requisitos.

    1. Verificacion de trazabilidad: module -> component -> requirement
    2. Quality Gates: dispara gates predefinidos
    3. Validacion: LLM-as-a-Judge (escala 1-5, threshold configurable)
    """

    def __init__(
        self,
        context: AgentContext,
        llm_client: LLMClient | None = None,
        quality_gate: QualityGate | None = None,
        validation_threshold: int = 3,
    ) -> None:
        """Inicializar VerificationAgent.

        Args:
            context: Contexto del agente con event bus, KG y registry.
            llm_client: Cliente LLM opcional (default mock).
            quality_gate: QualityGate opcional para disparar gates.
            validation_threshold: Puntaje minimo para validacion (default 3).
        """
        super().__init__(context)
        self._llm = llm_client or LLMClient()
        self._custom_llm: bool = llm_client is not None
        self._quality_gate = quality_gate
        self._validation_threshold = validation_threshold

    @property
    def manifest(self) -> CapabilityManifest:
        """Return the capability manifest."""
        return CapabilityManifest(
            agent_id=self._ctx.agent_id,
            agent_name="VerificationAgent",
            description=(
                "Verifies traceability and validates generated code "
                "against requirements using LLM-as-a-Judge"
            ),
            iso_12207={"process": "6.4", "activities": ["6.4.1", "6.4.2"]},
            triggers=["code.committed"],
            output_events=[
                "verification.complete",
                "validation.complete",
                "quality.gate.failed",
            ],
        )

    async def handle_event(self, event: Event) -> None:
        """Process a ``code.committed`` event.

        Runs verification, quality gates, and LLM-as-a-Judge validation.
        """
        project_id: str = event.project_id
        module_id: str = str(event.data.get("module_id", ""))
        files: list[str] = event.data.get("files", [])

        # Step 1: Verification — traceability chain
        trace_ok, trace_detail = self._verify_trace(module_id)
        await self.emit(
            "verification.complete",
            project_id,
            {
                "module_id": module_id,
                "trace_ok": trace_ok,
                "detail": trace_detail,
            },
        )
        logger.info(
            "Verification %s for module %s: %s",
            "PASSED" if trace_ok else "FAILED",
            module_id,
            trace_detail,
        )

        # Step 2: Quality Gates
        if self._quality_gate is not None:
            await self._fire_quality_gates(project_id)

        # Step 3: Validation — LLM-as-a-Judge (only if trace OK)
        if trace_ok:
            validation_results = await self._validate_code(project_id, files)
            await self.emit(
                "validation.complete",
                project_id,
                {
                    "module_id": module_id,
                    "results": validation_results,
                },
            )

    def _verify_trace(
        self,
        module_id: str,
    ) -> tuple[bool, str]:
        """Verificar cadena de trazabilidad module -> component -> requirement.

        Args:
            module_id: ID del nodo code_module en el KG.

        Returns:
            Tuple de (passed: bool, detail: str).
        """
        module = self.read_graph(module_id)
        if module is None:
            # Try querying for code_module nodes by id pattern
            candidates = self.query_graph(node_type=NodeType.code_module)
            matching = [m for m in candidates if module_id in m.id]
            if not matching:
                return False, f"Code module '{module_id}' not found in KG"
            module = matching[0]

        # module --[IMPLEMENTS]--> component
        outgoing = self._ctx.knowledge_graph.get_outgoing(module.id)
        comp_edges = [e for e in outgoing if e.edge_type == EdgeType.implements]
        if not comp_edges:
            return (
                False,
                f"Module '{module.id}' has no outgoing IMPLEMENTS edges to any component",
            )

        # For each traced component, verify it traces to a requirement
        for comp_edge in comp_edges:
            comp_id = comp_edge.target_id
            comp_outgoing = self._ctx.knowledge_graph.get_outgoing(comp_id)
            req_edges = [e for e in comp_outgoing if e.edge_type == EdgeType.implements]
            if not req_edges:
                return (
                    False,
                    f"Component '{comp_id}' traced from module has no IMPLEMENTS edges to requirements",
                )

        return True, f"Traceability chain complete ({len(comp_edges)} component(s))"

    async def _fire_quality_gates(self, project_id: str) -> None:
        """Disparar quality gates predefinidos.

        Ejecuta los gates configurados en el QualityGate y emite
        ``quality.gate.failed`` para cada uno que falle.
        """
        if self._quality_gate is None:
            return

        from pdca_sdlc.core.quality_gate import (
            gate_componentes_tienen_trazabilidad,
            gate_modulos_tienen_trazabilidad,
        )

        self._quality_gate.register_gate(
            "componentes_tienen_trazabilidad",
            gate_componentes_tienen_trazabilidad,
        )
        self._quality_gate.register_gate(
            "modulos_tienen_trazabilidad",
            gate_modulos_tienen_trazabilidad,
        )

        for gate_name in ("componentes_tienen_trazabilidad", "modulos_tienen_trazabilidad"):
            result = await self._quality_gate.evaluate(
                gate_name,
                project_id,
                {"source": "verification_agent"},
            )
            logger.debug(
                "Quality gate '%s' for %s: %s",
                gate_name,
                project_id,
                result.value,
            )

    async def _validate_code(
        self,
        project_id: str,
        files: list[str],
    ) -> list[dict[str, Any]]:
        """Validar codigo generado contra requisitos via LLM-as-a-Judge.

        Para cada requisito en el KG, construye el prompt con el texto
        del requisito, sus criterios de aceptacion y el codigo generado.

        Args:
            project_id: ID del proyecto.
            files: Lista de rutas de archivos generados.

        Returns:
            Lista de resultados de validacion por requisito.
        """
        requirements: list[Node] = self.query_graph(node_type=NodeType.requirement)
        if not requirements:
            logger.warning("No requirements found for validation in %s", project_id)
            return []

        code_snippets = self._read_code_snippets(files)
        if not code_snippets:
            code_snippets = "// No code files available for validation"

        results: list[dict[str, Any]] = []
        for req in requirements:
            req_text = str(req.properties.get("text", ""))
            acceptance_criteria = req.properties.get("acceptance_criteria", [])
            ac_text = (
                "; ".join(str(a) for a in acceptance_criteria)
                if acceptance_criteria
                else "No criteria defined"
            )

            score = await self._judge_requirement(req_text, ac_text, code_snippets)
            passed = score >= self._validation_threshold

            results.append(
                {
                    "requirement_id": req.id,
                    "score": score,
                    "threshold": self._validation_threshold,
                    "passed": passed,
                },
            )
            logger.debug(
                "Validation %s for req %s: score=%d/%d",
                "PASSED" if passed else "FAILED",
                req.id,
                score,
                self._validation_threshold,
            )

        return results

    async def _judge_requirement(
        self,
        req_text: str,
        acceptance_criteria: str,
        code_snippet: str,
    ) -> int:
        """Evaluar un requisito contra codigo via LLM.

        Args:
            req_text: Texto del requisito.
            acceptance_criteria: Criterios de aceptacion.
            code_snippet: Fragmento de codigo generado.

        Returns:
            Puntaje 1-5. Retorna 1 si el LLM falla.
        """
        try:
            prompt = _VALIDATION_PROMPT.format(
                req_text=req_text,
                acceptance_criteria=acceptance_criteria,
                code_snippet=code_snippet,
            )
            response = self._llm.complete(prompt)
            score = self._parse_score(response)
            return max(1, min(5, score))
        except Exception as exc:
            logger.debug("LLM judge failed for req '%s': %s", req_text, exc)
            return 1

    @staticmethod
    def _parse_score(response: str) -> int:
        """Extraer un puntaje numerico 1-5 de la respuesta del LLM.

        Busca el primer numero entero en la respuesta.

        Args:
            response: Respuesta textual del LLM.

        Returns:
            Puntaje entero entre 1 y 5, o 1 si no se puede parsear.
        """
        import re

        match = re.search(r"\b([1-5])\b", response.strip())
        if match:
            return int(match.group(1))
        return 1

    @staticmethod
    def _read_code_snippets(files: list[str]) -> str:
        """Leer archivos de codigo y concatenarlos para el prompt.

        Args:
            files: Lista de rutas de archivo.

        Returns:
            Contenido concatenado de los archivos, o cadena vacia.
        """
        snippets: list[str] = []
        for filepath in files:
            try:
                path = Path(filepath)
                if path.exists() and path.is_file():
                    content = path.read_text(encoding="utf-8", errors="replace")
                    snippets.append(f"// --- {filepath} ---\n{content}")
            except OSError as exc:
                logger.debug("Could not read %s: %s", filepath, exc)
        return "\n\n".join(snippets) if snippets else ""
