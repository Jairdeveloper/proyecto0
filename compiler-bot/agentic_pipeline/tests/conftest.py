# ruff: noqa: E402 — sys.path setup must precede agentic_pipeline imports

import sys
from pathlib import Path

# Ensure compiler-bot/ is on sys.path so agentic_pipeline is importable.
_src_root = str(Path(__file__).resolve().parent.parent.parent)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)

import pytest

from agentic_pipeline.nodes.ir_nodes import IREntity, IRProject
from agentic_pipeline.state_models import Stage, StageContext


@pytest.fixture
def mock_context() -> StageContext:
    return StageContext(stage=Stage.PREPROCESSOR, input_data="test input")


@pytest.fixture
def mock_ir_project() -> IRProject:
    project = IRProject("test")
    user = IREntity("User", fields=[{"name": "id", "type": "String"}])
    project.add(user)
    return project


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


@pytest.fixture
def sample_prompts() -> dict[str, str]:
    return {
        "create_payments_module": "crea un modulo de pagos en nestjs",
        "create_user_entity": "crea una entidad usuario con id email y password",
        "create_crud_product": "haz un crud de productos con prisma",
        "explain_pipeline": "explica como funciona el pipeline del compilador",
        "empty": "",
    }


@pytest.fixture
def expected_dashboard_files() -> list[str]:
    return [
        "modules/pagos/pagos.module.ts",
        "modules/pagos/pagos.controller.ts",
        "modules/pagos/pagos.service.ts",
        "prisma/schema/usuario.prisma",
    ]
