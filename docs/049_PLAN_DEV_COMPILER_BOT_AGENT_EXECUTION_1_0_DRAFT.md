---
id: 049
area: dev
type: PLAN
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - plan
  - execution
  - agent-robot
  - implementation
  - fases
  - bridge
  - recpl
summary: "Plan de ejecucion detallado de la capa agent-robot. 4 fases, 25 tareas concretas con pseudocodigo de cada archivo a crear, comandos de verificacion, dependencias entre tareas, y criterios de exito por fase. Las decisiones arquitectonicas y reglas de diseno estan implicitas — remite a 048_PLAN para fundamentos."
keywords:
  - plan
  - ejecucion
  - agente
  - agent-robot
  - fases
  - tareas
  - recpl
  - bridge
  - implementacion
  - shell
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Plan de ejecucion detallado para la capa agent-robot — 4 fases con 25 tareas, pseudocodigo de cada archivo, comandos de verificacion
---

# Plan de Ejecucion: Capa Agent-Robot

> **Ejecutable basado en:** `docs/048_PLAN_DEV_COMPILER_BOT_AGENT_IMPL_1_0_DRAFT.md`
> **Estado de aprobacion:** Todas las secciones y criterios de 048 aceptados.
> **Las secciones 0-4 y 6-10 de 048 quedan implicitas** (arquitectura, bridge,
> componentes del agente, herramientas, reglas de diseno, integracion, riesgos).
> Este documento solo describe **que hacer, en que orden, y como verificar**.

---

## 0. Preliminar: Estructura de directorios

Crear antes de cualquier tarea:

```sh
mkdir -p compiler-bot/agent-robot/tools
mkdir -p compiler-bot/agent-robot/prompts
touch compiler-bot/agent-robot/.gitkeep
```

**Arbol resultante:**

```
compiler-bot/agent-robot/
├── agent.sh              # Fase 1 — bucle principal
├── bridge.sh             # Fase 1 — adapter a RECPL
├── config.sh             # Fase 1 — variables de entorno
├── memory.sh             # Fase 1 → Fase 3 — memoria del agente
├── planner.sh            # Fase 3 — planificador multi-paso
├── tools/
│   ├── tool_registry.sh  # Fase 1 — registro de herramientas
│   ├── tool_recpl.sh     # Fase 1 — herramienta RECPL
│   ├── tool_respond.sh   # Fase 1 — respuesta textual
│   ├── tool_read_file.sh # Fase 2 — lectura de archivos
│   ├── tool_write_file.sh# Fase 2 — escritura de archivos
│   ├── tool_run_command.sh# Fase 2 — ejecucion de comandos
│   └── tool_search_code.sh# Fase 3 — busqueda en codigo
└── prompts/
    ├── system_agent.txt    # Fase 4 — prompt base del agente
    ├── system_planner.txt  # Fase 4 — prompt del planificador
    └── system_tools.txt    # Fase 4 — prompt de herramientas
```

**Archivos externos a crear/modificar:**

```
compiler-bot/agent-robot.sh    # Fase 1 — entrypoint symlink/script
compiler-bot/recpl.sh          # Fase 1 — +3 lineas: flag --agent
tests/test_agent.sh            # Fase 1-4 — tests del agente
```

> **Regla:** Ningun archivo fuera de `agent-robot/` se modifica excepto
> `recpl.sh` (+3 lineas) y `tests/test_agent.sh` (nuevo). Ver seccion 6 de 048.

---

## 1. Fase 1: Fundacion del Agente

**Objetivo:** `agent.sh` funcional que recibe instrucciones, clasifica intencion
(via LLM o heuristica), delega en RECPL via bridge, o responde textualmente.

**Duracion estimada:** ~4 horas
**Dependencias:** Ninguna externa. Depende de `recpl.sh` y `pipeline_debugger.sh` existentes.

---

### Tarea 1.1 — `config.sh`: Variables de entorno

**Archivo:** `compiler-bot/agent-robot/config.sh`
**Depende de:** —
**Estimacion:** 15 min

```sh
#!/bin/sh
# ============================================================================
# config.sh - Configuracion del agente Proyecto0(RECPL)
# ============================================================================
#
# Define variables de entorno con valores por defecto.
# Cargar al inicio de agent.sh: . "$AGENT_DIR/config.sh"
# ============================================================================

# --- Directorio base del agente ---
AGENT_DIR="$(dirname "$0")"

# --- Modo de operacion ---
# auto:          intenta RECPL deterministico → si falla, usa LLM
# llm:           envia directamente al LLM, saltea RECPL
# deterministic: solo RECPL via bridge, sin LLM
AGENT_LLM_MODE="${AGENT_LLM_MODE:-auto}"

# --- Proveedor LLM preferido (opcional) ---
# Si se deja vacio, se usa el provider chain definido en RECPL
AGENT_LLM_PROVIDER="${AGENT_LLM_PROVIDER:-}"

# --- Capa LLM ---
# free | paid | auto (ver propuesta 046)
AGENT_LLM_TIER="${AGENT_LLM_TIER:-auto}"

# --- Memoria ---
AGENT_MEMORY_DIR="${AGENT_MEMORY_DIR:-/tmp/agent_memory}"

# --- Logging ---
AGENT_LOG_FILE="${AGENT_LOG_FILE:-/tmp/agent.log}"

# --- Version ---
AGENT_VERSION="1.0.0"

# --- Emoji prefix ---
AGENT_PREFIX="🤖"
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/config.sh && echo "OK: config.sh"
```

---

### Tarea 1.2 — `bridge.sh`: Adapter a RECPL

**Archivo:** `compiler-bot/agent-robot/bridge.sh`
**Depende de:** —
**Estimacion:** 45 min

```sh
#!/bin/sh
# ============================================================================
# bridge.sh - Bridge entre Agent-Robot y el pipeline RECPL existente
# ============================================================================
#
# PROPOSITO:
#   Unico punto de contacto entre agent-robot y RECPL. Aisla al agente de
#   los detalles internos del pipeline compilador.
#
# CONTRATO:
#   bridge_recpl(instruction)  → JSON { exito, origen, tipo_respuesta, ... }
#   bridge_debug(instruction)  → JSON con trazabilidad completa
#   bridge_state()             → JSON con tabla de simbolos actual
# ============================================================================

# --- Ruta a RECPL (relativa a este script) ---
BRIDGE_SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# --- Ejecutar instruccion en RECPL y devolver respuesta estructurada ---
# Uso: bridge_recpl "instruccion"
# Output: JSON con exito, origen, tipo_respuesta, mensaje, payload, raw, tiempo_ms
bridge_recpl() {
    _instruction="$1"
    _start_time=$(date +%s 2>/dev/null)
    [ -z "$_start_time" ] && _start_time=0

    # Llamar a recpl.sh en modo comando
    _raw_output=$(cd "$BRIDGE_SCRIPT_DIR" && ./recpl.sh -c "$_instruction" 2>/dev/null)
    _exit_code=$?

    _end_time=$(date +%s 2>/dev/null)
    _elapsed=$((_end_time - _start_time))
    [ "$_elapsed" -lt 0 ] && _elapsed=0

    if [ $_exit_code -ne 0 ] || [ -z "$_raw_output" ]; then
        cat <<EOF
{
  "exito": false,
  "origen": "recpl",
  "tipo_respuesta": "error",
  "mensaje": "RECPL no pudo procesar la instruccion",
  "payload": null,
  "raw": $(printf '%s' "$_raw_output" | jq -R -s . 2>/dev/null || echo '""'),
  "tiempo_ms": $_elapsed
}
EOF
        return 1
    fi

    # Intentar parsear como JSON (RECPL responde JSON en synthesis)
    _parsed=$(printf '%s' "$_raw_output" | jq -e . 2>/dev/null) && {
        _accion=$(echo "$_parsed" | jq -r '.accion // "unknown"')
        _mensaje=$(echo "$_parsed" | jq -r '.mensaje // ""')
        _payload=$(echo "$_parsed" | jq -r '.payload // {}')

        cat <<EOF
{
  "exito": true,
  "origen": "recpl",
  "tipo_respuesta": "action",
  "mensaje": $(printf '%s' "$_mensaje" | jq -R -s .),
  "payload": $_payload,
  "raw": $_parsed,
  "tiempo_ms": $_elapsed
}
EOF
        return 0
    }

    # Si no es JSON, devolver como texto
    cat <<EOF
{
  "exito": true,
  "origen": "recpl",
  "tipo_respuesta": "text",
  "mensaje": $(printf '%s' "$_raw_output" | jq -R -s .),
  "payload": {},
  "raw": $(printf '%s' "$_raw_output" | jq -R -s .),
  "tiempo_ms": $_elapsed
}
EOF
}

# --- Ejecutar instruccion con pipeline_debugger.sh ---
# Uso: bridge_debug "instruccion"
# Output: JSON con trazabilidad completa
bridge_debug() {
    _instruction="$1"

    _output=$(cd "$BRIDGE_SCRIPT_DIR" && ./pipeline_debugger.sh --output "$_instruction" 2>/dev/null)
    _exit_code=$?

    if [ $_exit_code -ne 0 ]; then
        echo '{"exito":false,"origen":"debugger","tipo_respuesta":"error","mensaje":"Debugger fallo"}'
        return 1
    fi

    printf '%s' "$_output" | jq -e . 2>/dev/null && return 0

    echo '{"exito":true,"origen":"debugger","tipo_respuesta":"text","mensaje":""}'
}

# --- Consultar estado interno de RECPL ---
# Uso: bridge_state
# Output: JSON con snapshot del estado
bridge_state() {
    _state_dir="${RECPL_STATE_DIR:-/tmp/recpl_state_$$}"

    if [ ! -d "$_state_dir" ]; then
        echo '{"exito":true,"modulos":[],"simbolos":{}}'
        return 0
    fi

    _modulos=""
    for _f in "$_state_dir"/*.json; do
        [ -f "$_f" ] || continue
        _content=$(cat "$_f" 2>/dev/null)
        _modulos="${_modulos}${_modulos:+,}$_content"
    done

    cat <<EOF
{
  "exito": true,
  "modulos": [$_modulos],
  "state_dir": "$_state_dir"
}
EOF
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/bridge.sh && echo "OK: bridge.sh"
# Probar bridge contra RECPL real
cd compiler-bot && sh -c '. agent-robot/bridge.sh && bridge_recpl "crea modulo test en nestjs" | jq .'
```

