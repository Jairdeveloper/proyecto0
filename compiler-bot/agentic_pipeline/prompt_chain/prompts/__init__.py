"""Importa y registra todos los prompts del sistema.

Importar este modulo ejecuta el registro de los 6 prompts
en PromptRegistry via register_prompt() en cada submodulo.
"""

from __future__ import annotations

# Cada import ejecuta register_prompt() en el modulo correspondiente
from agentic_pipeline.prompt_chain.prompts import (  # noqa: F401
    format as _format,
    generate as _generate,
    intent as _intent,
    plan as _plan,
    preprocess as _preprocess,
    verify as _verify,
)

__all__ = [
    "preprocess",
    "intent",
    "plan",
    "generate",
    "verify",
    "format",
]
