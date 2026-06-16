from pydantic import BaseModel
from typing import Optional


class NLPContract(BaseModel):
    raw: str
    intent: dict
    entities: dict
    slots: dict
    ambiguity: dict


class PreprocessorContract(BaseModel):
    normalized_text: str
    domain: str
    enriched: Optional[dict] = None


class LexerContract(BaseModel):
    tokens: list[dict]
    enriched: Optional[dict] = None


class ParserContract(BaseModel):
    ast: dict
    grammar: str


class SemanticContract(BaseModel):
    ast: dict
    semantic_errors: list[str]
    warnings: list[str]


class IRContract(BaseModel):
    ir_json: str


class PlannerContract(BaseModel):
    tasks: list[dict]
    commands: list[dict]
    complexity: str


class SynthesisContract(BaseModel):
    generated_files: list[str]
    errors: list[str]


class UIContract(BaseModel):
    generated_files: list[str]


class ValidatorContract(BaseModel):
    results: list[dict]
    should_retry: bool


STAGE_CONTRACTS: dict[str, type[BaseModel]] = {
    "intent": NLPContract,
    "preprocessor": PreprocessorContract,
    "lexer": LexerContract,
    "parser": ParserContract,
    "semantic_analyzer": SemanticContract,
    "ir_generator": IRContract,
    "planner": PlannerContract,
    "synthesis": SynthesisContract,
    "ui_generator": UIContract,
    "validator": ValidatorContract,
}
