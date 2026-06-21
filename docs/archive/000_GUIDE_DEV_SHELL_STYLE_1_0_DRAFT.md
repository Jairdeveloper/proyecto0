---
id: 000
area: dev
type: guide
module: shell-style
version: 1.0
status: DRAFT
tags:
  - shell
  - style
  - convention
  - posix
  - workflow
summary: "Guia de estilo para scripts Shell en @Proyecto0. Define convenciones de nomenclatura, estructura de archivos, manejo de errores, logging y patrones de diseño para mantener scripts legibles, mantenibles y consistentes."
keywords:
  - shell
  - sh
  - posix
  - estilo
  - convencion
  - nomenclatura
  - scripting
changelog:
  - version: 1.0
    date: 2026-06-02
    author: workflow-agent
    description: Creacion inicial de la guia de estilo Shell
---

# Guia de Estilo Shell — @tienda/api

## 0. Filosofia

Los scripts Shell en este proyecto siguen tres principios fundamentales:

1. **Everything is a file** — Estado, colas, configuracion, artefactos y aprobaciones son archivos en disco. Esto hace que el sistema sea inspeccionable, auditable, y recuperable ante fallos.

2. **Explicit over implicit** — No usar `set -e`. Cada comando se protege individualmente. Los errores se manejan donde ocurren, no en un handler global.

3. **Self-documenting** — El codigo debe explicarse a si mismo mediante nombres descriptivos, estructura clara y un bloque de ayuda completo en el header.

---

## 1. Estructura del archivo

### 1.1 Orden de secciones

```
1. Shebang
2. Bloque de documentacion (header)
3. Constantes (SCREAMING_SNAKE_CASE)
4. Variables de entorno (con defaults)
5. Funciones de utilidad
6. Funciones de dominio (logica del programa)
7. Funcion main() de dispatch
8. Ejecucion: main "$@"
```

### 1.2 Separadores visuales

```
# ============================================================================
# SECTION HEADER
# ============================================================================
```

```
# --- Sub-section ---
```

---

## 2. Convenciones de nomenclatura

### 2.1 Archivos

```
snake_case.sh
```

### 2.2 Constantes

```
SCREAMING_SNAKE_CASE — para paths, configuraciones fijas y flags de entorno.

Ejemplos:
  PROJECT_ROOT
  WORKFLOW_DIR
  STATE_FILE
  DRY_RUN
  AUTO_APPROVE
```

### 2.3 Variables locales

```
snake_case — descriptiva, sin abreviaturas crípticas.

Ejemplos:
  instruction
  proposal_file
  cycle_number
  approval_status
  plan_file_path
```

### 2.4 Funciones

```
snake_case — verbo al inicio, seguido de sustantivo.

Ejemplos:
  get_state()
  set_state()
  generate_proposal()
  await_approval()
  execute_plan()
  show_status()
  sanitize_slug()
```

### 2.5 Nombres prohibidos

- No usar `x`, `y`, `z`, `tmp`, `foo` como nombres de variable
- No usar nombres de una sola letra (excepto `$?`, `$$`, `$@`, `$*`)
- No usar `func` o `function` como nombre
- No usar mayusculas para variables locales

---

## 3. Formato y espaciado

### 3.1 Indentacion

- Usar **4 espacios** por nivel (NO tabs)
- Maximo 100 caracteres por linea
- Tuberias largas: indentar continuaciones con 4 espacios

```sh
# Correcto
generate_context() {
    instruction="$*"
    context_file="$WORKFLOW_DIR/context.md"

    {
        echo "# Project Context"
        find "$PROJECT_ROOT" -name "*.ts" \
            -path "*${word}*" \
            2>/dev/null | head -5
    } > "$context_file"
}

# Incorrecto
generate_context() {
instruction="$*"
context_file="$WORKFLOW_DIR/context.md"
{
echo "# Project Context"
find "$PROJECT_ROOT" -name "*.ts" -path "*${word}*" 2>/dev/null | head -5
} > "$context_file"
}
```

