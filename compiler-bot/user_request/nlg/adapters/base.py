"""Abstract base class for NLG channel adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from user_request.contracts.response import ResponseObject


class ChannelAdapter(ABC):
    """Adapta el contenido generado al formato del canal destino."""

    @abstractmethod
    def adapt(self, content: str, response: ResponseObject) -> str:
        """Adapta el contenido al formato del canal.

        Args:
            content: Contenido textual generado por el formatter.
            response: ResponseObject original (para metadatos).

        Returns:
            Contenido adaptado al formato del canal.
        """
