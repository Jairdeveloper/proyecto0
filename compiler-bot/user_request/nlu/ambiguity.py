"""Ambiguity detection and interactive disambiguation."""

from __future__ import annotations

import re
from typing import Any

from user_request.contracts.enums import IntentType
from user_request.contracts.request import (
    AmbiguityResult,
    Entities,
    IntentResult,
    RequestObject,
    Slots,
)


class AmbiguityResolver:
    """Detecta ambiguedades en la solicitud del usuario y genera
    preguntas declarativas para resolverlas.

    Extiende el legacy ``AmbiguityDetector`` (agentic_pipeline.nlp.ambiguity_detector)
    anadiendo generacion de preguntas en lenguaje natural.
    """

    PRONOMBRES: list[str] = ["lo", "le", "la", "ello", "eso", "le"]

    # Mapeo de slot faltante a pregunta en lenguaje natural
    SLOT_QUESTIONS: dict[str, str] = {
        "accion": "Que accion quieres realizar? (crear, consultar, modificar, eliminar)",
        "tipo": "Que tipo de componente quieres? (modulo, entidad, proyecto)",
        "nombre": "Como se llama el componente?",
        "objetivo": "Que quieres consultar?",
        "cambio": "Que cambio quieres aplicar?",
        "topico": "Sobre que tema quieres informacion?",
        "parametro": "Que parametro quieres configurar?",
        "valor": "Que valor quieres asignar?",
        "tech": "En que tecnologia? (NestJS, Prisma, React...)",
    }

    def resolve(self, request: RequestObject) -> RequestObject:
        """Analiza el RequestObject y marca ambiguedades detectadas.

        Realiza el mismo analisis que el legacy ``AmbiguityDetector.detect()``
        pero opera directamente sobre el RequestObject.
        """
        ambiguity = self.detect(
            request.raw,
            request.intent,
            request.entities,
            request.slots,
        )
        request_dict = request.model_dump()
        request_dict["ambiguity"] = {
            "detected": ambiguity.detected,
            "elementos": ambiguity.elementos,
        }
        return RequestObject.model_validate(request_dict)

    def detect(
        self,
        text: str,
        intent: IntentResult,
        entities: Entities,
        slots: Slots,
    ) -> AmbiguityResult:
        """Detecta ambiguedades en la entrada del usuario.

        Args:
            text: Texto original del usuario.
            intent: Intencion clasificada.
            entities: Entidades extraidas.
            slots: Slots rellenos.

        Returns:
            AmbiguityResult con problemas detectados.
        """
        result = AmbiguityResult()

        # Intencion desconocida
        if intent.primary == IntentType.CREATE and intent.confidence < 0.3:
            result = self._add_issue(
                result,
                "intencion_baja",
                "No se pudo clasificar la intencion",
                "Quieres crear, consultar, modificar o eliminar algo?",
            )
            return result

        # Baja confianza
        if intent.confidence < 0.4:
            result = self._add_issue(
                result,
                "intencion_baja",
                "No se puede determinar la intencion principal",
                "Quieres crear, consultar, modificar o eliminar algo?",
            )

        # Multi-intencion
        if intent.scores:
            top_two = sorted(intent.scores.items(), key=lambda x: -x[1])
            if len(top_two) >= 2 and (top_two[0][1] - top_two[1][1]) < 0.1:
                result = self._add_issue(
                    result,
                    "multi_intencion",
                    f"{top_two[0][0]} y {top_two[1][0]} tienen scores similares",
                    None,
                    opciones=[top_two[0][0], top_two[1][0]],
                )

        # Slots faltantes
        if slots.faltantes:
            result = self._add_issue(
                result,
                "slot_faltante",
                f"Faltan slots: {', '.join(slots.faltantes)}",
                None,
                faltantes=slots.faltantes,
            )

        # Pronombres sin antecedente
        text_lower = text.lower()
        for p in self.PRONOMBRES:
            if re.search(rf"\b{p}\b", text_lower):
                result = self._add_issue(
                    result,
                    "referencia_pendiente",
                    f"Pronombre '{p}' sin antecedente",
                    "A que modulo te refieres?",
                )
                break

        return result

    def generate_questions(self, request: RequestObject) -> list[str]:
        """Genera preguntas en lenguaje natural para resolver ambiguedades.

        Args:
            request: RequestObject con ambiguedades detectadas.

        Returns:
            Lista de preguntas para resolver los problemas detectados.
        """
        questions: list[str] = []

        if request.ambiguity is None:
            return questions

        for elemento in request.ambiguity.elementos:
            tipo = elemento.get("tipo", "")

            if tipo == "slot_faltante":
                faltantes = elemento.get("faltantes", [])
                for slot in faltantes:
                    q = self.SLOT_QUESTIONS.get(slot)
                    if q:
                        questions.append(q)

            elif tipo == "intencion_baja":
                sugerencia = elemento.get("sugerencia")
                if sugerencia:
                    questions.append(sugerencia)

            elif tipo == "referencia_pendiente":
                sugerencia = elemento.get("sugerencia")
                if sugerencia:
                    questions.append(sugerencia)

            elif tipo == "multi_intencion":
                opciones = elemento.get("opciones", [])
                if opciones:
                    questions.append(
                        f"Cual de estas opciones prefieres? ({' / '.join(opciones)})"
                    )

        return questions

    def _add_issue(
        self,
        result: AmbiguityResult,
        tipo: str,
        descripcion: str,
        sugerencia: str | None,
        opciones: list[str] | None = None,
        faltantes: list[str] | None = None,
    ) -> AmbiguityResult:
        elemento: dict[str, Any] = {
            "tipo": tipo,
            "descripcion": descripcion,
        }
        if sugerencia:
            elemento["sugerencia"] = sugerencia
        if opciones:
            elemento["opciones"] = opciones
        if faltantes:
            elemento["faltantes"] = faltantes

        current = result.elementos
        current.append(elemento)
        return AmbiguityResult(detected=True, elementos=current)
