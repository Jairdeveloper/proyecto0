"""Editor adapter — snippets cortos para plugins de IDE."""

from __future__ import annotations

from user_request.contracts.response import ResponseObject
from user_request.nlg.adapters.base import ChannelAdapter


class EditorAdapter(ChannelAdapter):
    """Adapta contenido para plugins de editor (VSCode, etc.).

    - Mensajes cortos (max 200 chars)
    - Sin adornos
    - Formato optimizado para notificaciones del editor
    """

    _MAX_LENGTH: int = 200

    def adapt(self, content: str, response: ResponseObject) -> str:
        """Acorta contenido para notificaciones de editor.

        Args:
            content: Contenido textual.
            response: ResponseObject original.

        Returns:
            Texto truncado a 200 chars.
        """
        if not content:
            return ""

        if len(content) > self._MAX_LENGTH:
            content = content[: self._MAX_LENGTH - 3] + "..."

        if response.success:
            return f"✓ {content}"
        return f"✗ {content}"
