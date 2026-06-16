"""RequirementDecomposer pipeline stage."""

from __future__ import annotations

import logging

from .ast_cache import ASTCache
from ..base_stage import PipelineStage
from ..feedback_loop import get_global_feedback
from ..state_models import (
    ActionPlan,
    AnalysisResult,
    RequirementGraph,
    StageContext,
    StageOutput,
)
from ..tools.llm_tools import (
    ConstraintDetector,
    DomainClassifier,
    EntityExtractor,
    FeatureIdentifier,
    LLMOrchestrator,
    StoryGenerator,
)

logger = logging.getLogger(__name__)


class RequirementDecomposer(PipelineStage):
    """Stage 1: decomposes raw user requirement into a structured RequirementGraph."""

    name = "requirement_decomposer"

    def __init__(self, context: StageContext, llm: LLMOrchestrator | None = None):
        super().__init__(context)
        self._llm = llm
        self._domain_classifier = DomainClassifier(self._llm)
        self._entity_extractor = EntityExtractor(self._llm)
        self._feature_identifier = FeatureIdentifier()
        self._constraint_detector = ConstraintDetector()
        self._story_generator = StoryGenerator()
        self._feedback = get_global_feedback()
        self._cache = ASTCache(maxsize=64)
        self._raw_text = ""

    def receive_mission(self, input_data: object) -> None:
        self._raw_text = str(input_data)
        logger.debug("RequirementDecomposer received: %.100s", self._raw_text)

    def analyze(self) -> AnalysisResult:
        domain = self._domain_classifier.classify(self._raw_text)
        logger.info("Domain detected: %s", domain)
        return AnalysisResult(
            observations=[f"Domain detected: {domain}"],
            detected_patterns=[domain],
            risks=[],
            complexity_score=0.3,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(
            steps=[
                {"action": "extract_entities"},
                {"action": "identify_features"},
                {"action": "detect_constraints"},
                {"action": "generate_stories"},
            ],
            strategy="llm_assisted",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        logger.debug("Executing RequirementDecomposer plan: %s", plan.steps)
        graph = self._cache.get_or_compute(
            self._raw_text,
            lambda: self._build_graph(),
        )
        return StageOutput(
            stage=self.context.stage,
            output_data=graph.model_dump(),
            metrics={
                "entities": len(graph.entities),
                "features": len(graph.features),
                "constraints": len(graph.constraints),
                "stories": len(graph.user_stories),
            },
        )

    def _build_graph(self) -> RequirementGraph:
        domain = self._domain_classifier.classify(self._raw_text)
        entities = self._entity_extractor.extract(self._raw_text)
        features = self._feature_identifier.identify(self._raw_text)
        constraints = self._constraint_detector.detect(self._raw_text)
        stories = self._story_generator.generate(features, entities)
        logger.info(
            "RequirementGraph: domain=%s, entities=%d, features=%d",
            domain,
            len(entities),
            len(features),
        )
        return RequirementGraph(
            domain=domain,
            entities=entities,
            features=features,
            constraints=constraints,
            user_stories=stories,
            raw_text=self._raw_text,
        )

    def learn_and_improve(self, feedback: object) -> None:
        self._feedback.record_stage(
            self.name,
            {"input_len": len(self._raw_text)},
        )
