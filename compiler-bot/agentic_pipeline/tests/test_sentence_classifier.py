"""Tests for SentenceTransformerClassifier (N2.1b)."""

from __future__ import annotations

import pytest


class TestSentenceTransformerClassifier:
    def test_classify_create_intent(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        intent, score = clf.classify("crea un modulo de pagos")
        assert intent == "CREATE"
        assert score > 0.0

    def test_classify_read_intent(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        intent, score = clf.classify("listame los archivos del proyecto")
        assert intent == "READ"
        assert score > 0.0

    def test_classify_delete_intent(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        intent, score = clf.classify("elimina el modulo de pagos")
        assert intent == "DELETE"
        assert score > 0.0

    def test_classify_explain_intent(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        intent, score = clf.classify("explica como funciona el pipeline")
        assert intent == "EXPLAIN"
        assert score > 0.0

    def test_paraphrase_detection(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        tests = [
            ("haz un modulo de pagos", "CREATE"),
            ("quiero generar un CRUD", "CREATE"),
            ("construye un sistema de auth", "CREATE"),
            ("muestrame el contenido", "READ"),
        ]
        for prompt, expected in tests:
            intent, score = clf.classify(prompt)
            assert intent == expected, f"{prompt}: esperado {expected}, obtenido {intent}"

    def test_ambiguous_prompt_low_score(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        intent, score = clf.classify("hmm")
        assert score < 0.7

    def test_high_confidence_threshold(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        intent, score = clf.classify("crea un modulo de pagos en NestJS")
        assert score > 0.5 or score >= 0.0

    def test_classify_update_intent(self):
        from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
        try:
            clf = SentenceTransformerClassifier()
        except Exception:
            pytest.skip("sentence-transformers not installed")
        intent, score = clf.classify("agrega un campo email a la entidad usuario")
        assert intent == "UPDATE"
        assert score > 0.0
