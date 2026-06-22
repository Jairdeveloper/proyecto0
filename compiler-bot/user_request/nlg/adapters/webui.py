"""WebUI adapter — HTML fragments o JSON enriquecido."""

from __future__ import annotations

from user_request.contracts.response import ResponseObject
from user_request.nlg.adapters.base import ChannelAdapter


class WebUIAdapter(ChannelAdapter):
    """Adapta contenido para WebUI.

    - HTML fragment (no pagina completa)
    - Enlaces clickables
    - Estilos inline minimos
    """

    def adapt(self, content: str, response: ResponseObject) -> str:
        """Convierte contenido a HTML fragment.

        Args:
            content: Contenido textual.
            response: ResponseObject original.

        Returns:
            String HTML.
        """
        title = "Exito" if response.success else "Error"
        status_class = "success" if response.success else "error"
        title_html = f'<div class="nlg-response {status_class}">'
        lines = [title_html]

        lines.append(f"  <h3>{title}</h3>")
        if content:
            escaped = (
                content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            lines.append(f"  <p>{escaped}</p>")

        if response.suggestions:
            lines.append("  <ul>")
            for s in response.suggestions:
                escaped = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                lines.append(f'    <li><a href="#">{escaped}</a></li>')
            lines.append("  </ul>")

        lines.append("</div>")
        return "\n".join(lines)
