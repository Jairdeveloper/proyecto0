import pytest

from agentic_pipeline.state_models import StageContext, Stage


@pytest.fixture
def mock_context():
    return StageContext(stage=Stage.PREPROCESSOR, input_data="test input")
