"""LLM orchestration and domain classification tools."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..config import config

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

SAAS_FEATURES: dict[str, list[str]] = {
    "auth": ["User model", "JWT", "login/signup", "session management"],
    "qr": ["QR code generation", "QR library integration"],
    "pagos": ["Payment model", "transaction log", "payment gateway"],
    "analytics": ["Click tracking", "visit stats", "event logging"],
    "dashboard": ["Admin panel", "charts", "recent activity feed"],
    "email": ["Email service", "notification templates", "mail queue"],
    "storage": ["File upload", "CDN", "asset management"],
}

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "web": ["pagina", "web", "frontend", "interfaz", "ui", "landing"],
    "mobile": ["app", "movil", "android", "ios", "mobile", "celular"],
    "api": ["api", "rest", "endpoint", "servicio", "backend"],
    "cli": ["cli", "terminal", "comando", "consola", "linea de comandos"],
    "data": ["base de datos", "data", "analisis", "reporte", "dashboard"],
    "infra": ["infra", "deploy", "docker", "nube", "cloud", "servidor"],
}

CONSTRAINT_KEYWORDS: dict[str, list[str]] = {
    "performance": ["rapido", "veloz", "responsive", "carga", "segundo"],
    "security": ["seguro", "auth", "permisos", "roles", "encriptado"],
    "scalability": ["escalable", "concurrencia", "muchos", "trafico"],
    "usability": ["usable", "intuitivo", "accesible", "facil"],
    "maintainability": ["mantenible", "modular", "extensible", "limpio"],
}

DOMAIN_TEMPLATES: dict[str, dict[str, Any]] = {
    "web": {
        "stack": ["frontend", "backend", "database"],
        "framework_hints": ["React", "Next.js", "Tailwind"],
    },
    "mobile": {
        "stack": ["mobile_app", "api_backend"],
        "framework_hints": ["React Native", "Expo"],
    },
    "api": {
        "stack": ["api_service", "database"],
        "framework_hints": ["NestJS", "FastAPI"],
    },
}

# ============================================================================
# DOMAIN CLASSIFIER
# ============================================================================


class DomainClassifier:
    """Classifies domain using keyword matching + LLM fallback."""

    def __init__(self, llm_orchestrator: LLMOrchestrator | None = None):
        self._llm = llm_orchestrator

    def classify(self, text: str) -> str:
        text_lower = text.lower()
        scores: dict[str, int] = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[domain] = score
        if scores:
            return max(scores, key=scores.get)
        if self._llm:
            return self._llm.classify_domain(text)
        return "web"


# ============================================================================
# ENTITY EXTRACTOR
# ============================================================================


class EntityExtractor:
    """Extracts entities using regex patterns + LLM fallback."""

    ENTITY_PATTERNS: list[tuple[str, str]] = [
        (r"(?:tabla|modelo|entidad)\s+(\w+)", "model"),
        (r"(?:formulario|form)\s+(?:de\s+)?(\w+)", "form"),
        (r"(?:pagina|page|pantalla|screen)\s+(?:de\s+)?(\w+)", "page"),
        (r"(?:usuario|user|cliente|customer)", "user"),
        (r"(?:enlace|link|url|link)", "link"),
        (r"(?:click|clic)", "click"),
    ]

    def __init__(self, llm_orchestrator: LLMOrchestrator | None = None):
        self._llm = llm_orchestrator

    def extract(self, text: str) -> list[dict]:
        text_lower = text.lower()
        entities: list[dict] = []
        seen: set[str] = set()
        for pattern, entity_type in self.ENTITY_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                name = match.group(1) if match.lastindex else entity_type
                name = name.capitalize()
                if name not in seen:
                    seen.add(name)
                    entities.append(
                        {"name": name, "type": entity_type, "attributes": []}
                    )
        if not entities and self._llm:
            entities = self._llm.extract_entities(text)
        return entities


# ============================================================================
# FEATURE IDENTIFIER
# ============================================================================


class FeatureIdentifier:
    """Identifies features using a whitelist of SaaS features."""

    def identify(self, text: str) -> list[str]:
        text_lower = text.lower()
        features: list[str] = []
        seen: set[str] = set()
        for keyword, feature_list in SAAS_FEATURES.items():
            if keyword in text_lower and keyword not in seen:
                seen.add(keyword)
                features.extend(feature_list)
        return features


# ============================================================================
# CONSTRAINT DETECTOR
# ============================================================================


class ConstraintDetector:
    """Detects constraints using keyword matching."""

    def detect(self, text: str) -> list[str]:
        text_lower = text.lower()
        constraints: list[str] = []
        for category, keywords in CONSTRAINT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                constraints.append(category)
        return constraints


# ============================================================================
# LLM ORCHESTRATOR
# ============================================================================


class LLMOrchestrator:
    """Orchestrates LLM calls for domain classification and entity extraction."""

    def __init__(self):
        self._llm: ChatOpenAI | None = None

    def _get_llm(self) -> ChatOpenAI:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=config.llm_model,
                temperature=config.llm_temperature,
            )
        return self._llm

    def classify_domain(self, text: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Clasifica el dominio del siguiente requerimiento. "
                    "Responde solo con una palabra: web, mobile, api, cli, data, infra.",
                ),
                ("human", "{text}"),
            ]
        )
        chain = prompt | self._get_llm()
        return chain.invoke({"text": text}).content.strip().lower()

    def extract_entities(self, text: str) -> list[dict]:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Extrae las entidades del requerimiento. "
                    "Responde como JSON array: "
                    '[{"name": str, "type": str, "attributes": [str]}]',
                ),
                ("human", "{text}"),
            ]
        )
        chain = prompt | self._get_llm()
        result = chain.invoke({"text": text}).content.strip()
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON: %s", result)
            return []


# ============================================================================
# STORY GENERATOR
# ============================================================================


class StoryGenerator:
    """Generates user stories from features and entities."""

    def generate(self, features: list[str], entities: list[dict]) -> list[str]:
        stories: list[str] = []
        for feature in features:
            stories.append(f"Como usuario quiero {feature.lower()}")
        return stories
