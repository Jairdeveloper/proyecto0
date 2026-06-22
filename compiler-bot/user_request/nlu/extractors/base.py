"""Abstract base class for entity extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod

from user_request.contracts.request import Entities


class EntityExtractor(ABC):
    """Interfaz abstracta para extractores de entidades.

    Cada implementacion concreta define su propio ``min_confidence``
    y la logica de extraccion via ``extract()``.
    """

    min_confidence: float = 0.0

    @abstractmethod
    def extract(self, text: str) -> Entities:
        """Extrae entidades del texto.

        Args:
            text: Texto normalizado del usuario.

        Returns:
            Entities con modulos, techs y requisitos extraidos.
        """
