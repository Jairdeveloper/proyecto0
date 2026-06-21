---
id: 054
area: dev
type: plan
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - plan
  - execution
  - agent-robot
  - llm
  - planner
  - tui
  - next-steps
  - roadmap
summary: "Plan de implementacion para los proximos pasos sugeridos en 053_REP. Analiza 4 alternativas (LLM real, Planner LLM, TUI mejorada, Modo servidor), las prioriza segun impacto viabilidad, y define 3 fases de ejecucion con pseudocodigo, dependencias y criterios de exito."
keywords:
  - plan
  - proximos-pasos
  - roadmap
  - llm
  - planner
  - tui
  - whiptail
  - servidor
  - fases
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Plan de implementacion para proximos pasos — 3 fases, 10 tareas, pseudocodigo y criterios de exito
---

# Plan de Implementacion: Proximos Pasos del Agent-Robot

> **Documento de origen:** `docs/053_REP_DEV_COMPILER_BOT_FASE4_AGENT_PROMPTS_ROBUSTEZ_1_0_DRAFT.md`
> **Seccion de origen:** "Proximo Paso Sugerido"
> **Estado:** DRAFT — pendiente de aprobacion

---

## 0. Analisis de las 4 Alternativas

### Alternativa A — Integracion LLM real

**Que existe:** Adaptadores Claude/OpenAI en `providers/`, `llm_classifier.sh`, `router.sh`, `llm_ir_mapper.sh`. El pipeline RECPL ya soporta `--llm` y `RECPL_LLM_MODE`.

**Que falta:** `agent.sh --llm` no esta conectado al pipeline LLM. El flujo actual de `agent.sh` ignora `AGENT_LLM_MODE` y `_mode` — siempre pasa por `classify_intent()` deterministico. No hay mecanismo para que `agent.sh` delegue al LLM cuando no entiende la instruccion.

**Dependencias:** Fase 1-4 completas.
**Impacto:** Alto — desbloquea comprension de lenguaje natural real.
**Esfuerzo:** 2-3 horas.

### Alternativa B — Planner con LLM

**Que existe:** `planner.sh` heuristico (regex), `agent.sh` con deteccion de `plan` intent, LLM pipeline completo.

**Que falta:** El planner heuristico es limitado a "crea X y Y". Un planner LLM podria descomponer instrucciones arbitrarias ("crea un microservicio de pagos con validacion JWT, base de datos PostgreSQL, y cola de Redis"). Depende de Alternativa A (LLM real debe funcionar primero).

**Dependencias:** Alternativa A.
**Impacto:** Alto — desbloquea scaffolding complejo.
**Esfuerzo:** 3-4 horas.

### Alternativa C — TUI/CLI mejorada

**Que existe:** `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` con diseno completo de whiptail wrapper.

**Que falta:** Archivo `tui.sh`, flag `--tui` en `recpl.sh` y `agent.sh`.

**Dependencias:** Ninguna (ortogonal al resto).
**Impacto:** Medio — mejora experiencia de usuario pero no agrega capacidad nueva.
**Esfuerzo:** 1-2 horas.

### Alternativa D — Modo servidor

