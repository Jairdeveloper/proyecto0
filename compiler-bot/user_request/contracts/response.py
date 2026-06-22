"""Modelos Pydantic de salida: ResponseObject."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from user_request.contracts.enums import RequestChannel


class ResponseObject(BaseModel):
    """Contrato de salida del sistema hacia el usuario.

    Attributes:
        success: Estado global de la operacion.
        data: Datos estructurados (IR, comandos, etc.).
        message: Mensaje en lenguaje natural para el usuario.
        error: Mensaje de error human-readable (solo si success=False).
        suggestions: Lista de sugerencias de seguimiento.
        channel: Canal destino de la respuesta.
        metadata: Metadatos (timestamp, duracion, stages ejecutados).
    """

    success: bool = True
    data: dict[str, Any] | None = None
    message: str | None = None
    error: str | None = None
    suggestions: list[str] = []
    channel: RequestChannel = RequestChannel.CLI
    metadata: dict[str, Any] = {}
