# ruff: noqa: E402 — sys.path setup must precede agentic_pipeline imports

import sys
from pathlib import Path

# Ensure compiler-bot/ is on sys.path so agentic_pipeline is importable.
_src_root = str(Path(__file__).resolve().parent.parent.parent)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)

import pytest

from agentic_pipeline.state_models import Stage, StageContext


@pytest.fixture
def mock_context():
    return StageContext(stage=Stage.PREPROCESSOR, input_data="test input")