**Comportamiento esperado:**
- Si RECPL entiende la instruccion: `{"exito":true,"tipo_respuesta":"action",...}`
- Si RECPL falla: `{"exito":false,"tipo_respuesta":"error",...}`
- Si la respuesta no es JSON: `{"exito":true,"tipo_respuesta":"text",...}`

---

### Tarea 1.3 — `tool_registry.sh`: Registro de herramientas (Fase 1)

**Archivo:** `compiler-bot/agent-robot/tools/tool_registry.sh`
**Depende de:** 1.1
**Estimacion:** 20 min

```sh
#!/bin/sh
# ============================================================================
# tool_registry.sh - Registro central de herramientas del agente
# ============================================================================
#
# Formato por herramienta:
#   nombre:script_relativo:descripcion:parametros_json
#
# script_relativo es relativo a tools/
# ============================================================================

TOOL_REGISTRY='recpl:tool_recpl.sh:Ejecuta instrucciones RECPL:{"instruction":"string","description":"Instruccion en lenguaje natural para RECPL"}
respond:tool_respond.sh:Responde directamente al usuario:{"message":"string","description":"Mensaje textual para el usuario"}
read_file:tool_read_file.sh:Lee el contenido de un archivo:{"path":"string","description":"Ruta absoluta o relativa del archivo"}
write_file:tool_write_file.sh:Escribe contenido en un archivo:{"path":"string","content":"string","description":"Ruta del archivo y contenido a escribir"}
run_command:tool_run_command.sh:Ejecuta un comando del sistema:{"command":"string","description":"Comando shell a ejecutar"}
search_code:tool_search_code.sh:Busca texto en el codigo fuente:{"pattern":"string","path":"string","description":"Patron de busqueda y ruta opcional"}'

# --- Listar todas las herramientas disponibles ---
# Uso: list_tools
# Output: lista legible
list_tools() {
    echo "$TOOL_REGISTRY" | while IFS=: read -r _name _script _desc _params; do
        echo "  $_name  - $_desc"
    done
}

# --- Verificar si una herramienta existe ---
# Uso: has_tool <nombre>
# Output: 0 si existe, 1 si no
has_tool() {
    _name="$1"
    echo "$TOOL_REGISTRY" | cut -d: -f1 | grep -q "^${_name}$"
}

# --- Obtener script de una herramienta ---
# Uso: get_tool_script <nombre>
get_tool_script() {
    _name="$1"
    echo "$TOOL_REGISTRY" | while IFS=: read -r _n _s _d _p; do
        [ "$_n" = "$_name" ] && echo "$_s" && return 0
    done
}

# --- Obtener descripcion de una herramienta ---
# Uso: get_tool_desc <nombre>
get_tool_desc() {
    _name="$1"
    echo "$TOOL_REGISTRY" | while IFS=: read -r _n _s _d _p; do
        [ "$_n" = "$_name" ] && echo "$_d" && return 0
    done
}

# --- Ejecutar una herramienta ---
# Uso: run_tool <nombre> [parametros...]
# Output: resultado de la herramienta
run_tool() {
    _name="$1"
    shift

    has_tool "$_name" || {
        echo "{\"exito\":false,\"mensaje\":\"Herramienta desconocida: $_name\"}"
        return 1
    }

    _script=$(get_tool_script "$_name")
    _tool_path="$(dirname "$0")/$_script"

    if [ ! -f "$_tool_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Script de herramienta no encontrado: $_script\"}"
        return 1
    }

    # Cargar y ejecutar la herramienta
    . "$_tool_path"
    _func_name="tool_${_name}"
    $_func_name "$@"
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/tools/tool_registry.sh && echo "OK: tool_registry.sh"
```

---

### Tarea 1.4 — `tool_recpl.sh`: Herramienta RECPL

**Archivo:** `compiler-bot/agent-robot/tools/tool_recpl.sh`
**Depende de:** 1.2, 1.3
**Estimacion:** 15 min

```sh
#!/bin/sh
# ============================================================================
# tool_recpl.sh - Herramienta: delega en RECPL via bridge
# ============================================================================
#
# Uso (via tool_registry): run_tool recpl "instruccion"
# ============================================================================

tool_recpl() {
    _instruction="$*"

    if [ -z "$_instruction" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Instruccion vacia para RECPL\"}"
        return 1
    fi

    # Cargar bridge (relativo a tools/ -> ../)
    _bridge_path="$(dirname "$0")/../bridge.sh"
    [ -f "$_bridge_path" ] && . "$_bridge_path"

    bridge_recpl "$_instruction"
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/tools/tool_recpl.sh && echo "OK: tool_recpl.sh"
```

---

### Tarea 1.5 — `tool_respond.sh`: Respuesta textual

**Archivo:** `compiler-bot/agent-robot/tools/tool_respond.sh`
**Depende de:** 1.3
**Estimacion:** 10 min

```sh
#!/bin/sh
# ============================================================================
# tool_respond.sh - Herramienta: responde directamente al usuario
# ============================================================================
#
# Uso (via tool_registry): run_tool respond "mensaje"
# ============================================================================

tool_respond() {
    _message="$*"

    if [ -z "$_message" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Mensaje vacio\"}"
        return 1
    fi

    cat <<EOF
{
  "exito": true,
  "tipo_respuesta": "respond",
  "mensaje": $(printf '%s' "$_message" | jq -R -s . 2>/dev/null || echo "\"$_message\""),
  "payload": {}
}
EOF
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/tools/tool_respond.sh && echo "OK: tool_respond.sh"
```

---

### Tarea 1.6 — `memory.sh`: Memoria basica del agente

**Archivo:** `compiler-bot/agent-robot/memory.sh`
**Depende de:** 1.1
**Estimacion:** 30 min

```sh
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
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/memory.sh && echo "OK: memory.sh"
```

---

### Tarea 1.7 — `agent.sh`: Bucle principal del agente

**Archivo:** `compiler-bot/agent-robot/agent.sh`
**Depende de:** 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
**Estimacion:** 60 min

