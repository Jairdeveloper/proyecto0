"""Prompt GENERATE: genera codigo NestJS/Prisma para cada tarea."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.prompt_chain.contracts import (
    SynthesisContract,
    SynthesisInput,
)
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
        name="generate",
        system_prompt=(
            "Eres un generador de codigo NestJS + Prisma.\n"
            "Genera el codigo completo para cada tarea del plan.\n\n"
            "Convenciones:\n"
            "- NestJS: modulo, controller, service, DTO, entity\n"
            "- Prisma: schema con modelo, campos, relaciones\n"
            "- Typescript: tipado estricto, decoradores\n"
            "- Incluye imports completos"
        ),
        template="Tareas: {tasks}\nArchivos existentes: {existing_files}",
        input_schema=SynthesisInput,
        output_schema=SynthesisContract,
        fallback_name="generator_factory",
        temperature=0.4,
    )
)


class GenerateHandler(PromptHandler):
    """Handler para la etapa GENERATE."""

    name = "generate"
    output_contract = SynthesisContract
    input_fields = ["tasks"]

    def _build_prompt_kwargs(
        self,
        request: PromptRequest,
        ctx_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "tasks": ctx_data.get("tasks", []),
            "existing_files": ctx_data.get("existing_files", []),
        }
