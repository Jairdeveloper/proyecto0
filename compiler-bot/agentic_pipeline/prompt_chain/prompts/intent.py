"""Prompt INTENT: clasifica intencion y extrae entidades."""

from __future__ import annotations

import logging

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.contracts import NLPContract, NLPInput
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate,
    PromptRegistry,
    register_prompt,
)

logger = logging.getLogger(__name__)

INTENT_TEMPLATE = register_prompt(PromptTemplate(
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
))


async def intent_handler(
    normalized_text: str,
    domain: str = "backend",
    llm: LLMBackend | None = None,
    ctx: ChainContext | None = None,
) -> dict:
    """Ejecuta INTENT prompt con fallback rule-based.

    Args:
        normalized_text: Texto ya normalizado.
        domain: Dominio detectado (backend, frontend, infra, general).
        llm: Backend LLM opcional.
        ctx: ChainContext opcional para publicar resultado.

    Returns:
        Dict validado contra NLPContract.
    """
    if llm is None:
        llm = build_llm_backend()

    template = PromptRegistry.get("intent")
    prompt = template.render(normalized_text=normalized_text, domain=domain)

    result = await llm.generate_structured(
        prompt=prompt,
        system=template.system_prompt,
        output_schema=template.output_schema,
        temperature=template.temperature,
    )

    if not result.success:
        logger.info("LLM intent failed, using fallback")
        output = execute_fallback(
            "intent_classifier",
            normalized_text=normalized_text,
            domain=domain,
        )
    else:
        output = result.structured  # type: ignore[assignment]

    if ctx:
        ctx.set_output("intent", output, contract=NLPContract)

    return output
