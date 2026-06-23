#!/bin/sh
# ============================================================================
# masterindex.sh — Generador de indices de documentacion (adaptado)
# ============================================================================
#
# PROPOSITO:
#   Genera indices de documentacion a partir del frontmatter YAML de los
#   archivos markdown en docs/. Adaptacion del clasico masterindex de
#   Dale Dougherty (O'Reilly, 1990) para el ecosistema Proyecto0.
#
# ORIGINAL:
#   masterindex 1.1 — 7/9/90 — Dale Dougherty
#   Procesaba macros troff (.XX/.XN/.XB) para indices de libros.
#
# ADAPTACION:
#   Procesa frontmatter YAML (id, area, type, module, summary) de archivos
#   .md y genera indices en formato markdown.
#
# USO:
#   ./masterindex.sh                  # Equivalente a generate_docs_index.sh
#   ./masterindex.sh -s               # Vista resumida (screen)
#   ./masterindex.sh -p archivo.md    # Vista detalle por documento (page)
#   ./masterindex.sh -m               # Indice multi-area (master)
#   ./masterindex.sh --help           # Esta ayuda
#
# PATRON DE FILTROS (herencia modular):
#   extract_fm (awk) → sort → agrupar → formatear (markdown)
#
# REQUIERE:
#   awk, sed, sort, cut
# ============================================================================

SCRIPT_NAME="masterindex.sh"
DOCS_DIR="$(cd "$(dirname "$0")/docs" && pwd 2>/dev/null || echo "./docs")"
SCRIPT_DIR="$(dirname "$0")"
MODE=""
MASTER=""
TARGET_FILE=""

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

show_help() {
    cat <<HELP
masterindex.sh — Generador de indices de documentacion (adaptado)

USO:
  $SCRIPT_NAME                         Indice completo (markdown)
  $SCRIPT_NAME -s                      Vista resumida (screen)
  $SCRIPT_NAME -p <archivo.md>         Vista detalle por documento
  $SCRIPT_NAME -m                      Indice multi-area
  $SCRIPT_NAME --help                  Esta ayuda

ORIGEN:
  Adaptacion de masterindex 1.1 (Dale Dougherty, O'Reilly 1990)

DESCRIPCION:
  Escanea archivos .md en docs/, extrae frontmatter YAML y genera
  indices estructurados. El modo por defecto (-s) produce una vista
  resumida en tabla. El modo -p muestra el frontmatter detallado de
  un documento. El modo -m genera indices separados por area.

  Internamente delega en scripts/generate_docs_index.sh para el
  indice completo. Los modos -s y -p son implementaciones directas
  que preservan el espiritu del masterindex original.

EJEMPLOS:
  $SCRIPT_NAME                         # Indice completo
  $SCRIPT_NAME -s                      # Vista resumida (screen)
  $SCRIPT_NAME -p docs/INDEX.md        # Detalle de INDEX.md
  $SCRIPT_NAME -m                      # Indices por area
HELP
}

extract_fm() {
    file="$1"
    key="$2"
    awk -v k="$key" '
        BEGIN { found = 0 }
        /^---$/ { found++; next }
        found == 1 && $1 == k ":" {
            line = $0
            sub(/^[^:]+:[[:space:]]*/, "", line)
            gsub(/^"|"$/, "", line)
            print line
            exit
        }
        found == 2 { exit }
    ' "$file"
}

extract_nnn() {
    name="$1"
    case "$name" in
        ALGP003*) echo "ALGP003" ;;
        *) echo "$name" | sed 's/^\([0-9]*\).*/\1/' ;;
    esac
}

