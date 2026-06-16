from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional
from datetime import datetime


class Stage(Enum):
    INTENT = "intent"
    PERCEPTION = "perception"
    REQUIREMENT_DECOMPOSER = "requirement_decomposer"
    PREPROCESSOR = "preprocessor"
    LEXER = "lexer"
    PARSER = "parser"
    SEMANTIC_ANALYZER = "semantic_analyzer"
    IR_GENERATOR = "ir_generator"
    PLANNER = "planner"
    REASONING = "reasoning"
    SYNTHESIS = "synthesis"
    EXECUTION = "execution"
    UI_GENERATOR = "ui_generator"
    VALIDATOR = "validator"


class StageContext(BaseModel):
    mission_id: str = Field(default_factory=lambda: datetime.now().isoformat())
    stage: Stage
    input_data: Any
    previous_output: Optional[Any] = None
    config_overrides: dict = {}
    last_error: Optional[str] = None


class AnalysisResult(BaseModel):
    observations: list[str]
    detected_patterns: list[str]
    risks: list[str]
    complexity_score: float = 0.0


class ActionPlan(BaseModel):
    steps: list[dict]
    strategy: str
    fallback_strategy: str = "deterministic"
    estimated_cost: float = 0.0


class StageOutput(BaseModel):
    stage: Stage
    output_data: Any
    metrics: dict = {}
    feedback: dict = {}
    success: bool = True
    error: Optional[str] = None


class Token(BaseModel):
    value: str
    type: str
    category: str
    position: int
    confidence: float = 1.0
    context: dict = {}


class DesignTokens(BaseModel):
    primary_color: str = "#6366F1"
    secondary_color: str = "#10B981"
    font_family: str = "'Inter', sans-serif"
    border_radius: str = "8px"
    spacing_unit: str = "4px"


class RequirementGraph(BaseModel):
    domain: str
    entities: list[dict] = []
    features: list[str] = []
    constraints: list[str] = []
    user_stories: list[str] = []
    raw_text: str = ""
