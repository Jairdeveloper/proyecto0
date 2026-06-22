"""Rule-based intent classifier using regex patterns."""

from __future__ import annotations

import re

from user_request.contracts.enums import IntentType
from user_request.contracts.request import IntentResult
from user_request.nlu.classifiers.base import IntentClassifier


class RuleIntentClassifier(IntentClassifier):
    """Clasificador de intencion basado en regex (rule-based).

    Usa la misma taxonomia de patrones que el legacy ``IntentClassifier``
    pero mapea los resultados a la taxonomia unificada via alias.

    Min confidence: 0.6
    """

    min_confidence: float = 0.6

    TAXONOMY: dict[str, list[str]] = {
        "SCAFFOLD": [
            r"crea",
            r"genera",
            r"nuev[oa]",
            r"necesit[ao]",
            r"quier[eo]",
            r"haz",
            r"construye",
            r"implementa",
            r"anade",
            r"disena",
        ],
        "QUERY": [
            r"c[oó]mo",
            r"qu[eé] es",
            r"explica",
            r"configura",
            r"ayuda",
            r"help",
            r"qu[eé] son",
            r"muestra",
            r"listame",
        ],
        "MODIFY": [
            r"actualiza",
            r"cambia",
            r"modifica",
            r"agrega",
            r"edita",
            r"aniade",
        ],
        "DELETE": [
            r"borra",
            r"elimina",
            r"remove",
            r"delete",
            r"saca",
            r"quita",
        ],
        "EXPLORE": [
            r"qu[eé] m[oó]dulos",
            r"listame",
            r"qu[eé] tengo",
            r"estado",
            r"status",
        ],
        "CONFIGURE": [
            r"configura",
            r"usa",
            r"por defecto",
            r"cambia idioma",
            r"set",
        ],
        "CLARIFY": [
            r"^(s[ií]|no|ok|vale)$",
            r"el de",
            r"con ",
        ],
    }

    DOMAIN_PATTERNS: dict[str, list[str]] = {
        "backend": ["api", "servicio", "backend", "database", "db", "crud"],
        "frontend": ["frontend", "ui", "pagina", "web", "interfaz", "componente"],
        "infra": ["docker", "deploy", "ci/cd", "devops", "infra"],
    }

    def classify(self, text: str) -> IntentResult:
        """Clasifica usando regex y mapea a taxonomia unificada."""
        text_lower = text.lower()
        scores: dict[str, float] = {}
        for intent, patterns in self.TAXONOMY.items():
            score = self._score(text_lower, patterns)
            if score > 0:
                scores[intent] = score

        if not scores:
            scores["UNKNOWN"] = 1.0

        primary_legacy = max(scores, key=scores.get)
        max_score = max(scores.values())
        domain = self._detect_domain(text_lower)

        primary = IntentType.from_alias(primary_legacy)
        secondary = self._resolve_secondary(scores, primary_legacy, max_score)

        return IntentResult(
            primary=primary,
            secondary=secondary,
            confidence=round(max_score, 4),
            classifier="rule",
            scores=scores,
            domain=domain,
        )

    def _score(self, text: str, patterns: list[str]) -> float:
        matches = 0
        for p in patterns:
            if re.search(p, text):
                matches += 1
        return min(matches / 2.0, 1.0) if matches > 0 else 0.0

    def _detect_domain(self, text: str) -> str:
        for domain, patterns in self.DOMAIN_PATTERNS.items():
            for p in patterns:
                if p in text:
                    return domain
        return "backend"

    def _resolve_secondary(
        self,
        scores: dict[str, float],
        primary_legacy: str,
        max_score: float,
    ) -> IntentType | None:
        if len(scores) < 2:
            return None
        sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
        if len(sorted_scores) >= 2:
            second_legacy = sorted_scores[1][0]
            if (max_score - sorted_scores[1][1]) < 0.1:
                return IntentType.from_alias(second_legacy)
        return None
