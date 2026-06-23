#!/bin/sh
# ============================================================================
# spellcheck_docs.sh — Corrector ortografico interactivo para docs/
# ============================================================================
#
# PROPOSITO:
#   Corrector ortografico interactivo para archivos .md en docs/.
#   Adaptacion del clasico spellcheck.awk de Dale Dougherty
#   (O'Reilly, 1990 — "UNIX Text Processing") usando aspell como
#   motor de revision moderno.
#
# ORIGINAL:
#   spellcheck.awk — Dale Dougherty, O'Reilly & Associates, 1990
#   Corrector interactivo en awk que invocaba UNIX spell y ofrecia
#   correccion por ocurrencia (C), global (G), adicion a diccionario
#   (A), ayuda (H) y salida (Q).
#
# ADAPTACION:
#   Shell script que usa aspell (GNU Aspell) para revisar archivos .md.
#   Preserva el flujo interactivo original (C/G/A/H/Q), el sistema de
#   respaldo .orig, archivos temporales, y confirmacion antes de guardar.
#
# USO:
#   scripts/spellcheck_docs.sh [opciones] [archivo...]
#   scripts/spellcheck_docs.sh --help
#
# OPCIONES:
#   -d <dict>   Diccionario personalizado (archivo con una palabra por linea)
#   -l <lang>   Idioma para aspell (default: es)
#   -n          Dry-run: lista errores sin interactuar
#   -h, --help  Esta ayuda
#
# MODO INTERACTIVO (respuestas por palabra):
#   C   Cambiar cada ocurrencia (prompt por cada una)
#   G   Cambio global (todas las ocurrencias a la vez)
#   A   Agregar al diccionario personal
#   H   Ayuda
#   Q   Salir
#   CR  Ignorar esta palabra
#
# EJEMPLOS:
#   scripts/spellcheck_docs.sh docs/INDEX.md
#   scripts/spellcheck_docs.sh -d docs/.aspell.pws docs/*.md
#   scripts/spellcheck_docs.sh -l en_US docs/onboarding/*.md
#   scripts/spellcheck_docs.sh -n docs/*.md    # solo listar errores
#
# REQUIERE:
#   aspell (GNU Aspell)
# ============================================================================

# ============================================================================
# CONSTANTES
# ============================================================================

