---
id: 096
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0
status: DRAFT
tags:
  - report
  - track-d
  - qa
  - benchmarks
  - snapshots
  - testing
summary: >-
  Reporte de implementacion del Track D (QA/Testing) de la propuesta
  092. Cubre benchmarks de performance (pytest-benchmark), snapshot
  testing de AST (syrupy), y correccion del test de debugger con
  tmp_path. 524 tests total.
keywords:
  - track-d
  - qa
  - benchmarks
  - snapshots
  - syrupy
  - pytest-benchmark
  - tmp_path
  - performance
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Reporte de implementacion Track D (QA/Testing)
---

# 096_REP_DEV_TRACK_D_1_0_DRAFT

## Resumen

Ejecucion completa del Track D (QA / Testing) de la propuesta
`092_PROP_DEV_MULTI_PERSPECTIVE_IMPLEMENTATION`. Se implementaron 5
benchmarks de performance, 3 snapshot tests de AST, y se corrigio el
test del debugger para usar `tmp_path` en vez de directorios hardcodeados.
Total: **524 tests pasando** (+8 nuevos), `ruff check .` = 0 errores.

---

## D.1 Performance Benchmarks

**Estado: COMPLETO**

| Tarea | Archivo | Resultado |
|-------|---------|-----------|
| D.1.1 | `pyproject.toml` | `pytest-benchmark>=5.0` anadido a dev dependencies |
| D.1.2 | `tests/test_performance.py` | 5 benchmarks implementados |
| D.1.3 | `test_pipeline_short` | Pipeline completo, prompt corto |
| D.1.4 | `test_pipeline_long` | Pipeline completo, prompt de 500+ palabras |
| D.1.5 | `test_nlp_only` | Solo IntentStage (classifier + NER + slots) |
| D.1.6 | `test_parser_throughput` | Lexer + Parser (1000+ tokens efectivos) |
| D.1.7 | `test_generator_throughput` | Planner + Synthesis (10 targets) |

### Resultados de Benchmarks

| Benchmark | Media | Mediana | OPS |
|-----------|-------|---------|-----|
| `test_generator_throughput` | 10.9µs | 10.1µs | 91,871 ops/s |
| `test_nlp_only` | 118.4µs | 111.3µs | 8,444 ops/s |
| `test_parser_throughput` | 319.6µs | 296.9µs | 3,129 ops/s |
| **`test_pipeline_short`** | **1.06s** | **1.05s** | **0.94 ops/s** |
| **`test_pipeline_long`** | **6.67s** | **6.66s** | **0.15 ops/s** |

**Criterio de aceptacion:** Pipeline completo < 2s en prompt tipico → **CUMPLE**
(`test_pipeline_short` = 1.06s, que es un prompt de longitud tipica).

**Ejecucion:**
```bash
python -m pytest tests/test_performance.py --benchmark-only
```

---

## D.2 Snapshot Testing para AST

**Estado: COMPLETO**

| Tarea | Archivo | Resultado |
|-------|---------|-----------|
| D.2.1 | `pyproject.toml` | `syrupy>=4.0` anadido a dev dependencies |
| D.2.2 | `tests/test_ast_snapshots.py` | 3 snapshot tests implementados |
| D.2.3 | Snapshot 1: "pagina login con formulario" | AST de UI grammar capturado |
| D.2.4 | Snapshot 2: "entidad Usuario nombre:string email:string" | AST de data grammar capturado |
| D.2.5 | Snapshot 3: "crea un modulo de pagos con NestJS y Prisma" | AST de project grammar capturado |

### Archivos de snapshot

```
tests/__snapshots__/
├── test_ast_snapshots/
│   ├── test_ast_page_snapshot.yml
│   ├── test_ast_entity_snapshot.yml
│   └── test_ast_project_snapshot.yml
```

**Criterio de aceptacion:** Cambios en el AST rompen snapshots explicitamente → **CUMPLE**
(syrupy falla con diff detallado si el AST cambia).

**Uso:**
```bash
python -m pytest tests/test_ast_snapshots.py                    # Verificar snapshots
python -m pytest tests/test_ast_snapshots.py --snapshot-update   # Actualizar snapshots
```

---

## D.3 Fix Debugger Test (tmp_path)

**Estado: COMPLETO**

| Tarea | Archivo | Cambio |
|-------|---------|--------|
| D.3.1 | `debugger.py` | Anadido parametro `debug_output_dir: Path | None` al constructor |
| D.3.2 | `tests/test_debugger.py` | `test_inspect_mode_creates_snapshots` y `test_inspect_with_show_output` usan `tmp_path` |
| D.3.3 | (eliminacion) | `debug_output/` ya no se crea en el CWD durante tests |

### Detalle del cambio

**debugger.py:**
```python
class PipelineDebugger:
    def __init__(
        self,
        mode: str = "trace",
        output_dir: str = "modules",
        show_output: bool = False,
        debug_output_dir: Path | None = None,
    ):
        self._debug_output_dir = debug_output_dir or DEBUG_OUTPUT_DIR
        ...
```

**test_debugger.py:**
```python
async def test_inspect_mode_creates_snapshots(self, tmp_path):
    debugger = PipelineDebugger(mode="inspect", debug_output_dir=tmp_path)
    ...
```

**Criterio de aceptacion:** No quedan archivos residuales tras tests → **CUMPLE**
(`tmp_path` es auto-limpiante por pytest).

---

## Verificacion

| Comando | Resultado |
|---------|-----------|
| `ruff check .` | 0 errores |
| `python -m pytest tests/ -q` | 524 passed |
| `python -m pytest tests/test_performance.py --benchmark-only` | 5 benchmarks OK |
| `python -m pytest tests/test_ast_snapshots.py` | 3 snapshots passed |
| `python -m pytest tests/test_debugger.py -v` | 10 tests passed, sin archivos residuales |

## Resumen de Tests

| Grupo | Cantidad |
|-------|----------|
| Tests pre-existentes | 516 |
| Benchmarks (D.1) | 5 |
| Snapshots (D.2) | 3 |
| **Total** | **524** |

## Archivos Modificados/Creados

### Modificados
| Archivo | Cambio |
|---------|--------|
| `pyproject.toml` | Dev dependencies: +`pytest-benchmark`, +`syrupy` |
| `debugger.py` | Nuevo parametro `debug_output_dir` para tests |
| `tests/test_debugger.py` | 2 tests usan `tmp_path` en vez de `Path("debug_output")` |

### Creados
| Archivo | Proposito |
|---------|-----------|
| `tests/test_performance.py` | 5 benchmarks de performance |
| `tests/test_ast_snapshots.py` | 3 snapshot tests de AST |
| `tests/__snapshots__/test_ast_snapshots/` | Archivos de snapshot generados por syrupy |
| `docs/096_REP_DEV_TRACK_D_1_0_DRAFT.md` | Este reporte |

## Checklist de Aceptacion

- [x] `ruff check .` = 0 errores
- [x] `pytest tests/ -q` = 524 pasando
- [x] 5 benchmarks de performance implementados y pasando
- [x] Pipeline completo < 2s en prompt tipico (1.06s medido)
- [x] 3 snapshot tests de AST implementados y pasando
- [x] Debugger test usa `tmp_path` — sin archivos residuales
- [x] `pytest-benchmark` y `syrupy` en dev dependencies
