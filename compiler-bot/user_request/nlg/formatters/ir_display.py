"""IR display formatter — muestra el IR de forma legible."""

from __future__ import annotations

import json

from user_request.contracts.response import ResponseObject
from user_request.nlg.formatters.base import NLGFormatter


class IRFormatter(NLGFormatter):
    """Formatea el Intermediate Representation de forma legible.

    No produce JSON crudo sino una representacion estructurada
    pero legible por humanos.
    """

    def format(self, response: ResponseObject) -> str:
        """Formatea el IR como texto legible.

        Args:
            response: ResponseObject con data conteniendo IR.

        Returns:
            IR formateado como texto estructurado.
        """
        ir_data = response.data.get("ir") if response.data else None
        if ir_data is None:
            return json.dumps(response.data, indent=2, default=str) if response.data else "(sin datos)"

        lines: list[str] = []
        lines.append("=== Intermediate Representation ===")
        lines.append("")

        accion = ir_data.get("accion") or ir_data.get("action", "")
        modulo = ir_data.get("modulo") or ir_data.get("module", "")
        if accion:
            lines.append(f"Accion: {accion}")
        if modulo:
            lines.append(f"Modulo: {modulo}")

        entities = ir_data.get("entidades") or ir_data.get("entities", [])
        if entities:
            lines.append("")
            lines.append(f"Entidades ({len(entities)}):")
            for ent in entities:
                name = ent.get("nombre") or ent.get("name", "")
                etype = ent.get("tipo") or ent.get("type", "")
                lines.append(f"  - {name} ({etype})")

        techs = ir_data.get("tecnologias") or ir_data.get("techs", [])
        if techs:
            lines.append("")
            lines.append(f"Tecnologias ({len(techs)}): {', '.join(techs)}")

        plan = ir_data.get("plan", [])
        if plan:
            lines.append("")
            lines.append("Plan:")
            for i, step in enumerate(plan, 1):
                desc = step.get("descripcion") or step.get("description", str(step))
                lines.append(f"  {i}. {desc}")

        return "\n".join(lines)
