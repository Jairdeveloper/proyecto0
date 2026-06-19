from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    primary: str
    secondary: str | None = None
    confidence: float
    scores: dict[str, float] = {}
    domain: str = "backend"


class Entity(BaseModel):
    nombre: str
    tipo: str
    rol: str = ""
    negado: bool = False


class Entities(BaseModel):
    modulos: list[Entity] = []
    techs: list[Entity] = []
    requisitos: list[Entity] = []


class Slots(BaseModel):
    accion: str | None = None
    tipo: str | None = None
    nombre: str | None = None
    tech: str | None = None
    dominio: str | None = None
    completado: bool = False
    faltantes: list[str] = []


class AmbiguityResult(BaseModel):
    detected: bool = False
    elementos: list[dict] = []


class ContextState(BaseModel):
    turno: int = 1
    session_id: str = ""
    historial: list[dict] = []
    ultima_entidad: str = ""
    defaults: dict = {"tech": "nestjs"}


class EnrichedInput(BaseModel):
    raw: str
    intent: IntentResult
    entities: Entities
    slots: Slots
    ambiguity: AmbiguityResult
    context: ContextState = Field(default_factory=ContextState)
