"""Formatter registry — resolve_formatter() factory."""

from __future__ import annotations

from user_request.contracts.response import ResponseObject
from user_request.nlg.formatters.base import NLGFormatter
from user_request.nlg.formatters.error import ErrorFormatter
from user_request.nlg.formatters.ir_display import IRFormatter
from user_request.nlg.formatters.metrics import MetricFormatter
from user_request.nlg.formatters.success import SuccessFormatter

_FORMATTER_REGISTRY: dict[str, NLGFormatter] = {
    "success": SuccessFormatter(),
    "error": ErrorFormatter(),
    "ir": IRFormatter(),
    "metrics": MetricFormatter(),
}

__all__ = [
    "ErrorFormatter",
    "IRFormatter",
    "MetricFormatter",
    "NLGFormatter",
    "SuccessFormatter",
    "resolve_formatter",
]


def resolve_formatter(response: ResponseObject) -> NLGFormatter:
    """Resuelve el formateador adecuado para un ResponseObject.

    La seleccion se basa en el contenido del ResponseObject:
    - Si ``error`` no es None → ErrorFormatter
    - Si ``data`` tiene clave ``\"ir\"`` → IRFormatter
    - Si ``data`` tiene clave ``\"metrics\"`` → MetricFormatter
    - Por defecto → SuccessFormatter
    """
    if response.error is not None:
        return _FORMATTER_REGISTRY["error"]
    if response.data is not None:
        if "ir" in response.data:
            return _FORMATTER_REGISTRY["ir"]
        if "metrics" in response.data:
            return _FORMATTER_REGISTRY["metrics"]
    return _FORMATTER_REGISTRY["success"]
