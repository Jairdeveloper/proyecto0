"""Prompt VERIFY: verifica archivos generados contra requisitos."""

from __future__ import annotations

import logging

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.contracts import (
    ValidatorContract,
    ValidatorInput,
)
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate,
    PromptRegistry,
    register_prompt,
)

logger = logging.getLogger(__name__)

VERIFY_TEMPLATE = register_prompt(
    PromptTemplate(
        name="verify",
        system_prompt=(
            "Eres un revisor de codigo NestJS/Prisma. Verifica que los "
            "archivos generados cumplan los requisitos y las mejores practicas.\n\n"
            "Criterios:\n"
            "- Estructura de archivos correcta (modulo, controller, etc.)\n"
            "- Imports necesarios presentes\n"
            "- Naming conventions (PascalCase, camelCase)\n"
            "- Relaciones Prisma correctas\n"
            "- Decoradores NestJS correctos"
        ),
        template=(
            "Requisitos: {requirements}\n\nArchivos: {files}\n\nCriterios: {criteria}"
        ),
        input_schema=ValidatorInput,
        output_schema=ValidatorContract,
        fallback_name="validator_pipeline",
        temperature=0.1,
    )
)


async def verify_handler(
    requirements: dict,
    files: list[dict],
    criteria: list[str] | None = None,
    llm: LLMBackend | None = None,
    ctx: ChainContext | None = None,
) -> dict:
    """Ejecuta VERIFY prompt con fallback rule-based.

    Args:
        requirements: Requisitos originales (intent, module, etc.).
        files: Archivos generados con path y content.
        criteria: Criterios de verificacion especificos.
        llm: Backend LLM opcional.
        ctx: ChainContext opcional para publicar resultado.

    Returns:
        Dict validado contra ValidatorContract.
    """
    if llm is None:
        llm = build_llm_backend()

    template = PromptRegistry.get("verify")
    prompt = template.render(
        requirements=requirements,
        files=files,
        criteria=criteria or [],
    )

    result = await llm.generate_structured(
        prompt=prompt,
        system=template.system_prompt,
        output_schema=template.output_schema,
        temperature=template.temperature,
    )

    if not result.success:
        logger.info("LLM verify failed, using fallback")
        output = execute_fallback(
            "validator_pipeline",
            requirements=requirements,
            files=files,
            criteria=criteria,
        )
    else:
        output = result.structured  # type: ignore[assignment]

    if ctx:
        try:
            ctx.set_output("verify", output, contract=ValidatorContract)
        except Exception as exc:
            logger.warning("verify ctx.set_output failed: %s", exc)

    return output
