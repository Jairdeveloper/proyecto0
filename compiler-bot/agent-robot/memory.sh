#!/bin/sh
# ============================================================================
# memory.sh - Memoria del agente Proyecto0(RECPL)
# ============================================================================
#
# Gestiona el estado del agente entre interacciones: historial de instrucciones,
# contexto actual, y datos persistentes.
#
# Almacenamiento: Archivo JSON en AGENT_MEMORY_DIR/
# ============================================================================

# --- Inicializar memoria ---
# Uso: memory_init
memory_init() {
    mkdir -p "$AGENT_MEMORY_DIR"
    _mem_file="$AGENT_MEMORY_DIR/agent_memory.json"

    if [ ! -f "$_mem_file" ]; then
        echo '{"historial":[],"contexto":{},"sesiones":[]}' > "$_mem_file"
    fi

    _log_file="${AGENT_LOG_FILE:-/tmp/agent.log}"
    touch "$_log_file"
}

# --- Leer archivo de memoria ---
_memory_read() {
    _mem_file="$AGENT_MEMORY_DIR/agent_memory.json"
    if [ -f "$_mem_file" ]; then
        cat "$_mem_file"
    else
        echo '{"historial":[],"contexto":{},"sesiones":[]}'
    fi
}

# --- Escribir archivo de memoria ---
_memory_write() {
    _content="$1"
    _mem_file="$AGENT_MEMORY_DIR/agent_memory.json"
    printf '%s' "$_content" > "$_mem_file"
}

# --- Guardar un valor en el contexto ---
# Uso: memory_save <clave> <valor>
memory_save() {
    _key="$1"
    _value="$2"

    _data=$(_memory_read)
    _data=$(echo "$_data" | jq --arg k "$_key" --arg v "$_value" '.contexto[$k] = $v' 2>/dev/null)
    _memory_write "$_data"
}

# --- Recuperar un valor del contexto ---
# Uso: memory_get <clave>
memory_get() {
    _key="$1"
    _data=$(_memory_read)
    echo "$_data" | jq -r --arg k "$_key" '.contexto[$k] // ""' 2>/dev/null
}

# --- Agregar entrada al historial ---
# Uso: memory_add_history <instruccion> <respuesta>
memory_add_history() {
    _instruction="$1"
    _response="$2"
    _timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || echo "unknown")

    _data=$(_memory_read)
    _entry=$(cat <<EOF
{"timestamp":"$_timestamp","instruccion":$(printf '%s' "$_instruction" | jq -R -s .),"respuesta":$(printf '%s' "$_response" | jq -R -s .)}
EOF
)
    _data=$(echo "$_data" | jq --argjson e "$_entry" '.historial += [$e]' 2>/dev/null)
    _memory_write "$_data"
}

# --- Obtener historial completo ---
# Uso: memory_history
memory_history() {
    _data=$(_memory_read)
    echo "$_data" | jq -c '.historial' 2>/dev/null || echo '[]'
}

# --- Obtener contexto completo ---
# Uso: memory_context
memory_context() {
    _data=$(_memory_read)
    echo "$_data" | jq -c '.contexto' 2>/dev/null || echo '{}'
}

# --- Obtener ultimas N instrucciones ---
# Uso: memory_last <n>
memory_last() {
    _n="${1:-5}"
    _data=$(_memory_read)
    echo "$_data" | jq -c --argjson n "$_n" '.historial[-$n:]' 2>/dev/null || echo '[]'
}

# --- Registrar en log ---
# Uso: memory_log <mensaje>
memory_log() {
    _msg="$1"
    _timestamp=$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
    _log_file="${AGENT_LOG_FILE:-/tmp/agent.log}"
    echo "[$_timestamp] $_msg" >> "$_log_file"
}

# --- Logging por niveles ---
# Uso: memory_log_debug "mensaje"
#      memory_log_info "mensaje"
#      memory_log_warn "mensaje"
#      memory_log_error "mensaje"
memory_log_debug() {
    [ "${AGENT_LOG_LEVEL:-info}" = "debug" ] && memory_log "DEBUG: $*"
}
memory_log_info() {
    memory_log "INFO: $*"
}
memory_log_warn() {
    memory_log "WARN: $*"
}
memory_log_error() {
    memory_log "ERROR: $*"
}

# --- Listar sesiones disponibles ---
# Uso: memory_list_sessions
memory_list_sessions() {
    if [ -d "$AGENT_MEMORY_DIR" ]; then
        ls "$AGENT_MEMORY_DIR"/agent_memory_*.json 2>/dev/null | while read -r f; do
            _name=$(basename "$f" .json | sed 's/agent_memory_//')
            _size=$(wc -c < "$f" 2>/dev/null || echo 0)
            echo "  $_name ($_size bytes)"
        done
    fi
}

# --- Cambiar de sesion ---
# Uso: memory_set_session "nombre_sesion"
memory_set_session() {
    _session="$1"
    [ -z "$_session" ] && return 1
    echo "$AGENT_MEMORY_DIR/agent_memory_${_session}.json"
}

# --- Exportar memoria a JSON legible ---
# Uso: memory_export
memory_export() {
    _mem_file="$AGENT_MEMORY_DIR/agent_memory.json"
    if [ -f "$_mem_file" ]; then
        cat "$_mem_file" | jq '.'
    else
        echo '{}'
    fi
}
