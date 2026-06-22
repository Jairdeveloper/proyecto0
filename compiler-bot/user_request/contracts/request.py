"""Modelos Pydantic de entrada: RequestObject y tipos auxiliares."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field

from user_request.contracts.enums import IntentType, RequestChannel


# ---------------------------------------------------------------------------
# Data-classes inmutables para sub-componentes de RequestObject
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IntentResult:
    """Resultado de la clasificacion de intencion.

    Attributes:
        primary: Intencion principal detectada.
        secondary: Segunda intencion posible (si hay ambiguedad).
        confidence: Confianza del clasificador ganador (0.0 - 1.0).
        classifier: Identificador del clasificador que produjo el resultado
                    (``"llm"``, ``"semantic"``, ``"rule"``).
        scores: Diccionario completo de scores por intencion.
        domain: Dominio detectado (backend, frontend, infra).
    """

    primary: IntentType
    secondary: IntentType | None = None
    confidence: float = 0.0
    classifier: str = "rule"
    scores: dict[str, float] = field(default_factory=dict)
    domain: str = "backend"


@dataclass(frozen=True)
class Entity:
    """Una entidad extraida del texto del usuario.

    Attributes:
        nombre: Nombre de la entidad.
        tipo: Tipo semantico (module, tech, requirement, ...).
        rol: Rol dentro de la entidad (opcional).
        negado: True si la entidad aparece en contexto negativo ("sin ...").
    """

    nombre: str
    tipo: str
    rol: str = ""
    negado: bool = False


@dataclass(frozen=True)
class Entities:
    """Conjunto de entidades extraidas, agrupadas por categoria."""

    modulos: list[Entity] = field(default_factory=list)
    techs: list[Entity] = field(default_factory=list)
    requisitos: list[Entity] = field(default_factory=list)


@dataclass(frozen=True)
class Slots:
    """Slots rellenos tras el proceso de SlotFilling.

    Cada slot representa un parametro estructurado necesario
    para ejecutar la intencion del usuario.
    """

    accion: str | None = None
    tipo: str | None = None
    nombre: str | None = None
    tech: str | None = None
    dominio: str | None = None
    atributos: list[tuple[str, str]] = field(default_factory=list)
    completado: bool = False
    faltantes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AmbiguityResult:
    """Resultado del analisis de ambiguedad.

    Attributes:
        detected: True si se detecto alguna ambiguedad o problema.
        elementos: Lista de problemas detectados con sugerencias.
    """

    detected: bool = False
    elementos: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class RequestContext:
    """Contexto de la solicitud: sesion, historial, defaults.

    Attributes:
        session_id: Identificador unico de sesion.
        history: Historial de interacciones previas (lista de dicts).
        defaults: Valores por defecto del usuario (tech, output dir, ...).
        channel: Canal de la solicitud actual.
    """

    session_id: str = ""
    history: list[dict] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=lambda: {"tech": "nestjs"})
    channel: RequestChannel = RequestChannel.CLI


# ---------------------------------------------------------------------------
# RequestObject — contrato de entrada principal
# ---------------------------------------------------------------------------


class RequestObject(BaseModel):
    """Contrato de entrada inmutable que representa la intencion del usuario
    ya procesada por el pipeline NLU.

    Attributes:
        raw: Texto original del usuario (sin modificar).
        normalized: Texto normalizado (lowercase, unicode NFKC, etc.).
        intent: Intencion clasificada.
        entities: Entidades extraidas.
        slots: Slots rellenos.
        ambiguity: Resultado del analisis de ambiguedad.
        channel: Canal de la solicitud.
        context: Contexto de sesion (historial, defaults).
        metadata: Metadatos adicionales (timestamp, version, flags).
    """

    raw: str
    normalized: str
    intent: IntentResult
    entities: Entities
    slots: Slots
    ambiguity: AmbiguityResult | None = None
    channel: RequestChannel = RequestChannel.CLI
    context: RequestContext | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