**Que existe:** Menciones en `docs/013_PROP` y `docs/016_PLAN` (C core), pero **explicitamente abandonado** en `docs/048_PLAN` (Decision #2): "Sin API HTTP, sin extension VS Code, sin desktop app. Solo scripts shell."

**Recomendacion:** NO IMPLEMENTAR. Requeriria reescribir todo el pipeline en otro lenguaje (C, Node, Python) para servir HTTP. El proyecto es shell-based por diseno.

---

## 1. Priorizacion

| Prioridad | Alternativa | Justificacion |
|-----------|-------------|---------------|
| **P1** | A — LLM real | Desbloquea comprension de lenguaje natural. Requisito para B. |
| **P2** | B — Planner LLM | Depende de A. Mayor impacto en scaffolding complejo. |
| **P3** | C — TUI mejorada | Independiente. Bajo esfuerzo, mejora UX. |
| **--** | D — Servidor | **DESCARTADO.** Violaria la arquitectura shell-only del proyecto. |

---

## 2. Fase 1: LLM real en agent.sh

**Objetivo:** Conectar `agent.sh --llm` y `AGENT_LLM_MODE` al pipeline LLM existente.

**Duracion estimada:** 2-3 horas
**Depende de:** Fase 1-4 completas

### Tarea 1.1 — Diagnosticar estado actual de `--llm`

**Archivo:** `compiler-bot/agent-robot/agent.sh`

Actualmente `agent.sh` define `_mode` pero no lo usa:

```sh
main() {
    _mode="${AGENT_LLM_MODE:-auto}"
    ...
    # _mode nunca se usa despues de parsear argumentos
    _intent=$(classify_intent "$_instruction")  # siempre deterministico
}
```

**Cambio:** Pasar `_mode` a `classify_intent()` y `execute_intent()`.

### Tarea 1.2 — Modificar `classify_intent()` para modo LLM

**Archivo:** `compiler-bot/agent-robot/agent.sh`

```sh
classify_intent() {
    _instruction="$1"
    _mode="${2:-auto}"

    # Si modo es "llm", delegar directamente al LLM
    if [ "$_mode" = "llm" ]; then
        echo "llm"
        return
    fi

    # Si modo es "auto", primero intentar deterministico
    # ... (resto de la logica actual)
    # Si nada matchea y modo es "auto", devolver "llm" como fallback
    echo "llm"  # en vez de "recpl"
}
```

### Tarea 1.3 — Agregar caso `llm` en `execute_intent()`

**Archivo:** `compiler-bot/agent-robot/agent.sh`

```sh
llm)
    # Delegar al pipeline LLM via bridge
    . "$SCRIPT_DIR/bridge.sh"
    bridge_llm "$_instruction"
    ;;
```

### Tarea 1.4 — Agregar `bridge_llm()` en `bridge.sh`

**Archivo:** `compiler-bot/agent-robot/bridge.sh`

```sh
# --- Bridge para LLM ---
# Uso: bridge_llm "instruccion"
# Output: JSON con respuesta del LLM
bridge_llm() {
    _instruction="$1"

    _raw_output=$(cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)

    if [ -z "$_raw_output" ]; then
        jq -n --arg exito false --arg origen "llm" \
            --arg tipo "error" \
            --arg msg "LLM no produjo respuesta" \
            '{exito: $exito, origen: $origen, tipo_respuesta: $tipo, mensaje: $msg, payload: null, raw: ""}'
        return
    fi

    jq -n --arg exito true --arg origen "llm" \
        --arg tipo "llm_response" \
        --arg respuesta "$_raw_output" \
        '{exito: $exito, origen: $origen, tipo_respuesta: $tipo, mensaje: $respuesta, payload: {}, raw: $respuesta}'
}
```

### Tarea 1.5 — Integrar `AGENT_LLM_PROVIDER` en el bridge

**Archivo:** `compiler-bot/agent-robot/bridge.sh`

Pasar `AGENT_LLM_PROVIDER` como variable de entorno a `recpl.sh`:

```sh
bridge_llm() {
    _instruction="$1"
    _provider="${AGENT_LLM_PROVIDER:-}"

    if [ -n "$_provider" ]; then
        _raw_output=$(RECPL_LLM_PROVIDER="$_provider" \
            cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)
    else
        _raw_output=$(cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh --llm -c "$_instruction" 2>/dev/null)
    fi
    ...
}
```

### Tarea 1.6 — Agregar modo `auto` con fallback

En modo `auto`, si `classify_intent()` no reconoce la instruccion como deterministico, debe devolver `llm` como fallback.

```sh
# En classify_intent(), reemplazar el default:
# Por defecto: en modo auto, intentar LLM
if [ "$_mode" = "auto" ]; then
    echo "llm"
    return
fi
# En modo deterministic: fallar
echo "recpl"
```

### Tarea 1.7 — Tests Fase LLM

**Archivo:** `compiler-bot/tests/test_agent.sh`

```sh
# --- Fase LLM: modo llm ---
test_agent_llm_mode() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh --llm "hola" 2>/dev/null)
    if echo "$_result" | grep -qi "respuesta\|llm\|proyecto0"; then
        echo "  ✅ Agent --llm funciona"
    else
        echo "  ⚠️  Agent --llm (requiere API key)"
    fi
}
```

---

## 3. Fase 2: Planner con LLM

**Objetivo:** Reemplazar el planner heuristico por descomposicion via LLM para instrucciones arbitrarias.

**Duracion estimada:** 3-4 horas
**Depende de:** Fase 1 (LLM real en agent.sh)

### Tarea 2.1 — `planner_llm.sh`: Planificador via LLM

**Archivo:** `compiler-bot/agent-robot/planner_llm.sh`

```sh
#!/bin/sh
# ============================================================================
# planner_llm.sh - Planificador via LLM para Proyecto0(RECPL)
# ============================================================================
#
# PROPOSITO:
#   Usa el pipeline LLM de RECPL para descomponer instrucciones complejas
#   en pasos atomicos. Reemplaza al planner heuristico (planner.sh) cuando
#   el LLM esta disponible.
#
# USO:
#   . planner_llm.sh
#   planificar_llm "instruccion compleja"
#   -> JSON con lista de pasos
# ============================================================================

SCRIPT_DIR_PLANNER="$(dirname "$0")"

# --- Planificar via LLM ---
planificar_llm() {
    _instruction="$1"

    # Construir system prompt para descomposicion
    _system_prompt=$(cat <<PROMPT
Eres un planificador que descompone instrucciones de desarrollo de software
en pasos ejecutables. Cada paso debe ser una instruccion simple que el
sistema RECPL o una herramienta shell pueda ejecutar.

REGLAS:
1. Cada paso debe ser atomico
2. Los pasos son secuenciales
3. No asumas que pasos anteriores fallaron

FORMATO DE RESPUESTA (solo JSON, sin explicacion):
{
  "tipo": "multi_create" | "multi_tool" | "simple",
  "instruccion_original": "...",
  "tech": "nestjs" | "prisma" | "mixto",
  "total_pasos": N,
  "pasos": [
    {"orden": 1, "accion": "recpl" | "write_file" | "run_command", "parametros": {...}},
    ...
  ]
}
PROMPT
)

    # Llamar al LLM via recpl pipeline (modo --llm con system prompt)
    _raw=$(RECPL_LLM_SYSTEM_PROMPT="$_system_prompt" \
        cd "$SCRIPT_DIR_PLANNER/.." && ./recpl.sh --llm -c "Descompone: $_instruction" 2>/dev/null)

    # Validar que la respuesta sea JSON valido con la estructura esperada
    _tipo=$(echo "$_raw" | jq -r '.tipo // ""' 2>/dev/null)
    if [ -z "$_tipo" ]; then
        # Fallback al planner heuristico
        . "$SCRIPT_DIR_PLANNER/planner.sh"
        planificar "$_instruction"
        return
    fi

    echo "$_raw"
}
```

### Tarea 2.2 — Integrar planner LLM en `agent.sh`

Modificar `execute_intent()` para el caso `plan`:

```sh
plan)
    # Intentar planner LLM primero, fallback a heuristico
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

### Tarea 2.3 — Tests de planner LLM

```sh
# --- Fase LLM: planner ---
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

---

## 4. Fase 3: TUI con whiptail

**Objetivo:** Implementar la capa TUI propuesta en `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md`.

**Duracion estimada:** 1-2 horas
**Depende de:** Fase 1-4 completas (independiente de LLM)

### Tarea 3.1 — `tui.sh`: Menu principal

**Archivo:** `compiler-bot/agent-robot/tui.sh`

Basado en `039_PROP`:

```sh
#!/bin/sh
# ============================================================================
# tui.sh - Capa TUI (whiptail) para Proyecto0(RECPL)
# ============================================================================

# --- Verificar whiptail ---
tui_check() {
    command -v whiptail >/dev/null 2>&1 || {
        echo "whiptail no instalado. Ejecuta: sudo apt install whiptail"
        return 1
    }
}

# --- Menu principal ---
tui_menu() {
    _choice=$(whiptail --title "Proyecto0(RECPL)" \
        --menu "Selecciona una opcion:" 20 60 10 \
        "1" "Ejecutar instruccion RECPL" \
        "2" "Modo interactivo" \
        "3" "Configurar LLM" \
        "4" "Ver historial" \
        "5" "Ayuda" \
        "6" "Salir" 3>&1 1>&2 2>&3)

    echo "$_choice"
}

# --- Dialogo de instruccion ---
tui_input() {
    _result=$(whiptail --title "Instruccion" \
        --inputbox "Escribe tu instruccion:" 10 60 3>&1 1>&2 2>&3)
    echo "$_result"
}

# --- Output box ---
tui_output() {
    _msg="$1"
    whiptail --title "Resultado" --msgbox "$_msg" 20 60
}
```

### Tarea 3.2 — Integrar TUI en `agent.sh`

Agregar flag `--tui`:

```sh
--tui)
    . "$SCRIPT_DIR/tui.sh"
    tui_check || return 1
    _mode="tui"
    shift
    ;;
```

Y en `main()`:

```sh
tui)
    . "$SCRIPT_DIR/tui.sh"
    while true; do
        _choice=$(tui_menu)
        case "$_choice" in
            1)
                _inst=$(tui_input)
                [ -n "$_inst" ] && main "$_inst"
                ;;
            2)
                echo "Modo interactivo no implementado via TUI aun"
                ;;
            3)
                tui_llm_config
                ;;
            4)
                tui_history
                ;;
            5)
                tui_help
                ;;
            6)
                exit 0
                ;;
        esac
    done
    ;;
```

### Tarea 3.3 — Tests de TUI

```sh
# --- Fase TUI: whiptail disponible ---
test_tui_whiptail() {
    if command -v whiptail >/dev/null 2>&1; then
        echo "  ✅ whiptail disponible"
    else
        echo "  ⚠️  whiptail no instalado (opcional)"
    fi
}
```

---

## 5. Resumen de Tareas

| Fase | Tarea | Archivo | Estimacion |
|------|-------|---------|------------|
| 1 | 1.1 Diagnosticar --llm | agent.sh | 15 min |
| 1 | 1.2 Modificar classify_intent() | agent.sh | 20 min |
| 1 | 1.3 Agregar caso llm en execute_intent() | agent.sh | 10 min |
| 1 | 1.4 Agregar bridge_llm() | bridge.sh | 20 min |
| 1 | 1.5 Integrar AGENT_LLM_PROVIDER | bridge.sh | 10 min |
| 1 | 1.6 Agregar modo auto con fallback | agent.sh | 10 min |
| 1 | 1.7 Tests Fase LLM | test_agent.sh | 20 min |
| 2 | 2.1 planner_llm.sh | planner_llm.sh | 60 min |
| 2 | 2.2 Integrar planner LLM | agent.sh | 20 min |
| 2 | 2.3 Tests planner LLM | test_agent.sh | 20 min |
| 3 | 3.1 tui.sh | tui.sh | 40 min |
| 3 | 3.2 Integrar TUI en agent.sh | agent.sh + recpl.sh | 20 min |
| 3 | 3.3 Tests TUI | test_agent.sh | 10 min |

**Total estimado:** ~4.5 horas (distribuido en 3 fases)

---

## 6. Dependencias Entre Fases

```
Fase 1 (LLM real)
  |
  ├──→ Fase 2 (Planner LLM) — REQUIERE Fase 1
  |
  └──→ Fase 3 (TUI) — INDEPENDIENTE, puede ejecutarse en paralelo
```

---

## 7. Criterios de Exito

### Fase 1 — LLM real

```sh
# 1. --llm flag funciona
./compiler-bot/agent-robot/agent.sh --llm "hola" 2>/dev/null
# Output: respuesta del LLM (no error deterministico)

# 2. Modo auto fallback a LLM
./compiler-bot/agent-robot/agent.sh "esta es una instruccion que RECPL no entiende" 2>/dev/null
# Output: intenta LLM como fallback

# 3. Tests pasan
./compiler-bot/tests/test_agent.sh | grep "FAIL=0"
```

### Fase 2 — Planner LLM

```sh
# 1. Planner LLM descompone instrucciones arbitrarias
./compiler-bot/agent-robot/agent.sh "crea un microservicio de pagos con JWT y PostgreSQL" 2>/dev/null
# Output: Plan de ejecucion con 2+ pasos

# 2. Fallback a planner heuristico si LLM no disponible
AGENT_LLM_MODE=deterministic ./compiler-bot/agent-robot/agent.sh "crea modulo X y Y" 2>/dev/null
# Output: Plan heuristico funciona

# 3. Tests pasan
./compiler-bot/tests/test_agent.sh | grep "FAIL=0"
```

### Fase 3 — TUI

```sh
# 1. --tui flag abre menu
./compiler-bot/agent-robot/agent.sh --tui 2>/dev/null
# Output: menu whiptail (requiere terminal)
```

---

## 8. Riesgos

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|------------|
| API keys de LLM no configuradas | Alta | Modo deterministico sigue funcionando siempre |
| whiptail no instalado | Media (headless) | `tui_check()` informa como instalar |
| LLM timeout en planner | Media | Fallback a planner heuristico |
| Proveedor LLM cambia API | Baja | Adaptadores desacoplan cambios |
| Modo servidor incompatible con arquitectura shell | Alta | **DESCARTADO** — no implementar |

---

## 9. Referencias

| Documento | Relacion |
|-----------|----------|
| `docs/053_REP_DEV_COMPILER_BOT_FASE4_AGENT_PROMPTS_ROBUSTEZ_1_0_DRAFT.md` | Reporte que origina este plan (seccion "Proximo Paso Sugerido") |
| `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` | Propuesta de TUI con whiptail (base para Fase 3) |
| `docs/031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` | Plan de integracion LLM (fases L1-L4, ya implementadas en el pipeline) |
| `docs/048_PLAN_DEV_COMPILER_BOT_AGENT_IMPL_1_0_DRAFT.md` | Decision #2: "Sin API HTTP, sin extension VS Code" (descarte de modo servidor) |
| `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` | Propuesta de provider gratuito (integracion futura opcional) |
| `compiler-bot/agent-robot/agent.sh` | Archivo principal a modificar en las 3 fases |
| `compiler-bot/agent-robot/bridge.sh` | Bridge a modificar para LLM |
| `compiler-bot/agent-robot/planner.sh` | Planner heuristico (fallback de planner LLM) |
