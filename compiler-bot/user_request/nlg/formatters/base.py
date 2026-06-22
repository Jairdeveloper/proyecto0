"""Abstract base class for NLG formatters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from user_request.contracts.response import ResponseObject


class NLGFormatter(ABC):
    """Transforma un ``ResponseObject`` en una representacion textual
    segun el tipo de contenido (success, error, ir, metrics).
    """

    @abstractmethod
    def format(self, response: ResponseObject) -> str:
        """Formatea la respuesta como texto legible.

        Args:
            response: ResponseObject a formatear.

        Returns:
            String con el contenido formateado.
        """
