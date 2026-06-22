"""SlotFiller v2 — taxonomia unificada de intenciones.

La taxonomia unificada mapea las 6 intenciones canonicas (CREATE, READ,
UPDATE, DELETE, EXPLAIN, CONFIGURE) a sus slots requeridos y opcionales,
con soporte de alias para compatibilidad con la taxonomia legacy
(SCAFFOLD, QUERY, MODIFY, etc.).
"""

from __future__ import annotations

from typing import Any

from user_request.contracts.enums import IntentType, SlotName
from user_request.contracts.request import Entities, IntentResult, Slots

# ---------------------------------------------------------------------------
# Taxonomia unificada
# ---------------------------------------------------------------------------

UnifiedTaxonomyEntry = dict[str, Any]

UNIFIED_TAXONOMY: dict[str, UnifiedTaxonomyEntry] = {
    IntentType.CREATE.value: {
        "aliases": ["SCAFFOLD", "GENERATE", "NEW"],
        "required_slots": [SlotName.ACCION, SlotName.TIPO, SlotName.NOMBRE],
        "optional_slots": [SlotName.TECH, SlotName.ATRIBUTOS, SlotName.DOMINIO],
    },
    IntentType.READ.value: {
        "aliases": ["QUERY", "EXPLORE", "GET"],
        "required_slots": [SlotName.ACCION, SlotName.OBJETIVO],
        "optional_slots": [SlotName.FILTRO, SlotName.LIMITE],
    },
    IntentType.UPDATE.value: {
        "aliases": ["MODIFY", "EDIT", "CHANGE"],
        "required_slots": [SlotName.ACCION, SlotName.NOMBRE, SlotName.CAMBIO],
        "optional_slots": [SlotName.VALOR],
    },
    IntentType.DELETE.value: {
        "aliases": ["REMOVE"],
        "required_slots": [SlotName.ACCION, SlotName.NOMBRE],
        "optional_slots": [],
    },
    IntentType.EXPLAIN.value: {
        "aliases": ["QUERY", "HELP"],
        "required_slots": [SlotName.ACCION, SlotName.TOPICO],
        "optional_slots": [SlotName.PROFUNDIDAD],
    },
    IntentType.CONFIGURE.value: {
        "aliases": ["SET", "CONFIG"],
        "required_slots": [SlotName.PARAMETRO, SlotName.VALOR],
        "optional_slots": [],
    },
}

# ---------------------------------------------------------------------------
# Mapeo IntentType → accion string
# ---------------------------------------------------------------------------

ACTION_MAP: dict[str, str] = {
    IntentType.CREATE.value: "create",
    IntentType.READ.value: "read",
    IntentType.UPDATE.value: "update",
    IntentType.DELETE.value: "delete",
    IntentType.EXPLAIN.value: "explain",
    IntentType.CONFIGURE.value: "configure",
}

# ---------------------------------------------------------------------------
# Mapeo de tipos de entidad
# ---------------------------------------------------------------------------

TYPE_MAP: dict[str, str] = {
    "modulo": "module",
    "entidad": "entity",
    "proyecto": "project",
    "sistema": "project",
}


class SlotFiller:
    """Rellena slots estructurados a partir de la intencion y entidades.

    Usa la taxonomia unificada (``UNIFIED_TAXONOMY``) para determinar que
    slots son requeridos segun la intencion, y los rellena extrayendo
    valores de las entidades extraidas.
    """

    def fill(self, intent: IntentResult, entities: Entities) -> Slots:
        """Crea un ``Slots`` a partir de la intencion y entidades.

        Args:
            intent: Resultado de la clasificacion de intencion.
            entities: Entidades extraidas del texto.

        Returns:
            Slots con los valores inferidos y el estado de completitud.
        """
        intent_value = intent.primary.value if isinstance(intent.primary, IntentType) else str(intent.primary).lower()
        slots = self._build_slots(intent_value, entities)
        slots = self._mark_missing(slots, intent_value)
        return slots

    def _build_slots(self, intent_value: str, entities: Entities) -> Slots:
        """Construye un objeto ``Slots`` infiriendo valores de entidades."""
        accion = ACTION_MAP.get(intent_value)
        tipo = self._infer_type(entities)
        nombre = self._infer_name(entities)
        tech = self._infer_tech(entities)
        dominio = self._infer_domain(entities)
        atributos = self._infer_atributos(entities)

        return Slots(
            accion=accion,
            tipo=tipo,
            nombre=nombre,
            tech=tech,
            dominio=dominio,
            atributos=atributos,
        )

    def _mark_missing(self, slots: Slots, intent_value: str) -> Slots:
        """Marca slots faltantes segun la taxonomia unificada."""
        entry = UNIFIED_TAXONOMY.get(intent_value)
        if entry is None:
            # Intencion desconocida: no validar slots
            return slots

        required_slot_names = {s.value for s in entry["required_slots"]}
        faltantes: list[str] = []

        if "accion" in required_slot_names and slots.accion is None:
            faltantes.append("accion")
        if "tipo" in required_slot_names and slots.tipo is None:
            faltantes.append("tipo")
        if "nombre" in required_slot_names and slots.nombre is None:
            faltantes.append("nombre")
        if "objetivo" in required_slot_names:
            faltantes.append("objetivo")
        if "cambio" in required_slot_names and slots.nombre is None:
            faltantes.append("cambio")
        if "topico" in required_slot_names:
            faltantes.append("topico")
        if "parametro" in required_slot_names:
            faltantes.append("parametro")

        faltantes = sorted(set(faltantes))
        completado = len(faltantes) == 0

        # Reconstruir Slots con estado actualizado
        slots_dict = {
            "accion": slots.accion,
            "tipo": slots.tipo,
            "nombre": slots.nombre,
            "tech": slots.tech,
            "dominio": slots.dominio,
            "atributos": slots.atributos,
            "completado": completado,
            "faltantes": faltantes,
        }
        return Slots(**slots_dict)

    def _infer_type(self, entities: Entities) -> str | None:
        if entities.modulos:
            raw_tipo = entities.modulos[0].tipo
            return TYPE_MAP.get(raw_tipo, raw_tipo)
        return None

    def _infer_name(self, entities: Entities) -> str | None:
        if entities.modulos:
            return entities.modulos[0].nombre
        return None

    def _infer_tech(self, entities: Entities) -> str | None:
        if entities.techs:
            return entities.techs[0].nombre
        return None

    def _infer_domain(self, entities: Entities) -> str | None:
        return None

    def _infer_atributos(self, entities: Entities) -> list[tuple[str, str]]:
        _ = entities
        return []
