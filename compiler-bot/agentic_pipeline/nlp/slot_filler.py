from agentic_pipeline.nlp.enriched_input import Entities, IntentResult, Slots


class SlotFiller:
    REQUIRED: dict[str, list[str]] = {
        "SCAFFOLD": ["accion", "tipo", "nombre"],
        "MODIFY": ["accion", "nombre"],
        "DELETE": ["accion", "nombre"],
        "QUERY": ["dominio"],
    }

    ACTION_MAP: dict[str, str] = {
        "SCAFFOLD": "create",
        "MODIFY": "update",
        "DELETE": "delete",
        "EXPLORE": "read",
        "QUERY": "read",
        "CONFIGURE": "configure",
    }

    TYPE_MAP: dict[str, str] = {
        "modulo": "module",
        "entidad": "entity",
        "proyecto": "project",
        "sistema": "project",
    }

    def fill(self, intent: IntentResult, entities: Entities) -> Slots:
        slots = Slots(
            accion=self.ACTION_MAP.get(intent.primary),
            tipo=self._infer_type(intent, entities),
            nombre=self._infer_name(entities),
            tech=self._infer_tech(entities),
            dominio=intent.domain,
        )
        required = self.REQUIRED.get(intent.primary, [])
        slots.faltantes = [s for s in required if getattr(slots, s) is None]
        slots.completado = len(slots.faltantes) == 0
        return slots

    def _infer_type(self, intent: IntentResult, entities: Entities) -> str | None:
        if entities.modulos:
            return "module"
        if intent.primary == "SCAFFOLD":
            return "module"
        return None

    def _infer_name(self, entities: Entities) -> str | None:
        if entities.modulos:
            return entities.modulos[0].nombre
        return None

    def _infer_tech(self, entities: Entities) -> str | None:
        if entities.techs:
            return entities.techs[0].nombre
        return None
