"""Importa y registra todos los prompts del sistema.

Importar este modulo ejecuta el registro de los 6 prompts
en PromptRegistry via register_prompt() en cada submodulo.
"""

from __future__ import annotations

# Cada import ejecuta register_prompt() en el modulo correspondiente
# y expone las clases handler
from agentic_pipeline.prompt_chain.prompts.format import FormatHandler  # noqa: F401
from agentic_pipeline.prompt_chain.prompts.generate import GenerateHandler  # noqa: F401
from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler  # noqa: F401
from agentic_pipeline.prompt_chain.prompts.plan import PlanHandler  # noqa: F401
from agentic_pipeline.prompt_chain.prompts.preprocess import PreprocessHandler  # noqa: F401
from agentic_pipeline.prompt_chain.prompts.verify import VerifyHandler  # noqa: F401

__all__ = [
    "PreprocessHandler",
    "IntentHandler",
    "PlanHandler",
    "GenerateHandler",
    "VerifyHandler",
    "FormatHandler",
]
