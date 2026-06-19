import logging
import time
from abc import ABC, abstractmethod

from agentic_pipeline.contracts import STAGE_CONTRACTS
from agentic_pipeline.observers.audit_observer import AuditObserver
from agentic_pipeline.observers.metrics_observer import MetricsObserver as _MetricsObserver
from agentic_pipeline.prompt_chain.observer_base import StageEvent, StageSubject
from agentic_pipeline.state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    name: str
    subject: StageSubject = StageSubject()
    """StageSubject compartido por todas las subclases.

    Los observers (MetricsObserver, DebugObserver, etc.) se
    registran aqui para recibir eventos de todos los stages.
    """

    def __init__(self, context: StageContext):
        self.context = context

    @abstractmethod
    def receive_mission(self, input_data: object) -> None: ...

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[],
            detected_patterns=[],
            risks=[],
            complexity_score=0.0,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    @abstractmethod
    def act(self, plan: ActionPlan) -> StageOutput: ...

    def learn_and_improve(self, feedback: object) -> None:
        pass

    def execute(self, input_data: object) -> StageOutput:
        self.receive_mission(input_data)
        analysis = self.analyze()
        plan = self.reflect_and_plan(analysis)
        t0 = time.time()
        try:
            output = self.act(plan)
            contract = STAGE_CONTRACTS.get(self.name)
            if contract and output.success:
                contract.model_validate(output.output_data)
            duration = time.time() - t0
            event = StageEvent(
                stage=self.name,
                duration=round(duration, 4),
                success=output.success,
                output=(output.output_data if isinstance(output.output_data, dict) else {}),
                error=output.error,
                metadata=output.metrics,
            )
            self.subject.notify(event)
        except Exception as exc:
            duration = time.time() - t0
            logger.error("Stage %s failed after %.2fs: %s", self.name, duration, exc)
            event = StageEvent(
                stage=self.name,
                duration=round(duration, 4),
                success=False,
                error=str(exc),
            )
            self.subject.notify(event)
            raise
        self.learn_and_improve(output.feedback)
        return output


# Attach default observers so all stages automatically record metrics
# and audit logs without modifying subclasses.
PipelineStage.subject.attach(_MetricsObserver())
PipelineStage.subject.attach(AuditObserver())
