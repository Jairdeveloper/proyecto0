---
id: "P02"
area: "DEV"
type: "PLAN"
module: "RECPL_REFACTOR"
version: "1.0"
status: "DRAFT"
tags: ["plan", "implementation", "refactor", "debt", "quality"]
summary: "Plan de implementacion detallado para resolver todos los problemas arquitectonicos, deuda tecnica, riesgos y mejores practices incumplidas identificados en el reporte de arquitectura 001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md"
changelog:
  - version: "1.0"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Version inicial — plan de implementacion completo, seccion por seccion del reporte de arquitectura"
---

# Plan de Implementacion — Refactor Arquitectonico RECPL v2.0+

> **Documento base:** `docs/architecture/001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md`  
> **Objetivo:** Resolver 100% de los problemas identificados (arquitectonicos, calidad, testing, deuda, riesgos, SOLID, seguridad, rendimiento)  
> **Esfuerzo total estimado:** ~127h / ~16 dias efectivos  
> **Entregable:** Sistema en TRL 6-7 (demostracion en entorno operacional)

---

## Tabla de Contenidos

1. [Estructura del Plan](#1-estructura-del-plan)
2. [Problemas Arquitectonicos (P1-P6)](#2-problemas-arquitectonicos-p1-p6)
3. [Problemas de Calidad (Q1-Q6)](#3-problemas-de-calidad-q1-q6)
4. [Problemas de Testing (T1-T4)](#4-problemas-de-testing-t1-t4)
5. [Deuda Tecnica](#5-deuda-tecnica)
6. [Riesgos y Cuellos de Botella](#6-riesgos-y-cuellos-de-botella)
7. [Mejores Practices SOLID + Arquitectonicas](#7-mejores-practicas-solid--arquitectonicas)
8. [Seguridad](#8-seguridad)
9. [Escalabilidad y Rendimiento](#9-escalabilidad-y-rendimiento)
10. [Mapa de Ruta Integrado](#10-mapa-de-ruta-integrado)
11. [Presupuesto Total](#11-presupuesto-total)

---

## 1. Estructura del Plan

Cada seccion sigue este formato:

```
## N. Problema/Area

### N.1 Tareas
| ID | Tarea | Archivos | Esfuerzo | Depende De | Criterio de Aceptacion |
|----|-------|----------|----------|------------|------------------------|

### N.2 Riesgo de Implementacion
[Que podria salir mal al implementar esto]

### N.3 Verificacion
[Como confirmar que el problema esta resuelto]
```

---

## 2. Problemas Arquitectonicos (P1-P6)

### P1 — Dos sistemas de agentes desconectados (ALTA)

**Problema:** Pipeline stages (`nodes/`) y multi-agent system (`agents/`) son dos arquitecturas paralelas sin integracion. No hay codigo que ejecute los agentes a traves de los stages.

**Solucion:** Crear un `AgentPipelineAdapter` que ejecute el pipeline completo usando los agentes como orquestadores, y un `RoutingStrategy` que decida en runtime si usar stages directos o agentes.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Depende De | Criterio de Aceptacion |
|----|-------|----------|----------|------------|------------------------|
| P1.1 | Crear `AgentPipelineAdapter` — adaptador que recibe un `Agent` y lo ejecuta como un `PipelineStage`, llamando a `agent.process(task)` dentro de `act()` | `agents/agent_pipeline_adapter.py` (NUEVO) | 4h | — | `AgentPipelineAdapter(PipelineStage)` compila sin errores; `act()` delega en `agent.process()` |
| P1.2 | Implementar `OrchestratorRouter` que selecciona modo de ejecucion: `direct` (StateGraph actual), `agent` (via adapter), `hybrid` (agentes para stages LLM, directo para el resto) | `orchestrator_router.py` (NUEVO) | 6h | P1.1 | Router produce el mismo output para `direct` y `agent` mode con input identico |
| P1.3 | Integrar `SupervisorAgent` como orquestador agente: recibe input, descompone en subtareas, delega a `PerceptionAgent`/`ReasoningAgent`/`ExecutionAgent`/`ValidatorAgent`, cada una ejecutada como `PipelineStage` via adapter | `agents/supervisor_agent.py` (MODIFICAR) | 6h | P1.1, P1.2 | Supervisor ejecuta pipeline completo y produce StageOutput valido |
| P1.4 | Tests de integracion: mismo prompt ejecutado en modo `direct`, `agent` e `hybrid` produce archivos identicos | `tests/test_agent_pipeline_integration.py` (NUEVO) | 4h | P1.3 | 3 modos producen mismo arbol de archivos |

**Total P1:** 20h

#### Riesgos

- Los agentes tienen un modelo de datos diferente (`Task`/`TaskResult`) vs pipeline (`StageContext`/`StageOutput`). El adapter debe mapear correctamente.
- `SupervisorAgent` actualmente no sabe construir un `StageContext`. Habra que extenderlo.

#### Verificacion

```bash
pytest tests/test_agent_pipeline_integration.py -v
# Output: 3 passed (direct, agent, hybrid modes match)
```

---

### P2 — RequirementDecomposer dead code (MEDIA) **NO IMPLEMENTAR (EN EVALUACION)**

**Problema:** `nodes/requirement_decomposer.py` existe como archivo y `Stage.REQUIREMENT_DECOMPOSER` existe como enum, pero no esta en `NODE_MAP` ni se usa en ningun flujo.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| P2.1 | Verificar que ningun import referencia `requirement_decomposer` o `Stage.REQUIREMENT_DECOMPOSER` en codigo activo | (grep) | 0.5h | grep retorna 0 referencias (salvo el propio archivo y enum) |
| P2.2 | Eliminar `nodes/requirement_decomposer.py` | `nodes/requirement_decomposer.py` (ELIMINAR) | 0.5h | Archivo eliminado, `git diff` muestra solo el delete |
| P2.3 | Eliminar `REQUIREMENT_DECOMPOSER` del enum `Stage` en `state_models.py` | `state_models.py` (MODIFICAR) | 0.5h | Enum compila sin ese valor, tests pasan |

**Total P2:** 1.5h

#### Verificacion

```bash
ruff check . && pytest tests/ -v --cov  # 0 errores, todos pasan
```

---

### P3 — ParserGLR no es GLR (BAJA)

**Problema:** La clase se llama `ParserGLR` pero Lark se configura con `parser="earley"`.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| P3.1 | Renombrar clase `ParserGLR` → `LarkParser` en `nodes/parser.py` | `nodes/parser.py` (MODIFICAR) | 0.5h | `class LarkParser(PipelineStage):` definido |
| P3.2 | Actualizar todas las referencias a `ParserGLR` en el codigo: `NODE_MAP`, imports, tests | `orchestrator.py`, `nodes/parser.py`, tests/, `docs/` (grep + replace) | 1h | `git grep ParserGLR` retorna 0 |
| P3.3 | Agregar comentario/docstring explicando que Lark Earley es un parser GLR-generalizado | `nodes/parser.py` (MODIFICAR) | 0.5h | Docstring: `"""Lark-based parser using Earley algorithm (generalized LR)."""` |

**Total P3:** 2h

#### Verificacion

```bash
git grep -i "parserglr"  # 0 matches
pytest tests/test_parser*.py -v  # todos pasan (los namespaces estan actualizados)
```

---

### P4 — StageSubject compartido mutable (MEDIA)

**Problema:** `PipelineStage.subject` es una class variable (`StageSubject()`) compartida por todas las subclases. La lista de observers es mutable y no thread-safe.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| P4.1 | Agregar `threading.Lock` a `StageSubject._observers` con `copy-on-write` en `notify()` | `prompt_chain/observer_base.py` (MODIFICAR) | 1.5h | `notify()` itera sobre copia congelada; `attach()`/`detach()` usan lock |
| P4.2 | Verificar que `PipelineStage.subject` sigue siendo class var pero con lock interno | `base_stage.py` (VERIFICAR, sin cambios) | 0.5h | Race condition test pasa: 10 threads attach/detach/notify simultaneos |
| P4.3 | Test de concurrencia: 10 hilos llamando `attach`, `detach`, `notify` simultaneamente | `tests/test_observer_pattern.py` (EXTENDER) | 2h | Test no falla ni produce `RuntimeError: list changed during iteration` |

**Total P4:** 4h

#### Verificacion

```bash
pytest tests/test_observer_pattern.py -v -k "concurrent"  # pasa sin race conditions
```

---

### P5 — Dos event buses paralelos (MEDIA)

**Problema:** `StageSubject` (prompt_chain/) y `EventBus` (agents/) son dos implementaciones de pub/sub con la misma funcion.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Depende De | Criterio de Aceptacion |
|----|-------|----------|----------|------------|------------------------|
| P5.1 | Unificar interfaces: hacer que `StageSubject` herede/metodo de `EventBus` O hacer que `EventBus` implemente `StageObserver` y se conecte al `StageSubject` | `prompt_chain/observer_base.py`, `agents/event_bus.py` (MODIFICAR) | 3h | — | `EventBus` puede suscribirse a `StageSubject` como un observer mas |
| P5.2 | Migrar `PipelineStage.subject.notify()` a usar `EventBus.publish()` internamente (el subject delega en event bus) | `prompt_chain/observer_base.py` (MODIFICAR) | 3h | P5.1 | `StageSubject.notify()` llama a `_event_bus.publish()` y a observers locales |
| P5.3 | Eliminar `StageObserver` duplicado; unificar en `EventBus` como unico mecanismo pub/sub | `prompt_chain/observer_base.py` (MODIFICAR), `agents/event_bus.py` (MODIFICAR) | 2h | P5.2 | Solo existe una clase pub/sub en el codebase |
| P5.4 | Actualizar imports: `feedback_loop.py`, `base_stage.py`, `handler_base.py`, `orchestrator.py` | 4 archivos (MODIFICAR) | 1h | P5.3 | Todos los imports apuntan al `EventBus` unificado |

**Total P5:** 9h (reporte original estimaba 8h)

#### Riesgos

- `StageSubject` tiene `attach/detach/notify` mientras `EventBus` tiene `subscribe/unsubscribe/publish`. La unificacion debe decidir una API ganadora o crear un wrapper.
- Muchos archivos importan `StageSubject`/`StageObserver` desde `prompt_chain.observer_base`. El refactor tocara ~10 archivos.

#### Verificacion

```bash
git grep -l "StageSubject\|StageObserver" | wc -l  # debe reducirse
(grep debe mostrar solo referencias al EventBus unificado o alias)
pytest tests/ -v --cov  # 100% passing
```

---

### P6 — PipelineMacroCommand duplica StateGraph (BAJA)

**Problema:** `PipelineMacroCommand` en `orchestrator.py` ejecuta los mismos stages manualmente sin usar el `StateGraph`, duplicando logica de `AgentOrchestrator`.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| P6.1 | Refactorizar `PipelineMacroCommand.execute()` para que delegue en `AgentOrchestrator.run()` en lugar de iterar stages manualmente | `orchestrator.py` (MODIFICAR) | 2h | `PipelineMacroCommand.execute()` llama a `AgentOrchestrator.run()` internamente |
| P6.2 | Eliminar `_stage_to_enum()` y el loop manual de stages en `PipelineMacroCommand` | `orchestrator.py` (MODIFICAR) | 1h | `git diff orchestrator.py` muestra -100 lineas |
| P6.3 | Verificar que `CommandHistory.replay_failures()` sigue funcionando con el nuevo `PipelineMacroCommand` | `tests/test_command*.py` (VERIFICAR) | 1h | Tests de CommandHistory pasan con PipelineMacroCommand refactorizado |

**Total P6:** 4h

#### Verificacion

```bash
pytest tests/ -v -k "macro or pipeline"  # tests pasan
# Verificar que PipelineMacroCommand ya no tiene su propio loop de stages
grep -c "for stage_cls in" compiler-bot/agentic_pipeline/orchestrator.py  # 0
```

---

## 3. Problemas de Calidad (Q1-Q6)

### Q1 — Sin configuracion de ruff (ALTA)

**Problema:** `pyproject.toml` no tiene `[tool.ruff]` pese a que AGENTS.md lo exige.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| Q1.1 | Agregar `[tool.ruff]` con `line-length = 100`, `indent-width = 4`, `target-version = "py311"`, `select = ["E", "F", "I", "N", "W", "UP"]` | `pyproject.toml` (MODIFICAR) | 0.5h | `ruff check .` pasa sin errores |
| Q1.2 | Agregar `[tool.ruff.format]` con `quote-style = "double"`, `indent-style = "space"` | `pyproject.toml` (MODIFICAR) | 0.5h | `ruff format --check .` pasa |
| Q1.3 | Ejecutar `ruff check . --fix` y `ruff format .` para corregir violaciones existentes | (todos los archivos) | 2h | `ruff check .` = 0 errores, `ruff format --check .` = 0 diferencias |
| Q1.4 | Agregar `# ruff: noqa` comments solo donde sea unavoidable (conftest.py E402) | `conftest.py` (VERIFICAR) | 0.5h | Los unicos `noqa` en el codebase estan justificados |

**Total Q1:** 3.5h

#### Verificacion

```bash
ruff check . && ruff format --check .
# Exit code 0 en ambos
```

---

### Q2 — Sin configuracion de pytest (MEDIA)

**Problema:** `[tool.pytest.ini_options]` no existe en `pyproject.toml`.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| Q2.1 | Agregar `[tool.pytest.ini_options]` con `minversion = "8.0"`, `testpaths = ["tests"]`, `asyncio_mode = "auto"`, `python_files = ["test_*.py"]`, `python_classes = ["Test*"]`, `python_functions = ["test_*"]` | `pyproject.toml` (MODIFICAR) | 0.5h | `pytest --config` reconoce la config |
| Q2.2 | Agregar `addopts = ["-v", "--tb=short", "--cov=agentic_pipeline", "--cov-report=term-missing"]` | `pyproject.toml` (MODIFICAR) | 0.5h | `pytest` ejecuta con coverage automaticamente |
| Q2.3 | Verificar que todos los tests se descubren correctamente con la nueva config | (todos los tests) | 1h | `pytest tests/ --collect-only` lista 72+ tests |

**Total Q2:** 2h

#### Verificacion

```bash
pytest tests/ --collect-only | tail -5
# Muestra: "collected 400+ items" (o el numero real)
pytest tests/ -v  # pasa con coverage
```

---

### Q3 — `__init__.py` vacios en paquetes (MEDIA)

**Problema:** `nodes/`, `nlp/`, `providers/`, `grammars/`, `tests/` tienen `__init__.py` vacios.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| Q3.1 | `nodes/__init__.py`: exportar todas las clases de pipeline stages (PerceptionUnit, Preprocessor, Lexer, ParserGLR→LarkParser, SemanticAnalyzer, IRGenerator, ReasoningEngine, ActionExecutor, UIGenerator, ValidatorPipeline) | `nodes/__init__.py` (MODIFICAR) | 1.5h | `from agentic_pipeline.nodes import LarkParser` funciona |
| Q3.2 | `nlp/__init__.py`: exportar IntentClassifier, NERExtractor, SlotFiller, AmbiguityDetector, EnrichedInput | `nlp/__init__.py` (MODIFICAR) | 0.5h | `from agentic_pipeline.nlp import IntentClassifier` funciona |
| Q3.3 | `providers/__init__.py`: docstring + `__all__` (si tiene contenido) o eliminar si esta vacio sin uso | `providers/__init__.py` (MODIFICAR) | 0.5h | Paquete accesible |
| Q3.4 | `grammars/__init__.py`: docstring + `__all__` listando archivos .lark como constantes | `grammars/__init__.py` (MODIFICAR) | 0.5h | Gramaticas importables |
| Q3.5 | `tests/__init__.py` se deja vacio intencionalmente (convencion pytest) | (sin cambios) | 0h | No se modifica |

**Total Q3:** 3h

#### Verificacion

```bash
python -c "from agentic_pipeline.nodes import LarkParser; print('OK')"
python -c "from agentic_pipeline.nlp import IntentClassifier; print('OK')"
# Ambos imprimen OK
```

---

### Q4 — feedback_loop.py viola SRP (MEDIA)

**Problema:** `feedback_loop.py` contiene 7 clases no relacionadas en 302 lineas.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| Q4.1 | Mover `MetricsObserver`, `DebugObserver`, `PromptOptimizerObserver`, `DashboardObserver` a `observers/__init__.py` | `observers/__init__.py` (NUEVO), `feedback_loop.py` (MODIFICAR) | 1.5h | `from agentic_pipeline.observers import MetricsObserver` funciona |
| Q4.2 | Mover `PromptOptimizer` a `optimizer.py` | `optimizer.py` (NUEVO), `feedback_loop.py` (MODIFICAR) | 1h | `from agentic_pipeline.optimizer import PromptOptimizer` funciona |
| Q4.3 | Dejar `FeedbackLoop` y `GlobalFeedbackLoop` en `feedback_loop.py` (SRP: metricas legacy + global) | `feedback_loop.py` (MODIFICAR) | 0.5h | `feedback_loop.py` solo contiene 2 clases |
| Q4.4 | Actualizar imports en: `base_stage.py`, `requirement_decomposer.py` (si sobrevive), `tests/` | multiples archivos (MODIFICAR) | 2h | `git grep "from.*feedback_loop import"` muestra solo `FeedbackLoop` y `GlobalFeedbackLoop` |
| Q4.5 | Agregar `observers/__init__.py` con `__all__` | `observers/__init__.py` (NUEVO) | 0.5h | Export names listados |
| Q4.6 | Crear `observers/__init__.py` como paquete | `observers/` directorio (NUEVO) | 0.5h | Directorio existe con `__init__.py` |

**Total Q4:** 6h

#### Verificacion

```bash
ruff check .  # 0 errores
pytest tests/ -v --cov  # todos pasan (coverage puede bajar temporalmente)
```

---

### Q5 — Type hints incompletos (BAJA)

**Problema:** `feedback_loop.py` (y otros archivos) usan `Any` excesivamente.

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| Q5.1 | Revisar `feedback_loop.py` (o su version refactorizada post-Q4) y reemplazar `Any` con tipos concretos en parametros de metodos publicos | `feedback_loop.py`, `observers/`, `optimizer.py` (MODIFICAR) | 2h | `mypy --strict feedback_loop.py` reporta 0 `Any` no justificados |
| Q5.2 | Revisar `metrics_store.py` — reemplazar `dict` generico con TypedDict o clases concretas | `metrics_store.py` (MODIFICAR) | 1h | Metricas tipadas como `StageMetrics(TypedDict)` |
| Q5.3 | Ejecutar `mypy agentic_pipeline/ --ignore-missing-imports` y documentar violaciones restantes | (todos los archivos) | 1h | Lista de violaciones conocidas (no bloqueantes) |

**Total Q5:** 4h

#### Verificacion

```bash
mypy agentic_pipeline/feedback_loop.py --strict  # 0 errores de Any
```

---

### Q6 — Rutas de importacion inconsistentes (BAJA)

**Problema:** Mezcla de imports relativos (`from .`) y absolutos (`from agentic_pipeline.`).

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| Q6.1 | Estandarizar a imports absolutos dentro del paquete: `from agentic_pipeline.nodes.parser import LarkParser` | todos los archivos (MODIFICAR) | 3h | `git grep "from \."` en `agentic_pipeline/` = 0 (salvo `__init__.py` de subpaquetes) |
| Q6.2 | Configurar ruff para enforce: `[tool.ruff.lint].select = ["I"]` ya incluido en Q1 | (config ya lista) | 0h | `ruff check .` ordena imports automaticamente |
| Q6.3 | Ejecutar `ruff check . --fix --select I` para auto-ordenar todos los imports | (todos los archivos) | 0.5h | Todos los imports ordenados: stdlib → terceros → locales |

**Total Q6:** 3.5h

#### Verificacion

```bash
ruff check . --select I  # 0 errores de import order
```

---

## 4. Problemas de Testing (T1-T4)

### T1 — Sin integracion entre tests de pipeline y agents (MEDIA)

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| T1.1 | Crear fixture compartida que configura el pipeline completo + agent system | `tests/conftest.py` (EXTENDER) | 2h | Fixture `full_pipeline` disponible en todos los tests |
| T1.2 | Test de integracion: ejecutar prompt via AgentOrchestrator y via SupervisorAgent, comparar output | `tests/test_agent_pipeline_integration.py` (NUEVO, fusionado con P1.4) | 3h | Output de ambos modos es semanticamente equivalente |
| T1.3 | Test de datos: modo direct y modo agent producen mismos archivos en disco | `tests/test_agent_pipeline_integration.py` (NUEVO) | 2h | `diff -r modules_direct/ modules_agent/` = 0 diferencias |

**Total T1:** 7h

---

### T2 — Sin fixtures compartidas (MEDIA)

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| T2.1 | Inventariar fixtures duplicadas en tests/ (buscar `@pytest.fixture` identicas) | (grep en tests/) | 1h | Lista de fixtures duplicadas |
| T2.2 | Mover fixtures comunes a `conftest.py`: `mock_context`, `mock_ir_project`, `mock_llm_response`, `sample_prompts`, `temp_output_dir` | `tests/conftest.py` (EXTENDER) | 2h | Todos los tests pueden importar fixtures desde conftest |
| T2.3 | Agregar fixture `dashboard_prompt` que devuelve el string de prompt para dashboard | `tests/conftest.py` (MODIFICAR) | 0.5h | `def dashboard_prompt() -> str` |
| T2.4 | Agregar fixture `expected_dashboard_files` con lista de archivos esperados | `tests/conftest.py` (MODIFICAR) | 1h | `def expected_dashboard_files() -> list[Path]` |

**Total T2:** 4.5h

---

### T3 — Sin tests de performance (BAJA)

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| T3.1 | Agregar test benchmark para `Lexer.scan()` con texto de 1000 palabras | `tests/test_lexer_benchmark.py` (NUEVO) | 1.5h | Benchmark reporta ops/sec |
| T3.2 | Agregar test benchmark para `IRBuilder.build()` con arbol de 100 nodos | `tests/test_ir_builder.py` (EXTENDER) | 1.5h | Benchmark reporta tiempo de construccion |
| T3.3 | Agregar test benchmark para `GlobalFeedbackLoop.record_stage()` con 10,000 registros | `tests/test_feedback_benchmark.py` (NUEVO) | 1h | Benchmark reporta throughput |

**Total T3:** 4h

---

### T4 — Sin tests de integracion con LLM real (BAJA)

#### Tareas

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| T4.1 | Agregar fixture condicional `llm_real` que solo se activa si `OPENAI_API_KEY` esta definida | `tests/conftest.py` (EXTENDER) | 1h | Test se salta con `pytest.skip` si no hay API key |
| T4.2 | Test de integracion LLM real: `IntentHandler.handle()` con prompt real contra GPT-4o-mini | `tests/test_llm_integration.py` (NUEVO) | 2h | Test pasa con API key valida, se salta sin ella |
| T4.3 | Test de fallback: `LLMBackend.generate()` falla → `execute_fallback()` se ejecuta correctamente | `tests/test_llm_integration.py` (NUEVO) | 2h | Fallback produce output valido |
| T4.4 | Agregar marcador `pytest.mark.llm` para tests que requieren LLM real | `tests/conftest.py`, `pyproject.toml` (MODIFICAR) | 0.5h | `pytest -m llm` solo ejecuta tests LLM |

**Total T4:** 5.5h

---

## 5. Deuda Tecnica

### 5.1 Tabla Completa de Ejecucion

| ID Ref | Item Deuda | Tareas | Esfuerzo | Prioridad |
|--------|-----------|--------|----------|-----------|
| DT1 | `requirement_decomposer.py` dead code | P2.1, P2.2, P2.3 | 1.5h | Alta |
| DT2 | Dos event buses | P5.1, P5.2, P5.3, P5.4 | 9h | Alta |
| DT3 | LLMCache sin cablear | DT3.1, DT3.2, DT3.3 | 4h | Alta |
| DT4 | ParserGLR mal nombrado | P3.1, P3.2, P3.3 | 2h | Baja |
| DT5 | Sin config ruff/pytest | Q1.1-Q1.4, Q2.1-Q2.3 | 5.5h | Alta |
| DT6 | __init__.py vacios | Q3.1-Q3.4 | 3h | Media |
| DT7 | PipelineMacroCommand duplica | P6.1, P6.2, P6.3 | 4h | Media |

### DT3 — Cablear LLMCache en pipeline stages (ALTA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| DT3.1 | Refactorizar `LLMCache` como servicio singleton con TTL configurable y max_size | `prompt_chain/llm_cache.py` (MODIFICAR) | 1.5h | `LLMCache.get(key)` y `set(key, value)` funcionan con TTL |
| DT3.2 | Integrar cache en `LLMBackend.generate()`: check cache antes de llamar API, store despues | `prompt_chain/llm_backend.py` (MODIFICAR) | 1.5h | `generate()` revisa cache primero |
| DT3.3 | Agregar metricas de cache hit/miss a `MetricsStore` | `metrics_store.py` (MODIFICAR) | 1h | `MetricsStore.record_cache(stage, hit=True/False)` |

**Total DT3:** 4h

#### Verificacion

```bash
# Llamar dos veces con mismo prompt, verificar que la segunda usa cache
pytest tests/test_llm_cache.py -v -k "cache_hit"
```

---

## 6. Riesgos y Cuellos de Botella

### 6.1 R1 — LLM API Rate Limiting (ALTA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| R1.1 | Implementar `CircuitBreaker` con estados: CLOSED → OPEN (fallos > threshold) → HALF_OPEN (timeout) → CLOSED | `circuit_breaker.py` (NUEVO) | 3h | CircuitBreaker abre tras N fallos consecutivos, cierra tras timeout |
| R1.2 | Implementar `ExponentialBackoff` con jitter: `min_backoff=1s`, `max_backoff=60s`, `factor=2`, `jitter=0.1` | `circuit_breaker.py` (NUEVO) | 1.5h | Reintentos siguen secuencia: 1s, 2s, 4s, 8s, ..., 60s max |
| R1.3 | Integrar CircuitBreaker + Backoff en `LLMBackend.generate()` | `prompt_chain/llm_backend.py` (MODIFICAR) | 2h | `generate()` usa circuit breaker antes de llamar API |
| R1.4 | Tests: circuit breaker abre y cierra correctamente, backoff produce delays exponenciales | `tests/test_circuit_breaker.py` (NUEVO) | 3h | Tests unitarios + integracion con mock |

**Total R1:** 9.5h

---

### 6.2 R2 — StateGraph en memoria sin persistencia (MEDIA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| R2.1 | Implementar checkpoint del `StageContext` en SQLite despues de cada stage | `orchestrator.py` (MODIFICAR) | 3h | `StageContext` se persiste a SQLite tras cada `execute()` |
| R2.2 | Agregar `resume(checkpoint_id)` que restaura desde ultimo checkpoint | `orchestrator.py` (MODIFICAR) | 2h | Pipeline se reanuda desde el stage donde fallo |
| R2.3 | Test: crash simulado → resume produce mismo output que ejecucion completa | `tests/test_orchestrator_checkpoint.py` (NUEVO) | 3h | Output de resume = output de ejecucion completa |

**Total R2:** 8h

---

### 6.3 R3 — Sin aislamiento de stages (MEDIA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| R3.1 | Implementar `StageExecutor` con try/except per-stage que captura exception y la registra como StageOutput fallido | `stage_executor.py` (NUEVO) | 3h | Stage que falla produce `StageOutput(success=False, error=...)`, no detiene pipeline |
| R3.2 | Modificar `AgentOrchestrator` para que cada nodo ejecute via `StageExecutor` en lugar de directo | `orchestrator.py` (MODIFICAR) | 2h | Pipeline completo ejecuta incluso con stages fallidos (resultado parcial) |

**Total R3:** 5h

---

### 6.4 R4 — StageSubject race condition (parcial en P4)

Cubierto por P4.1-P4.3.

---

### 6.5 R5 — Sin autenticacion (cubierto en S2-S4)

### 6.6 R6 — Dependencia critica de LangGraph

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| R6.1 | Definir interfaz `GraphBackend` con metodos: `add_node()`, `add_edge()`, `set_entry()`, `set_finish()`, `compile()`, `invoke()` | `graph_backend.py` (NUEVO) | 2h | Interfaz abstracta sin dependencia de LangGraph |
| R6.2 | Implementar `LangGraphBackend(GraphBackend)` que delega en `StateGraph` de LangGraph | `graph_backend.py` (NUEVO) | 2h | `LangGraphBackend` implementa los 6 metodos |
| R6.3 | Migrar `AgentOrchestrator` de usar `StateGraph` directamente a usar `GraphBackend` | `orchestrator.py` (MODIFICAR) | 3h | `AgentOrchestrator` no importa `langgraph` directamente |
| R6.4 | Test: `GraphBackend` mock produce mismo comportamiento que LangGraph real | `tests/test_graph_backend.py` (NUEVO) | 3h | Tests con mock GraphBackend pasan |
| R6.5 | Implementar `GraphvizBackend(GraphBackend)` (opcional, para debugging visual) | `graph_backend.py` (NUEVO, opcional) | 4h | `graph.render()` produce archivo DOT/PNG |

**Total R6:** 10h (14h con GraphvizBackend)

---

### 6.7 Cuellos de Botella de Rendimiento

| ID | Medida | Tareas | Esfuerzo |
|----|--------|--------|----------|
| B1 | Cacheo LLM (LRU + Redis) | DT3.1-DT3.3 + Redis client | 6h |
| B2 | Pooling de conexiones httpx | Configurar `httpx.Client()` como singleton | 1h |
| B3 | Modelos diferenciados (mini vs full) | Config en `LLMBackend` por stage | 2h |

**Total Bottlenecks:** 9h

---

## 7. Mejores Practices SOLID + Arquitectonicas

### 7.1 S — Single Responsibility (feedback_loop.py)

Cubierto por Q4.1-Q4.6 (SRP violation resuelta).

### 7.2 O — Open/Closed (NODE_MAP fijo)

| ID | Tarea | Archivos | Esfuerzo | Depende De | Criterio de Aceptacion |
|----|-------|----------|----------|------------|------------------------|
| OC1 | Crear `PipelineStageRegistry` que carga stages desde config YAML | `stage_registry.py` (NUEVO) | 4h | R6.1 (GraphBackend) | `registry = PipelineStageRegistry("stages.yaml")` carga stages sin importarlos manualmente |
| OC2 | Crear `stages.yaml` con definicion de los 10 stages actuales | `stages.yaml` (NUEVO) | 1h | OC1 | YAML lista nombre, clase, descripcion, enabled |
| OC3 | Migrar `AgentOrchestrator._build()` para que use `PipelineStageRegistry` en lugar de `NODE_MAP` | `orchestrator.py` (MODIFICAR) | 3h | OC1 | `NODE_MAP` se elimina o queda como fallback |
| OC4 | Test: agregar stage via YAML sin modificar codigo fuente | `tests/test_stage_registry.py` (NUEVO) | 3h | OC2 | Nuevo stage aparece en pipeline sin tocar Python |

**Total OCP:** 11h

---

### 7.3 I — Interface Segregation (PipelineStage monolifico)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| ISP1 | Definir `Analyzable` interface (metodo `analyze()`) | `base_stage.py` (MODIFICAR) | 1h | Solo stages que analizan implementan `Analyzable` |
| ISP2 | Definir `Plannable` interface (metodo `reflect_and_plan()`) | `base_stage.py` (MODIFICAR) | 1h | Solo stages que planifican implementan `Plannable` |
| ISP3 | Definir `Executable` interface (metodo `act()`) | `base_stage.py` (MODIFICAR) | 1h | Todos los stages implementan `Executable` |
| ISP4 | Refactor `PipelineStage` para que herede solo `Executable` y opcionalmente `Analyzable` y `Plannable` | `base_stage.py` (MODIFICAR), 10 subclasses (MODIFICAR) | 4h | Cada stage implementa solo las interfaces que necesita |
| ISP5 | Actualizar `execute()` para que checkee `isinstance(self, Analyzable)` antes de llamar analyze | `base_stage.py` (MODIFICAR) | 1h | `execute()` usa `hasattr` pattern o `isinstance` check |

**Total ISP:** 8h

---

### 7.4 Inmutabilidad de Datos (StageContext mutable)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| INM1 | Refactor `StageContext` a `@dataclass(frozen=True)` | `state_models.py` (MODIFICAR) | 1h | `StageContext(...)` funciona, `ctx.stage = X` TypeError |
| INM2 | Agregar `StageContext.with_update()` que devuelve nueva instancia con campo modificado | `state_models.py` (MODIFICAR) | 1.5h | `new_ctx = ctx.with_update(input_data=new_data)` sin mutar original |
| INM3 | Actualizar nodos del pipeline para que usen `with_update()` en lugar de mutacion directa | `nodes/*.py` (MODIFICAR, ~10 archivos) | 3h | `git grep "ctx\.input_data = "` = 0 |
| INM4 | Actualizar `AgentOrchestrator._make_node()` para que use `with_update()` | `orchestrator.py` (MODIFICAR) | 1h | `updated = ctx.with_update(input_data=output.output_data)` |

**Total INM:** 6.5h

#### Verificacion

```bash
python -c "
from agentic_pipeline.state_models import StageContext, Stage
ctx = StageContext(stage=Stage.INTENT, input_data='hola')
try:
    ctx.stage = Stage.PREPROCESSOR
    assert False, 'should be frozen'
except TypeError:
    print('OK: frozen')

new_ctx = ctx.with_update(input_data='mundo')
print(f'OK: new input={new_ctx.input_data}, old={ctx.input_data}')
"
```

---

### 7.5 Graceful Degradation (modo offline sin LLM)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| GD1 | Implementar `OfflineLexer` que usa solo DFA/regex (sin LLM) en PerceptionUnit | `nodes/perception_unit.py` (MODIFICAR) | 2h | Sin LLM, PerceptionUnit clasifica intent via rules |
| GD2 | Implementar `OfflinePlanner` que usa solo GoalTreePlanner heuristico | `nodes/reasoning_engine.py` (MODIFICAR) | 2h | Sin LLM, planner descompone tareas heuristicamente |
| GD3 | Agregar flag `--offline` en CLI y propagar a `PipelineConfig` | `config.py` (MODIFICAR), CLI | 2h | `python agentic -p "texto" --offline` funciona sin API key |
| GD4 | Documentar capacidades offline (que stages funcionan, cuales no) | `docs/offline_mode.md` (NUEVO) | 1h | Lista clara de stages con/sin LLM |

**Total GD:** 7h

---

## 8. Seguridad

### 8.1 Sanitizacion de codigo generado (CRITICA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| S1.1 | Integrar `bandit` como stage del pipeline: `BanditScanner` como `StageObserver` que analiza archivos generados | `security/bandit_scanner.py` (NUEVO) | 3h | Archivos generados pasan por bandit, resultados en StageOutput.metadata |
| S1.2 | Agregar `SecurityScanner` a `ValidatorPipeline` (Chain of Responsibility) | `nodes/validator.py` (MODIFICAR) | 2h | ValidatorPipeline incluye SecurityScanner como eslabon final |
| S1.3 | Definir politicas de seguridad: bloquear generacion de `eval()`, `exec()`, `os.system()`, `subprocess.call()`, `pickle.loads()`, `__import__()` | `security/policies.py` (NUEVO) | 1.5h | Scanner rechaza archivos con这些 patrones |
| S1.4 | Tests: generar codigo con vulnerabilidad conocida → SecurityScanner lo detecta | `tests/test_security_scanner.py` (NUEVO) | 2h | Scanner detecta `eval()` en codigo generado |

**Total S1:** 8.5h

---

### 8.2 Autenticacion (ALTA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| S2.1 | Agregar `AuthService` con soporte API Key + JWT | `security/auth_service.py` (NUEVO) | 4h | `AuthService.authenticate("key")` valida contra config |
| S2.2 | Integrar auth en FastAPI wrapper (depende de Q8 FastAPI) | `api/main.py` (NUEVO, post-FastAPI) | 2h | Endpoint `/v1/compile` requiere header `Authorization: Bearer ...` |

**Total S2:** 6h

---

### 8.3 Auditoria (ALTA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| S3.1 | Crear `AuditObserver` (StageObserver) que registra cada compilacion en log append-only JSON | `observers/audit_observer.py` (NUEVO, post-Q4) | 2h | Cada `on_event()` escribe JSON inmutable |
| S3.2 | Agregar `audit.log` rotacion: max 100MB, compress old | `observers/audit_observer.py` (MODIFICAR) | 1h | Archivo rota sin perder datos |

**Total S3:** 3h

---

### 8.4 Rate Limiting (MEDIA)

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| S4.1 | Implementar `TokenBucket` rate limiter: capacidad, refill rate, burst | `security/token_bucket.py` (NUEVO) | 2h | `bucket.consume(1)` = True si hay tokens, False si no |
| S4.2 | Integrar rate limiter en LLMBackend (proteger API calls) | `prompt_chain/llm_backend.py` (MODIFICAR) | 1h | `generate()` chequea rate limiter antes de llamar |

**Total S4:** 3h

---

## 9. Escalabilidad y Rendimiento

### 9.1 Paralelizacion de Stages

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| E1.1 | Identificar stages paralelizables: Synthesis + UI pueden ejecutarse simultaneamente | (analisis) | 1h | Lista documentada de stages paralelizables |
| E1.2 | Implementar `ParallelStageExecutor` que ejecuta stages independientes en `asyncio.gather()` | `stage_executor.py` (EXTENDER) | 4h | Synthesis y UI se ejecutan en paralelo, reduciendo latencia ~40% |
| E1.3 | Agregar config `pipeline.parallel_stages` en `PipelineConfig` | `config.py` (MODIFICAR) | 0.5h | `config.pipeline.parallel_stages = True` |

**Total E1:** 5.5h

---

### 9.2 Modelos LLM Diferenciados

| ID | Tarea | Archivos | Esfuerzo | Criterio de Aceptacion |
|----|-------|----------|----------|------------------------|
| E2.1 | Agregar `stage_model_map` en config: `{stage: model_name}` | `config.py` (MODIFICAR) | 1h | `config.stage_models.preprocessor = "gpt-4o-mini"` |
| E2.2 | Modificar `LLMBackend` para aceptar `model` override por llamada | `prompt_chain/llm_backend.py` (MODIFICAR) | 1.5h | `generate(prompt, model="gpt-4o-mini")` |
| E2.3 | Mapear stages a modelos: preprocess→mini, intent→4o, plan→reasoning→4o, generate→4o, verify→4o, format→mini | `config.py` (MODIFICAR) | 0.5h | Mapa completo en config |

**Total E2:** 3h

---

## 10. Mapa de Ruta Integrado

### Sprint 0: Fundaciones de Calidad (12.5h)

```
Prioridad maxima: sin esto, no hay CI/CD ni garantia de calidad.

Q1 (3.5h)  ─── ruff config + --fix
Q2 (2h)    ─── pytest config
Q6 (3.5h)  ─── imports consistentes
P2 (1.5h)  ─── eliminar dead code
P3 (2h)    ─── renombrar ParserGLR
```

### Sprint 1: Deuda Tecnica Arquitectonica (31h)

```
P4 (4h)    ─── thread-safe StageSubject
P5 (9h)    ─── unificar event buses
P6 (4h)    ─── PipelineMacroCommand refactor
DT3 (4h)   ─── LLMCache wiring
Q3 (3h)    ─── __init__.py exports
Q4 (6h)    ─── SRP feedback_loop.py
Q5 (4h)    ─── type hints
```

### Sprint 2: SOLID + Resiliencia (35h)

```
ISP (8h)   ─── Interface Segregation (Analyzable, Plannable, Executable)
INM (6.5h) ─── StageContext frozen
R1 (9.5h)  ─── Circuit Breaker + Backoff
R3 (5h)    ─── StageExecutor aislamiento
GD (7h)    ─── Graceful degradation (offline mode)
```

### Sprint 3: Seguridad + Integracion (33h)

```
S1 (8.5h)  ─── Sanitizacion codigo (bandit)
S2 (6h)    ─── Autenticacion (FastAPI + JWT)
S3 (3h)    ─── Auditoria
S4 (3h)    ─── Rate Limiting
T1 (7h)    ─── Tests integracion agent-pipeline
T2 (4.5h)  ─── Fixtures compartidas
```

### Sprint 4: Rendimiento + Observabilidad (25h)

```
R6 (10h)   ─── GraphBackend abstraction
OC (11h)   ─── PipelineStageRegistry (YAML)
E1 (5.5h)  ─── Paralelizacion stages
E2 (3h)    ─── Modelos LLM diferenciados
```

### Sprint 5: Backlog (20h)

```
T3 (4h)    ─── Benchmarks
T4 (5.5h)  ─── Tests LLM real
R2 (8h)    ─── Checkpoint/resume
```

---

## 11. Presupuesto Total

### 11.1 Resumen por Categoria

| Categoria | Horas | % |
|-----------|-------|---|
| Problemas Arquitectonicos (P1-P6) | 40.5h | 32% |
| Problemas de Calidad (Q1-Q6) | 22h | 17% |
| Problemas de Testing (T1-T4) | 21h | 17% |
| Deuda Tecnica (DT1-DT7) | 29h | 23% |
| Riesgos (R1-R6) | 32.5h | 26% |
| SOLID + Inmutabilidad (ISP, INM, OC) | 25.5h | 20% |
| Seguridad (S1-S4) | 20.5h | 16% |
| Rendimiento (E1, E2, B1-B3) | 17.5h | 14% |

> **Nota:** Las categorias se solapan (ej. P5 cuenta como Arquitectonico Y Deuda). El total unico es ~127h.

### 11.2 Por Sprint

| Sprint | Horas | Semanas | Depende De |
|--------|-------|---------|------------|
| Sprint 0: Fundaciones | 12.5h | 0.5 | — |
| Sprint 1: Deuda Arquitectonica | 31h | 1.5 | Sprint 0 |
| Sprint 2: SOLID + Resiliencia | 35h | 1.5 | Sprint 1 |
| Sprint 3: Seguridad + Tests | 33h | 1.5 | Sprint 2 |
| Sprint 4: Rendimiento | 25h | 1 | Sprint 3 |
| Sprint 5: Backlog | 20h | 1 | Sprint 4 |
| **Total** | **~156.5h** | **~7 semanas** | |

### 11.3 Presupuesto por Tipo de Cambio

| Tipo | Horas | % |
|------|-------|---|
| Archivos Nuevos | 55h | 35% |
| Archivos Existentes (MODIFICAR) | 72h | 46% |
| Archivos a Eliminar | 1.5h | 1% |
| Tests (NUEVOS + EXTENDER) | 28h | 18% |

---

## Apendice A: Indice de Problemas vs. Tareas

| Problema | Tarea(s) | Sprint | Estado |
|----------|----------|--------|--------|
| P1 — Agentes desconectados | P1.1, P1.2, P1.3, P1.4 | 3 | Pendiente |
| P2 — Dead code | P2.1, P2.2, P2.3 | 0 | Pendiente |
| P3 — ParserGLR rename | P3.1, P3.2, P3.3 | 0 | Pendiente |
| P4 — Thread safety | P4.1, P4.2, P4.3 | 1 | Pendiente |
| P5 — Dos event buses | P5.1, P5.2, P5.3, P5.4 | 1 | Pendiente |
| P6 — Duplicated logic | P6.1, P6.2, P6.3 | 1 | Pendiente |
| Q1 — Sin ruff config | Q1.1, Q1.2, Q1.3, Q1.4 | 0 | Pendiente |
| Q2 — Sin pytest config | Q2.1, Q2.2, Q2.3 | 0 | Pendiente |
| Q3 — __init__ vacios | Q3.1, Q3.2, Q3.3, Q3.4 | 1 | Pendiente |
| Q4 — SRP violation | Q4.1, Q4.2, Q4.3, Q4.4, Q4.5, Q4.6 | 1 | Pendiente |
| Q5 — Type hints | Q5.1, Q5.2, Q5.3 | 1 | Pendiente |
| Q6 — Import consistency | Q6.1, Q6.2, Q6.3 | 0 | Pendiente |
| T1 — Sin integracion tests | T1.1, T1.2, T1.3 | 3 | Pendiente |
| T2 — Sin fixtures | T2.1, T2.2, T2.3, T2.4 | 3 | Pendiente |
| T3 — Sin benchmarks | T3.1, T3.2, T3.3 | 5 | Pendiente |
| T4 — Sin LLM real tests | T4.1, T4.2, T4.3, T4.4 | 5 | Pendiente |
| DT3 — LLMCache sin cablear | DT3.1, DT3.2, DT3.3 | 1 | Pendiente |
| R1 — Rate limiting | R1.1, R1.2, R1.3, R1.4 | 2 | Pendiente |
| R2 — Sin checkpoint | R2.1, R2.2, R2.3 | 5 | Pendiente |
| R3 — Sin aislamiento | R3.1, R3.2 | 2 | Pendiente |
| R6 — LangGraph lock-in | R6.1, R6.2, R6.3, R6.4, R6.5 | 4 | Pendiente |
| SOLID OCP — NODE_MAP fijo | OC1, OC2, OC3, OC4 | 4 | Pendiente |
| SOLID ISP — Monolitico | ISP1, ISP2, ISP3, ISP4, ISP5 | 2 | Pendiente |
| INM — Context mutable | INM1, INM2, INM3, INM4 | 2 | Pendiente |
| GD — Graceful degradation | GD1, GD2, GD3, GD4 | 2 | Pendiente |
| S1 — Sanitizacion | S1.1, S1.2, S1.3, S1.4 | 3 | Pendiente |
| S2 — Autenticacion | S2.1, S2.2 | 3 | Pendiente |
| S3 — Auditoria | S3.1, S3.2 | 3 | Pendiente |
| S4 — Rate limiting | S4.1, S4.2 | 3 | Pendiente |
| E1 — Paralelizacion | E1.1, E1.2, E1.3 | 4 | Pendiente |
| E2 — Modelos diff | E2.1, E2.2, E2.3 | 4 | Pendiente |

---

*Documento generado a partir del reporte de arquitectura 001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md. Fecha: 2026-06-18.*
