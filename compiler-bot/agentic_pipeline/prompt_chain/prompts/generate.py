"""Prompt GENERATE: genera codigo NestJS/Prisma para cada tarea."""

from __future__ import annotations

import logging

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.contracts import (
    SynthesisContract,
    SynthesisInput,
)
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate,
    PromptRegistry,
    register_prompt,
)

logger = logging.getLogger(__name__)

GENERATE_TEMPLATE = register_prompt(
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


async def generate_handler(
    tasks: list[dict],
    existing_files: list[str] | None = None,
    llm: LLMBackend | None = None,
    ctx: ChainContext | None = None,
) -> dict:
    """Ejecuta GENERATE prompt con fallback rule-based.

    Args:
        tasks: Lista de tareas del plan.
        existing_files: Archivos existentes en el proyecto.
        llm: Backend LLM opcional.
        ctx: ChainContext opcional para publicar resultado.

    Returns:
        Dict validado contra SynthesisContract.
    """
    if llm is None:
        llm = build_llm_backend()

    template = PromptRegistry.get("generate")
    prompt = template.render(
        tasks=tasks,
        existing_files=existing_files or [],
    )

    result = await llm.generate_structured(
        prompt=prompt,
        system=template.system_prompt,
        output_schema=template.output_schema,
        temperature=template.temperature,
    )

    if not result.success:
        logger.info("LLM generate failed, using fallback")
        output = execute_fallback(
            "generator_factory",
            tasks=tasks,
            existing_files=existing_files,
        )
    else:
        output = result.structured  # type: ignore[assignment]

    if ctx:
        try:
            ctx.set_output("generate", output, contract=SynthesisContract)
        except Exception as exc:
            logger.warning("generate ctx.set_output failed: %s", exc)

    return output
