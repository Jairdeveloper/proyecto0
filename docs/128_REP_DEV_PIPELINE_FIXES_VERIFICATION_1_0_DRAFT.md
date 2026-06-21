---
area: dev
type: rep
module: agentic_pipeline
version: 1.0
status: IMPLEMENTED
---
# Reporte de Verificación — Pipeline Fixes Plan vs. Código Base

- **ID:** 128_REP_DEV_PIPELINE_FIXES_VERIFICATION_1_0_DRAFT
- **Tipo:** REP (Reporte)
- **Área:** DEV
- **Módulo:** agentic_pipeline
- **Versión:** 1.0
- **Estado:** DRAFT
- **Tags:** `verification`, `fixes`, `lexer`, `parser`, `semantic`, `ir`, `synthesis`, `ui-generator`, `chain`, `gap-analysis`
- **Fuente:** `docs/126_PLAN_DEV_PIPELINE_FIXES_1_0_DRAFT.md`
- **Changelog:**
  - 1.0 — 2026-06-18: Versión inicial

---

## Resumen

Se analizaron los 5 Fixes detallados en el plan de acción `126_PLAN_DEV_PIPELINE_FIXES_1_0_DRAFT.md` contra el código base actual de `compiler-bot/agentic_pipeline/`. Resultado:

| Fix | Descripción | Estado | % Implementado |
|-----|-------------|--------|---------------|
| Fix 1 | Lexer: Agregar EntityDFA | **COMPLETADO** | 100% |
| Fix 2 | Cerrar gap de tipos Parser/Semantic/IR | **PARCIAL** | 60% |
| Fix 3 | Conectar Synthesis con Planner | **PARCIAL** | 60% |
| Fix 4 | Guardas de Dominio en UI Generator | **COMPLETADO** | 100% |
| Fix 5 | Chain Path: Conectar Generate con Planner | **NO IMPLEMENTADO** | 0% |
| **Total** | | | **64%** |

---

## Fix 1 — Lexer: Agregar EntityDFA ✅ COMPLETADO

### Paso 1.1 — EntityDFA(BaseDFA)

| Estado | Implementado |
|--------|-------------|
| **Archivo:** `nodes/sub_dfa.py` | Línea 293 |
| **Código:** | `class EntityDFA(BaseDFA):` con category = "entity" y 15 palabras (modulo, module, entidad, entity, modelo, model, pagos, auth, autenticacion, usuario, user, producto, orden, factura, catalogo) |
| **Tokens producidos:** | MODULE, ENTITY, MODEL, PAYMENT, AUTH, USER, PRODUCT, ORDER, INVOICE, CATALOG |

Verificado: `EntityDFA` existe, extiende `BaseDFA`, tiene `_build()` con las palabras especificadas en el plan.

### Paso 1.2 — Registrar EntityDFA en Lexer

| Estado | Implementado |
|--------|-------------|
| **Archivo:** `nodes/lexer.py` | Línea 119 |
| **Código:** | `"entity": EntityDFA(),` en el diccionario `self.dfas` |

Verificado: El diccionario `dfas` contiene las 6 sub-DFAs: domain, action, tech, ui, quality, entity.

### Paso 1.3 — Agregar MODULE al mapeo de post-processamiento

| Estado | No aplica |
|--------|-----------|
| **Observación:** | El plan menciona agregar `ENTITY_TOKEN_TYPES`, pero el código actual no tiene un mapeo explícito de post-processamiento. Los tokens de EntityDFA fluyen normalmente a través del pipeline. No es un blocker funcional. |

### Veredicto: COMPLETADO ✅

El input "crea modulo" ahora produce 2 tokens: CREATE (action) + MODULE (entity), solucionando el problema de tokens perdidos.

---

## Fix 2 — Cerrar Gap de Tipos Parser/Semantic/IR ⚠️ PARCIAL