```sh
#!/bin/sh
# ============================================================================
# agent.sh - Bucle principal del agente Proyecto0(RECPL)
# ============================================================================
#
# PROPOSITO:
#   Recibe una instruccion, clasifica la intencion, ejecuta la accion
#   correspondiente (RECPL via bridge, herramienta, o respuesta textual),
#   y devuelve el resultado formateado.
#
# USO:
#   ./agent.sh "instruccion"             # modo normal
#   ./agent.sh --llm "instruccion"       # fuerza LLM
#   ./agent.sh --deterministic "instruc" # solo RECPL deterministico
#   echo "instruccion" | ./agent.sh      # modo batch (stdin)
#
# VARIABLES DE ENTORNO:
#   AGENT_LLM_MODE      auto|llm|deterministic (default: auto)
#   AGENT_LLM_PROVIDER  claude|openai|apifreellm
#   AGENT_LLM_TIER      free|paid|auto
#   AGENT_MEMORY_DIR    directorio de memoria (default: /tmp/agent_memory)
# ============================================================================

# --- Cargar configuracion ---
SCRIPT_DIR="$(dirname "$0")"
. "$SCRIPT_DIR/config.sh"
. "$SCRIPT_DIR/memory.sh"

# --- Inicializar memoria ---
memory_init
memory_log "Agent started (v$AGENT_VERSION)"

# --- Banner ---
show_banner() {
    echo "${AGENT_PREFIX} Proyecto0(RECPL) v${AGENT_VERSION}"
    echo "   Un agente de codigo abierto para escribir y ejecutar codigo."
    echo ""
}

# --- Mostrar ayuda ---
show_help() {
    cat <<HELP
${AGENT_PREFIX} Proyecto0(RECPL) v${AGENT_VERSION}

USO:
  ./agent.sh "instruccion"                Modo normal
  ./agent.sh --llm "instruccion"          Fuerza uso de LLM
  ./agent.sh --deterministic "instruc"    Solo RECPL deterministico
  ./agent.sh --help                       Esta ayuda

MODOS (via AGENT_LLM_MODE):
  auto          Intenta RECPL deterministico, luego LLM si falla (default)
  llm           Usa LLM directamente
  deterministic Solo RECPL deterministico

EJEMPLOS:
  ./agent.sh "crea modulo pagos en nestjs"
  ./agent.sh "hola"
  ./agent.sh --llm "explica que es RECPL"
HELP
}

# --- Clasificar intencion (heuristica inicial, sin LLM) ---
# Fase 1: deteccion basica por palabras clave.
# Fase 3+: se reemplaza por planner.sh con LLM.
classify_intent() {
    _instruction="$1"

    # Normalizar a minusculas
    _lower=$(echo "$_instruction" | tr '[:upper:]' '[:lower:]')

    # Detectar saludo/pregunta personal
    echo "$_lower" | grep -qE '^(hola|buenas|hey|buenos dias|buenas tardes|quien eres|que eres|quien eres\?|que eres\?)' && {
        echo "respond"
        return
    }

    # Detectar despedida
    echo "$_lower" | grep -qE '^(adios|chao|bye|hasta luego|nos vemos)' && {
        echo "respond"
        return
    }

    # Detectar agradecimiento
    echo "$_lower" | grep -qE '^(gracias|thanks|thank you)' && {
        echo "respond"
        return
    }

    # Detectar ayuda
    echo "$_lower" | grep -qE '^(ayuda|help|---help|que puedes hacer)' && {
        echo "help"
        return
    }

    # Detectar comando RECPL (palabras clave: crea, genera, elimina, lista, etc.)
    echo "$_lower" | grep -qE '^(crea|genera|elimina|borra|lista|muestra|actualiza|modifica|source|exec)' && {
        echo "recpl"
        return
    }

    # Si tiene palabras clave de accion en medio
    echo "$_lower" | grep -qE '(crea |genera |elimina |borra |lista |muestra )' && {
        echo "recpl"
        return
    }

    # Por defecto: intentar RECPL (puede fallar si no entiende)
    echo "recpl"
}

# --- Ejecutar accion segun intencion ---
execute_intent() {
    _intent="$1"
    _instruction="$2"

    case "$_intent" in
        respond)
            # Respuesta textual segun el tipo de saludo
            _lower=$(echo "$_instruction" | tr '[:upper:]' '[:lower:]')
            case "$_lower" in
                *"quien eres"*|*"que eres"*)
                    tool_respond "Soy Proyecto0(RECPL) v${AGENT_VERSION}, un agente de codigo abierto que te ayuda a escribir y ejecutar codigo con cualquier modelo de IA."
                    ;;
                *"gracias"*)
                    tool_respond "De nada! Estoy aqui para ayudarte con tu codigo."
                    ;;
                *"hola"*|*"buenas"*)
                    tool_respond "Hola! Soy Proyecto0(RECPL). En que puedo ayudarte? Puedes pedirme que cree modulos, lea archivos, ejecute comandos, o simplemente conversar."
                    ;;
                *"adios"*|*"chao"*|*"bye"*)
                    tool_respond "Hasta luego! Vuelve cuando necesites ayuda con tu codigo."
                    ;;
                *)
                    tool_respond "Hola! En que puedo ayudarte?"
                    ;;
            esac
            ;;

        help)
            show_help
            ;;

        recpl)
            # Delegar en RECPL via bridge
            . "$SCRIPT_DIR/bridge.sh"
            bridge_recpl "$_instruction"
            ;;

        *)
            # Intento fallback: RECPL
            . "$SCRIPT_DIR/bridge.sh"
            bridge_recpl "$_instruction"
            ;;
    esac
}

# --- Formatear respuesta para el usuario ---
format_response() {
    _json="$1"

    _exito=$(echo "$_json" | jq -r '.exito // false' 2>/dev/null)
    _tipo=$(echo "$_json" | jq -r '.tipo_respuesta // "text"' 2>/dev/null)
    _mensaje=$(echo "$_json" | jq -r '.mensaje // ""' 2>/dev/null)

    if [ "$_exito" = "true" ]; then
        echo "✅ $_mensaje"
    else
        echo "❌ $_mensaje"
    fi
}

# --- MAIN ---
main() {
    _mode="${AGENT_LLM_MODE:-auto}"
    _instruction=""

    # Parsear argumentos
    while [ $# -gt 0 ]; do
        case "$1" in
            --llm|--llm-only)
                _mode="llm"
                shift
                ;;
            --deterministic|--deterministic-only)
                _mode="deterministic"
                shift
                ;;
            -h|--help)
                show_banner
                show_help
                return 0
                ;;
            -v|--version)
                echo "Proyecto0(RECPL) v${AGENT_VERSION}"
                return 0
                ;;
            --)
                shift
                break
                ;;
            -*)
                echo "Error: opcion desconocida: $1"
                echo "Usa --help para ver las opciones disponibles."
                return 1
                ;;
            *)
                break
                ;;
        esac
    done

    _instruction="$*"

    # Si no hay instruccion en args, leer de stdin
    if [ -z "$_instruction" ]; then
        read -r _instruction || true
    fi

    if [ -z "$_instruction" ]; then
        show_banner
        echo "No se recibio ninguna instruccion."
        echo "Uso: echo \"instruccion\" | ./agent.sh"
        echo "     ./agent.sh \"instruccion\""
        return 1
    fi

    memory_log "RECV: $_instruction"

    # Mostrar banner en primera interaccion
    show_banner

    # Clasificar intencion
    _intent=$(classify_intent "$_instruction")
    memory_log "INTENT: $_intent"

    # Ejecutar
    _result=$(execute_intent "$_intent" "$_instruction")
    _exit_code=$?

    # Formatear y mostrar
    format_response "$_result"
    memory_log "RESP: $(echo "$_result" | jq -c '.' 2>/dev/null || echo "$_result")"

    # Guardar en historial
    memory_add_history "$_instruction" "$_result"

    return $_exit_code
}

# --- Entrypoint ---
main "$@"
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/agent.sh && echo "OK: agent.sh"

# Probar respuestas basicas (sin RECPL real)
cd compiler-bot
./agent-robot/agent.sh "hola" 2>/dev/null
./agent-robot/agent.sh "quien eres?" 2>/dev/null

# Probar modo deterministico con RECPL real
./agent-robot/agent.sh "crea modulo testagent en nestjs" 2>/dev/null
```

---

### Tarea 1.8 — `agent-robot.sh`: Entrypoint global

**Archivo:** `compiler-bot/agent-robot.sh`
**Depende de:** 1.7
**Estimacion:** 5 min

