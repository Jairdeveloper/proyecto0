"""Entity extractor using spaCy NLP pipeline."""

from __future__ import annotations

import logging

from user_request.contracts.request import Entities, Entity
from user_request.nlu.extractors.base import EntityExtractor

logger = logging.getLogger(__name__)


class SpacyEntityExtractor(EntityExtractor):
    """Extractor de entidades basado en spaCy.

    Carga el modelo lazy — no afecta tiempo de importacion.
    Si el modelo no esta instalado, ``extract()`` devuelve ``Entities()`` vacio.

    Min confidence: 0.8
    """

    min_confidence: float = 0.8
    MODEL_NAME: str = "es_core_news_sm"

    _nlp = None

    @classmethod
    def _get_nlp(cls):
        if cls._nlp is None:
            try:
                import spacy

                cls._nlp = spacy.load(cls.MODEL_NAME)
            except Exception as exc:
                logger.warning("spaCy model '%s' not available: %s", cls.MODEL_NAME, exc)
                return None
        return cls._nlp

    @classmethod
    def is_available(cls) -> bool:
        """Verifica si el modelo spaCy esta instalado."""
        return cls._get_nlp() is not None

    def extract(self, text: str) -> Entities:
        """Extrae entidades usando el pipeline NER de spaCy.

        Filtra entidades de tipo ORG, PERSON, PRODUCT, LOC como
        posibles modulos o tecnologias.
        """
        nlp = self._get_nlp()
        if nlp is None:
            return Entities()

        doc = nlp(text)
        techs: list[Entity] = []
        modulos: list[Entity] = []

        for ent in doc.ents:
            name = ent.text.lower().strip()
            if ent.label_ in {"ORG", "PRODUCT", "MISC"}:
                techs.append(Entity(nombre=name, tipo="tech", rol=ent.label_))
            elif ent.label_ in {"WORK_OF_ART", "EVENT"}:
                modulos.append(Entity(nombre=name, tipo="module"))

        return Entities(modulos=modulos, techs=techs)
