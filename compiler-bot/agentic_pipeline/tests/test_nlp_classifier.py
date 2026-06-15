from agentic_pipeline.nlp.intent_classifier import IntentClassifier


class TestIntentClassifier:
    def test_scaffold_detected(self):
        clf = IntentClassifier()
        r = clf.classify("crea un modulo de pagos")
        assert r.primary == "SCAFFOLD"
        assert r.confidence >= 0.5

    def test_query_detected(self):
        clf = IntentClassifier()
        r = clf.classify("como se configura nestjs")
        assert r.primary == "QUERY"

    def test_delete_detected(self):
        clf = IntentClassifier()
        r = clf.classify("borra modulo payments")
        assert r.primary == "DELETE"

    def test_empty_input_returns_unknown(self):
        clf = IntentClassifier()
        r = clf.classify("")
        assert r.primary == "UNKNOWN"

    def test_domain_detection(self):
        clf = IntentClassifier()
        r = clf.classify("crea una api rest")
        assert r.domain == "backend"

    def test_modify_detected(self):
        clf = IntentClassifier()
        r = clf.classify("actualiza modulo de usuarios")
        assert r.primary == "MODIFY"

    def test_explore_detected(self):
        clf = IntentClassifier()
        r = clf.classify("que modulos tengo")
        assert r.primary == "EXPLORE"

    def test_configure_detected(self):
        clf = IntentClassifier()
        r = clf.classify("configura nestjs por defecto")
        assert r.primary == "CONFIGURE"

    def test_clarify_detected(self):
        clf = IntentClassifier()
        r = clf.classify("si")
        assert r.primary == "CLARIFY"

    def test_frontend_domain(self):
        clf = IntentClassifier()
        r = clf.classify("crea una pagina web")
        assert r.domain == "frontend"

    def test_infra_domain(self):
        clf = IntentClassifier()
        r = clf.classify("configura docker para el proyecto")
        assert r.domain == "infra"
