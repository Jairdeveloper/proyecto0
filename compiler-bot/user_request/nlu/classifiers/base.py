"""Abstract base class for intent classifiers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from user_request.contracts.request import IntentResult


class IntentClassifier(ABC):
    """Interfaz abstracta para clasificadores de intencion.

    Cada implementacion concreta define su propio ``min_confidence``
    y la logica de clasificacion via ``classify()``.

    Los clasificadores se encadenan en un ``ClassifierManager`` usando
    Chain of Responsibility: si un clasificador no alcanza su umbral
    de confianza, se delega al siguiente.
    """

    min_confidence: float = 0.0

    @abstractmethod
    def classify(self, text: str) -> IntentResult:
        """Clasifica la intencion del texto.

        Args:
            text: Texto normalizado del usuario.

        Returns:
            IntentResult con la intencion detectada y su confianza.
        """
