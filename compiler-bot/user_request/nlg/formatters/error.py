"""Error formatter — mensajes de error en lenguaje natural."""

from __future__ import annotations

from user_request.contracts.response import ResponseObject
from user_request.nlg.formatters.base import NLGFormatter


class ErrorFormatter(NLGFormatter):
    """Formatea respuestas de error del sistema.

    Produce mensajes como:
        "No se pudo crear el modulo: el nombre ya existe."
    """

    def format(self, response: ResponseObject) -> str:
        """Formatea un ResponseObject de error como texto legible.

        Args:
            response: ResponseObject con success=False.

        Returns:
            Mensaje de error en lenguaje natural.
        """
        if response.error:
            msg = f"Error: {response.error}"
        elif response.message:
            msg = f"Error: {response.message}"
        else:
            msg = "Error: la operacion no pudo completarse."

        if response.suggestions:
            msg += "\n\nSugerencias:"
            for s in response.suggestions:
                msg += f"\n  - {s}"

        return msg
