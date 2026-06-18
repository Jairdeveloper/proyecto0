"""Prompt PREPROCESS: normaliza y segmenta texto del usuario."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.prompt_chain.contracts import (
    PreprocessorContract,
    PreprocessorInput,
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
        name="preprocess",
        system_prompt=(
            "Eres un asistente que normaliza instrucciones de desarrollo "
            "de software. Analiza el texto y extrae informacion estructurada.\n\n"
            "Reglas:\n"
            "- Corrige errores ortograficos obvios\n"
            "- Segmenta en oraciones\n"
            "- Identifica el dominio principal\n"
            "- Si el texto es ambiguo, marcalo"
        ),
        template="Normaliza el siguiente texto:\n\n{raw_text}",
        input_schema=PreprocessorInput,
        output_schema=PreprocessorContract,
        fallback_name="preprocessor_filters",
        temperature=0.1,
    )
)


class PreprocessHandler(PromptHandler):
    """Handler para la etapa PREPROCESS."""

    name = "preprocess"
    output_contract = PreprocessorContract
    input_fields: list[str] = []

    def _build_prompt_kwargs(
        self,
        request: PromptRequest,
        ctx_data: dict[str, Any],
    ) -> dict[str, Any]:
        return {"raw_text": request.raw_input}
