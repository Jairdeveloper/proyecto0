"""PerceptionAgent — analiza entrada con spaCy, SentenceTransformers, WordNet (N3.2a)."""

from __future__ import annotations

from ..world_model import WorldModel
from .base_agent import Agent, SharedContext, Task, TaskResult


class PerceptionAgent(Agent):
    """Agente especializado en percepcion y analisis semantico."""

    name = "perception_agent"
    role = "analizar entrada del usuario con NLP"

    def __init__(self, context: SharedContext, world: WorldModel | None = None):
        super().__init__(context)
        self.world = world or WorldModel()
        self._spacy = None
        self._classifier = None

    def _get_spacy(self):
        if self._spacy is None:
            try:
                from agentic_pipeline.nodes.preprocessor import SpacyProcessor
                self._spacy = SpacyProcessor()
            except Exception:
                self._spacy = False
        return self._spacy if self._spacy else None

    def _get_classifier(self):
        if self._classifier is None:
            try:
                from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
                self._classifier = SentenceTransformerClassifier()
            except Exception:
                self._classifier = False
        return self._classifier if self._classifier else None

    def _disambiguate(self, term: str, context: list[str]) -> dict | None:
        try:
            from agentic_pipeline.nodes.parser import disambiguate_term
            return disambiguate_term(term, context)
        except Exception:
            return None

    async def process(self, task: Task) -> TaskResult:
        text = task.params.get("text", task.description)

        analysis: dict = {"raw": text, "spacy": None, "intent": None, "disambiguation": None}

        # spaCy enrichment
        spacy_proc = self._get_spacy()
        if spacy_proc:
            spacy_result = spacy_proc.process(text)
            if spacy_result:
                analysis["spacy"] = spacy_result
                analysis["tokens"] = spacy_result["tokens"]

        # SentenceTransformers classifier
        clf = self._get_classifier()
        if clf:
            intent, score = clf.classify(text)
            analysis["intent"] = {"intent": intent, "score": score}

        # WordNet disambiguation
        terms = [t.get("text", "") for t in (analysis.get("tokens") or [])
                 if not t.get("is_stop", False)]
        ambiguous = [t for t in terms if t in ("modulo", "entidad", "servicio", "pagina")]
        for term in ambiguous:
            result = self._disambiguate(term, [text])
            if result:
                analysis["disambiguation"] = result

        self.context.publish("perception_result", analysis)
        return TaskResult(task_id=task.id, success=True, data=analysis)