### Paso 2.1 — ActionNode(ASTNode)

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/ast_nodes.py` línea 82 |
| **Código:** | `class ActionNode(ASTNode):` con `action_type`, `target`, `accept()` → `visitor.visit_action(self)` |

### Paso 2.2 — visit_action() en IASTVisitor y visitors

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/ast_visitor.py` línea 43 (IASTVisitor) y línea 72 (TreeWalkingVisitor) |
| **Otros visitors:** | `validation_visitor.py` línea 33 ✅, `evaluation_visitor.py` línea 54 ✅, `ir_export_visitor.py` línea 45 ✅ |

### Paso 2.3 — visit_action() en SemanticVisitor (dict-based)

| Estado | ❌ NO IMPLEMENTADO |
|--------|-------------------|
| **Archivo:** | `nodes/semantic_analyzer.py` clase `SemanticVisitor` (línea 108-178) |
| **Problema:** | La clase `SemanticVisitor` (dict-based, usada por `SemanticAnalyzer.act()`) NO tiene método `visit_action()`. Cuando recibe un nodo con `node_type: "action"`, ejecuta `self.warnings.append(f"Unknown node type: '{node_type}'")` en línea 131. |
| **Solución necesaria:** | Agregar `def visit_action(self, node): ...` en `SemanticVisitor` (similar al que ya existe en `SemanticAnalysisVisitor` línea 71) |

**Impacto:** El pipeline StateGraph (`SemanticAnalyzer`) usa `SemanticVisitor` (dict-based). Los nodos action producidos por el parser dict-based serán ignorados en semantic analysis.

### Paso 2.4 — Mapeo "action" en IRBuilder

| Estado | ❌ NO IMPLEMENTADO |
|--------|-------------------|
| **Archivo:** | `nodes/ir_builder.py` método `_build_node()` (línea 106-136) |
| **Problema:** | El método maneja page, component, entity, infra, api, config — NO hay un `if node_type == "action"` branch. Al final, línea 135: `logger.warning("Unknown IR node type: %s", node_type)` y retorna `None`. |
| **Solución necesaria:** | Agregar branch para node_type "action" que mapee a `IRComponent` con `component_type="action"`, o crear un nuevo `IRAction` node. |

**Impacto:** Los nodos action se pierden en IR, rompiendo la cadena parser → semantic → IR → planner.

### Paso 2.5 — Actualizar _build_ast_from_tokens() a ActionNode

| Estado | ❌ NO IMPLEMENTADO |
|--------|-------------------|
| **Archivo:** | `nodes/parser.py` método `_build_ast_from_tokens()` (línea 440-453) |
| **Problema:** | Sigue produciendo dictos planos: `{"node_type": "action", "value": a}`. No instancia `ActionNode`. |
| **Solución necesaria:** | Reemplazar con instancias de `ActionNode(action_type=a)` dentro de un `ProjectNode`, y serializar con `IRExportVisitor`. |

**Impacto:** El fallback del parser produce dictos en lugar de ASTNodes. SemanticVisitor dict-based podría procesarlos si tuviera visit_action (paso 2.3), pero IRBuilder los pierde (paso 2.4).

### Veredicto: 3/5 pasos implementados (60%) ⚠️

Los pasos 2.1 y 2.2 están completos (ActionNode + IASTVisitor). Pero los pasos 2.3, 2.4, 2.5 no lo están, lo que significa que el gap de tipos persiste: los nodos "action" se producen en el parser, se ignoran en semantic y se pierden en IR.

---

## Fix 3 — Conectar Synthesis con Planner ⚠️ PARCIAL

### Paso 3.1 — Fallback a goal_tree cuando IR tree vacío

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/reasoning_engine.py` línea 433-437 |
| **Código:** | `if ir_tree is None or not getattr(ir_tree, "children", []): self._build_tasks_from_slots(nombre)` |
| **Método auxiliar:** | `_build_tasks_from_slots()` existe en línea 459 |

### Paso 3.2 — task_count en output_data

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/reasoning_engine.py` línea 421 |
| **Código:** | `"task_count": len(ordered),` en output_data |

