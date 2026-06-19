"""PerceptionUnit — clasificador de intencion con SentenceTransformers (N2.1b)."""

from datetime import datetime

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.nlp.ambiguity_detector import AmbiguityDetector
from agentic_pipeline.nlp.enriched_input import ContextState, EnrichedInput
from agentic_pipeline.nlp.intent_classifier import IntentClassifier
from agentic_pipeline.nlp.ner_extractor import NERExtractor
from agentic_pipeline.nlp.slot_filler import SlotFiller
from agentic_pipeline.state_models import ActionPlan, AnalysisResult, StageContext, StageOutput


class SentenceTransformerClassifier:
    """Clasificador de intencion por embeddings semanticos (N2.1b)."""

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer

            cls._model = SentenceTransformer(cls.MODEL_NAME)
        return cls._model

    def __init__(self):
        self.model = self.get_model()
        self.references = self._build_references()

    def _build_references(self):
        from sentence_transformers import util as st_util

        self._util = st_util
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

    def classify(self, text: str) -> tuple[str, float]:
        emb = self.model.encode(text, convert_to_tensor=True)
        best_intent, best_score = "UNKNOWN", 0.0

        for intent, refs in self.references.items():
            scores = self._util.cos_sim(emb, refs)
            max_score = scores.max().item()
            if max_score > best_score:
                best_score = max_score
                best_intent = intent

        return best_intent, best_score


class PerceptionUnit(PipelineStage):
    name = "intent"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_text = ""
        self._classifier = IntentClassifier()
        self._ner = NERExtractor()
        self._slots = SlotFiller()
        self._ambiguity = AmbiguityDetector()
        self._semantic_classifier = None

    def _get_semantic_classifier(self):
        if self._semantic_classifier is None:
            try:
                self._semantic_classifier = SentenceTransformerClassifier()
            except Exception:
                self._semantic_classifier = False
        return self._semantic_classifier if self._semantic_classifier else None

    def receive_mission(self, input_data: object) -> None:
        self._input_text = str(input_data) if input_data else ""

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Input: {self._input_text[:50]}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.1,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        intent = self._classifier.classify(self._input_text)
        entities = self._ner.extract(self._input_text)
        slots = self._slots.fill(intent, entities)
        ambiguity = self._ambiguity.detect(
            self._input_text,
            intent,
            entities,
            slots,
        )

        # SentenceTransformers enrichment (N2.1b, opcional)
        semantic_intent = None
        semantic_score = 0.0
        semantic_confianza = None
        clf = self._get_semantic_classifier()
        if clf:
            si, ss = clf.classify(self._input_text)
            semantic_intent = si
            semantic_score = ss
            if ss >= 0.7:
                semantic_confianza = "high"
            elif ss >= 0.6:
                semantic_confianza = "medium"
            else:
                semantic_confianza = "low"

        enriched = EnrichedInput(
            raw=self._input_text,
            intent=intent,
            entities=entities,
            slots=slots,
            ambiguity=ambiguity,
            context=ContextState(
                turno=1,
                session_id=datetime.now().isoformat(),
            ),
        )

        output = enriched.model_dump()
        if semantic_intent:
            output["semantic_intent"] = semantic_intent
            output["semantic_score"] = semantic_score
            output["semantic_confianza"] = semantic_confianza

        ambiguity_detected = ambiguity.detected
        return StageOutput(
            stage=self.context.stage,
            output_data=output,
            metrics={
                "intent": intent.primary,
                "confidence": intent.confidence,
                "domain": intent.domain,
                "entities": len(entities.modulos) + len(entities.techs),
                "slots_complete": slots.completado,
                "semantic_intent": semantic_intent or intent.primary,
                "semantic_score": semantic_score,
                "ambiguity_detected": ambiguity_detected,
            },
            success=True,
            error=None,
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
