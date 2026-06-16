from agentic_pipeline.nlp.ambiguity_detector import AmbiguityDetector
from agentic_pipeline.nlp.intent_classifier import IntentClassifier
from agentic_pipeline.nlp.ner_extractor import NERExtractor
from agentic_pipeline.nlp.slot_filler import SlotFiller


class TestAmbiguityDetector:
    def test_no_ambiguity(self):
        clf = IntentClassifier()
        ner = NERExtractor()
        filler = SlotFiller()
        detector = AmbiguityDetector()
        text = "crea un modulo de pagos"
        intent = clf.classify(text)
        entities = ner.extract(text)
        slots = filler.fill(intent, entities)
        result = detector.detect(text, intent, entities, slots)
        assert not result.detected

    def test_no_false_positive_on_modulo(self):
        """'modulo' ends with 'lo' but is NOT a pronoun."""
        clf = IntentClassifier()
        ner = NERExtractor()
        filler = SlotFiller()
        detector = AmbiguityDetector()
        text = "crea modulo"
        intent = clf.classify(text)
        entities = ner.extract(text)
        slots = filler.fill(intent, entities)
        result = detector.detect(text, intent, entities, slots)
        assert not result.detected

    def test_low_confidence_detected(self):
        detector = AmbiguityDetector()
        clf = IntentClassifier()
        intent = clf.classify("xyz")
        from agentic_pipeline.nlp.enriched_input import Entities, Slots

        result = detector.detect("xyz", intent, Entities(), Slots())
        assert result.detected

    def test_missing_slots_detected(self):
        detector = AmbiguityDetector()
        clf = IntentClassifier()
        ner = NERExtractor()
        filler = SlotFiller()
        text = "crea algo"
        intent = clf.classify(text)
        entities = ner.extract(text)
        slots = filler.fill(intent, entities)
        result = detector.detect(text, intent, entities, slots)
        assert result.detected
        tipos = [e["tipo"] for e in result.elementos]
        assert "slot_faltante" in tipos

    def test_pronominal_reference_detected(self):
        detector = AmbiguityDetector()
        clf = IntentClassifier()
        from agentic_pipeline.nlp.enriched_input import Entities, Slots

        intent = clf.classify("crea lo que te pedi")
        result = detector.detect("crea lo que te pedi", intent, Entities(), Slots())
        assert result.detected