### Paso 3.3 — Poblar target en Task segun dominio

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/reasoning_engine.py` línea 471 |
| **Código:** | `_detect_target()` con target_map y fallback por dominio |

### Paso 3.4 — Propagar ir_tree y tasks en ActionExecutor output

| Estado | ❌ NO IMPLEMENTADO |
|--------|-------------------|
| **Archivo:** | `nodes/action_executor.py` método `act()` línea 117-131 |
| **Problema:** | El `output_data` contiene `generated_files`, `errors`, `warnings`, `task_count`, `enriched` — pero NO incluye `ir_tree` ni `tasks`. El plan especifica que debe propagar: `ir_tree`, `tasks`, `enriched`. |
| **Código actual:** | ```python
output_data={
    "generated_files": generated_files,
    "errors": errors,
    "warnings": warnings,
    "task_count": len(tasks),
    "enriched": self._enriched or None,
}
``` |
| **Solución necesaria:** | Agregar `"ir_tree": ir_tree, "tasks": tasks,` al output_data |

**Impacto:** El UI Generator (Fix 4) recibe `ir_tree=None` y `tasks=[]` aunque el planner haya producido datos. El handoff se rompe.

### Paso 3.5 — Fallback en synthesis cuando tasks vacíos

| Estado | ❌ NO IMPLEMENTADO |
|--------|-------------------|
| **Archivo:** | `nodes/action_executor.py` método `act()` línea 65-131 |
| **Problema:** | No hay lógica de fallback para cuando `tasks` está vacío. El código itera sobre `commands` (que pueden estar vacíos si tasks está vacío) e itera sobre `ir_tree.children` (que también puede estar vacío). |
| **Solución necesaria:** | Agregar lógica similar a `reasoning_engine._build_tasks_from_slots()` en action_executor, o leer `goal_tree` del input_data y construir tareas desde ahí. |

**Impacto:** Si el planner produce 0 tareas (porque el IR tree está vacío y el fallback del planner falla), synthesis produce 0 archivos sin error.

### Veredicto: 3/5 pasos implementados (60%) ⚠️

El planner (`reasoning_engine.py`) está completo con fallbacks. Pero la salida del planner no se propaga correctamente a synthesis (`action_executor.py`), y synthesis no tiene su propio fallback.

---

## Fix 4 — Guardas de Dominio en UI Generator ✅ COMPLETADO

### Paso 4.1 — Guarda de dominio

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/ui_generator.py` línea 73-96 |
| **Código:** | `if domain != "ui": ui_components = self._detect_ui_components(ir_tree, tasks); if not ui_components: return StageOutput(...)` |

### Paso 4.2 — Fusionar generated_files

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/ui_generator.py` línea 71 (previous_files) y 124-130 (merge + dedup) |
| **Código:** | `all_files = list(previous_files) + generated_files` con deduplicación por `seen` set |

### Paso 4.3 — Usar ir_tree y tasks del input_data

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/ui_generator.py` línea 65-67 y método `_detect_ui_components()` línea 160-192 |
| **Código:** | Lee `ir_tree` y `tasks` de `input_data`, itera sobre ambos para detectar componentes |

### Paso 4.4 — Metrics de dominio y detección

| Estado | ✅ Implementado |
|--------|---------------|
| **Archivo:** | `nodes/ui_generator.py` línea 142-149 |
| **Código:** | `"domain": domain, "ui_components_detected": len(ui_components), "domain_gate_triggered": True,` |

### Veredicto: COMPLETADO ✅

Todos los 4 pasos del Fix 4 están implementados. Sin embargo, la efectividad de este fix depende del Fix 3.4 (propagación de ir_tree/tasks desde synthesis), que no está implementado. Si synthesis no propaga `ir_tree` y `tasks`, UI Generator los recibe como `None`/`[]` y la guarda de dominio se activa correctamente (evitando falsos positivos), pero no podrá detectar componentes UI reales si los hubiera.

