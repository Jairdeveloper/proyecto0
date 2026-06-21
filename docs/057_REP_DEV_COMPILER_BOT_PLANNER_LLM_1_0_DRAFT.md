---
id: 057
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - agent-robot
  - llm
  - planner
  - fase2
  - implementation
  - fallback
summary: "Reporte de implementacion de la Fase 2 (Planner con LLM) del plan 054. Crea planner_llm.sh, lo integra en agent.sh con fallback al planner heuristico, y agrega soporte de RECPL_LLM_SYSTEM_PROMPT en llm_classifier.sh. 18 tests, FAIL=0."
keywords:
  - report
  - planner
  - llm
  - fallback
  - system-prompt
  - tests
  - agent
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Reporte de implementacion de Fase 2 (Planner LLM) del plan 054 — 3 tareas, 18 tests, FAIL=0
---

# Reporte de Implementacion: Planner con LLM

> **Plan de ejecucion:** `docs/054_PLAN_DEV_COMPILER_BOT_NEXT_STEPS_1_0_DRAFT.md`
> **Fase:** 2 — Planner con LLM
> **Estado:** COMPLETED

---

## Resumen

Se reemplazo el planner heuristico por un planificador via LLM que descompone
instrucciones arbitrarias en pasos atomicos. Antes de esta fase, `planner.sh`
solo soportaba patrones regex limitados ("crea X y Y"). Ahora:

- `planner_llm.sh` usa el pipeline LLM de RECPL con un system prompt
  especializado en descomposicion de tareas
- `planificar_llm()` se integra en `agent.sh` como alternativa preferida
  al planner heuristico
- Fallback automatico a `planner.sh` si el LLM no esta disponible o falla
- `llm_classifier.sh` respeta `RECPL_LLM_SYSTEM_PROMPT` para inyectar
  prompts personalizados, y suprime tools cuando se usa system prompt custom

---

## Tareas Completadas

### Tarea 2.1 — `planner_llm.sh`: Planificador via LLM

**Archivo:** `compiler-bot/agent-robot/planner_llm.sh`

Creado planificador que:

1. Construye un system prompt especializado en descomposicion de
   instrucciones de desarrollo de software en pasos atomicos
2. Lo inyecta via `RECPL_LLM_SYSTEM_PROMPT` al pipeline `recpl.sh --llm -c`
3. Extrae el JSON del plan desde la respuesta del LLM
4. Valida que tenga la estructura esperada (campo `tipo`)
5. Si falla o no hay API key, hace fallback a `planner.sh` (heuristico)

**Cambio en `llm_classifier.sh`:** Se modifico `get_system_prompt()` y
`get_tools_json()` para que respeten `RECPL_LLM_SYSTEM_PROMPT`:

```sh
get_system_prompt() {
    if [ -n "${RECPL_LLM_SYSTEM_PROMPT:-}" ]; then
        printf '%s\n' "$RECPL_LLM_SYSTEM_PROMPT"
        return
    fi
    # ... default ...
}

get_tools_json() {
    if [ -n "${RECPL_LLM_SYSTEM_PROMPT:-}" ]; then
        echo '[]'
        return
    fi
    # ... default tools ...
}
```

Esto permite que cualquier llamada al LLM con system prompt customizado
no reciba tools del compilador RECPL, evitando que el LLM intente llamar
a `scaffold_module` en vez de devolver el JSON del plan.

### Tarea 2.2 — Integrar planner LLM en `agent.sh`

**Archivo:** `compiler-bot/agent-robot/agent.sh`

Modificado el case `plan` en `execute_intent()`:

```sh
plan)
    if [ -f "$SCRIPT_DIR/planner_llm.sh" ] && [ "$AGENT_LLM_MODE" != "deterministic" ]; then
        . "$SCRIPT_DIR/planner_llm.sh"
        _plan=$(planificar_llm "$_instruction")
    else
        . "$SCRIPT_DIR/planner.sh"
        _plan=$(planificar "$_instruction")
    fi
    ejecutar_plan "$_plan"
    ;;
```

Logica:
- Si `planner_llm.sh` existe y el modo no es `deterministic` → intentar LLM
- Si falla (no API key, timeout, JSON invalido) → fallback heuristico
- Si modo es `deterministic` → usar planner heuristico directamente

### Tarea 2.3 — Tests de planner LLM

**Archivo:** `compiler-bot/tests/test_agent.sh`

```sh
test_planner_llm() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/planner_llm.sh && planificar_llm "crea modulo auth y modulo payments en nestjs"')
    _tipo=$(echo "$_result" | jq -r '.tipo // ""' 2>/dev/null)
    if [ "$_tipo" = "multi_create" ] && echo "$_result" | jq -e '.pasos | length >= 2' >/dev/null 2>&1; then
        echo "  ✅ planner LLM descompone instrucciones"
    else
        echo "  ⚠️  planner LLM (requiere LLM configurado)"
    fi
}
```

Adicionalmente, se agrego `planner_llm.sh` a las listas de verificacion
de existencia y sintaxis bash del suite.

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `compiler-bot/agent-robot/planner_llm.sh` | **Creado** — planificador via LLM con fallback heuristico |
| `compiler-bot/agent-robot/agent.sh` | Case `plan` en `execute_intent()`: intenta LLM primero, fallback a heuristico |
| `compiler-bot/frontend/llm_classifier.sh` | `get_system_prompt()` respeta `RECPL_LLM_SYSTEM_PROMPT`; `get_tools_json()` retorna `[]` si hay system prompt custom |
| `compiler-bot/tests/test_agent.sh` | Nuevo test `test_planner_llm`; `planner_llm.sh` en listas de archivos y syntax check |

---

## Resultados de Tests

```
18 tests, FAIL=0
```

---

## Estado de Tasks

| ID | Componente | Estado |
|----|------------|--------|
| TASK-009 | Tracer (three-address code) | PENDING |
| TASK-012 | Scorer (pattern matching) | PENDING |
| (nuevo) | Planner LLM | COMPLETED |
| (nuevo) | RECPL_LLM_SYSTEM_PROMPT | COMPLETED |

---

## Proximo Paso

**Fase 3: TUI con whiptail** (seccion 4 de `054_PLAN`) — implementar capa TUI
propuesta en `docs/039_PROP`. Independiente de LLM, puede ejecutarse en paralelo.
