from agentic_pipeline.nlp.ner_extractor import NERExtractor


class TestNERExtractor:
    def test_extract_module(self):
        ner = NERExtractor()
        entities = ner.extract("crea un modulo de pagos")
        assert len(entities.modulos) == 1
        assert entities.modulos[0].nombre == "pagos"
        assert entities.modulos[0].tipo == "module"

    def test_extract_tech(self):
        ner = NERExtractor()
        entities = ner.extract("crea un modulo con nestjs")
        assert len(entities.techs) == 1
        assert entities.techs[0].nombre == "nestjs"

    def test_extract_requirement(self):
        ner = NERExtractor()
        entities = ner.extract("crea un modulo con autenticacion jwt")
        assert len(entities.requisitos) >= 1

    def test_extract_no_modules_returns_empty(self):
        ner = NERExtractor()
        entities = ner.extract("hola mundo")
        assert len(entities.modulos) == 0

    def test_extract_multiple_techs(self):
        ner = NERExtractor()
        entities = ner.extract("crea modulo con nestjs y prisma")
        assert len(entities.techs) >= 2

    def test_extract_entity_pattern(self):
        ner = NERExtractor()
        entities = ner.extract("crea entidad usuario")
        assert len(entities.modulos) == 1
        assert entities.modulos[0].nombre == "usuario"
