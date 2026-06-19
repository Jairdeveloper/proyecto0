import pytest

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.state_models import (
    ActionPlan,
    AnalysisResult,
    Stage,
    StageContext,
    StageOutput,
)


class MockStage(PipelineStage):
    name = "mock"

    def receive_mission(self, input_data):
        self.mission = input_data

    def analyze(self):
        return AnalysisResult(
            observations=["mock observation"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.1,
        )

    def reflect_and_plan(self, analysis):
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan):
        return StageOutput(stage=Stage.PREPROCESSOR, output_data={"done": True})

    def learn_and_improve(self, feedback):
        pass


def test_mock_stage_executes():
    ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="test")
    stage = MockStage(ctx)
    result = stage.execute("hello")
    assert result is not None
    assert result.output_data == {"done": True}
    assert result.success is True


def test_mock_stage_mission():
    ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="test")
    stage = MockStage(ctx)
    stage.receive_mission("custom_input")
    assert stage.mission == "custom_input"


def test_pipeline_stage_is_abstract():
    with pytest.raises(TypeError):
        PipelineStage(StageContext(stage=Stage.PREPROCESSOR, input_data="x"))
