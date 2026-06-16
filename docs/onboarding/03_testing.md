---
id: ONB-003
area: DEV
type: GUIDE
module: ONBOARDING
version: 1.0
status: DRAFT
tags:
  - onboarding
  - testing
  - pytest
summary: "Tutorial 3: como escribir tests unitarios y de integracion para los stages del pipeline."
---

# Tutorial 3: Escribir Tests para un Stage

## Estructura de tests

Los tests estan en `tests/` y usan `pytest` con `pytest-asyncio`.

## Test unitario de un stage

```python
import pytest
from agentic_pipeline.nodes.preprocessor import Preprocessor
from agentic_pipeline.state_models import Stage, StageContext


def test_preprocessor_normaliza_texto():
    ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
    stage = Preprocessor(ctx, domain="web")
    stage.receive_mission({"raw": "CREA un MODULO de PAGOS", "intent": {"domain": "web"}})
    plan = stage.reflect_and_plan(stage.analyze())
    output = stage.act(plan)
    assert output.success
    assert output.output_data["normalized_text"] == "crea un modulo de pagos"
```

## Test de integracion (parser)

```python
from agentic_pipeline.nodes.lexer import Lexer
from agentic_pipeline.nodes.parser import ParserGLR
from agentic_pipeline.nodes.preprocessor import Preprocessor
from agentic_pipeline.state_models import Stage, StageContext


def test_parser_produce_ast():
    pre = Preprocessor(StageContext(stage=Stage.PREPROCESSOR, input_data=""), domain="web")
    pre.receive_mission({"raw": "pagina login con formulario", "intent": {"domain": "web"}})
    pre_output = pre.act(pre.reflect_and_plan(pre.analyze()))

    lex = Lexer(StageContext(stage=Stage.LEXER, input_data=""))
    lex.receive_mission(pre_output.output_data)
    lex_output = lex.act(lex.reflect_and_plan(lex.analyze()))

    par = ParserGLR(StageContext(stage=Stage.PARSER, input_data=""))
    par.receive_mission(lex_output.output_data)
    par_output = par.act(par.reflect_and_plan(par.analyze()))
    assert "ast" in par_output.output_data
```

## Ejecutar tests

```bash
python -m pytest tests/ -v --tb=short           # Todos los tests
python -m pytest tests/test_mi_stage.py -v       # Solo mi stage
python -m pytest tests/test_performance.py --benchmark-only  # Benchmarks
python -m pytest tests/test_ast_snapshots.py     # Snapshots
```

## Convenciones

- Tests en clases con `Test` prefix o funciones con `test_` prefix
- Usar `tmp_path` para archivos temporales (no `Path("debug_output")`)
- Cada test debe ser independiente
- `ruff check .` debe pasar antes de commit
