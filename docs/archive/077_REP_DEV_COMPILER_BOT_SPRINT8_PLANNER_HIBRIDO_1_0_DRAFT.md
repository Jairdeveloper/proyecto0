---
id: 077
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0
status: IMPLEMENTED
tags:
  - sprint
  - planner
  - hybrid
  - heuristic
  - llm
  - task-graph
  - plan-executor
  - rollback
summary: Reporte Sprint 8 — Planner Híbrido con TaskGraph, HeuristicPlanner, HybridPlanner, PlanExecutor y rollback
keywords:
  - planner
  - heuristic
  - llm
  - task-graph
  - topological-sort
  - plan-executor
  - rollback
  - template-method
  - observer
  - command
changelog:
  - version: 1.0
    date: 2026-06-14
    description: Documento inicial del Sprint 8
---

# 077_REP_DEV_COMPILER_BOT_SPRINT8_PLANNER_HIBRIDO_1_0_DRAFT

## Resumen

Sprint 8 completado. Implementación del Planner Híbrido (etapa 7 del pipeline RECPL v2.0) con modelo Task/TaskGraph, HeuristicPlanner para casos simples (≤5 tareas), HybridPlanner como PipelineStage, PlanExecutor con Template Method y Observer, TaskCommand con execute/undo, y rollback de comandos.

## Logros

- **Task model** (`nodes/planner.py`): modelo Pydantic con `id`, `description`, `dependencies`, `state` (PENDING/READY/RUNNING/DONE/FAILED/BLOCKED), `can_run(done_ids)` para chequeo de dependencias

- **TaskGraph** (`nodes/planner.py`): grafo dirigido con `add_task()`, `get_task()`, `topological_order()` vía `graphlib.TopologicalSorter`, `has_cycle()`, `ready_tasks(done_ids)` que excluye tareas ya completadas

- **HeuristicPlanner** (`nodes/planner.py`): planificador determinístico con `plan()` (orden topológico), `group_by_layer()` (config/domain/data/api/ui/infra), `estimate_complexity()` (simple ≤3, moderate ≤5, complex >5)

- **HybridPlanner** (`nodes/planner.py`): PipelineStage de 5 pasos (receive_mission → analyze → reflect_and_plan → act → learn_and_improve) con delegación heurística; construye tareas desde árbol IR, agrupa por capa, genera commands

- **TaskCommand pattern** (`nodes/task_command.py`): `FileCreateCommand` y `ScaffoldCommand` con `execute()` y `undo()` para rollback transaccional

- **PlanExecutor Template Method** (`nodes/plan_executor.py`): `PlanExecutor` con `execute()` (template method con pre/post/on_error hooks), `PlanObserver` logging de cambios de estado, `HeuristicExecutor` para ejecución concreta

- **Conexión en orquestador**: pipeline `input → preprocessor → lexer → parser → semantic_analyzer → ir_generator → planner → output`

- **49 nuevos tests**: 13 HeuristicPlanner, 9 HybridPlanner, 10 PlanExecutor, 7 Rollback commands, + cobertura existing

## Problemas encontrados y soluciones

| Problema | Solución |
|----------|----------|
| `ready_tasks({"a"})` retornaba tarea "a" (sin dependencias) además de "b" — porque `can_run()` es vacuously true para tareas sin dependencias, y no se filtraba por `done_ids` | Agregar `t.id not in done_ids` al filtro de `ready_tasks()` |
| `test_act_empty` y `test_act_with_ir_tree` usaban `output.output_data["task_count"]` pero `task_count` está en `output.metrics` | Cambiar a `output.metrics["task_count"]` |

## Archivos creados/modificados

| Archivo | Cambio |
|---------|--------|
| `nodes/planner.py` | Creado — Task, TaskGraph, HeuristicPlanner, HybridPlanner (268 líneas) |
| `nodes/task_command.py` | Creado — FileCreateCommand, ScaffoldCommand (108 líneas) |
| `nodes/plan_executor.py` | Creado — PlanObserver, PlanExecutor, HeuristicExecutor (108 líneas) |
| `tests/test_heuristic_planner.py` | Creado — 13 tests |
| `tests/test_llm_planner.py` | Creado — 9 tests |
| `tests/test_plan_executor.py` | Creado — 10 tests |
| `tests/test_rollback.py` | Creado — 7 tests |
| `orchestrator.py` | Modificado — conectado planner node |

## Tests

```
333 passed in 1.59s
```

- **Task/TaskGraph**: 13 tests (default state, can_run, topological order, cycle detection, ready_tasks)
- **HybridPlanner**: 9 tests (receive_mission, analyze, reflect_and_plan, act, execute full flow, layers, complexity, learn_and_improve, commands)
- **PlanExecutor**: 10 tests (execute success/failure, rollback, observer notification, pause/resume)
- **Rollback commands**: 7 tests (FileCreateCommand execute/undo, ScaffoldCommand execute/undo, rollback idempotent)
- **Sprints anteriores**: 284 tests sin cambios

## Pipeline actual

```
input → preprocessor → lexer → parser → semantic_analyzer → ir_generator → planner → output
```

## Riesgos

- HybridPlanner.act() no tiene implementación LLM real — solo delegación heurística (requiere API key + integración openai/langchain)
- PlanExecutor es abstracto — HeuristicExecutor es la única implementación concreta
- TaskCommand undo() asume que el archivo no ha sido modificado externamente — riesgo de race condition
- No hay persistencia de planes entre sesiones — TaskGraph es reconstruido en cada act()

## Próximos pasos

- Sprint 9: Synthesis Multi-Target (react, nestjs, prisma, docker)
- Agregar integración LLM real al HybridPlanner
- Implementar persistencia de TaskGraph (serialización)
- Agregar más validaciones al Task (target type checking, dependency cycles reporting)
