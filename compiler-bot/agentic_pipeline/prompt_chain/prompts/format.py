"""Prompt FORMAT: genera resumen final para el usuario."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.prompt_chain.contracts import OutputContract, OutputInput
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
        name="format",
        system_prompt=(
            "Eres un asistente de desarrollo. Genera un resumen claro "
            "de lo que se ha creado o modificado para el usuario."
        ),
        template=(
            "Solicitud original: {original_request}\n\n"
            "Plan: {plan}\n\n"
            "Archivos generados: {generated_files}\n\n"
            "Validacion: {validation}"
        ),
        input_schema=OutputInput,
        output_schema=OutputContract,
        fallback_name="explain_tool",
        temperature=0.5,
    )
)


class FormatHandler(PromptHandler):
    """Handler para la etapa FORMAT."""

    name = "format"
    output_contract = OutputContract
    input_fields = [
        "tasks",
        "execution_order",
        "files",
        "valid",
        "checks",
        "suggestions",
    ]

    def _build_prompt_kwargs(
        self,
        request: PromptRequest,
        ctx_data: dict[str, Any],
    ) -> dict[str, Any]:
        plan = {
            "tasks": ctx_data.get("tasks", []),
            "execution_order": ctx_data.get("execution_order", []),
        }
        generated_files = ctx_data.get("files", [])
        validation = {
            "valid": ctx_data.get("valid", False),
            "checks": ctx_data.get("checks", []),
            "suggestions": ctx_data.get("suggestions", []),
        }
        return {
            "original_request": request.raw_input,
            "plan": plan,
            "generated_files": generated_files,
            "validation": validation,
        }
