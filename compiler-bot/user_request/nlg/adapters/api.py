"""API adapter — JSON puro para consumo programatico."""

from __future__ import annotations

import json

from user_request.contracts.response import ResponseObject
from user_request.nlg.adapters.base import ChannelAdapter


class APIAdapter(ChannelAdapter):
    """Adapta contenido para APIs REST.

    - JSON puro (no texto plano)
    - El mensaje va en field ``message``
    - Datos estructurados en field ``data``
    """

    def adapt(self, content: str, response: ResponseObject) -> str:
        """Convierte ResponseObject a JSON string.

        Args:
            content: Contenido textual (se coloca en field ``message``).
            response: ResponseObject original.

        Returns:
            JSON string con fields success, message, data, error, suggestions.
        """
        payload = {
            "success": response.success,
            "message": content if content else response.message,
            "data": response.data,
            "error": response.error,
            "suggestions": response.suggestions,
            "channel": response.channel.value,
        }
        return json.dumps(payload, indent=2, default=str, ensure_ascii=False)
