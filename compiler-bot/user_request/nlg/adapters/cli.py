"""CLI adapter — texto plano, compacto, sin adornos."""

from __future__ import annotations

import textwrap

from user_request.contracts.response import ResponseObject
from user_request.nlg.adapters.base import ChannelAdapter


class CLIAdapter(ChannelAdapter):
    """Adapta contenido para terminal.

    - Texto plano sin adornos
    - Max 80 caracteres por linea
    - Sin HTML, sin markdown
    """

    _MAX_LINE_WIDTH: int = 80

    def adapt(self, content: str, response: ResponseObject) -> str:
        """Adapta contenido para salida por terminal.

        Args:
            content: Contenido textual.
            response: ResponseObject original.

        Returns:
            Texto plano con lineas truncadas a 80 chars.
        """
        if not content:
            return ""

        wrapped = textwrap.fill(content, width=self._MAX_LINE_WIDTH)
        return wrapped
