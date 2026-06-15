from ..base_stage import PipelineStage
from ..nlp.intent_classifier import IntentClassifier
from ..nlp.ner_extractor import NERExtractor
from ..nlp.slot_filler import SlotFiller
from ..nlp.ambiguity_detector import AmbiguityDetector
from ..nlp.enriched_input import EnrichedInput, ContextState
from ..state_models import StageContext, StageOutput, AnalysisResult, ActionPlan
from datetime import datetime


class IntentStage(PipelineStage):
    name = "intent"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_text = ""
        self._classifier = IntentClassifier()
        self._ner = NERExtractor()
        self._slots = SlotFiller()
        self._ambiguity = AmbiguityDetector()

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
            self._input_text, intent, entities, slots,
        )

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

        return StageOutput(
            stage=self.context.stage,
            output_data=enriched.model_dump(),
            metrics={
                "intent": intent.primary,
                "confidence": intent.confidence,
                "domain": intent.domain,
                "entities": len(entities.modulos) + len(entities.techs),
                "slots_complete": slots.completado,
            },
            success=not ambiguity.detected,
            error=(
                "; ".join(e["descripcion"] for e in ambiguity.elementos)
                if ambiguity.detected else None
            ),
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
