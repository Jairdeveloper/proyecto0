import re
from .enriched_input import IntentResult


class IntentClassifier:
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
        text_lower = text.lower()
        scores: dict[str, float] = {}
        for intent, patterns in self.TAXONOMY.items():
            score = self._score(text_lower, patterns)
            if score > 0:
                scores[intent] = score

        if not scores:
            scores["UNKNOWN"] = 1.0

        max_score = max(scores.values())
        primary = max(scores, key=scores.get)
        domain = self._detect_domain(text_lower)

        return IntentResult(
            primary=primary,
            confidence=round(max_score, 4),
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
