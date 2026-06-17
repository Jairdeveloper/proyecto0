"""Prompt PLAN: descompone objetivo en tareas ejecutables."""

from __future__ import annotations

import logging

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.contracts import PlannerContract, PlannerInput
from agentic_pipeline.prompt_chain.fallbacks import execute_fallback
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend, build_llm_backend
from agentic_pipeline.prompt_chain.prompt_template import (
    PromptTemplate,
    PromptRegistry,
    register_prompt,
)

logger = logging.getLogger(__name__)

PLAN_TEMPLATE = register_prompt(
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


async def plan_handler(
    intent: str,
    module: str | None = None,
    entity: str | None = None,
    tech: list[str] | None = None,
    features: list[str] | None = None,
    llm: LLMBackend | None = None,
    ctx: ChainContext | None = None,
) -> dict:
    """Ejecuta PLAN prompt con fallback rule-based.

    Args:
        intent: Intencion detectada (CREATE, READ, etc.).
        module: Nombre del modulo (opcional).
        entity: Nombre de entidad (opcional).
        tech: Lista de tecnologias (opcional).
        features: Lista de features (opcional).
        llm: Backend LLM opcional.
        ctx: ChainContext opcional para publicar resultado.

    Returns:
        Dict validado contra PlannerContract.
    """
    if llm is None:
        llm = build_llm_backend()

    template = PromptRegistry.get("plan")
    prompt = template.render(
        intent=intent,
        module=module,
        entity=entity,
        tech=tech or [],
        features=features or [],
    )

    result = await llm.generate_structured(
        prompt=prompt,
        system=template.system_prompt,
        output_schema=template.output_schema,
        temperature=template.temperature,
    )

    if not result.success:
        logger.info("LLM plan failed, using fallback")
        output = execute_fallback(
            "goal_tree_planner",
            intent=intent,
            module=module,
            entity=entity,
            tech=tech,
            features=features,
        )
    else:
        output = result.structured  # type: ignore[assignment]

    if ctx:
        try:
            ctx.set_output("plan", output, contract=PlannerContract)
        except Exception as exc:
            logger.warning("plan ctx.set_output failed: %s", exc)

    return output
