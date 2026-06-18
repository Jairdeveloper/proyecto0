"""Prompt VERIFY: verifica archivos generados contra requisitos."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.prompt_chain.contracts import (
    ValidatorContract,
    ValidatorInput,
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


class VerifyHandler(PromptHandler):
    """Handler para la etapa VERIFY."""

    name = "verify"
    output_contract = ValidatorContract
    input_fields = ["intent", "module", "entity", "tech", "features", "files"]

    def _build_prompt_kwargs(
        self,
        request: PromptRequest,
        ctx_data: dict[str, Any],
    ) -> dict[str, Any]:
        requirements = {
            "intent": ctx_data.get("intent", ""),
            "module": ctx_data.get("module"),
            "entity": ctx_data.get("entity"),
            "tech": ctx_data.get("tech", []),
            "features": ctx_data.get("features", []),
        }
        return {
            "requirements": requirements,
            "files": ctx_data.get("files", []),
            "criteria": ctx_data.get("criteria", []),
        }
