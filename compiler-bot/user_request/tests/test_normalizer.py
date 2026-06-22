"""Tests for Normalizer."""

from user_request.nlu.normalizer import Normalizer


class TestNormalizer:
    def test_lowercase(self):
        n = Normalizer()
        assert n.normalize("CREA MODULO PAGOS") == "crea modulo pagos"

    def test_collapse_spaces(self):
        n = Normalizer()
        assert n.normalize("crea   modulo    pagos") == "crea modulo pagos"

    def test_strip_punctuation(self):
        n = Normalizer()
        assert n.normalize("¡crea modulo pagos!") == "crea modulo pagos"

    def test_unicode_nfkc(self):
        n = Normalizer()
        result = n.normalize("crea módulo pagos")
        assert "módulo" in result or "modulo" in result

    def test_empty_string(self):
        n = Normalizer()
        assert n.normalize("") == ""

    def test_whitespace_only(self):
        n = Normalizer()
        assert n.normalize("   ") == ""

    def test_mixed_case_and_punctuation(self):
        n = Normalizer()
        result = n.normalize("  HAZ UN MODULO DE PAGOS CON NESTJS!!  ")
        assert result == "haz un modulo de pagos con nestjs"
