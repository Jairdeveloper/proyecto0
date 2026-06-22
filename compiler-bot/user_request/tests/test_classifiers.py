"""Tests for intent classifiers chain."""

from user_request.contracts.enums import IntentType
from user_request.nlu.classifiers import ClassifierManager
from user_request.nlu.classifiers.base import IntentClassifier
from user_request.nlu.classifiers.rule import RuleIntentClassifier


class TestRuleIntentClassifier:
    def test_scaffold_creates_create(self):
        clf = RuleIntentClassifier()
        r = clf.classify("crea un modulo de pagos")
        assert r.primary == IntentType.CREATE
        assert r.confidence >= 0.5
        assert r.classifier == "rule"

    def test_query_resolves_to_read(self):
        clf = RuleIntentClassifier()
        r = clf.classify("como se configura nestjs")
        assert r.primary == IntentType.READ

    def test_delete_resolves_to_delete(self):
        clf = RuleIntentClassifier()
        r = clf.classify("borra modulo payments")
        assert r.primary == IntentType.DELETE

    def test_modify_resolves_to_update(self):
        clf = RuleIntentClassifier()
        r = clf.classify("actualiza modulo de usuarios")
        assert r.primary == IntentType.UPDATE

    def test_explore_resolves_to_read(self):
        clf = RuleIntentClassifier()
        r = clf.classify("que modulos tengo")
        assert r.primary == IntentType.READ

    def test_configure_resolves_to_configure(self):
        clf = RuleIntentClassifier()
        r = clf.classify("configura nestjs por defecto")
        assert r.primary == IntentType.CONFIGURE

    def test_empty_input_returns_unknown_as_create(self):
        """Vacio no matchea nada → scores vacio → falls back a CREATE"""
        clf = RuleIntentClassifier()
        r = clf.classify("")
        assert r.primary == IntentType.CREATE
        assert r.confidence <= 1.0

    def test_domain_detection_backend(self):
        clf = RuleIntentClassifier()
        r = clf.classify("crea una api rest")
        assert r.domain == "backend"

    def test_domain_detection_frontend(self):
        clf = RuleIntentClassifier()
        r = clf.classify("pagina web con react")
        assert r.domain == "frontend"

    def test_domain_detection_infra(self):
        clf = RuleIntentClassifier()
        r = clf.classify("docker compose para postgres")
        assert r.domain == "infra"


class TestClassifierManager:
    def test_chain_returns_result(self):
        manager = ClassifierManager()
        r = manager.classify("crea un modulo de pagos")
        assert r.primary == IntentType.CREATE
        assert r.confidence > 0

    def test_chain_handles_unknown(self):
        manager = ClassifierManager()
        r = manager.classify("")
        assert r.primary is not None

    def test_chain_default_order(self):
        """Semantic primero, rule segundo."""
        manager = ClassifierManager()
        assert len(manager.chain) >= 2


class TestClassifierABC:
    def test_abc_cannot_be_instantiated(self):
        import pytest

        with pytest.raises(TypeError):
            IntentClassifier()  # type: ignore[abstract]