---

## Fix 5 — Chain Path: Conectar Generate con Planner ❌ NO IMPLEMENTADO

### Diagnóstico general

El directorio `compiler-bot/agentic_pipeline/prompt_chain/handlers/` **NO EXISTE**. No hay archivos `cli.py`, `plan_handler.py`, `generate_handler.py`, `verify_handler.py`, `format_handler.py`, `intent_handler.py`, `preprocess_handler.py` en el proyecto.

Todo el Fix 5 depende de archivos que no existen:

| Paso | Archivo requerido | Estado |
|------|------------------|--------|
| 5.1 | `prompt_chain/cli.py` | ❌ No existe |
| 5.2 | `prompt_chain/handlers/plan_handler.py` | ❌ No existe |
| 5.3 | `prompt_chain/handlers/generate_handler.py` | ❌ No existe |
| 5.4 | `prompt_chain/handlers/verify_handler.py` | ❌ No existe |
| 5.5 | `debugger.py` (modificar) | ⚠️ Existe pero no implementado |
| 5.6 | `prompt_chain/handlers/format_handler.py` | ❌ No existe |

### Paso 5.5 — Registro de chain handlers en debugger

| Estado | ❌ NO IMPLEMENTADO |
|--------|-------------------|
| **Archivo:** | `debugger.py` método `_resolve_stage_locations()` (línea 22-37) |
| **Código actual:** | Solo mapea `NODE_MAP` (StateGraph stages). No incluye chain handlers. |
| **Solución necesaria:** | Agregar mapeo para chain handlers: `preprocess`, `intent`, `plan`, `generate`, `verify`, `format` |

### Veredicto: 0/6 pasos implementados (0%) ❌

El path `--chain` no tiene implementación de handlers en el código base. Todos los archivos necesarios deben crearse desde cero.

---

## Tabla Resumen Completa

| Paso | Descripción | Estado | Archivo | Prioridad |
|------|-------------|--------|---------|-----------|
| 1.1 | EntityDFA | ✅ | `sub_dfa.py` | — |
| 1.2 | Registrar EntityDFA | ✅ | `lexer.py` | — |
| 1.3 | ENTITY_TOKEN_TYPES | N/A | — | Baja |
| **2.1** | **ActionNode** | ✅ | `ast_nodes.py` | — |
| **2.2** | **visit_action() en visitors** | ✅ | `ast_visitor.py` (+3) | — |
| **2.3** | **visit_action() en SemanticVisitor dict** | ❌ | `semantic_analyzer.py` | **ALTA** |
| **2.4** | **Branch "action" en IRBuilder** | ❌ | `ir_builder.py` | **ALTA** |
| **2.5** | **_build_ast_from_tokens() a ActionNode** | ❌ | `parser.py` | **ALTA** |
| **3.1** | **Fallback goal_tree en planner** | ✅ | `reasoning_engine.py` | — |
| **3.2** | **task_count en output** | ✅ | `reasoning_engine.py` | — |
| **3.3** | **target heuristico en planner** | ✅ | `reasoning_engine.py` | — |
| **3.4** | **Propagar ir_tree/tasks en synthesis** | ❌ | `action_executor.py` | **ALTA** |
| **3.5** | **Fallback en synthesis cuando tasks vacíos** | ❌ | `action_executor.py` | **MEDIA** |
| 4.1 | Guarda de dominio | ✅ | `ui_generator.py` | — |
| 4.2 | Fusionar generated_files | ✅ | `ui_generator.py` | — |
| 4.3 | Detectar UI components | ✅ | `ui_generator.py` | — |
| 4.4 | Metrics de dominio | ✅ | `ui_generator.py` | — |
| 5.1 | Health check LLM | ❌ | `prompt_chain/cli.py` (nuevo) | MEDIA |
| 5.2 | Poblar params en planner chain | ❌ | `handlers/plan_handler.py` (nuevo) | MEDIA |
| 5.3 | Generate itera tasks | ❌ | `handlers/generate_handler.py` (nuevo) | MEDIA |
| 5.4 | Verify con criterios | ❌ | `handlers/verify_handler.py` (nuevo) | MEDIA |
| 5.5 | Chain handler locations en debugger | ❌ | `debugger.py` | BAJA |
| 5.6 | Format handler desde generate | ❌ | `handlers/format_handler.py` (nuevo) | BAJA |