SCRIPT_NAME="spellcheck_docs.sh"
SCRIPT_DIR="$(dirname "$0")"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
ASPELL_LANG="es"
DICT_FILE=""
DRY_RUN=""
CHANGES_MADE=0

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# --- Mostrar ayuda ---
show_help() {
    cat <<'HELP_EOF'
spellcheck_docs.sh — Corrector ortografico interactivo para documentacion

USO:
  scripts/spellcheck_docs.sh [opciones] [archivo...]
  scripts/spellcheck_docs.sh --help

OPCIONES:
  -d <dict>   Diccionario personalizado (archivo con una palabra por linea)
  -l <lang>   Idioma para aspell (default: es)
  -n          Dry-run: lista errores sin interactuar
  -h, --help  Esta ayuda

MODO INTERACTIVO:
  Al encontrar una palabra desconocida, se muestran estas opciones:
    C  Cambiar cada ocurrencia — muestra cada linea donde aparece la
       palabra y pide confirmacion para corregirla
    G  Cambio global — reemplaza todas las ocurrencias a la vez
    A  Agregar al diccionario personal — anade la palabra a un archivo
       de diccionario local para que no se marque como error
    H  Ayuda — muestra este mensaje
    Q  Salir — termina la revision del archivo actual
    CR (Enter) — Ignorar esta palabra por ahora

EJEMPLOS:
  scripts/spellcheck_docs.sh docs/INDEX.md
  scripts/spellcheck_docs.sh -d docs/.aspell.pws docs/*.md
  scripts/spellcheck_docs.sh -l en_US docs/onboarding/*.md
  scripts/spellcheck_docs.sh -n docs/*.md

ADAPTACION:
  Basado en spellcheck.awk (Dale Dougherty, O'Reilly 1990)
  Para Proyecto0 — RECPL Compiler Bot v2.0

REQUIERE:
  aspell (GNU Aspell)
HELP_EOF
}

# --- Verificar dependencias ---
check_deps() {
    if ! command -v aspell >/dev/null 2>&1; then
        echo "ERROR: aspell no esta instalado."
        echo ""
        echo "Para instalarlo:"
        echo "  Debian/Ubuntu: apt-get install aspell aspell-es"
        echo "  macOS:         brew install aspell"
        echo "  RHEL/Fedora:   dnf install aspell aspell-es"
        exit 1
    fi
}

# ============================================================================
# EXTRACCION DE TEXTO (saltar bloques de codigo en markdown)
# ============================================================================

# --- Extraer solo el texto legible de un .md (sin bloques de codigo) ---
extract_text() {
    file="$1"
    # Eliminar bloques de codigo (```...```) y codigo inline (`...`)
    # Luego pasar solo palabras a traves de tr para normalizar
    sed '/^```/,/^```/d' "$file" \
        | sed 's/`[^`]*`//g' \
        | sed 's/\[[^]]*\]([^)]*)//g' \
        | tr -s '[:space:]' '\n' \
        | sed '/^[[:space:]]*$/d' \
        | sed 's/^[^a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]//' \
        | sed 's/[^a-zA-ZáéíóúñüÁÉÍÓÚÑÜ]$//' \
        | tr '[:upper:]' '[:lower:]' \
        | grep -v '^.$' \
        | sort -u
}

# ============================================================================
# INTEGRACION CON ASPELL
# ============================================================================

# --- Obtener lista de errores para un archivo ---
get_misspellings() {
    file="$1"
    lang="$2"
    dict_arg="$3"

    extra=""
    if [ -n "$dict_arg" ] && [ -f "$dict_arg" ]; then
        extra="--add-extra-dicts=$dict_arg"
    fi

    # Extraer texto, pasar por aspell list, obtener errores unicos
    extract_text "$file" \
        | aspell list -l "$lang" --encoding=utf-8 $extra 2>/dev/null \
        | sort -u
    return 0
}

# --- Obtener sugerencias para una palabra ---
get_suggestions() {
    word="$1"
    lang="$2"
    dict_arg="$3"

    extra=""
    if [ -n "$dict_arg" ] && [ -f "$dict_arg" ]; then
        extra="--add-extra-dicts=$dict_arg"
    fi

    echo "$word" \
        | aspell pipe -l "$lang" --encoding=utf-8 $extra 2>/dev/null \
        | grep '^&' \
        | sed 's/^[^:]*://' \
        | sed 's/, /\n/g' \
        | head -10 \
        | paste -sd ',' -
}

# ============================================================================
# CONTEXTO Y OCURRENCIAS
# ============================================================================

# --- Encontrar lineas donde aparece una palabra (con numero de linea) ---
find_occurrences() {
    file="$1"
    word="$2"
    grep -ni "$word" "$file" 2>/dev/null || true
}

# --- Extraer linea por numero ---
get_line() {
    file="$1"
    lineno="$2"
    sed -n "${lineno}p" "$file" 2>/dev/null
}

# --- Mostrar linea con caret apuntando a la palabra ---
show_line_with_caret() {
    line="$1"
    word="$2"
    echo "$line"
    # Calcular posicion de la palabra en la linea
    # Buscar la palabra (case-insensitive) y posicionar caret
    rest="$line"
    pos=0
    while true; do
        # Encontrar la palabra en el resto de la linea
        case "$rest" in
            *"$word"*)
                prefix="${rest%%"$word"*}"
                pos=$((pos + ${#prefix} + 1))
                carets=$(printf "%${pos}s" "" | tr ' ' '^')
                echo "$carets"
                break
                ;;
            *)
                break
                ;;
        esac
    done
}

# ============================================================================
# CORRECCIONES
# ============================================================================

# --- make_change: cambiar cada ocurrencia individualmente ---
# (preserva el patron recursivo del original)
make_change() {
    file="$1"
    word="$2"
    correction="$3"

    if [ -z "$correction" ]; then
        printf "  Cambiar a: "
        read -r correction
    fi

    changes=0
    while [ -z "$correction" ]; do
        printf "  Cambiar a: "
        read -r correction
    done

    # Leer el archivo y reemplazar la primera ocurrencia
    tmpfile="/tmp/spellchange_$$.tmp"
    trap 'rm -f "$tmpfile"' EXIT
    : > "$tmpfile"

    first_occurrence=true
    while IFS= read -r line; do
        if $first_occurrence && echo "$line" | grep -qi "$word"; then
            modified=$(echo "$line" | sed "s/${word}/${correction}/gI")
            echo "$modified" >> "$tmpfile"
            echo ""
            echo "  > $modified"
            first_occurrence=false
            changes=$((changes + 1))
            CHANGES_MADE=$((CHANGES_MADE + 1))
        else
            echo "$line" >> "$tmpfile"
        fi
    done < "$file"

    mv "$tmpfile" "$file"

    if [ "$changes" -gt 0 ]; then
        printf "  %d linea(s) cambiada(s). Guardar cambios? (y/n): " "$changes"
        read -r confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            log "WARN: cambios NO guardados"
        fi
    fi

    # Buscar mas ocurrencias (recursivo como el original)
    remaining=$(grep -ci "$word" "$file" 2>/dev/null || echo 0)
    if [ "$remaining" -gt 0 ]; then
        printf "  Quedan %d ocurrencia(s). Cambiar siguiente? (y/n): " "$remaining"
        read -r cont
        if [ "$cont" = "y" ] || [ "$cont" = "Y" ]; then
            make_change "$file" "$word" ""
        fi
    fi
}

# --- make_global_change: cambiar todas las ocurrencias a la vez ---
make_global_change() {
    file="$1"
    word="$2"
    correction="$3"

    if [ -z "$correction" ]; then
        printf "  Cambio global a: "
        read -r correction
    fi

    changes=0
    while [ -z "$correction" ]; do
        printf "  Cambio global a: "
        read -r correction
    done

    tmpfile="/tmp/spellglobal_$$.tmp"
    trap 'rm -f "$tmpfile"' EXIT
    : > "$tmpfile"

    total=0
    while IFS= read -r line; do
        if echo "$line" | grep -qi "$word"; then
            modified=$(echo "$line" | sed "s/${word}/${correction}/gI")
            echo "$modified" >> "$tmpfile"
            if [ "$line" != "$modified" ]; then
                echo "  > $modified"
                total=$((total + 1))
                CHANGES_MADE=$((CHANGES_MADE + 1))
            fi
        else
            echo "$line" >> "$tmpfile"
        fi
    done < "$file"

    mv "$tmpfile" "$file"

    if [ "$total" -gt 0 ]; then
        echo ""
        printf "  %d linea(s) cambiada(s). Guardar cambios? (y/n): " "$total"
        read -r confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            log "WARN: cambios NO guardados para: $word"
        fi
    else
        echo "  No se encontraron ocurrencias de: $word"
    fi
}

# ============================================================================
# PROCESAMIENTO DE ARCHIVOS
# ============================================================================

# --- Procesar un archivo ---
process_file() {
    file="$1"
    lang="$2"
    dict_arg="$3"

    if [ ! -f "$file" ]; then
        echo "Error: archivo no encontrado: $file"
        return 1
    fi

    filename=$(basename "$file")
    log "Procesando: $filename"

    # Obtener lista de errores
    misspellings=$(get_misspellings "$file" "$lang" "$dict_arg")

    if [ -z "$misspellings" ]; then
        log "OK: no se encontraron errores ortograficos en ${filename}"
        return 0
    fi

    word_count=$(echo "$misspellings" | wc -l)
    log "Se encontraron $word_count palabra(s) desconocida(s) en ${filename}"

    # Modo dry-run: solo listar
    if [ -n "$DRY_RUN" ]; then
        echo "=================================================="
        echo "  ${filename}:"
        echo "=================================================="
        for word in $misspellings; do
            suggestions=$(get_suggestions "$word" "$lang" "$dict_arg")
            occurrences=$(find_occurrences "$file" "$word" | wc -l | tr -d ' ')
            if [ -n "$suggestions" ]; then
                printf "  %-20s (%d ocurrencias) sugerencias: %s\n" "$word" "$occurrences" "$suggestions"
            else
                printf "  %-20s (%d ocurrencias) [sin sugerencias]\n" "$word" "$occurrences"
            fi
        done
        echo ""
        return 0
    fi

    # Crear copia de seguridad
    cp "$file" "${file}.orig"
    log "Copia de seguridad: ${filename}.orig"

    # Archivo temporal de trabajo
    workfile="/tmp/spellcheck_work_$$.md"
    cp "$file" "$workfile"
    trap 'rm -f "$workfile"' EXIT

    # Contador de palabras procesadas
    total_words=$(echo "$misspellings" | wc -l)
    current=0

    response_list="Respuestas:
    C - Cambiar cada ocurrencia
    G - Cambio global
    A - Agregar al diccionario
    H - Ayuda
    Q - Salir
    ENTER - Ignorar"

    echo ""
    echo "========================================================================"
    echo "  Revisando: ${filename}"
    echo "  ${total_words} palabra(s) para revisar"
    echo "${response_list}"
    echo "========================================================================"
    echo ""

    for word in $misspellings; do
        current=$((current + 1))
        suggestions=$(get_suggestions "$word" "$lang" "$dict_arg")

        echo "---"
        echo "[${current}/${total_words}] Palabra: '${word}'"

        if [ -n "$suggestions" ]; then
            echo "  Sugerencias: ${suggestions}"
        else
            echo "  [sin sugerencias]"
        fi

        # Mostrar contexto
        context=$(find_occurrences "$workfile" "$word" | head -5)
        if [ -n "$context" ]; then
            echo "  Contexto:"
            echo "$context" | head -3 | while IFS= read -r ctx_line; do
                echo "    ${ctx_line}"
            done
        fi

        # Prompt interactivo
        while true; do
            printf "\n  ${word} (C/G/A/H/Q/ENTER): "
            read -r response

            case "$(echo "$response" | tr '[:lower:]' '[:upper:]')" in
                C|CHANGE)
                    echo "  Cambiando cada ocurrencia..."
                    make_change "$workfile" "$word" ""
                    cp "$workfile" "$file"
                    break
                    ;;
                G|GLOBAL)
                    echo "  Cambio global..."
                    make_global_change "$workfile" "$word" ""
                    cp "$workfile" "$file"
                    break
                    ;;
                A|ADD)
                    if [ -n "$dict_arg" ]; then
                        echo "$word" >> "$dict_arg"
                        log "OK: '${word}' agregado al diccionario: ${dict_arg}"
                    else
                        default_dict="${file}.dict"
                        echo "$word" >> "$default_dict"
                        log "OK: '${word}' agregado al diccionario: ${default_dict}"
                    fi
                    break
                    ;;
                H|HELP)
                    echo "${response_list}"
                    ;;
                Q|QUIT)
                    log "Revision interrumpida por el usuario."
                    break 2
                    ;;
                "")
                    log "Ignorando: ${word}"
                    break
                    ;;
                *)
                    echo "  Respuesta no valida. Use C, G, A, H, Q o ENTER."
                    ;;
            esac
        done
    done

    # Confirmar guardado final
    if [ -n "$DRY_RUN" ]; then
        return 0
    fi

    if diff -q "$workfile" "$file" >/dev/null 2>&1; then
        # Sin cambios
        rm -f "${file}.orig"
        log "OK: sin cambios en ${filename}"
    else
        echo ""
        echo "========================================================================"
        printf "  %d correccion(es) realizada(s). Guardar cambios en %s? (y/n): " \
            "$CHANGES_MADE" "$filename"
        read -r save_confirm
        if [ "$save_confirm" = "y" ] || [ "$save_confirm" = "Y" ]; then
            cp "$workfile" "$file"
            log "OK: cambios guardados en ${filename}"
            log "INFO: respaldo en ${filename}.orig"
        else
            cp "${file}.orig" "$file"
            rm -f "${file}.orig"
            log "INFO: cambios descartados para ${filename}"
        fi
    fi

    rm -f "$workfile" 2>/dev/null
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    files=""
    dict_arg=""
    lang="$ASPELL_LANG"

    # Procesar argumentos
    while [ $# -gt 0 ]; do
        case "$1" in
            -h|--help)
                show_help
                exit 0
                ;;
            -d)
                shift
                dict_arg="$1"
                if [ ! -f "$dict_arg" ]; then
                    echo "Error: archivo de diccionario no encontrado: $dict_arg"
                    exit 1
                fi
                ;;
            -l)
                shift
                lang="$1"
                if [ -z "$lang" ]; then
                    echo "Error: idioma no especificado"
                    exit 1
                fi
                ;;
            -n)
                DRY_RUN="true"
                ;;
            -*)
                echo "Error: opcion desconocida: $1"
                echo "Use --help para ver las opciones disponibles."
                exit 1
                ;;
            *)
                files="$files $1"
                ;;
        esac
        shift
    done

    # Verificar aspell
    check_deps

    # Si no hay archivos, usar docs/*.md
    if [ -z "$files" ]; then
        files="$DOCS_DIR"/*.md
    fi

    total_files=0
    total_processed=0

    for file in $files; do
        [ ! -f "$file" ] && continue
        total_files=$((total_files + 1))
    done

    if [ "$total_files" -eq 0 ]; then
        echo "Error: no se encontraron archivos .md para revisar"
        echo "Uso: $SCRIPT_NAME [opciones] <archivo.md>..."
        exit 1
    fi

    log "Iniciando revision ortografica (idioma: ${lang})"
    if [ -n "$DRY_RUN" ]; then
        log "Modo: dry-run (solo listar)"
    fi
    if [ -n "$dict_arg" ]; then
        log "Diccionario personalizado: ${dict_arg}"
    fi
    echo ""

    for file in $files; do
        [ ! -f "$file" ] && continue
        CHANGES_MADE=0
        if process_file "$file" "$lang" "$dict_arg"; then
            total_processed=$((total_processed + 1))
        fi
    done

    echo ""
    log "Revision completada: ${total_processed}/${total_files} archivos procesados"
}

main "$@"
