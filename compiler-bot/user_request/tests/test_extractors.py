"""Tests for entity extractors."""

from user_request.nlu.extractors import EntityExtractorManager
from user_request.nlu.extractors.base import EntityExtractor
from user_request.nlu.extractors.rule import RuleEntityExtractor


class TestRuleEntityExtractor:
    def test_extract_module(self):
        ex = RuleEntityExtractor()
        entities = ex.extract("crea un modulo de pagos")
        assert len(entities.modulos) == 1
        assert entities.modulos[0].nombre == "pagos"
        assert entities.modulos[0].tipo == "module"

    def test_extract_tech(self):
        ex = RuleEntityExtractor()
        entities = ex.extract("crea modulo con NestJS")
        assert len(entities.techs) == 1
        assert entities.techs[0].nombre == "nestjs"

    def test_extract_multiple_techs(self):
        ex = RuleEntityExtractor()
        entities = ex.extract("modulo con NestJS y Prisma")
        assert len(entities.techs) >= 2

    def test_extract_requirement(self):
        ex = RuleEntityExtractor()
        entities = ex.extract("modulo con autenticacion jwt")
        assert len(entities.requisitos) >= 1

    def test_extract_negated_requirement(self):
        ex = RuleEntityExtractor()
        entities = ex.extract("modulo sin autenticacion")
        negados = [r for r in entities.requisitos if r.negado]
        assert len(negados) >= 1

    def test_empty_input(self):
        ex = RuleEntityExtractor()
        entities = ex.extract("")
        assert len(entities.modulos) == 0
        assert len(entities.techs) == 0

    def test_no_false_positive_on_tech_whitelist(self):
        ex = RuleEntityExtractor()
        entities = ex.extract("hola mundo")
        assert len(entities.techs) == 0


class TestEntityExtractorManager:
    def test_empty_input(self):
        mgr = EntityExtractorManager()
        entities = mgr.extract("")
        assert len(entities.modulos) == 0

    def test_extract_with_module(self):
        mgr = EntityExtractorManager()
        entities = mgr.extract("crea un modulo de pagos")
        assert len(entities.modulos) >= 1

    def test_dedup_on_multiple_extractors(self):
        """El manager no debe duplicar entradas entre extractores."""
        mgr = EntityExtractorManager()
        entities = mgr.extract("crea un modulo de pagos con NestJS")
        nombres = [e.nombre for e in entities.techs]
        assert len(nombres) == len(set(nombres))

    def test_chain_default_order(self):
        mgr = EntityExtractorManager()
        assert len(mgr.chain) >= 2


class TestEntityExtractorABC:
    def test_abc_cannot_be_instantiated(self):
        import pytest

        with pytest.raises(TypeError):
            EntityExtractor()  # type: ignore[abstract]
