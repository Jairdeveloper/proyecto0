"""Prompt PREPROCESS: normaliza y segmenta texto del usuario."""

from __future__ import annotations

import logging

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.contracts import (
    PreprocessorContract,
    PreprocessorInput,
)
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate,
    PromptRegistry,
    register_prompt,
)

logger = logging.getLogger(__name__)

PREPROCESS_TEMPLATE = register_prompt(PromptTemplate(
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
))


async def preprocess_handler(
    raw_text: str,
    llm: LLMBackend | None = None,
    ctx: ChainContext | None = None,
) -> dict:
    """Ejecuta PREPROCESS prompt con fallback rule-based.

    Args:
        raw_text: Texto crudo del usuario.
        llm: Backend LLM (opcional, se autoconfigura si no se provee).
        ctx: ChainContext opcional para publicar resultado.

    Returns:
        Dict validado contra PreprocessorContract.
    """
    if llm is None:
        llm = build_llm_backend()

    template = PromptRegistry.get("preprocess")
    prompt = template.render(raw_text=raw_text)

    result = await llm.generate_structured(
        prompt=prompt,
        system=template.system_prompt,
        output_schema=template.output_schema,
        temperature=template.temperature,
    )

    if not result.success:
        logger.info("LLM preprocess failed, using fallback")
        output = execute_fallback("preprocessor_filters", raw_text=raw_text)
    else:
        output = result.structured  # type: ignore[assignment]

    if ctx:
        ctx.set_output("preprocess", output, contract=PreprocessorContract)

    return output