### 3.2 Espaciado en estructuras de control

```sh
# Correcto
if [ -z "$instruction" ]; then
    handle_error "instruction is empty"
fi

for file in "$INBOX_DIR"/*.md; do
    [ -f "$file" ] || continue
    process_instruction "$file"
done

# Incorrecto
if [ -z "$instruction" ];then
handle_error "instruction is empty"
fi
```

### 3.3 Here documents

- Usar `<<-EOF` para heredocs con indentacion
- La palabra de cierre debe estar al inicio de la linea (con tab si usas `<<-`)

```sh
cat > "$file" <<-EOF
	line 1
	line 2
EOF
```

---

## 4. Manejo de errores

### 4.1 Regla de oro

**NO usar `set -e`.** El manejo de errores debe ser explicito en cada punto
donde pueda ocurrir un fallo.

```sh
# Correcto
if ! mkdir -p "$directory" 2>/dev/null; then
    log_error "failed to create directory: $directory"
    return 1
fi

# Incorrecto
set -e
mkdir -p "$directory"
```

### 4.2 Funciones de error

```sh
handle_error() {
    message="$1"
    exit_code="${2:-1}"
    log "ERROR: $message"
    set_state "error"
    exit "$exit_code"
}
```

### 4.3 Validacion de argumentos

```sh
validate_args() {
    if [ -z "$1" ]; then
        echo "Usage: $0 propose <instruction>"
        exit 1
    fi
}
```

---

## 5. Logging

### 5.1 Log estructurado

```sh
# Timestamp ISO + mensaje
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
    echo "$*" >&2
}
```

### 5.2 Output para el usuario

```sh
# Output a stdout para pipe / captura
output() {
    echo "$*"
}
```

### 5.3 Mensajes informativos

- `STATE → proposing` — cambios de estado
- `CYCLE → 5` — cambios de ciclo
- `ERROR: ...` — errores
- `WARN: ...` — advertencias
- `OK: ...` — confirmaciones

---

## 6. Funciones

### 6.1 Estructura de funcion

```sh
# --- Descripcion breve de lo que hace ---
function_name() {
    variable="$1"

    # Validacion
    if [ -z "$variable" ]; then
        log "ERROR: descripcion del error"
        return 1
    fi

    # Logica central
    result=$(do_something "$variable")

    # Output
    echo "$result"
}
```

### 6.2 Funciones siempre con `()`

Usar `funcion() { ... }`, NO `function funcion { ... }`.

### 6.3 Return vs Exit

- Funciones utilizables: `return` (codigo de error)
- Puntos de entrada: `exit` (termina el script)

---

## 7. Seguridad

### 7.1 Quoting

**Siempre** usar comillas dobles alrededor de variables:

```sh
# Correcto
cat "$file"
rm -f "$LOCK_FILE"
output="$WORKFLOW_DIR/$filename"

# Incorrecto
cat $file
rm -f $LOCK_FILE
output=$WORKFLOW_DIR/$filename
```

### 7.2 NO usar eval

```sh
# Prohibido
eval "$user_input"
```

Si necesitas ejecutar comandos desde un archivo de plan, usar un mecanismo
controlado con dry-run:

```sh
# Permitido solo con dry-run check
if [ "$DRY_RUN" != "true" ]; then
    sh -c "$command" || handle_error "command failed: $command"
fi
```

### 7.3 Archivos temporales

- Usar `$$` para evitar colisiones: `/tmp/scriptname_$$.tmp`
- Limpiar con `trap` o en bloque `finally`

```sh
temp_file="/tmp/workflow_steps_$$.tmp"
trap 'rm -f "$temp_file"' EXIT
```

### 7.4 Lock files

Usar lock files con PID para evitar ejecucion concurrente:

