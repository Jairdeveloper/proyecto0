import logging
import time
from abc import ABC, abstractmethod

from .contracts import STAGE_CONTRACTS
from .feedback_loop import get_global_feedback
from .state_models import StageContext, AnalysisResult, ActionPlan, StageOutput

logger = logging.getLogger(__name__)


class PipelineStage(ABC):
    name: str

    def __init__(self, context: StageContext):
        self.context = context

    @abstractmethod
    def receive_mission(self, input_data: object) -> None: ...

    @abstractmethod
    def analyze(self) -> AnalysisResult: ...

    @abstractmethod
    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan: ...

    @abstractmethod
    def act(self, plan: ActionPlan) -> StageOutput: ...

    @abstractmethod
    def learn_and_improve(self, feedback: object) -> None: ...

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
            metrics = {
                "duration_seconds": round(duration, 4),
                "success": output.success,
                "error": output.error,
                **output.metrics,
            }
            get_global_feedback().record_stage(self.name, metrics)
        except Exception as exc:
            duration = time.time() - t0
            logger.error("Stage %s failed after %.2fs: %s", self.name, duration, exc)
            get_global_feedback().record_stage(
                self.name,
                {
                    "duration_seconds": round(duration, 4),
                    "success": False,
                    "error": str(exc),
                },
            )
            raise
        self.learn_and_improve(output.feedback)
        return output
