#!/bin/sh
# ============================================================================
# planner.sh - Planificador multi-paso del agente Proyecto0(RECPL)
# ============================================================================
#
# PROPOSITO:
#   Descompone instrucciones complejas en una secuencia de pasos ejecutables.
#   Cada paso es una instruccion simple que puede ejecutar agent.sh o
#   delegarse a una herramienta especifica.
#
# USO:
#   . planner.sh
#   planificar "instruccion compleja"
#   -> JSON con lista de pasos
# ============================================================================

# --- Planificar: descomponer instruccion en pasos ---
# Uso: planificar "instruccion"
# Output: JSON con plan (lista de pasos)
planificar() {
    _instruction="$1"
    _lower=$(echo "$_instruction" | tr '[:upper:]' '[:lower:]')
    _pasos=""

    # Detectar multi-creacion: "crea X y Y"
    if echo "$_lower" | grep -qE '(y |,| y )'; then
        _pasos=$(_plan_multi_create "$_instruction")
    fi

    # Detectar "proyecto completo con X y Y"
    if echo "$_lower" | grep -qE '(proyecto |full |completo )'; then
        _pasos=$(_plan_full_project "$_instruction")
    fi

    # Si no se pudo planificar, devolver un solo paso con la instruccion original
    if [ -z "$_pasos" ]; then
        cat <<EOF
{
  "tipo": "simple",
  "instruccion_original": $(printf '%s' "$_instruction" | jq -R -s .),
  "pasos": [
    {"orden": 1, "accion": "recpl", "parametros": {"instruccion": $(printf '%s' "$_instruction" | jq -R -s .)}}
  ],
  "total_pasos": 1
}
EOF
        return
    fi

    echo "$_pasos"
}

# --- Planificar multi-creacion ---
# Ej: "crea modulo auth y modulo payments en nestjs"
_plan_multi_create() {
    _instruction="$1"
    _lower=$(echo "$_instruction" | tr '[:upper:]' '[:lower:]')

    # Extraer tecno stack (nestjs, prisma, etc.)
    _tech="nestjs"
    echo "$_lower" | grep -q "prisma" && _tech="prisma"

    # Extraer modulos individuales
    # Nota: usar sed con espacios para reemplazar "y" como palabra, no como caracter
    # Nota: " en " (con espacios) evita cortar palabras como "payments" que contienen "en"
    _modulos=$(echo "$_lower" | sed 's/crea //' | sed 's/genera //' | sed 's/modulo //g' | sed 's/modulos //g' | sed 's/ en .*$//' | sed 's/,/ /g' | sed 's/ y / /g' | sed 's/^y //' | sed 's/ y$//' | xargs)

    _count=0
    _pasos_json=""
    for _mod in $_modulos; do
        [ -z "$_mod" ] && continue
        _count=$((_count + 1))
        _inst="crea modulo $_mod en $_tech"
        _sep=""
        [ -n "$_pasos_json" ] && _sep=","
        _pasos_json="${_pasos_json}${_sep}{\"orden\":$_count,\"accion\":\"recpl\",\"parametros\":{\"instruccion\":$(printf '%s' "$_inst" | jq -R -s .)}}"
    done

    cat <<EOF
{
  "tipo": "multi_create",
  "instruccion_original": $(printf '%s' "$_instruction" | jq -R -s .),
  "tech": "$_tech",
  "total_modulos": $_count,
  "pasos": [$_pasos_json],
  "total_pasos": $_count
}
EOF
}

# --- Planificar proyecto completo ---
_plan_full_project() {
    _instruction="$1"

    # Por ahora, trata como multi-create
    _plan_multi_create "$_instruction"
}

# --- Ejecutar plan ---
# Uso: ejecutar_plan <json_del_plan>
# Output: JSON con resultados consolidados (stderr para texto legible)
ejecutar_plan() {
    _plan="$1"
    _total=$(echo "$_plan" | jq -r '.total_pasos // 0' 2>/dev/null)
    _resultados=""

    echo " Plan de ejecucion: $_total pasos" >&2
    echo "" >&2

    _i=0
    while [ "$_i" -lt "$_total" ]; do
        _i=$((_i + 1))
        _paso=$(echo "$_plan" | jq -c ".pasos[] | select(.orden == $_i)" 2>/dev/null)
        _accion=$(echo "$_paso" | jq -r '.accion // "recpl"' 2>/dev/null)
        _inst=$(echo "$_paso" | jq -r '.parametros.instruccion // ""' 2>/dev/null)

        echo "   Paso $_i/$_total: $_inst" >&2

        # Ejecutar paso
        _result=$(cd "$SCRIPT_DIR" && ./agent.sh "$_inst" 2>/dev/null)
        _sep=""
        [ -n "$_resultados" ] && _sep=","
        _resultados="${_resultados}${_sep}{\"paso\":$_i,\"instruccion\":$(printf '%s' "$_inst" | jq -R -s .),\"resultado\":$(printf '%s' "$_result" | jq -R -s .)}"

        echo "" >&2
    done

    cat <<EOF
{
  "exito": true,
  "tipo": "plan_completed",
  "total_pasos": $_total,
  "resultados": [$_resultados]
}
EOF
}
