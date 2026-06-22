"""Tests for AmbiguityResolver."""

from user_request.contracts.enums import IntentType
from user_request.contracts.request import (
    AmbiguityResult,
    Entities,
    Entity,
    IntentResult,
    RequestObject,
    Slots,
)
from user_request.nlu.ambiguity import AmbiguityResolver


class TestAmbiguityResolver:
    def test_no_ambiguity(self):
        resolver = AmbiguityResolver()
        result = resolver.detect(
            "crea modulo pagos",
            IntentResult(primary=IntentType.CREATE, confidence=0.95),
            Entities(modulos=[Entity(nombre="pagos", tipo="module")]),
            Slots(accion="create", tipo="module", nombre="pagos", completado=True),
        )
        assert not result.detected
        assert len(result.elementos) == 0

    def test_low_confidence_detected(self):
        resolver = AmbiguityResolver()
        result = resolver.detect(
            "texto ambiguo",
            IntentResult(primary=IntentType.CREATE, confidence=0.2),
            Entities(),
            Slots(),
        )
        assert result.detected
        tipos = [e["tipo"] for e in result.elementos]
        assert "intencion_baja" in tipos

    def test_missing_slots_detected(self):
        resolver = AmbiguityResolver()
        result = resolver.detect(
            "crea algo",
            IntentResult(primary=IntentType.CREATE, confidence=0.8),
            Entities(),
            Slots(
                accion="create",
                tipo=None,
                nombre=None,
                completado=False,
                faltantes=["tipo", "nombre"],
            ),
        )
        assert result.detected
        tipos = [e["tipo"] for e in result.elementos]
        assert "slot_faltante" in tipos

    def test_pronominal_reference_detected(self):
        resolver = AmbiguityResolver()
        result = resolver.detect(
            "agrega un campo a eso",
            IntentResult(primary=IntentType.UPDATE, confidence=0.8),
            Entities(),
            Slots(accion="update", nombre="campo"),
        )
        assert result.detected
        tipos = [e["tipo"] for e in result.elementos]
        assert "referencia_pendiente" in tipos

    def test_multi_intent_detected(self):
        resolver = AmbiguityResolver()
        result = resolver.detect(
            "configura y crea",
            IntentResult(
                primary=IntentType.CONFIGURE,
                confidence=0.5,
                scores={"CONFIGURE": 0.5, "CREATE": 0.45},
            ),
            Entities(),
            Slots(),
        )
        tipos = [e["tipo"] for e in result.elementos]
        assert "multi_intencion" in tipos

    def test_no_false_positive_on_modulo(self):
        resolver = AmbiguityResolver()
        result = resolver.detect(
            "crea modulo pagos",
            IntentResult(primary=IntentType.CREATE, confidence=0.95),
            Entities(modulos=[Entity(nombre="pagos", tipo="module")]),
            Slots(accion="create", tipo="module", nombre="pagos", completado=True),
        )
        assert not result.detected


class TestGenerateQuestions:
    def test_generates_questions_for_missing_slots(self):
        resolver = AmbiguityResolver()
        request = RequestObject(
            raw="crea algo",
            normalized="crea algo",
            intent=IntentResult(primary=IntentType.CREATE, confidence=0.8),
            entities=Entities(),
            slots=Slots(
                accion="create",
                completado=False,
                faltantes=["tipo", "nombre"],
            ),
            ambiguity=AmbiguityResult(
                detected=True,
                elementos=[
                    {
                        "tipo": "slot_faltante",
                        "descripcion": "Faltan slots: tipo, nombre",
                        "faltantes": ["tipo", "nombre"],
                    }
                ],
            ),
        )
        questions = resolver.generate_questions(request)
        assert len(questions) == 2
        assert any("componente" in q.lower() for q in questions)
        assert any("llama" in q.lower() for q in questions)

    def test_generates_suggestion_for_low_confidence(self):
        resolver = AmbiguityResolver()
        request = RequestObject(
            raw="xyz",
            normalized="xyz",
            intent=IntentResult(primary=IntentType.CREATE, confidence=0.2),
            entities=Entities(),
            slots=Slots(),
            ambiguity=AmbiguityResult(
                detected=True,
                elementos=[
                    {
                        "tipo": "intencion_baja",
                        "descripcion": "No se pudo clasificar",
                        "sugerencia": "Quieres crear, consultar, modificar o eliminar algo?",
                    }
                ],
            ),
        )
        questions = resolver.generate_questions(request)
        assert len(questions) == 1
        assert "crear" in questions[0].lower()

    def test_no_questions_when_no_ambiguity(self):
        resolver = AmbiguityResolver()
        request = RequestObject(
            raw="crea modulo pagos",
            normalized="crea modulo pagos",
            intent=IntentResult(primary=IntentType.CREATE, confidence=0.95),
            entities=Entities(modulos=[Entity(nombre="pagos", tipo="module")]),
            slots=Slots(accion="create", tipo="module", nombre="pagos", completado=True),
            ambiguity=None,
        )
        questions = resolver.generate_questions(request)
        assert len(questions) == 0


class TestResolveRequestObject:
    def test_resolve_detects_ambiguity(self):
        resolver = AmbiguityResolver()
        request = RequestObject(
            raw="crea algo",
            normalized="crea algo",
            intent=IntentResult(primary=IntentType.CREATE, confidence=0.8),
            entities=Entities(),
            slots=Slots(
                accion="create",
                completado=False,
                faltantes=["tipo", "nombre"],
            ),
        )
        resolved = resolver.resolve(request)
        assert resolved.ambiguity is not None
        assert resolved.ambiguity.detected
