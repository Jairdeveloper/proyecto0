import re

from agentic_pipeline.nlp.enriched_input import AmbiguityResult, Entities, IntentResult, Slots


class AmbiguityDetector:
    PRONOMBRES: list[str] = ["lo", "le", "la", "ello", "eso", "le"]

    def detect(
        self,
        text: str,
        intent: IntentResult,
        entities: Entities,
        slots: Slots,
    ) -> AmbiguityResult:
        result = AmbiguityResult()

        if intent.primary == "UNKNOWN":
            result.detected = True
            result.elementos.append(
                {
                    "tipo": "intencion_baja",
                    "descripcion": "No se pudo clasificar la intencion",
                    "sugerencia": "Quieres crear, consultar, modificar o eliminar algo?",
                }
            )
            return result

        if intent.confidence < 0.4:
            result.detected = True
            result.elementos.append(
                {
                    "tipo": "intencion_baja",
                    "descripcion": "No se puede determinar la intencion principal",
                    "sugerencia": "Quieres crear, consultar, modificar o eliminar algo?",
                }
            )

        top_two = sorted(intent.scores.items(), key=lambda x: -x[1])
        if len(top_two) >= 2 and (top_two[0][1] - top_two[1][1]) < 0.1:
            result.detected = True
            result.elementos.append(
                {
                    "tipo": "multi_intencion",
                    "descripcion": f"{top_two[0][0]} y {top_two[1][0]} tienen scores similares",
                    "opciones": [top_two[0][0], top_two[1][0]],
                }
            )

        if slots.faltantes:
            result.detected = True
            result.elementos.append(
                {
                    "tipo": "slot_faltante",
                    "descripcion": f"Faltan slots: {', '.join(slots.faltantes)}",
                    "faltantes": slots.faltantes,
                }
            )

        text_lower = text.lower()
        for p in self.PRONOMBRES:
            if re.search(rf"\b{p}\b", text_lower):
                result.detected = True
                result.elementos.append(
                    {
                        "tipo": "referencia_pendiente",
                        "descripcion": f"Pronombre '{p}' sin antecedente",
                        "sugerencia": "A que modulo te refieres?",
                    }
                )
                break

        return result
