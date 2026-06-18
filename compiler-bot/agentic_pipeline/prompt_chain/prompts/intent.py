"""Prompt INTENT: clasifica intencion y extrae entidades."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.prompt_chain.contracts import NLPContract, NLPInput
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
        name="intent",
        system_prompt=(
            "Eres un analista de requisitos de software. Del texto dado, "
            "identifica que accion se pide y con que detalles.\n\n"
            "Acciones disponibles:\n"
            "- CREATE: crear modulo, entidad, proyecto, crud\n"
            "- READ: consultar, listar, mostrar, leer archivos\n"
            "- UPDATE: modificar, actualizar, agregar campo, cambiar\n"
            "- DELETE: eliminar, borrar, quitar, remover\n"
            "- EXPLAIN: explicar, describir, como funciona"
        ),
        template="Texto normalizado: {normalized_text}\nDominio: {domain}",
        input_schema=NLPInput,
        output_schema=NLPContract,
        fallback_name="intent_classifier",
        temperature=0.2,
    )
)


class IntentHandler(PromptHandler):
    """Handler para la etapa INTENT."""

    name = "intent"
    output_contract = NLPContract
    input_fields = ["normalized", "domain"]

    def _build_prompt_kwargs(
        self,
        request: PromptRequest,
        ctx_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "normalized_text": ctx_data.get("normalized", ""),
            "domain": ctx_data.get("domain", "backend"),
        }
