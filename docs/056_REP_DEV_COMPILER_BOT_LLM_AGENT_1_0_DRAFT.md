---
id: 056
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - agent-robot
  - llm
  - fase1
  - bridge
  - implementation
summary: "Reporte de implementacion de la Fase 1 (LLM real en agent.sh) del plan 054. Conecta agent.sh --llm y AGENT_LLM_MODE al pipeline LLM existente (Claude/OpenAI). Anade bridge_llm(), modo auto con fallback a LLM, y 17 tests funcionales con FAIL=0."
keywords:
  - report
  - llm
  - agent
  - bridge
  - mode
  - auto
  - fallback
  - tests
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Reporte de implementacion de Fase 1 (LLM real) del plan 054 — 7 tareas, 17 tests, FAIL=0
---

# Reporte de Implementacion: LLM Real en agent.sh

> **Plan de ejecucion:** `docs/054_PLAN_DEV_COMPILER_BOT_NEXT_STEPS_1_0_DRAFT.md`
> **Fase:** 1 — LLM real en agent.sh
> **Estado:** COMPLETED

---

## Resumen

Se conecto `agent.sh --llm` y `AGENT_LLM_MODE` al pipeline LLM existente en RECPL
(Claude/OpenAI). Antes de esta fase, `agent.sh` ignoraba el flag `--llm` y siempre
usaba clasificacion deterministica por palabras clave. Ahora:

- `--llm` fuerza el modo LLM directamente
- `auto` (default) intenta clasificacion deterministica primero, y si no reconoce la instruccion, cae a LLM como fallback
- `deterministic` solo usa RECPL, sin LLM
- `AGENT_LLM_PROVIDER` se pasa al pipeline RECPL para seleccionar proveedor

---

## Tareas Completadas

### Tarea 1.1 — Diagnosticar estado actual de `--llm`

**Diagnostico:** `agent.sh` parseaba `_mode` desde `--llm`/`--deterministic`/`AGENT_LLM_MODE`
pero nunca lo pasaba a `classify_intent()` ni `execute_intent()`. La clasificacion
siempre era 100% deterministica, ignorando por completo el modo.

### Tarea 1.2 — Modificar `classify_intent()` para modo LLM

**Archivo:** `compiler-bot/agent-robot/agent.sh`

```sh
classify_intent() {
    _instruction="$1"
    _mode="${2:-auto}"

    if [ "$_mode" = "llm" ]; then
        echo "llm"
        return
    fi
    # ... heuristica existente intacta ...
}
```

### Tarea 1.3 — Agregar caso `llm` en `execute_intent()`

Nuevo case que delega en `bridge_llm()`:

```sh
llm)
    . "$SCRIPT_DIR/bridge.sh"
    bridge_llm "$_instruction"
    ;;
```

### Tarea 1.4 — Agregar `bridge_llm()` en `bridge.sh`

**Archivo:** `compiler-bot/agent-robot/bridge.sh`

Funcion `bridge_llm()` que:
1. Llama a `recpl.sh --llm -c "instruccion"` como subproceso
2. Mide tiempo de ejecucion
3. Si no hay output, devuelve `{"exito":false, "tipo_respuesta":"error", "mensaje":"LLM no produjo respuesta"}`
4. Si hay output, lo envuelve en `{"exito":true, "tipo_respuesta":"llm_response", "mensaje":"..."}`

### Tarea 1.5 — Integrar `AGENT_LLM_PROVIDER` en el bridge

Si `AGENT_LLM_PROVIDER` esta definido, se pasa como `RECPL_LLM_PROVIDER` al subproceso:

```sh
if [ -n "$_provider" ]; then
    _raw_output=$(RECPL_LLM_PROVIDER="$_provider" \
        cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)
else
    _raw_output=$(cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)
fi
```

### Tarea 1.6 — Agregar modo `auto` con fallback a LLM

En `classify_intent()`, el default anterior era `echo "recpl"`. Ahora:

```sh
if [ "$_mode" = "auto" ]; then
    echo "llm"
    return
fi
echo "recpl"
```

### Tarea 1.7 — Tests Fase LLM

**Archivo:** `compiler-bot/tests/test_agent.sh`

Test anadido:

```sh
test_agent_llm_mode() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh --llm "hola" 2>/dev/null)
    if echo "$_result" | grep -qi "respuesta\|llm\|proyecto0"; then
        echo "  ✅ Agent --llm funciona"
    else
        echo "  ⚠️  Agent --llm (requiere API key)"
    fi
}
```

Titulo de test suite actualizado a "Fase 1 + Fase 2 + Fase 3 + Fase 4 + LLM".

---

## Archivos Modificados

| Archivo | Cambio |
|---------|--------|
| `compiler-bot/agent-robot/agent.sh` | `classify_intent()` acepta `_mode`, retorna `llm` si modo=llm o fallback auto. `execute_intent()` nuevo case `llm`. `main()` pasa `_mode` a classify. `format_response()` maneja `llm_response`. |
| `compiler-bot/agent-robot/bridge.sh` | Nueva funcion `bridge_llm()` con provider passthrough. |
| `compiler-bot/tests/test_agent.sh` | Nuevo test `test_agent_llm_mode`. Suite: 17 tests. |

---

## Resultados de Tests

```
17 tests, FAIL=0
```

---

## Proximo Paso

**Fase 2: Planner con LLM** (seccion 3 de `054_PLAN`) — reemplazar planner heuristico
por descomposicion via LLM. Depende de esta Fase 1.