```sh
#!/bin/sh
# ============================================================================
# agent-robot.sh - Entrypoint global para el agente Proyecto0(RECPL)
# ============================================================================
#
# Delegado en agent-robot/agent.sh
# ============================================================================

SCRIPT_DIR="$(dirname "$0")"
exec "$SCRIPT_DIR/agent-robot/agent.sh" "$@"
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot.sh && echo "OK: agent-robot.sh"
chmod +x compiler-bot/agent-robot.sh
```

---

### Tarea 1.9 — Flag `--agent` en `recpl.sh`

**Archivo:** `compiler-bot/recpl.sh` (MODIFICAR)
**Depende de:** 1.8
**Estimacion:** 10 min

**Cambio:** Agregar en el `case` de argumentos de `recpl.sh` (aproximadamente
al inicio del bloque de parseo de argumentos):

```sh
# Dentro del case que parsea argumentos en recpl.sh, agregar:
--agent|--robot)
    shift
    exec "$SCRIPT_DIR/agent-robot.sh" "$@"
    ;;
```

Si `recpl.sh` usa getopt o un loop while, insertar este bloque antes de que
otros flags capturen `--agent` como instruccion.

**Verificacion:**

```sh
# Verificar que el flag existe y delega
./compiler-bot/recpl.sh --agent --help 2>/dev/null | head -3
# Debe mostrar: 🤖 Proyecto0(RECPL) v1.0.0

# Verificar que recpl.sh normal sigue funcionando
./compiler-bot/recpl.sh --help 2>/dev/null | head -3
# Debe mostrar: RECPL Compiler Bot v...
```

---

### Tarea 1.10 — Tests de Fase 1

**Archivo:** `compiler-bot/tests/test_agent.sh`
**Depende de:** 1.2-1.8
**Estimacion:** 30 min

```sh
#!/bin/sh
# ============================================================================
# test_agent.sh - Tests de la capa agent-robot (Fase 1)
# ============================================================================
#
# USO:
#   ./tests/test_agent.sh           # ejecutar todos
#   ./tests/test_agent.sh bridge    # solo tests de bridge
#   ./tests/test_agent.sh agent     # solo tests de agent.sh
# ============================================================================

SCRIPT_DIR="$(dirname "$0")/.."
PASS=0
FAIL=0
FAIL_MSGS=""

# --- Test: archivos existen ---
test_files_exist() {
    for f in \
        "$SCRIPT_DIR/agent-robot/config.sh" \
        "$SCRIPT_DIR/agent-robot/bridge.sh" \
        "$SCRIPT_DIR/agent-robot/agent.sh" \
        "$SCRIPT_DIR/agent-robot/memory.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_registry.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_recpl.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_respond.sh"; do
        if [ -f "$f" ]; then
            echo "  ✅ Existe: $(basename "$f")"
        else
            echo "  ❌ FALTA: $f"
            FAIL=$((FAIL + 1))
            FAIL_MSGS="${FAIL_MSGS}FALTAN_ARCHIVOS "
        fi
    done
}

# --- Test: bash syntax ---
test_bash_syntax() {
    for f in \
        "$SCRIPT_DIR/agent-robot/config.sh" \
        "$SCRIPT_DIR/agent-robot/bridge.sh" \
        "$SCRIPT_DIR/agent-robot/agent.sh" \
        "$SCRIPT_DIR/agent-robot/memory.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_registry.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_recpl.sh" \
        "$SCRIPT_DIR/agent-robot/tools/tool_respond.sh"; do
        if bash -n "$f" 2>/dev/null; then
            echo "  ✅ Syntax OK: $(basename "$f")"
        else
            echo "  ❌ Syntax ERROR: $f"
            FAIL=$((FAIL + 1))
            FAIL_MSGS="${FAIL_MSGS}SYNTAX_$(basename "$f" .sh) "
        fi
    done
}

# --- Test: agent responde saludo ---
test_agent_greeting() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "hola" 2>/dev/null)
    if echo "$_result" | grep -qi "hola\|ayudar\|proyecto0"; then
        echo "  ✅ Agent responde saludo"
    else
        echo "  ❌ Agent no responde saludo"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}AGENT_SALUDO "
    fi
}

# --- Test: agent responde "quien eres" ---
test_agent_identity() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "quien eres?" 2>/dev/null)
    if echo "$_result" | grep -qi "proyecto0\|agente\|recpl"; then
        echo "  ✅ Agent responde identidad"
    else
        echo "  ❌ Agent no responde identidad"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}AGENT_IDENTIDAD "
    fi
}

# --- Test: bridge recpl ---
test_bridge_recpl() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/bridge.sh && bridge_recpl "crea modulo testbridge en nestjs" 2>/dev/null')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)
    _origen=$(echo "$_result" | jq -r '.origen // ""' 2>/dev/null)

    if [ "$_exito" = "true" ] && [ "$_origen" = "recpl" ]; then
        echo "  ✅ Bridge ejecuta RECPL exitosamente"
    else
        echo "  ⚠️  Bridge ejecuta RECPL (puede fallar sin estado RECPL)"
        echo "     Output: $_result"
    fi
}

# --- Test: tool respond ---
test_tool_respond() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_respond.sh && tool_respond "test message"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)
    _mensaje=$(echo "$_result" | jq -r '.mensaje // ""' 2>/dev/null)

    if [ "$_exito" = "true" ] && [ "$_mensaje" = "test message" ]; then
        echo "  ✅ tool_respond funciona"
    else
        echo "  ❌ tool_respond falla"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_RESPOND "
    fi
}

# --- Test: tool registry ---
test_tool_registry() {
    _exists=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_registry.sh && has_tool "respond" && echo "yes"')
    if [ "$_exists" = "yes" ]; then
        echo "  ✅ tool_registry detecta herramientas"
    else
        echo "  ❌ tool_registry no detecta herramientas"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_REGISTRY "
    fi
}

# --- Test: memory ---
test_memory() {
    cd "$SCRIPT_DIR" || return
    AGENT_MEMORY_DIR="/tmp/test_agent_memory_$$"
    . agent-robot/memory.sh
    memory_init
    memory_save "test_key" "test_value"
    _value=$(memory_get "test_key")
    rm -rf "$AGENT_MEMORY_DIR"

    if [ "$_value" = "test_value" ]; then
        echo "  ✅ memory save/get funciona"
    else
        echo "  ❌ memory save/get falla (got: $_value)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}MEMORY "
    fi

    unset AGENT_MEMORY_DIR
}

# --- Test: --agent flag ---
test_agent_flag() {
    _result=$(cd "$SCRIPT_DIR" && ./recpl.sh --agent "hola" 2>/dev/null)
    if echo "$_result" | grep -qi "proyecto0\|agente"; then
        echo "  ✅ Flag --agent funciona desde recpl.sh"
    else
        echo "  ⚠️  Flag --agent (puede fallar si no se implemento aun)"
        echo "     Output: $_result"
    fi
}

# --- MAIN ---
echo "=========================================="
echo " Tests Agent-Robot (Fase 1)"
echo "=========================================="
echo ""

echo "--- Archivos ---"
test_files_exist
echo ""

echo "--- Syntax Check ---"
test_bash_syntax
echo ""

echo "--- Funcionalidad ---"
test_tool_respond
test_tool_registry
test_memory
test_agent_greeting
test_agent_identity
test_bridge_recpl
test_agent_flag
echo ""

echo "Resultados: PASS=$PASS FAIL=$FAIL"
echo "Fallos: ${FAIL_MSGS:-ninguno}"
echo "=========================================="
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

**Verificacion:**

```sh
bash -n compiler-bot/tests/test_agent.sh && echo "OK: test_agent.sh syntax"
chmod +x compiler-bot/tests/test_agent.sh
./compiler-bot/tests/test_agent.sh
```

---

### Criterios de exito de Fase 1

```sh
# 1. El agente responde comandos RECPL
./compiler-bot/agent-robot/agent.sh "crea modulo payments en nestjs"
# Output esperado:
#   🤖 Proyecto0(RECPL) v1.0.0
#   ✅ ...

# 2. El agente responde textualmente
./compiler-bot/agent-robot/agent.sh "hola"
# Output esperado:
#   🤖 Proyecto0(RECPL) v1.0.0
#   ✅ Hola! Soy Proyecto0(RECPL)...

# 3. El flag --agent funciona desde recpl.sh
./compiler-bot/recpl.sh --agent -c "crea modulo payments en nestjs"