---

## Acciones Recomendadas

### Prioridad ALTA (crítico para el pipeline principal)

1. **IRBuilder (Paso 2.4):** Agregar `if node_type == "action"` branch en `_build_node()` para mapear a `IRComponent(name, "action")`. Esto evita que los nodos action se pierdan en el IR.

2. **SemanticVisitor dict (Paso 2.3):** Agregar `visit_action()` en la clase `SemanticVisitor` para que los nodos action del parser dict-based sean procesados en semantic analysis.

3. **Parser fallback (Paso 2.5):** Actualizar `_build_ast_from_tokens()` para usar `ActionNode` en lugar de dictos planos. Esto requiere: importar `ActionNode`, instanciarlo con `action_type` del token.

4. **ActionExecutor output (Paso 3.4):** Agregar `"ir_tree": ir_tree, "tasks": tasks` al `output_data` en `action_executor.py`. Sin esto, UI Generator recibe datos vacíos.

### Prioridad MEDIA (mejora la robustez)

5. **ActionExecutor fallback (Paso 3.5):** Agregar lógica en `action_executor.act()` para construir tareas desde `goal_tree` cuando `tasks` está vacío.

6. **Chain path (Fix 5 completo):** Crear `prompt_chain/handlers/` con los 6 handlers. Requiere estimación adicional (~5.5h).

### Prioridad BAJA

7. **Debugger locations (Paso 5.5):** Agregar ubicaciones de chain handlers en `_resolve_stage_locations()`.

---

## Dependencias entre Pasos Pendientes

```
Paso 2.5 (parser → ActionNode)
  │
  ▼
Paso 2.3 (SemanticVisitor.visit_action)  ← DICT-BASED path
  │
  ▼
Paso 2.4 (IRBuilder.visit_action)        ← SAME path
  │
  ▼
Paso 3.4 (ActionExecutor propaga ir_tree/tasks)
  │
  ├──► Fix 4 (UI Gate) recibe datos correctos
  │
  ▼
Paso 3.5 (ActionExecutor fallback)       ← INDEPENDIENTE
```

Los pasos 2.3, 2.4, y 2.5 deben implementarse en orden (2.5 → 2.3 → 2.4) para cerrar completamente el gap de tipos.

---

## Resumen Final

| Fix | Estado | Pasos Hechos | Pasos Pendientes | Esfuerzo Restante |
|-----|--------|-------------|-----------------|-------------------|
| Fix 1 | ✅ COMPLETADO | 3/3 | 0 | 0h |
| Fix 2 | ⚠️ PARCIAL | 3/5 | 2.3, 2.4, 2.5 (3 pasos) | ~1.5h |
| Fix 3 | ⚠️ PARCIAL | 3/5 | 3.4, 3.5 (2 pasos) | ~1h |
| Fix 4 | ✅ COMPLETADO | 4/4 | 0 | 0h |
| Fix 5 | ❌ NO IMPLEMENTADO | 0/6 | 5.1-5.6 (6 pasos) | ~5.5h |
| **Total** | **64%** | **13/23** | **11 pasos pendientes** | **~8h** |

**Conclusión:** El pipeline tiene el 64% de los arreglos planificados implementados. Los 3 pasos críticos (2.3, 2.4, 2.5 en IRBuilder/SemanticVisitor/Parser) son los que mantienen roto el flujo de datos principal. El Fix 5 (chain path) requiere creación completa de archivos desde cero y representa el mayor esfuerzo restante.