```sh
acquire_lock() {
    if [ -f "$LOCK_FILE" ]; then
        pid=$(cat "$LOCK_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "ERROR: process $pid is already running"
            exit 1
        fi
        log "WARN: removing stale lock (pid $pid)"
    fi
    echo "$$" > "$LOCK_FILE"
    trap 'release_lock' EXIT
}

release_lock() {
    rm -f "$LOCK_FILE"
}
```

---

## 8. Estado (State Machine)

El estado del workflow se representa como un archivo de texto plano:

```sh
get_state() {
    cat "$STATE_FILE" 2>/dev/null || echo "idle"
}

set_state() {
    echo "$1" > "$STATE_FILE"
    log "STATE → $1"
}
```

Estados posibles: `idle`, `proposing`, `awaiting_review:proposal:N`,
`approved:proposal:N`, `rejected:proposal:N`, `planning`,
`awaiting_review:plan:N`, `approved:plan:N`, `rejected:plan:N`,
`executing`, `executed:N`, `verifying`, `verified:N`, `error`.

---

## 9. Estructura del ciclo completo

```
Paso 1: analyze     → escanea codigo, genera contexto
Paso 2: propose     → genera propuesta desde instruccion
Paso 3: approve     → humano revisa y acepta/rechaza
Paso 4: plan        → genera plan desde propuesta
Paso 5: approve     → humano revisa y acepta/rechaza
Paso 6: execute     → ejecuta plan paso a paso
Paso 7: verify      → ejecuta validaciones y reporta
```

---

## 10. Ejemplo completo

```sh
#!/bin/sh
# ============================================================================
# example.sh - Example script following @tienda/api shell style
# ============================================================================
#
# PURPOSE:
#   Demonstrates the shell style conventions used in this project.
#
# USAGE: ./example.sh <mode> [arguments]
#
# MODES:
#   greet <name>    Print a greeting
#   count <n>       Count to n
#   help            Show this help
# ============================================================================

# --- Constants ---
SCRIPT="$(realpath "$0")"
PROJECT_ROOT="$(dirname "$SCRIPT")"
LOG_FILE="$PROJECT_ROOT/example.log"

# --- Flags ---
VERBOSE="${VERBOSE:-false}"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
    echo "$*" >&2
}

output() {
    echo "$*"
}

# --- Greet ---
greet() {
    name="$1"

    if [ -z "$name" ]; then
        log "ERROR: name is required"
        output "Usage: $0 greet <name>"
        return 1
    fi

    output "Hello, $name!"
    log "OK: greeted $name"
}

# --- Count ---
count_to() {
    max="${1:-5}"

    i=1
    while [ "$i" -le "$max" ]; do
        output "$i"
        i=$((i + 1))
    done

    log "OK: counted to $max"
}

# --- Main dispatch ---
main() {
    case "${1:-help}" in
        greet)
            shift
            greet "$*"
            ;;
        count)
            count_to "$2"
            ;;
        help|--help|-h)
            echo "Example script following @tienda/api shell style"
            echo ""
            echo "Usage: $0 <mode> [arguments]"
            echo ""
            echo "Modes:"
            echo "  greet <name>    Print a greeting"
            echo "  count <n>       Count to n"
            echo "  help            Show this help"
            ;;
        *)
            echo "Unknown mode: $1"
            echo "Usage: $0 help"
            exit 1
            ;;
    esac
}

main "$@"
```

---

## 11. Checklist de validacion

Antes de dar por terminado un script:

- [ ] `bash -n script.sh` — sin errores de sintaxis
- [ ] `shellcheck script.sh` — sin warnings (si disponible)
- [ ] Todas las variables estan entre comillas dobles
- [ ] No hay `set -e`
- [ ] No hay `eval`
- [ ] No hay nombres de una sola letra
- [ ] Todos los errores tienen mensaje descriptivo en log
- [ ] El bloque de ayuda (help) esta completo y actualizado
- [ ] Todos los modos estan documentados en el header
- [ ] Las constantes estan en SCREAMING_SNAKE_CASE
- [ ] Las funciones estan en snake_case
- [ ] La indentacion es de 4 espacios
