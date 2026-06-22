"""Entity extractor chain.

El ``EntityExtractorManager`` sigue el mismo patron Chain of
Responsibility que ``ClassifierManager``.
"""

from __future__ import annotations

from user_request.contracts.request import Entities
from user_request.nlu.extractors.base import EntityExtractor

_DEFAULT_EXTRACTORS: list[EntityExtractor] | None = None


def _get_default_extractors() -> list[EntityExtractor]:
    global _DEFAULT_EXTRACTORS
    if _DEFAULT_EXTRACTORS is None:
        from user_request.nlu.extractors.rule import RuleEntityExtractor
        from user_request.nlu.extractors.spacy import SpacyEntityExtractor

        _DEFAULT_EXTRACTORS = [
            SpacyEntityExtractor(),
            RuleEntityExtractor(),
        ]
    return _DEFAULT_EXTRACTORS


class EntityExtractorManager:
    """Cadena de extractores con fallback."""

    def __init__(self, extractors: list[EntityExtractor] | None = None) -> None:
        self._chain = extractors or _get_default_extractors()

    def extract(self, text: str) -> Entities:
        """Extrae entidades usando la cadena completa."""
        results: list[Entities] = []
        used_labels: set[str] = set()

        for extractor in self._chain:
            entities = extractor.extract(text)
            # Deducir confianza del extractor basado en cantidad de entidades
            confidence = self._estimate_confidence(entities)
            if confidence >= extractor.min_confidence:
                # Merge: evitar duplicados por nombre
                deduped = self._dedup(entities, used_labels)
                results.append(deduped)
                used_labels.update(
                    e.nombre for e in deduped.modulos + deduped.techs + deduped.requisitos
                )

        return self._merge(results)

    def _estimate_confidence(self, entities: Entities) -> float:
        total = len(entities.modulos) + len(entities.techs) + len(entities.requisitos)
        if total >= 3:
            return 0.9
        if total >= 1:
            return 0.7
        return 0.0

    def _dedup(self, entities: Entities, used_labels: set[str]) -> Entities:
        return Entities(
            modulos=[e for e in entities.modulos if e.nombre not in used_labels],
            techs=[e for e in entities.techs if e.nombre not in used_labels],
            requisitos=[e for e in entities.requisitos if e.nombre not in used_labels],
        )

    def _merge(self, results: list[Entities]) -> Entities:
        modulos: list = []
        techs: list = []
        requisitos: list = []
        seen_modules: set[str] = set()
        seen_techs: set[str] = set()
        seen_reqs: set[str] = set()

        for r in results:
            for e in r.modulos:
                if e.nombre not in seen_modules:
                    modulos.append(e)
                    seen_modules.add(e.nombre)
            for e in r.techs:
                if e.nombre not in seen_techs:
                    techs.append(e)
                    seen_techs.add(e.nombre)
            for e in r.requisitos:
                if e.nombre not in seen_reqs:
                    requisitos.append(e)
                    seen_reqs.add(e.nombre)

        return Entities(modulos=modulos, techs=techs, requisitos=requisitos)

    @property
    def chain(self) -> list[EntityExtractor]:
        """Acceso a la cadena completa."""
        return list(self._chain)
