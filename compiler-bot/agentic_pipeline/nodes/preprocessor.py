"""Preprocessor stage with Chain of Responsibility of filters."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)

# ============================================================================
# DOMAIN STRATEGIES
# ============================================================================

DOMAIN_STRATEGIES: dict[str, dict[str, Any]] = {
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

IMPLICIT_REQUIREMENTS: dict[str, list[str]] = {
    "auth": ["User model", "JWT", "login/signup", "session management"],
    "qr": ["QR code library", "QR generation service"],
    "pagos": ["Payment model", "transaction log", "payment gateway"],
    "analytics": ["Click tracking", "event logging", "visit stats"],
    "dashboard": ["Admin panel", "charts", "activity feed"],
    "email": ["Email service", "notification templates"],
    "storage": ["File upload", "asset management"],
}

# ============================================================================
# BASE FILTER
# ============================================================================


class PreprocessingFilter(ABC):
    """Abstract filter with process(text, context) -> text interface."""

    @abstractmethod
    def process(self, text: str, context: dict[str, Any] | None = None) -> str: ...


# ============================================================================
# FILTERS
# ============================================================================


class NormalizationFilter(PreprocessingFilter):
    """Trims, lowercases, collapses punctuation and whitespace."""

    def process(self, text: str, context: dict[str, Any] | None = None) -> str:
        text = text.strip().lower()
        text = re.sub(r"[^\w\sáéíóúñü,.!?;:-]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text


class SegmentationFilter(PreprocessingFilter):
    """Splits text into sentence segments."""

    def process(self, text: str, context: dict[str, Any] | None = None) -> str:
        sentences = re.split(r"[.!?]+", text)
        segments = [s.strip() for s in sentences if s.strip()]
        return " [SEG] ".join(segments)


class EmbeddingEnricher(PreprocessingFilter):
    """Enriches text with similar known patterns via FAISS vector search.

    Requires langchain-community, faiss, and OpenAI API key.
    Falls back gracefully if dependencies are unavailable.
    """

    def __init__(self) -> None:
        self._vectorstore: Any = None

    def _ensure_loaded(self) -> bool:
        if self._vectorstore is not None:
            return True
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_openai import OpenAIEmbeddings

            embeddings = OpenAIEmbeddings()
            self._vectorstore = FAISS.from_texts(
                [
                    "pagina web responsive con tailwind",
                    "api rest con nestjs",
                    "autenticacion jwt",
                    "base de datos postgresql",
                    "panel de administracion con graficos",
                    "formulario de registro con validacion",
                    "codigo qr para compartir enlaces",
                    "dashboard de estadisticas con tablas",
                ],
                embeddings,
            )
            return True
        except Exception as e:
            logger.warning("EmbeddingEnricher unavailable: %s", e)
            return False

    def process(self, text: str, context: dict[str, Any] | None = None) -> str:
        if not self._ensure_loaded():
            return text
        docs = self._vectorstore.similarity_search(text, k=2)
        similar = [d.page_content for d in docs]
        return f"{text} [similar: {'; '.join(similar)}]"


# ============================================================================
# SPACY PROCESSOR (N2.1a)
# ============================================================================


class SpacyProcessor:
    """Procesador NLP con spaCy. Carga lazy — no afecta tiempo de inicio."""

    _nlp = None

    @classmethod
    def get_nlp(cls):
        if cls._nlp is None:
            import spacy

            cls._nlp = spacy.load("es_core_news_sm")
        return cls._nlp

    def process(self, text: str) -> dict | None:
        try:
            doc = self.get_nlp()(text)
            return {
                "tokens": [
                    {
                        "text": t.text,
                        "pos": t.pos_,
                        "lemma": t.lemma_,
                        "dep": t.dep_,
                        "head": t.head.text,
                        "is_stop": t.is_stop,
                    }
                    for t in doc
                ],
                "entities": [
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                    }
                    for ent in doc.ents
                ],
                "sentences": [str(s) for s in doc.sents],
            }
        except Exception:
            return None


# ============================================================================
# FILTER CHAIN BUILDER
# ============================================================================


def build_filter_chain(domain: str) -> list[PreprocessingFilter]:
    """Build filter chain using Strategy pattern per domain."""
    return [
        NormalizationFilter(),
        SegmentationFilter(),
    ]


# ============================================================================
# PREPROCESSOR STAGE
# ============================================================================


class Preprocessor(PipelineStage):
    """Stage 2: normalizes and enriches input text through a filter chain."""

    name = "preprocessor"

    def __init__(self, context: StageContext, domain: str = "web"):
        super().__init__(context)
        self.domain = domain
        self.filters = build_filter_chain(domain)
        self._input_text = ""
        self._enriched: dict = {}

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict) and "raw" in input_data:
            self._input_text = input_data["raw"]
            self.domain = input_data.get("intent", {}).get("domain", "web")
            self._enriched = {
                k: input_data[k]
                for k in ("intent", "entities", "slots", "ambiguity", "context")
                if k in input_data
            }
        else:
            self._input_text = str(input_data)
            self.domain = "web"
            self._enriched = {}
        logger.debug("Preprocessor received: %.100s", self._input_text)

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Input length: {len(self._input_text)}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.1,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        result = self._input_text
        context_dict = {"domain": self.domain}
        for f in self.filters:
            result = f.process(result, context_dict)
            logger.debug("After %s: %.80s", f.__class__.__name__, result)

        # spaCy enrichment (N2.1a, opcional)
        spacy_output = SpacyProcessor().process(self._input_text)

        return StageOutput(
            stage=self.context.stage,
            output_data={
                "normalized_text": result,
                "filters_applied": len(self.filters),
                "domain": self.domain,
                "enriched": self._enriched or None,
                "spacy": spacy_output,
                "token_count": len(result.split()),
            },
            metrics={
                "filters_applied": len(self.filters),
                "input_len": len(self._input_text),
                "spacy_enriched": spacy_output is not None,
            },
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
