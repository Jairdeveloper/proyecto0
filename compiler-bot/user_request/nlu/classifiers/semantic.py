"""Semantic intent classifier using SentenceTransformer embeddings."""

from __future__ import annotations

import logging

from user_request.contracts.enums import IntentType
from user_request.contracts.request import IntentResult
from user_request.nlu.classifiers.base import IntentClassifier

logger = logging.getLogger(__name__)


class SemanticIntentClassifier(IntentClassifier):
    """Clasificador de intencion por embeddings semanticos.

    Usa SentenceTransformer (paraphrase-multilingual-MiniLM-L12-v2)
    para calcular similitud coseno entre el texto de entrada y
    ejemplos de referencia por intencion.

    Min confidence: 0.7
    Carga lazy del modelo — no afecta tiempo de importacion.
    """

    min_confidence: float = 0.7
    MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"

    _model = None
    _util = None

    def __init__(self) -> None:
        self.model = self._get_model()
        self.references = self._build_references()

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            try:
                from sentence_transformers import SentenceTransformer, util

                cls._model = SentenceTransformer(cls.MODEL_NAME)
                cls._util = util
            except Exception as exc:
                logger.warning("SentenceTransformer unavailable: %s", exc)
                return None
        return cls._model

    def _build_references(self):
        if self.model is None:
            return {}

        refs = {
            "CREATE": [
                "crea un modulo de pagos",
                "quiero generar una entidad usuario",
                "haz un nuevo controlador para autenticacion",
                "necesito un crud de productos",
                "construye un sistema de login",
            ],
            "READ": [
                "muestrame el contenido del archivo",
                "que hay en este directorio",
                "listame los modulos existentes",
                "dime que archivos hay en pagos",
                "leeme el archivo de configuracion",
            ],
            "UPDATE": [
                "agrega un campo email a la entidad usuario",
                "modifica el controlador de auth",
                "anade una nueva ruta al modulo",
                "cambia el nombre del servicio",
                "actualiza el schema de prisma",
            ],
            "DELETE": [
                "elimina el modulo de pagos",
                "borra la entidad temporal",
                "quita el campo edad del schema",
                "remueve el controlador viejo",
                "limpia los archivos temporales",
            ],
            "EXPLAIN": [
                "explica como funciona el pipeline",
                "que hace este componente",
                "dime como se conectan los stages",
                "como se anade un nuevo generador",
                "describe la arquitectura del sistema",
            ],
        }
        return {
            intent: self.model.encode(examples, convert_to_tensor=True)
            for intent, examples in refs.items()
        }

    def classify(self, text: str) -> IntentResult:
        """Clasifica usando similitud coseno con ejemplos de referencia."""
        if self.model is None or not self.references:
            return IntentResult(
                primary=IntentType.CREATE,
                confidence=0.0,
                classifier="semantic",
            )

        from sentence_transformers import util as st_util

        emb = self.model.encode(text, convert_to_tensor=True)
        best_intent_str, best_score = "UNKNOWN", 0.0

        for intent_str, refs in self.references.items():
            scores = st_util.cos_sim(emb, refs)
            max_score = scores.max().item()
            if max_score > best_score:
                best_score = max_score
                best_intent_str = intent_str

        primary = IntentType.from_alias(best_intent_str)

        return IntentResult(
            primary=primary,
            confidence=round(best_score, 4),
            classifier="semantic",
        )

    @classmethod
    def is_available(cls) -> bool:
        """Verifica si el modelo de SentenceTransformer esta disponible."""
        return cls._get_model() is not None
