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

# Directorio base del planificador
# Cuando lo carga agent.sh: SCRIPT_DIR = agent-robot/
# Cuando se testea via sh -c: script relativo a CWD
SCRIPT_DIR_PLANNER="${SCRIPT_DIR:-agent-robot}"

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

    # La respuesta viene envuelta en un contenedor "respond":
    # {"tipo_respuesta":"respond","mensaje":"{...}","payload":null}
    # Extraer el JSON del plan desde el campo mensaje
    _plan_json=$(echo "$_raw" | jq -r '.mensaje // ""' 2>/dev/null)
    [ -z "$_plan_json" ] && _plan_json="$_raw"

    # Validar que tenga la estructura esperada (campo "tipo")
    _tipo=$(echo "$_plan_json" | jq -r '.tipo // ""' 2>/dev/null)
    if [ -z "$_tipo" ]; then
        # Fallback al planner heuristico
        . "$SCRIPT_DIR_PLANNER/planner.sh"
        planificar "$_instruction"
        return
    fi

    echo "$_plan_json"
}