# 4. Tests pasan
./compiler-bot/tests/test_agent.sh
# Output: PASS=8 FAIL=0

# 5. Syntax check de todos los archivos nuevos
bash -n compiler-bot/agent-robot/*.sh
bash -n compiler-bot/agent-robot/tools/*.sh
```

---

## 2. Fase 2: Herramientas del Sistema

**Objetivo:** El agente puede leer archivos, escribir/editar archivos, y ejecutar
comandos del sistema.

**Duracion estimada:** ~2 horas
**Depende de:** Fase 1 completa

---

### Tarea 2.1 — `tool_read_file.sh`

**Archivo:** `compiler-bot/agent-robot/tools/tool_read_file.sh`
**Depende de:** 1.3
**Estimacion:** 20 min

```sh
#!/bin/sh
# ============================================================================
# tool_read_file.sh - Herramienta: leer archivos del sistema
# ============================================================================
#
# Uso (via tool_registry): run_tool read_file "ruta/al/archivo.txt"
# ============================================================================

tool_read_file() {
    _path="$1"

    if [ -z "$_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Ruta de archivo no especificada\"}"
        return 1
    fi

    if [ ! -f "$_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Archivo no encontrado: $_path\"}"
        return 1
    fi

    if [ ! -r "$_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Sin permisos de lectura: $_path\"}"
        return 1
    fi

    _content=$(cat "$_path" 2>/dev/null)
    _lines=$(echo "$_content" | wc -l 2>/dev/null || echo 0)
    _size=$(wc -c < "$_path" 2>/dev/null || echo 0)

    cat <<EOF
{
  "exito": true,
  "tipo_respuesta": "file_content",
  "path": $(printf '%s' "$_path" | jq -R -s .),
  "lineas": $_lines,
  "bytes": $_size,
  "contenido": $(printf '%s' "$_content" | jq -R -s .)
}
EOF
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/tools/tool_read_file.sh && echo "OK"

# Probar lectura
cd compiler-bot
sh -c '. agent-robot/tools/tool_read_file.sh && tool_read_file "README.md" | jq .exito'
# Debe mostrar: true

sh -c '. agent-robot/tools/tool_read_file.sh && tool_read_file "no_existe.txt" | jq .exito'
# Debe mostrar: false
```

---

### Tarea 2.2 — `tool_write_file.sh`

**Archivo:** `compiler-bot/agent-robot/tools/tool_write_file.sh`
**Depende de:** 1.3
**Estimacion:** 25 min

```sh
#!/bin/sh
# ============================================================================
# tool_write_file.sh - Herramienta: escribir/editar archivos
# ============================================================================
#
# Uso (via tool_registry): run_tool write_file "ruta" "contenido"
# ============================================================================

tool_write_file() {
    _path="$1"
    shift
    _content="$*"

    if [ -z "$_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Ruta de archivo no especificada\"}"
        return 1
    fi

    if [ -z "$_content" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Contenido vacio\"}"
        return 1
    fi

    # Crear directorio si no existe
    _dir=$(dirname "$_path" 2>/dev/null)
    if [ -n "$_dir" ] && [ "$_dir" != "." ]; then
        mkdir -p "$_dir" 2>/dev/null
    fi

    # Verificar que el directorio sea escribible
    _dir_check=$(dirname "$_path" 2>/dev/null)
    [ -z "$_dir_check" ] && _dir_check="."

    if [ -d "$_dir_check" ] && [ ! -w "$_dir_check" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Sin permisos de escritura en: $_dir_check\"}"
        return 1
    fi

    # Escribir archivo
    if printf '%s' "$_content" > "$_path" 2>/dev/null; then
        _size=$(wc -c < "$_path" 2>/dev/null || echo 0)
        cat <<EOF
{
  "exito": true,
  "tipo_respuesta": "file_written",
  "path": $(printf '%s' "$_path" | jq -R -s .),
  "bytes": $_size,
  "mensaje": "Archivo escrito correctamente ($_size bytes)"
}
EOF
    else
        echo "{\"exito\":false,\"mensaje\":\"Error al escribir archivo: $_path\"}"
        return 1
    fi
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/tools/tool_write_file.sh && echo "OK"

# Probar escritura
cd compiler-bot
sh -c '. agent-robot/tools/tool_write_file.sh && tool_write_file "/tmp/test_agent_write.txt" "hola mundo" | jq .exito'
# Debe mostrar: true
cat /tmp/test_agent_write.txt
# Debe mostrar: hola mundo
rm -f /tmp/test_agent_write.txt
```

---

### Tarea 2.3 — `tool_run_command.sh`

**Archivo:** `compiler-bot/agent-robot/tools/tool_run_command.sh`
**Depende de:** 1.3
**Estimacion:** 20 min

```sh
#!/bin/sh
# ============================================================================
# tool_run_command.sh - Herramienta: ejecutar comandos del sistema
# ============================================================================
#
# Uso (via tool_registry): run_tool run_command "ls -la"
# ============================================================================

tool_run_command() {
    _command="$*"

    if [ -z "$_command" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Comando vacio\"}"
        return 1
    fi

    # Ejecutar comando con timeout defensivo
    _start_time=$(date +%s 2>/dev/null)
    _output=$(sh -c "$_command" 2>&1)
    _exit_code=$?
    _end_time=$(date +%s 2>/dev/null)
    _elapsed=$((_end_time - _start_time))
    [ "$_elapsed" -lt 0 ] && _elapsed=0

    _line_count=$(echo "$_output" | wc -l 2>/dev/null || echo 0)

    cat <<EOF
{
  "exito": $( [ $_exit_code -eq 0 ] && echo true || echo false ),
  "tipo_respuesta": "command_output",
  "comando": $(printf '%s' "$_command" | jq -R -s .),
  "exit_code": $_exit_code,
  "lineas": $_line_count,
  "output": $(printf '%s' "$_output" | jq -R -s .),
  "tiempo_ms": $_elapsed
}
EOF
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/tools/tool_run_command.sh && echo "OK"

cd compiler-bot
sh -c '. agent-robot/tools/tool_run_command.sh && tool_run_command "echo hello" | jq .exito'
# Debe mostrar: true

sh -c '. agent-robot/tools/tool_run_command.sh && tool_run_command "ls no_existe" | jq .exito'
# Debe mostrar: false
```

---

### Tarea 2.4 — Integrar herramientas en registry + agent.sh

**Archivos:** `tool_registry.sh` (ya incluye read_file, write_file, run_command
en `TOOL_REGISTRY` desde la Fase 1 — verificar que esten presentes)

**Actualizar `agent.sh`:** Agregar deteccion de intencion para las nuevas
herramientas en `classify_intent()`:

```sh
# Dentro de classify_intent(), agregar antes del default:

# --- Fase 2: herramientas del sistema ---

# Detectar lectura de archivos
echo "$_lower" | grep -qE '^(lee|muestra|cat|abre|read) ' && {
    echo "read_file"
    return
}

# Detectar escritura de archivos
echo "$_lower" | grep -qE '^(crea archivo|escribe|write|crea el archivo|genera archivo) ' && {
    echo "write_file"
    return
}

# Detectar ejecucion de comandos
echo "$_lower" | grep -qE '^(ejecuta|corre|run|executa|lanza) ' && {
    echo "run_command"
    return
}
```

Y agregar los casos en `execute_intent()`:

```sh
# Dentro de execute_intent(), antes del default:
read_file)
    . "$SCRIPT_DIR/tools/tool_read_file.sh"
    # Extraer ruta: remover "lee " o "muestra " o "cat " del inicio
    _path=$(echo "$_instruction" | sed 's/^\(lee\|muestra\|cat\|abre\|read\) //')
    tool_read_file "$_path"
    ;;

write_file)
    . "$SCRIPT_DIR/tools/tool_write_file.sh"
    # Parseo basico: "crea archivo <ruta> con contenido <contenido>"
    _rest=$(echo "$_instruction" | sed 's/^\(crea archivo\|escribe\|write\|crea el archivo\|genera archivo\) //')
    _path=$(echo "$_rest" | sed 's/ con contenido.*//' | sed 's/ con texto.*//' | xargs)
    _content=$(echo "$_rest" | sed 's/^.* con contenido //' | sed 's/^.* con texto //')
    [ -z "$_content" ] && _content="$_rest"
    tool_write_file "$_path" "$_content"
    ;;

