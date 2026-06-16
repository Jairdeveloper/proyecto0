"""Prompt FORMAT: genera resumen final para el usuario."""

from __future__ import annotations

import logging

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.contracts import OutputContract, OutputInput
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate,
    PromptRegistry,
    register_prompt,
)

logger = logging.getLogger(__name__)

FORMAT_TEMPLATE = register_prompt(PromptTemplate(
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
))


async def format_handler(
    original_request: str,
    plan: dict,
    generated_files: list[dict],
    validation: dict,
    llm: LLMBackend | None = None,
    ctx: ChainContext | None = None,
) -> dict:
    """Ejecuta FORMAT prompt con fallback rule-based.

    Args:
        original_request: Texto original del usuario.
        plan: Plan de tareas ejecutado.
        generated_files: Archivos generados.
        validation: Resultado de la validacion.
        llm: Backend LLM opcional.
        ctx: ChainContext opcional para publicar resultado.

    Returns:
        Dict validado contra OutputContract.
    """
    if llm is None:
        llm = build_llm_backend()

    template = PromptRegistry.get("format")
    prompt = template.render(
        original_request=original_request,
        plan=plan,
        generated_files=generated_files,
        validation=validation,
    )

    result = await llm.generate_structured(
        prompt=prompt,
        system=template.system_prompt,
        output_schema=template.output_schema,
        temperature=template.temperature,
    )

    if not result.success:
        logger.info("LLM format failed, using fallback")
        output = execute_fallback(
            "explain_tool",
            original_request=original_request,
            plan=plan,
            generated_files=generated_files,
            validation=validation,
        )
    else:
        output = result.structured  # type: ignore[assignment]

    if ctx:
        ctx.set_output("format", output, contract=OutputContract)

    return output