screen_mode() {
    tmpfile="/tmp/masterindex_screen_$$.tmp"
    trap 'rm -f "$tmpfile"' EXIT
    : > "$tmpfile"

    for file in "$DOCS_DIR"/*.md; do
        [ ! -f "$file" ] && continue
        name=$(basename "$file")
        [ "$name" = "INDEX.md" ] && continue
        [ "$name" = "index.md" ] && continue

        nnn=$(extract_nnn "$name")
        area=$(extract_fm "$file" "area");     [ -z "$area" ] && area="?"
        tipo=$(extract_fm "$file" "type");     [ -z "$tipo" ] && tipo="?"
        module=$(extract_fm "$file" "module"); [ -z "$module" ] && module="?"
        status=$(extract_fm "$file" "status"); [ -z "$status" ] && status="?"
        summary=$(extract_fm "$file" "summary" | cut -c1-70)

        echo "$area|$nnn|$tipo|$status|$module|$summary" >> "$tmpfile"
    done

    total=$(wc -l < "$tmpfile")
    echo "========================================================================"
    echo "  Indice de Documentacion — Proyecto0"
    echo "  $total documentos en $DOCS_DIR"
    echo "  Modo: screen (resumen)"
    echo "========================================================================"
    echo ""

    sort -t'|' -k1,1 -k2,2 "$tmpfile" | while IFS='|' read -r area nnn tipo status module summary; do
        printf "  [%s] %-6s %-5s %-7s %-20s %s\n" "$area" "$nnn" "$tipo" "$status" "$module" "$summary"
    done

    echo ""
    echo "========================================================================"
    echo "  Para generar docs/INDEX.md: ./masterindex.sh (sin flags)"
    echo "  Para vista detalle:         ./masterindex.sh -p <archivo>"
    echo "========================================================================"

    rm -f "$tmpfile"
}

page_mode() {
    file="$1"

    if [ ! -f "$file" ]; then
        if [ -f "$DOCS_DIR/$file" ]; then
            file="$DOCS_DIR/$file"
        else
            echo "Error: archivo no encontrado: $file"
            exit 1
        fi
    fi

    name=$(basename "$file")
    nnn=$(extract_nnn "$name")

    echo "========================================================================"
    echo "  Detalle de documento: $name"
    echo "========================================================================"
    echo ""

    for key in id area type module version status summary; do
        val=$(extract_fm "$file" "$key")
        if [ -n "$val" ]; then
            printf "  %-12s %s\n" "$key:" "$val"
        fi
    done

    tags=$(awk '/^tags:/ { found=1; next } found && /^  - / { gsub(/^  - /, ""); print } /^[a-z]/ && !/^  - / { exit }' "$file" 2>/dev/null | tr '\n' ', ' | sed 's/, $//')
    if [ -n "$tags" ]; then
        printf "  %-12s %s\n" "tags:" "$tags"
    fi

    kws=$(awk '/^keywords:/ { found=1; next } found && /^  - / { gsub(/^  - /, ""); print } /^[a-z]/ && !/^  - / { exit }' "$file" 2>/dev/null | tr '\n' ', ' | sed 's/, $//')
    if [ -n "$kws" ]; then
        printf "  %-12s %s\n" "keywords:" "$kws"
    fi

    cl_entries=$(awk '/^changelog:/ { found=1; next } found && /^  - version:/ { v=gensub(/.*version:[[:space:]]*"?([^"]*)"?/, "\\1", 1); next } found && /^    date:/ { d=gensub(/.*date:[[:space:]]*"?([^"]*)"?/, "\\1", 1); next } found && /^    description:/ { desc=gensub(/.*description:[[:space:]]*"?([^"]*)"?/, "\\1", 1); print "    " v " (" d "): " desc; v=""; d="" } /^[a-z]/ && !/^  - / && !/^    / { exit }' "$file" 2>/dev/null)
    if [ -n "$cl_entries" ]; then
        echo ""
        echo "  changelog:"
        echo "$cl_entries"
    fi

    echo ""
    echo "========================================================================"

    content_summary=$(awk '
        BEGIN { count = 0 }
        /^---$/ { fm++; next }
        fm < 2 { next }
        /^# / { next }
        /^$/ { if (p > 0) { count++; p=0 } next }
        /^[A-Za-z]/ {
            if (count < 3) {
                print
                p=1
            }
        }
        count >= 3 { exit }
    ' "$file" 2>/dev/null | head -10)

    if [ -n "$content_summary" ]; then
        echo ""
        echo "  Vista previa del contenido:"
        echo "$content_summary" | sed 's/^/    /'
        echo ""
        echo "========================================================================"
    fi
}

master_mode() {
    echo "[masterindex] Generando indices multi-area..."
    echo "[masterindex] $DOCS_DIR"

    areas=""
    for file in "$DOCS_DIR"/*.md; do
        [ ! -f "$file" ] && continue
        name=$(basename "$file")
        [ "$name" = "INDEX.md" ] && continue
        area=$(extract_fm "$file" "area")
        if [ -n "$area" ]; then
            case "$areas" in *"$area"*) ;; *) areas="$areas $area" ;; esac
        fi
    done

    tmpdir="/tmp/masterindex_multi_$$"
    mkdir -p "$tmpdir"
    trap 'rm -rf "$tmpdir"' EXIT

    for area in $areas; do
        areafile="${tmpdir}/${area}.md"
        count=0
        {
            echo "# Area: ${area}"
            echo ""
            echo "Documentos en el area \`${area}\`:"
            echo ""
            echo "| NNN | Tipo | Modulo | Estado | Resumen |"
            echo "|-----|------|--------|--------|---------|"
        } > "$areafile"

        for file in "$DOCS_DIR"/*.md; do
            [ ! -f "$file" ] && continue
            name=$(basename "$file")
            [ "$name" = "INDEX.md" ] && continue
            a=$(extract_fm "$file" "area")
            [ "$a" != "$area" ] && continue

            nnn=$(extract_nnn "$name")
            tipo=$(extract_fm "$file" "type");     [ -z "$tipo" ] && tipo="?"
            module=$(extract_fm "$file" "module"); [ -z "$module" ] && module="?"
            status=$(extract_fm "$file" "status"); [ -z "$status" ] && status="?"
            summary=$(extract_fm "$file" "summary" | cut -c1-60)

            echo "| $nnn | $tipo | $module | $status | $summary |" >> "$areafile"
            count=$((count + 1))
        done

        echo "" >> "$areafile"
        echo "**Total:** $count documentos" >> "$areafile"
        echo "[masterindex] Area '${area}': $count documentos -> ${areafile}"
    done

    echo ""
    echo "========================================================================"
    echo "  Indice multi-area generado en: ${tmpdir}/"
    echo "========================================================================"
    for area in $areas; do
        count=$(grep -c '^|' "${tmpdir}/${area}.md" 2>/dev/null)
        echo "  ${area}: $((count - 1)) documentos"
    done
    echo ""
    echo "  Para ver un area: cat ${tmpdir}/<area>.md"
    echo "  Ejemplo: cat ${tmpdir}/dev.md"
    echo "========================================================================"
}

while [ "$#" != "0" ]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        -s*|-screen)
            MODE="screen"
            ;;
        -p*|-page)
            MODE="page"
            shift
            TARGET_FILE="$1"
            ;;
        -m*|-master)
            MASTER="TRUE"
            ;;
        *)
            echo "$1: argumento no valido"
            echo "Use --help para ver las opciones disponibles."
            exit 1
            ;;
    esac
    shift
done

# Ejecutar segun modo
if [ "$MASTER" = "TRUE" ]; then
    master_mode
elif [ "$MODE" = "page" ]; then
    if [ -z "$TARGET_FILE" ]; then
        echo "Error: modo -p requiere un archivo"
        echo "Uso: $SCRIPT_NAME -p docs/206_REP_DEV_REVERSE_ENGINEERING_1_0_DRAFT.md"
        exit 1
    fi
    page_mode "$TARGET_FILE"
elif [ "$MODE" = "screen" ]; then
    screen_mode
else
    # Modo default: delegar en generate_docs_index.sh
    if [ -f "$SCRIPT_DIR/scripts/generate_docs_index.sh" ]; then
        echo "[masterindex] Delegando en generate_docs_index.sh..."
        "$SCRIPT_DIR/scripts/generate_docs_index.sh"
    else
        echo "[masterindex] scripts/generate_docs_index.sh no encontrado."
        echo "[masterindex] Usando implementacion interna (screen mode)..."
        screen_mode
    fi
fi