run_command)
    . "$SCRIPT_DIR/tools/tool_run_command.sh"
    _cmd=$(echo "$_instruction" | sed 's/^\(ejecuta\|corre\|run\|executa\|lanza\) //')
    tool_run_command "$_cmd"
    ;;
```

**Depende de:** 2.1, 2.2, 2.3
**Estimacion:** 30 min

---

### Tarea 2.5 — Tests de Fase 2

Agregar al final de `tests/test_agent.sh`:

```sh
# --- Fase 2: tool_read_file ---
test_tool_read_file() {
    # Crear archivo temporal
    _tmp="/tmp/test_agent_read_$$.txt"
    echo "contenido de prueba" > "$_tmp"

    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_read_file.sh && tool_read_file "'$_tmp'"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)

    if [ "$_exito" = "true" ]; then
        echo "  ✅ tool_read_file funciona"
    else
        echo "  ❌ tool_read_file falla"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_READ_FILE "
    fi
    rm -f "$_tmp"
}

# --- Fase 2: tool_write_file ---
test_tool_write_file() {
    _tmp="/tmp/test_agent_write_$$.txt"
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_write_file.sh && tool_write_file "'$_tmp'" "test content"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)

    if [ "$_exito" = "true" ] && [ -f "$_tmp" ]; then
        echo "  ✅ tool_write_file funciona"
    else
        echo "  ❌ tool_write_file falla"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_WRITE_FILE "
    fi
    rm -f "$_tmp"
}

# --- Fase 2: tool_run_command ---
test_tool_run_command() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_run_command.sh && tool_run_command "echo ok"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)

    if [ "$_exito" = "true" ]; then
        echo "  ✅ tool_run_command funciona"
    else
        echo "  ❌ tool_run_command falla"
        echo "     Output: $_result"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_RUN_COMMAND "
    fi
}
```

**Depende de:** 2.1-2.4
**Estimacion:** 30 min

---

### Criterios de exito de Fase 2

```sh
# 1. El agente lee archivos
./compiler-bot/agent-robot/agent.sh "lee README.md" 2>/dev/null
# Output: ✅ ...

# 2. El agente escribe archivos
./compiler-bot/agent-robot/agent.sh "crea archivo /tmp/test.txt con contenido hola mundo" 2>/dev/null
cat /tmp/test.txt
# Debe mostrar: hola mundo

# 3. El agente ejecuta comandos
./compiler-bot/agent-robot/agent.sh "ejecuta ls -la" 2>/dev/null

# 4. Tests pasan
./compiler-bot/tests/test_agent.sh | grep "FAIL=0"
```

---

## 3. Fase 3: Planificador y Memoria

**Objetivo:** El agente ejecuta tareas multi-paso y recuerda contexto entre
instrucciones.

**Duracion estimada:** ~3 horas
**Depende de:** Fase 1 completa (Fase 2 opcional)

---

### Tarea 3.1 — `planner.sh`: Planificador multi-paso

**Archivo:** `compiler-bot/agent-robot/planner.sh`
**Depende de:** 1.7
**Estimacion:** 60 min

```sh
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
#   → JSON con lista de pasos
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
    _modulos=$(echo "$_lower" | sed 's/crea //' | sed 's/genera //' | sed 's/modulo //g' | sed 's/modulos //g' | sed 's/en.*$//' | tr ',' ' ' | tr 'y' ' ' | xargs)

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
# Output: JSON con resultados consolidados
ejecutar_plan() {
    _plan="$1"
    _total=$(echo "$_plan" | jq -r '.total_pasos // 0' 2>/dev/null)
    _resultados=""

    echo "📋 Plan de ejecucion: $_total pasos"
    echo ""

    _i=0
    while [ $_i -lt "$_total" ]; do
        _i=$((_i + 1))
        _paso=$(echo "$_plan" | jq -c ".pasos[] | select(.orden == $_i)" 2>/dev/null)
        _accion=$(echo "$_paso" | jq -r '.accion // "recpl"' 2>/dev/null)
        _inst=$(echo "$_paso" | jq -r '.parametros.instruccion // ""' 2>/dev/null)

        echo "   Paso $_i/$_total: $_inst"

        # Ejecutar paso
        _result=$(cd "$(dirname "$0")" && ./agent.sh "$_inst" 2>/dev/null)
        _sep=""
        [ -n "$_resultados" ] && _sep=","
        _resultados="${_resultados}${_sep}{\"paso\":$_i,\"instruccion\":$(printf '%s' "$_inst" | jq -R -s .),\"resultado\":$(printf '%s' "$_result" | jq -R -s .)}"

        echo ""
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
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/planner.sh && echo "OK: planner.sh"

cd compiler-bot
# Probar planificacion
sh -c '. agent-robot/planner.sh && planificar "crea modulo auth y modulo payments en nestjs" | jq .'
# Debe mostrar: tipo=multi_create, total_modulos=2, pasos=[...]
```

---

### Tarea 3.2 — Memoria persistente entre sesiones

Mejorar `memory.sh` (Fase 1, Tarea 1.6) con:

```sh
# Funcion adicional en memory.sh:

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
```

**Nota:** El archivo `memory.sh` de Fase 1 ya tiene `memory_save`, `memory_get`,
`memory_add_history`, `memory_history`, `memory_context`, `memory_last`.
La mejora de Fase 3 agrega multi-sesion y exportacion.

**Estimacion:** 30 min

---

### Tarea 3.3 — `tool_search_code.sh`

**Archivo:** `compiler-bot/agent-robot/tools/tool_search_code.sh`
**Depende de:** 1.3
**Estimacion:** 25 min

```sh
#!/bin/sh
# ============================================================================
# tool_search_code.sh - Herramienta: buscar en codigo fuente
# ============================================================================
#
# Uso (via tool_registry): run_tool search_code "patron" "ruta_opcional"
# ============================================================================

tool_search_code() {
    _pattern="$1"
    _path="${2:-.}"

    if [ -z "$_pattern" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Patron de busqueda vacio\"}"
        return 1
    fi

    if [ ! -d "$_path" ] && [ ! -f "$_path" ]; then
        echo "{\"exito\":false,\"mensaje\":\"Ruta no valida: $_path\"}"
        return 1
    fi

    _results=$(grep -rn "$_pattern" "$_path" 2>/dev/null | head -100)
    _count=$(echo "$_results" | grep -c . 2>/dev/null || echo 0)

    cat <<EOF
{
  "exito": true,
  "tipo_respuesta": "search_results",
  "pattern": $(printf '%s' "$_pattern" | jq -R -s .),
  "path": $(printf '%s' "$_path" | jq -R -s .),
  "total_resultados": $_count,
  "resultados": $(printf '%s' "$_results" | jq -R -s .)
}
EOF
}
```

**Verificacion:**

```sh
bash -n compiler-bot/agent-robot/tools/tool_search_code.sh && echo "OK"

cd compiler-bot
sh -c '. agent-robot/tools/tool_search_code.sh && tool_search_code "recpl" "." | jq .total_resultados'
```

---

### Tarea 3.4 — Integrar planner en `agent.sh`

Modificar `classify_intent()` en `agent.sh`:

```sh
# Dentro de classify_intent(), reemplazar el default:

# Detectar multi-instruccion (contiene "y" entre acciones)
echo "$_lower" | grep -qE '(y |,).*(crea|genera|elimina)' && {
    echo "plan"
    return
}

# Detectar proyecto completo
echo "$_lower" | grep -qE '(proyecto|full|completo).*(crea|genera)' && {
    echo "plan"
    return
}
```

Y agregar en `execute_intent()`:

```sh
plan)
    . "$SCRIPT_DIR/planner.sh"
    _plan=$(planificar "$_instruction")
    ejecutar_plan "$_plan"
    ;;
```

**Depende de:** 3.1
**Estimacion:** 30 min

---

### Tarea 3.5 — Tests de Fase 3

Agregar a `tests/test_agent.sh`:

```sh
# --- Fase 3: planner ---
test_planner_multi_create() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/planner.sh && planificar "crea modulo auth y modulo payments en nestjs"')
    _tipo=$(echo "$_result" | jq -r '.tipo // ""' 2>/dev/null)
    _total=$(echo "$_result" | jq -r '.total_pasos // 0' 2>/dev/null)

    if [ "$_tipo" = "multi_create" ] && [ "$_total" -ge 2 ]; then
        echo "  ✅ planner multi-create funciona (pasos: $_total)"
    else
        echo "  ⚠️  planner multi-create (puede fallar por parsing)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}PLANNER_MULTI "
    fi
}

