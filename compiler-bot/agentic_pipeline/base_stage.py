from abc import ABC, abstractmethod

from .state_models import StageContext, AnalysisResult, ActionPlan, StageOutput


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
        output = self.act(plan)
        self.learn_and_improve(output.feedback)
        return output
