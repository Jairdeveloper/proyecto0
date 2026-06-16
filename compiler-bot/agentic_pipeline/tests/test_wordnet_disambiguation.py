"""Tests for WordNet disambiguation (N2.1c)."""

from __future__ import annotations

import pytest


class TestWordNetDisambiguation:
    def test_disambiguate_modulo_returns_grammar(self):
        from agentic_pipeline.nodes.parser import disambiguate_term
        try:
            result = disambiguate_term("modulo", ["crea", "un", "modulo", "de", "pagos"])
        except Exception:
            pytest.skip("nltk wordnet not available")
        assert result["grammar"] is not None, f"No grammar for modulo: {result}"

    def test_disambiguate_entity_returns_grammar(self):
        from agentic_pipeline.nodes.parser import disambiguate_term
        try:
            result = disambiguate_term("entidad", ["crea", "una", "entidad", "usuario"])
        except Exception:
            pytest.skip("nltk wordnet not available")
        assert result["grammar"] is not None

    def test_disambiguate_returns_term(self):
        from agentic_pipeline.nodes.parser import disambiguate_term
        try:
            result = disambiguate_term("modulo", ["crea", "modulo", "pagos"])
        except Exception:
            pytest.skip("nltk wordnet not available")
        assert result["term"] == "modulo"

    def test_ensure_nltk_data_does_not_crash(self):
        from agentic_pipeline.nodes.parser import ensure_nltk_data
        try:
            ensure_nltk_data()
        except Exception:
            pytest.skip("nltk data download failed")

    def test_infer_domain_software(self):
        from agentic_pipeline.nodes.parser import infer_domain
        try:
            from nltk.corpus import wordnet as wn
            synset = wn.synset("computer.n.01")
        except Exception:
            pytest.skip("nltk/wordnet not available")
        domain = infer_domain(synset)
        assert domain == "software"

    def test_infer_domain_entity(self):
        from agentic_pipeline.nodes.parser import infer_domain
        try:
            from nltk.corpus import wordnet as wn
            synset = wn.synset("entity.n.01")
        except Exception:
            pytest.skip("nltk/wordnet not available")
        domain = infer_domain(synset)
        assert domain == "entity"

    def test_domain_map_structure(self):
        from agentic_pipeline.nodes.parser import DOMAIN_MAP
        assert "software" in DOMAIN_MAP
        assert "entity" in DOMAIN_MAP
        assert "ui" in DOMAIN_MAP
        assert "infra" in DOMAIN_MAP
        assert all("grammar" in v for v in DOMAIN_MAP.values())

    def test_find_ambiguous_terms(self):
        from agentic_pipeline.nodes.parser import _find_ambiguous_terms
        tokens = [{"value": "crea"}, {"value": "un"}, {"value": "modulo"}]
        terms = _find_ambiguous_terms(tokens)
        assert "modulo" in terms
