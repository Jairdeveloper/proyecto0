"""Success formatter — respuesta positiva en lenguaje natural."""

from __future__ import annotations

from user_request.contracts.response import ResponseObject
from user_request.nlg.formatters.base import NLGFormatter


class SuccessFormatter(NLGFormatter):
    """Formatea respuestas exitosas del sistema.

    Produce mensajes como:
        "Creado modulo pagos en NestJS. Archivos: controller, service..."
    """

    def format(self, response: ResponseObject) -> str:
        """Formatea un ResponseObject exitoso como texto legible.

        Args:
            response: ResponseObject con success=True.

        Returns:
            Mensaje en lenguaje natural describiendo la accion realizada.
        """
        if response.message:
            parts = [response.message]
        elif response.data:
            parts = [self._format_data(response.data)]
        else:
            return "Operacion completada."

        if response.suggestions:
            parts.append("")
            parts.append("Sugerencias:")
            for s in response.suggestions:
                parts.append(f"  - {s}")

        return "\n".join(parts)

    def _format_data(self, data: dict) -> str:
        """Formatea datos estructurados como texto legible."""
        lines: list[str] = []

        module_name = data.get("module") or data.get("modulo", "")
        tech = data.get("tech") or data.get("tecnologia", "")

        if module_name:
            if tech:
                lines.append(f"Creado modulo {module_name} en {tech}.")
            else:
                lines.append(f"Creado modulo {module_name}.")

        files = data.get("files") or data.get("archivos", [])
        if files:
            lines.append(f"Archivos: {', '.join(files) if isinstance(files, list) else files}")

        entities = data.get("entities") or data.get("entidades", [])
        if entities:
            names = [e.get("nombre", str(e)) for e in entities] if isinstance(entities, list) else [str(entities)]
            lines.append(f"Entidades: {', '.join(names)}")

        if not lines:
            lines.append("Operacion completada exitosamente.")

        return " ".join(lines)
