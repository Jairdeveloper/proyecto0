"""Prompt PLAN: descompone objetivo en tareas ejecutables."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.prompt_chain.contracts import PlannerContract, PlannerInput
from agentic_pipeline.prompt_chain.handler_base import (
    PromptHandler,
    PromptRequest,
)
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate,
    register_prompt,
)

logger = logging.getLogger(__name__)

register_prompt(
    PromptTemplate(
        name="plan",
        system_prompt=(
            "Eres un arquitecto de software. Dado un objetivo y requisitos, "
            "genera un plan de tareas ejecutable con dependencias.\n\n"
            "Cada tarea debe tener:\n"
            '- id unico (ej: "t1", "t2")\n'
            "- tipo de accion\n"
            "- target (modulo, archivo, entidad)\n"
            "- parametros especificos\n"
            "- dependencias (task ids que deben completarse antes)\n\n"
            "Tipos de tarea disponibles:\n"
            "- scaffold_module: crear estructura de modulo NestJS\n"
            "- create_entity: crear entidad/schema Prisma\n"
            "- generate_code: generar archivo de codigo especifico\n"
            "- configure: modificar configuracion existente\n"
            "- verify: verificar que todo este correcto"
        ),
        template=(
            "Intencion: {intent}\n"
            "Modulo: {module}\n"
            "Entidad: {entity}\n"
            "Tecnologias: {tech}\n"
            "Features: {features}"
        ),
        input_schema=PlannerInput,
        output_schema=PlannerContract,
        fallback_name="goal_tree_planner",
        temperature=0.3,
    )
)


class PlanHandler(PromptHandler):
    """Handler para la etapa PLAN."""

    name = "plan"
    output_contract = PlannerContract
    input_fields = ["intent", "module", "entity", "tech", "features"]

    def _build_prompt_kwargs(
        self,
        request: PromptRequest,
        ctx_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "intent": ctx_data.get("intent", ""),
            "module": ctx_data.get("module"),
            "entity": ctx_data.get("entity"),
            "tech": ctx_data.get("tech", []),
            "features": ctx_data.get("features", []),
        }
