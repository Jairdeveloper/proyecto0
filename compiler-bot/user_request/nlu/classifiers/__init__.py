"""Classifier chain with Chain of Responsibility pattern.

El ``ClassifierManager`` implementa el patron Chain of Responsibility:
intenta clasificadores en orden decreciente de capacidad (semantic → rule),
delegando al siguiente si la confianza no alcanza el umbral minimo.
"""

from __future__ import annotations

from user_request.contracts.request import IntentResult
from user_request.nlu.classifiers.base import IntentClassifier

# Orden por defecto: mayor capacidad primero
_DEFAULT_CLASSIFIERS: list[IntentClassifier] | None = None


def _get_default_classifiers() -> list[IntentClassifier]:
    global _DEFAULT_CLASSIFIERS
    if _DEFAULT_CLASSIFIERS is None:
        from user_request.nlu.classifiers.semantic import SemanticIntentClassifier
        from user_request.nlu.classifiers.rule import RuleIntentClassifier

        _DEFAULT_CLASSIFIERS = [
            SemanticIntentClassifier(),
            RuleIntentClassifier(),
        ]
    return _DEFAULT_CLASSIFIERS


class ClassifierManager:
    """Cadena de clasificadores con fallback.

    Los clasificadores se intentan en orden. Si el primero no alcanza
    su ``min_confidence``, se delega al siguiente. El ultimo clasificador
    es siempre el fallback final.
    """

    def __init__(self, classifiers: list[IntentClassifier] | None = None) -> None:
        self._chain = classifiers or _get_default_classifiers()

    def classify(self, text: str) -> IntentResult:
        """Clasifica usando la cadena completa con fallback."""
        for classifier in self._chain:
            result = classifier.classify(text)
            if result.confidence >= classifier.min_confidence:
                return result
        # Fallback: el ultimo clasificador siempre devuelve algo
        return self._chain[-1].classify(text)

    @property
    def chain(self) -> list[IntentClassifier]:
        """Acceso a la cadena completa (para inspeccion/configuracion)."""
        return list(self._chain)
