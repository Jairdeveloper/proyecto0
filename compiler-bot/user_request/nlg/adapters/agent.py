"""Agent adapter — dict estructurado para consumo por otros agentes."""

from __future__ import annotations

import json

from user_request.contracts.response import ResponseObject
from user_request.nlg.adapters.base import ChannelAdapter


class AgentAdapter(ChannelAdapter):
    """Adapta contenido para consumo por otros agentes.

    - Formato JSON estructurado (no texto libre)
    - Campos semanticos para parsing automatico
    """

    def adapt(self, content: str, response: ResponseObject) -> str:
        """Convierte ResponseObject a JSON estructurado para agentes.

        Args:
            content: Contenido textual.
            response: ResponseObject original.

        Returns:
            JSON string con campos semanticos.
        """
        payload = {
            "_type": "agent_response",
            "_version": "1.0",
            "status": "ok" if response.success else "error",
            "summary": content or response.message or "",
            "data": response.data,
            "error": response.error,
            "suggestions": response.suggestions,
            "channel": response.channel.value,
        }
        return json.dumps(payload, indent=2, default=str, ensure_ascii=False)
