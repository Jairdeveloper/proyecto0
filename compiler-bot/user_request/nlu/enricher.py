"""Context enricher for NLU pipeline.

Anade informacion contextual al RequestObject: historial de sesion,
defaults del usuario, estado del sistema.
"""

from __future__ import annotations

from typing import Any, Callable

from user_request.contracts.enums import RequestChannel
from user_request.contracts.request import RequestContext, RequestObject


class Enricher:
    """Enriquece el RequestObject con informacion contextual.

    Centraliza la informacion contextual que actualmente esta dispersa
    en ``ContextState`` y ``perception_unit.py``.
    """

    def __init__(
        self,
        context_store: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        self._store = context_store

    def enrich(
        self,
        request: RequestObject,
        session_id: str = "",
        defaults: dict[str, Any] | None = None,
    ) -> RequestObject:
        """Anade contexto de sesion, historial y defaults al RequestObject.

        Args:
            request: RequestObject del pipeline NLU.
            session_id: Identificador de sesion (opcional).
            defaults: Valores por defecto del usuario (opcional).

        Returns:
            RequestObject con contexto enriquecido.
        """
        context_defaults = defaults or {"tech": "nestjs"}

        # Intentar obtener contexto del store externo
        if self._store is not None:
            try:
                stored = self._store()
                session_id = session_id or stored.get("session_id", "")
                context_defaults = stored.get("defaults", context_defaults)
            except Exception:
                pass

        context = RequestContext(
            session_id=session_id,
            defaults=context_defaults,
            channel=request.channel,
        )

        request_dict = request.model_dump()
        request_dict["context"] = {
            "session_id": context.session_id,
            "history": context.history,
            "defaults": context.defaults,
            "channel": context.channel.value if isinstance(context.channel, RequestChannel) else context.channel,
        }

        return RequestObject.model_validate(request_dict)
