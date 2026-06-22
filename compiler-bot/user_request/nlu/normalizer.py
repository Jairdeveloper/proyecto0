"""Text normalizer for NLU pipeline input."""

from __future__ import annotations

import re
import unicodedata


class Normalizer:
    """Normalizacion de texto de entrada.

    Operaciones:
    - Unicode NFKC normalization
    - Lowercase
    - Colapso de espacios multiples
    - Eliminacion de puntuacion redundante
    """

    _PUNCTUATION_RE = re.compile(r"[^\w\sáéíóúñü]")
    _WHITESPACE_RE = re.compile(r"\s+")

    def normalize(self, raw: str) -> str:
        """Normaliza el texto de entrada.

        Args:
            raw: Texto original del usuario.

        Returns:
            Texto normalizado (NFKC, lowercase, sin puntuacion redundante).
        """
        text = unicodedata.normalize("NFKC", raw.strip())
        text = text.lower()
        text = self._PUNCTUATION_RE.sub("", text)
        text = self._WHITESPACE_RE.sub(" ", text)
        return text
