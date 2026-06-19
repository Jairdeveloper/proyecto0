"""Tests for SpacyProcessor (N2.1a)."""

from __future__ import annotations

import pytest


class TestSpacyProcessor:
    def test_process_returns_tokens(self):
        from agentic_pipeline.nodes.preprocessor import SpacyProcessor

        processor = SpacyProcessor()
        result = processor.process("crea un modulo de pagos en NestJS")
        if result is None:
            pytest.skip("spaCy model not installed")
        assert "tokens" in result
        assert "entities" in result
        assert "sentences" in result
        assert len(result["tokens"]) > 0

    def test_process_detects_verbs(self):
        from agentic_pipeline.nodes.preprocessor import SpacyProcessor

        processor = SpacyProcessor()
        result = processor.process("crea un modulo de pagos")
        if result is None:
            pytest.skip("spaCy model not installed")
        tokens = result["tokens"]
        verbs = [t for t in tokens if t["pos"] == "VERB"]
        assert len(verbs) > 0

    def test_process_returns_nouns(self):
        from agentic_pipeline.nodes.preprocessor import SpacyProcessor

        processor = SpacyProcessor()
        result = processor.process("crea un modulo de pagos")
        if result is None:
            pytest.skip("spaCy model not installed")
        tokens = result["tokens"]
        nouns = [t for t in tokens if t["pos"] in ("NOUN", "PROPN")]
        assert len(nouns) > 0

    def test_lazy_loading_does_not_crash(self):
        from agentic_pipeline.nodes.preprocessor import SpacyProcessor

        p = SpacyProcessor()
        result = p.process("test")
        if result is None:
            pytest.skip("spaCy model not installed")
        assert result is not None

    def test_entities_field_present(self):
        from agentic_pipeline.nodes.preprocessor import SpacyProcessor

        processor = SpacyProcessor()
        result = processor.process("crea un modulo de pagos")
        if result is None:
            pytest.skip("spaCy model not installed")
        assert isinstance(result["entities"], list)

    def test_sentences_field_present(self):
        from agentic_pipeline.nodes.preprocessor import SpacyProcessor

        processor = SpacyProcessor()
        result = processor.process("crea un modulo de pagos en NestJS")
        if result is None:
            pytest.skip("spaCy model not installed")
        assert len(result["sentences"]) >= 1

    def test_lemmas_are_present(self):
        from agentic_pipeline.nodes.preprocessor import SpacyProcessor

        processor = SpacyProcessor()
        result = processor.process("creando modulos de pago")
        if result is None:
            pytest.skip("spaCy model not installed")
        tokens = result["tokens"]
        lemmas = [t["lemma"] for t in tokens]
        assert any(lemma == "crear" or lemma == "creando" for lemma in lemmas)
        assert any(lemma == "módulo" or lemma == "modulo" or lemma == "modular" for lemma in lemmas)