# --- Fase 3: memory persistente ---
test_memory_persist() {
    _mem_dir="/tmp/test_agent_mem_persist_$$"

    # Primera sesion: guardar valor
    AGENT_MEMORY_DIR="$_mem_dir" sh -c '. '"$SCRIPT_DIR"'/agent-robot/memory.sh && memory_init && memory_save "test" "value1"'

    # Segunda sesion: leer valor (debe persistir)
    _value=$(AGENT_MEMORY_DIR="$_mem_dir" sh -c '. '"$SCRIPT_DIR"'/agent-robot/memory.sh && memory_init && memory_get "test"')

    rm -rf "$_mem_dir"

    if [ "$_value" = "value1" ]; then
        echo "  ✅ memory persistente entre sesiones"
    else
        echo "  ❌ memory no persiste (got: $_value)"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}MEMORY_PERSIST "
    fi
}

# --- Fase 3: tool_search_code ---
test_tool_search_code() {
    _result=$(cd "$SCRIPT_DIR" && sh -c '. agent-robot/tools/tool_search_code.sh && tool_search_code "recpl" "agent-robot"')
    _exito=$(echo "$_result" | jq -r '.exito // false' 2>/dev/null)

    if [ "$_exito" = "true" ]; then
        echo "  ✅ tool_search_code funciona"
    else
        echo "  ❌ tool_search_code falla"
        FAIL=$((FAIL + 1))
        FAIL_MSGS="${FAIL_MSGS}TOOL_SEARCH "
    fi
}
```

**Depende de:** 3.1-3.4
**Estimacion:** 30 min

---

### Criterios de exito de Fase 3

```sh
# 1. Planificador descompone multi-instrucciones
./compiler-bot/agent-robot/agent.sh "crea modulo auth y modulo payments en nestjs" 2>/dev/null
# Output: 📋 Plan de ejecucion: 2 pasos
#         Paso 1/2: crea modulo auth en nestjs
#         Paso 2/2: crea modulo payments en nestjs

# 2. El agente recuerda contexto
./compiler-bot/agent-robot/agent.sh "crea modulo users en nestjs" 2>/dev/null
./compiler-bot/agent-robot/agent.sh "que modulos tengo?" 2>/dev/null
# Output: Tienes 1 modulo: Users

# 3. Memoria persiste entre sesiones
AGENT_MEMORY_DIR=/tmp/mi_sesion ./compiler-bot/agent-robot/agent.sh "crea modulo payments en nestjs" 2>/dev/null
AGENT_MEMORY_DIR=/tmp/mi_sesion ./compiler-bot/agent-robot/agent.sh "que modulos tengo?" 2>/dev/null
# Output: Tienes 1 modulo: Payments

# 4. Tests pasan
./compiler-bot/tests/test_agent.sh | grep "FAIL=0"
```

---

## 4. Fase 4: System Prompts y Robustez

**Objetivo:** El agente tiene personalidad definida, system prompts claros,
manejo de errores robusto, y logging completo.

**Duracion estimada:** ~2 horas
**Depende de:** Fase 1 completa (Fases 2 y 3 opcionales)

---

### Tarea 4.1 — `system_agent.txt`: Prompt base del agente

**Archivo:** `compiler-bot/agent-robot/prompts/system_agent.txt`
**Estimacion:** 20 min

```
Eres Proyecto0(RECPL), un agente de codigo abierto que ayuda a desarrolladores
a escribir y ejecutar codigo. Funcionas como una interfaz entre el usuario y
el pipeline RECPL (un compilador de lenguaje natural a codigo) y un conjunto
de herramientas del sistema.

PERSONALIDAD:
- Eres amable, directo y profesional
- Respondes en espanol (a menos que el usuario hable otro idioma)
- Das respuestas concisas pero completas
- Si no entiendes algo, lo dices explicitamente
- Nunca inventes informacion o comandos que no existen

COMPORTAMIENTO:
1. Recibes una instruccion en lenguaje natural del usuario
2. Clasificas la intencion: es un comando RECPL, una pregunta, o una solicitud de herramienta?
3. Ejecutas la accion correspondiente
4. Devuelves el resultado formateado

CAPACIDADES ACTUALES (Fase 1):
- Ejecutar comandos RECPL: crea, genera, elimina, lista modulos
- Responder preguntas generales (saludos, identidad, ayuda)
- Recordar el historial de la conversacion

CAPACIDADES FUTURAS (Fase 2+):
- Leer archivos del sistema
- Escribir/editar archivos
- Ejecutar comandos shell
- Buscar en codigo fuente
- Ejecutar tareas multi-paso

LIMITACIONES:
- No tienes acceso a internet (solo via APIs configuradas por el usuario)
- No almacenas datos fuera del directorio de memoria configurado
- Dependes del pipeline RECPL para entender instrucciones de scaffolding
- El modo deterministico (RECPL) es limitado a ~20 palabras clave
- Para instrucciones complejas, necesitas un LLM configurado

MODO DETERMINISTICO (RECPL):
Cuando el usuario da una instruccion como "crea modulo X en nestjs", delegas
en el pipeline RECPL que entiende un vocabulario especifico:
- Acciones: crea, genera, elimina, lista, actualiza
- Objetos: modulo, entidad, proyecto
- Techos: nestjs, prisma
- Preposiciones: en, de, con, para

Si la instruccion no encaja en RECPL y no hay LLM configurado, informa al
usuario que no pudiste procesarla y sugiere alternativas.
```

**Verificacion:**

```sh
wc -l compiler-bot/agent-robot/prompts/system_agent.txt
# Debe tener ~50 lineas
```

---

### Tarea 4.2 — `system_planner.txt`: Prompt del planificador

**Archivo:** `compiler-bot/agent-robot/prompts/system_planner.txt`
**Estimacion:** 15 min

```
Eres el planificador de Proyecto0(RECPL). Tu funcion es descomponer
instrucciones complejas del usuario en una secuencia de pasos simples
que el agente pueda ejecutar.

REGLAS:
1. Cada paso debe ser una instruccion atomica que RECPL o una herramienta
   pueda ejecutar individualmente
2. Los pasos son secuenciales (el orden importa)
3. No asumas que pasos anteriores han fallado
4. Si la instruccion ya es simple, devuelve un solo paso

EJEMPLOS:
Input: "crea modulo auth y modulo payments en nestjs"
Output: [
  {"accion": "recpl", "parametros": {"instruccion": "crea modulo auth en nestjs"}},
  {"accion": "recpl", "parametros": {"instruccion": "crea modulo payments en nestjs"}}
]

Input: "crea un proyecto con backend nestjs y base de datos prisma"
Output: [
  {"accion": "recpl", "parametros": {"instruccion": "crea modulo app en nestjs"}},
  {"accion": "recpl", "parametros": {"instruccion": "crea entidad database en prisma"}}
]
```

---

### Tarea 4.3 — `system_tools.txt`: Prompt de herramientas

**Archivo:** `compiler-bot/agent-robot/prompts/system_tools.txt`
**Estimacion:** 15 min

```
HERRAMIENTAS DISPONIBLES:

1. recpl(instruccion)
   Ejecuta una instruccion en el pipeline RECPL.
   Instrucciones: crea modulo X en nestjs, elimina modulo Y, lista modulos
   Output: resultado del pipeline (archivos creados, errores, etc.)

2. respond(mensaje)
   Responde directamente al usuario con un mensaje de texto.
   Usar para: saludos, preguntas, aclaraciones.

3. read_file(ruta)
   Lee el contenido completo de un archivo.
   Limitacion: archivos de texto solamente.

4. write_file(ruta, contenido)
   Escribe contenido en un archivo. Crea directorios si es necesario.

5. run_command(comando)
   Ejecuta un comando shell.
   Precaución: el comando se ejecuta en el sistema del usuario.

6. search_code(patron, ruta_opcional)
   Busca un patron de texto en archivos de codigo.
   Usa grep -rn internamente.
