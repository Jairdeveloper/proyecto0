"""NLU Pipeline — orquestador del pipeline de lenguaje natural."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from user_request.contracts.enums import RequestChannel
from user_request.contracts.request import (
    RequestContext,
    RequestObject,
)
from user_request.nlu.ambiguity import AmbiguityResolver
from user_request.nlu.classifiers import ClassifierManager
from user_request.nlu.enricher import Enricher
from user_request.nlu.extractors import EntityExtractorManager
from user_request.nlu.normalizer import Normalizer
from user_request.nlu.slot_filler import SlotFiller

logger = logging.getLogger(__name__)


class NLUPipeline:
    """Orquestador del pipeline NLU.

    Pipeline completo:
    normalizer → classifier_chain → extractor_chain →
    slot_filler → ambiguity_resolver → enricher

    Uso:
        >>> pipeline = NLUPipeline()
        >>> request = pipeline.process("crea un modulo de pagos")
        >>> request.intent.primary
        <IntentType.CREATE: 'create'>
    """

    def __init__(
        self,
        classifiers: ClassifierManager | None = None,
        extractors: EntityExtractorManager | None = None,
        slot_filler: SlotFiller | None = None,
        ambiguity: AmbiguityResolver | None = None,
        enricher: Enricher | None = None,
        normalizer: Normalizer | None = None,
    ) -> None:
        self.normalizer = normalizer or Normalizer()
        self.classifier = classifiers or ClassifierManager()
        self.extractor = extractors or EntityExtractorManager()
        self.slot_filler = slot_filler or SlotFiller()
        self.ambiguity = ambiguity or AmbiguityResolver()
        self.enricher = enricher or Enricher()

    def process(
        self,
        raw: str,
        context: RequestContext | None = None,
        channel: RequestChannel = RequestChannel.CLI,
        metadata: dict[str, Any] | None = None,
    ) -> RequestObject:
        """Ejecuta el pipeline NLU completo sobre el texto de entrada.

        Args:
            raw: Texto original del usuario.
            context: Contexto de sesion (opcional).
            channel: Canal de la solicitud.
            metadata: Metadatos adicionales.

        Returns:
            RequestObject con el resultado completo del pipeline.
        """
        _meta = {
            "timestamp": datetime.now().isoformat(),
            "pipeline": "nlu",
            "version": "2.9.0",
            **(metadata or {}),
        }

        # 1. Normalizar
        normalized = self.normalizer.normalize(raw)
        logger.debug("Normalized: %s -> %s", raw[:50], normalized[:50])

        # 2. Clasificar intencion
        intent = self.classifier.classify(normalized)
        logger.debug("Intent: %s (%.2f)", intent.primary.value, intent.confidence)

        # 3. Extraer entidades
        entities = self.extractor.extract(normalized)
        logger.debug(
            "Entities: %d modules, %d techs, %d reqs",
            len(entities.modulos),
            len(entities.techs),
            len(entities.requisitos),
        )

        # 4. Rellenar slots
        slots = self.slot_filler.fill(intent, entities)

        # 5. Detectar ambiguedad
        ambiguity = self.ambiguity.detect(raw, intent, entities, slots)

        # 6. Construir RequestObject
        request = RequestObject(
            raw=raw,
            normalized=normalized,
            intent=intent,
            entities=entities,
            slots=slots,
            ambiguity=ambiguity,
            channel=channel,
            metadata=_meta,
        )

        # 7. Enriquecer con contexto (si hay)
        if context is not None:
            request = self.enricher.enrich(
                request,
                session_id=context.session_id,
                defaults=context.defaults,
            )

        return request
