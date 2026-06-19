from agentic_pipeline.nlp.intent_classifier import IntentClassifier
from agentic_pipeline.nlp.ner_extractor import NERExtractor
from agentic_pipeline.nlp.slot_filler import SlotFiller


class TestSlotFiller:
    def test_scaffold_slots_complete(self):
        clf = IntentClassifier()
        ner = NERExtractor()
        filler = SlotFiller()
        intent = clf.classify("crea un modulo de pagos")
        entities = ner.extract("crea un modulo de pagos")
        slots = filler.fill(intent, entities)
        assert slots.accion == "create"
        assert slots.tipo == "module"
        assert slots.nombre == "pagos"
        assert slots.completado

    def test_scaffold_missing_name(self):
        clf = IntentClassifier()
        ner = NERExtractor()
        filler = SlotFiller()
        intent = clf.classify("crea algo")
        entities = ner.extract("crea algo")
        slots = filler.fill(intent, entities)
        assert not slots.completado
        assert "nombre" in slots.faltantes

    def test_delete_slots(self):
        clf = IntentClassifier()
        ner = NERExtractor()
        filler = SlotFiller()
        intent = clf.classify("borra modulo payments")
        entities = ner.extract("borra modulo payments")
        slots = filler.fill(intent, entities)
        assert slots.accion == "delete"
        assert slots.nombre == "payments"