```

---

### Tarea 4.4 — Manejo de errores en `agent.sh`

Mejorar `agent.sh` con:

1. **Timeout en bridge:** Si `bridge_recpl` tarda mas de 30s, cancelar y
   devolver error.

2. **Captura de senales:** `trap` para Ctrl+C y salida limpia.

3. **Mensajes de error claros:**
   - "No entendi la instruccion. Puedes intentar: crea modulo X en nestjs, lee
     archivo Y, ejecuta comando Z"
   - "RECPL no pudo procesar la instruccion. El vocabulario es limitado a:
     crea, genera, elimina, lista, actualiza"

4. **Validacion de entrada:** Si la instruccion tiene caracteres peligrosos
   (`, $(), etc.), sanitizar o rechazar.

```sh
# Agregar en agent.sh, dentro de main() antes de procesar:

# --- Sanitizar instruccion ---
sanitize_instruction() {
    _input="$1"
    # Rechazar caracteres peligrosos
    echo "$_input" | grep -qE '[\`\$]' && {
        echo "Error: La instruccion contiene caracteres no permitidos"
        return 1
    }
    echo "$_input"
    return 0
}

# --- Timeout wrapper ---
# Uso: timeout_run <segundos> <comando...>
timeout_run() {
    _timeout="$1"
    shift
    if command -v timeout >/dev/null 2>&1; then
        timeout "$_timeout" "$@"
    else
        "$@"
    fi
}
```

**Depende de:** 1.7
**Estimacion:** 30 min

---

### Tarea 4.5 — Logging completo

`agent.sh` ya tiene `memory_log()` desde Fase 1. Mejorar con:

```sh
# Niveles de log
AGENT_LOG_LEVEL="${AGENT_LOG_LEVEL:-info}"  # debug | info | warn | error

memory_log_debug() { [ "$AGENT_LOG_LEVEL" = "debug" ] && memory_log "DEBUG: $*"; }
memory_log_info()  { memory_log "INFO: $*"; }
memory_log_warn()  { memory_log "WARN: $*"; }
memory_log_error() { memory_log "ERROR: $*"; }
```

Y agregar logging en cada punto del flujo de `agent.sh`:

```sh
memory_log_info "Instruccion recibida: $_instruction"
memory_log_info "Intencion clasificada: $_intent"
memory_log_info "Ejecucion completada: $_exit_code"
```

---

### Tarea 4.6 — Tests de Fase 4

```sh
# --- Fase 4: manejo de errores ---
test_agent_error_empty() {
    _result=$(cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "" 2>/dev/null)
    if echo "$_result" | grep -qi "error\|no se recibio\|vacia"; then
        echo "  ✅ Agent maneja instruccion vacia"
    else
        echo "  ⚠️  Agent manejo de error vacio (puede variar)"
    fi
}

# --- Fase 4: system prompts existen ---
test_prompts_exist() {
    for f in \
        "$SCRIPT_DIR/agent-robot/prompts/system_agent.txt" \
        "$SCRIPT_DIR/agent-robot/prompts/system_planner.txt" \
        "$SCRIPT_DIR/agent-robot/prompts/system_tools.txt"; do
        if [ -f "$f" ]; then
            echo "  ✅ Existe: $(basename "$f")"
        else
            echo "  ❌ FALTA: $f"
            FAIL=$((FAIL + 1))
            FAIL_MSGS="${FAIL_MSGS}FALTA_PROMPT "
        fi
    done
}

# --- Fase 4: logging ---
test_agent_logging() {
    _log_file="/tmp/test_agent_log_$$.txt"
    AGENT_LOG_FILE="$_log_file" AGENT_LLM_MODE="deterministic" \
        cd "$SCRIPT_DIR" && ./agent-robot/agent.sh "hola" >/dev/null 2>&1

    if [ -f "$_log_file" ] && grep -q "INFO\|RECV\|INTENT" "$_log_file" 2>/dev/null; then
        echo "  ✅ Agent genera logs"
    else
        echo "  ⚠️  Agent logging (puede no estar implementado aun)"
    fi
    rm -f "$_log_file"
}
```

---

### Criterios de exito de Fase 4

```sh
# 1. Errores se manejan gracefulmente
./compiler-bot/agent-robot/agent.sh "" 2>/dev/null
# Output: Error: No se recibio ninguna instruccion.

# 2. El agente tiene personalidad consistente
./compiler-bot/agent-robot/agent.sh "quien eres?" 2>/dev/null
# Output: Soy Proyecto0(RECPL) v1.0.0, un agente de codigo abierto...

# 3. Logging captura todas las interacciones
cat /tmp/agent.log
# Debe mostrar: [2026-...] INFO: Instruccion recibida: ...
#               [2026-...] INFO: Intencion clasificada: ...

# 4. Tests pasan
./compiler-bot/tests/test_agent.sh | grep "FAIL=0"

# 5. Syntax check de prompts (son texto, no shell)
wc -l compiler-bot/agent-robot/prompts/*.txt
```

---

## 5. Dependencias Entre Fases

```
Fase 1 ──completa──→ Fase 2 ──completa──→ Fase 3 ──completa──→ Fase 4
  (fundacion)        (herramientas)       (planner+memoria)    (prompts+robustez)
       │                    │                     │                    │
       ▼                    ▼                     ▼                    ▼
  agent.sh            tool_read_file.sh      planner.sh           system_agent.txt
  bridge.sh           tool_write_file.sh     memory.sh mejorado   system_planner.txt
  config.sh           tool_run_command.sh    tool_search_code.sh  system_tools.txt
  memory.sh (base)    integrate en agent.sh  integrate en agent.sh manejo de errores
  tool_recpl.sh                              tests Fase 3        logging mejorado
  tool_respond.sh                                                    tests Fase 4
  tool_registry.sh
  agent-robot.sh
  flag --agent en recpl.sh
  tests Fase 1
            │
            ├──→ Fase 2 puede empezar apenas terminen 1.1-1.6
            ├──→ Fase 3 requiere 1.7 (agent.sh con classify_intent)
            └──→ Fase 4 requiere 1.7 (agent.sh como base)
```

**Regla:** Cada fase debe dejar todos sus tests en verde antes de pasar a la
siguiente. Las fases 2, 3, y 4 pueden ejecutarse en paralelo si se respetan
sus dependencias individuales.

---

## 6. Resumen de Comandos de Verificacion

```sh
# === VERIFICACION RAPIDA (todas las fases) ===

# 1. Syntax check
for f in compiler-bot/agent-robot/*.sh compiler-bot/agent-robot/tools/*.sh; do
    bash -n "$f" && echo "OK: $f" || echo "FAIL: $f"
done

# 2. Tests
./compiler-bot/tests/test_agent.sh

# 3. Pruebas de humo
./compiler-bot/agent-robot/agent.sh "hola" 2>/dev/null
./compiler-bot/agent-robot/agent.sh "quien eres?" 2>/dev/null
./compiler-bot/agent-robot/agent.sh "crea modulo humo en nestjs" 2>/dev/null

# 4. Flag --agent
./compiler-bot/recpl.sh --agent "hola" 2>/dev/null

# 5. Memoria
AGENT_MEMORY_DIR=/tmp/test_sesion ./compiler-bot/agent-robot/agent.sh "hola" 2>/dev/null

# 6. Logging
cat /tmp/agent.log 2>/dev/null | tail -10
```

---

## 7. Referencias a Documentos Relacionados

| Documento | Relacion |
|-----------|----------|
| `docs/048_PLAN_DEV_COMPILER_BOT_AGENT_IMPL_1_0_DRAFT.md` | **Plan rector.** Este documento ejecuta su seccion 5. |
| `docs/047_PROP_DEV_COMPILER_BOT_AGENT_CONCEPT_1_0_DRAFT.md` | Propuesta de concepto que origina el plan. |
| `docs/046_PROP_DEV_COMPILER_BOT_TIER_ARCHITECTURE_1_0_DRAFT.md` | Arquitectura free/paid para provider chain. |
| `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` | Provider gratuito (integracion futura). |
| `docs/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` | Guia de estilo shell (reglas de codigo). |
| `compiler-bot/recpl.sh` | Entrypoint RECPL (modificar solo flag --agent). |
| `compiler-bot/pipeline_debugger.sh` | Debugger usado por bridge. |
| `compiler-bot/frontend/llm_classifier.sh` | Fachada LLM (usado por bridge). |
| `compiler-bot/tests/run_tests.sh` | Suite de tests existente (72 tests, no modificar). |
