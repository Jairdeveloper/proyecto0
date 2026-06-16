"""Modelos Pydantic para validacion de entrada/salida de prompts."""

from __future__ import annotations

from pydantic import BaseModel


# ── Output contracts (validan salida de cada prompt) ──


class PreprocessorContract(BaseModel):
    """Salida del prompt PREPROCESS."""

    normalized: str
    domain: str
    language: str
    segments: list[str]
    has_ambiguity: bool
    confidence: float


class NLPContract(BaseModel):
    """Salida del prompt INTENT."""

    intent: str
    confidence: float
    module: str | None = None
    entity: str | None = None
    tech: list[str] = []
    features: list[str] = []
    is_ambiguous: bool = False
    missing_info: list[str] = []


class PlannerContract(BaseModel):
    """Salida del prompt PLAN."""

    tasks: list[dict]
    execution_order: list[str]
    complexity: str
    estimated_files: int = 0


class SynthesisContract(BaseModel):
    """Salida del prompt GENERATE."""

    files: list[dict]
    errors: list[str] = []


class ValidatorContract(BaseModel):
    """Salida del prompt VERIFY."""

    valid: bool
    checks: list[dict]
    should_retry: bool = False
    suggestions: list[str] = []


class OutputContract(BaseModel):
    """Salida del prompt FORMAT."""

    summary: str
    files_created: list[str]
    warnings: list[str] = []
    next_steps: list[str] = []
    success: bool


# ── Input contracts (validan argumentos de cada prompt template) ──


class PreprocessorInput(BaseModel):
    raw_text: str


class NLPInput(BaseModel):
    normalized_text: str
    domain: str = "backend"


class PlannerInput(BaseModel):
    intent: str
    module: str | None = None
    entity: str | None = None
    tech: list[str] = []
    features: list[str] = []


class SynthesisInput(BaseModel):
    tasks: list[dict]
    existing_files: list[str] = []


class ValidatorInput(BaseModel):
    requirements: dict
    files: list[dict]
    criteria: list[str] = []


class OutputInput(BaseModel):
    original_request: str
    plan: dict
    generated_files: list[dict]
    validation: dict
