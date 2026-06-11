#!/bin/sh
# ============================================================================
# generate_docs_index.sh - Genera INDEX.md y vistas parciales en docs/
# ============================================================================
#
# PROPOSITO:
#   Escanea archivos .md en docs/, extrae frontmatter YAML con awk,
#   y genera docs/INDEX.md (indice maestro) + docs/<area>/INDEX.md
#   (vistas parciales).
#
# USO:
#   ./scripts/generate_docs_index.sh
#
# REQUIERE:
#   awk, sed, sort, cut
# ============================================================================

SCRIPT_NAME="generate_docs_index.sh"
DOCS_DIR="$(cd "$(dirname "$0")/../docs" && pwd)"

# --- Logging ---
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# --- Extraer campo del frontmatter YAML ---
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

# --- Extraer NNN del nombre ---
extract_nnn() {
    name="$1"
    case "$name" in
        ALGP003*) echo "ALGP003" ;;
        *) echo "$name" | sed 's/^\([0-9]*\).*/\1/' ;;
    esac
}

# --- Escribir INDEX.md maestro ---
write_master_index() {
    tmpfile="/tmp/docs_master_$$.tmp"
    trap 'rm -f "$tmpfile"' EXIT
    : > "$tmpfile"

    for file in "$DOCS_DIR"/*.md; do
        [ ! -f "$file" ] && continue
        name=$(basename "$file")
        [ "$name" = "INDEX.md" ] && continue

        case "$name" in
            ALGP003*) nnn="ALGP003" ;;
            *) nnn=$(echo "$name" | sed 's/^\([0-9]*\).*/\1/') ;;
        esac
        area=$(extract_fm "$file" "area"); [ -z "$area" ] && area="?"
        tipo=$(extract_fm "$file" "type"); [ -z "$tipo" ] && tipo="?"
        module=$(extract_fm "$file" "module"); [ -z "$module" ] && module="?"
        summary=$(extract_fm "$file" "summary" | cut -c1-80); [ -z "$summary" ] && summary=""
        echo "$area|$nnn|$tipo|$module|$name|$summary" >> "$tmpfile"
    done

    sort -t'|' -k1,1 -k2,2 "$tmpfile" > "${tmpfile}_sorted"
    mv "${tmpfile}_sorted" "$tmpfile"

    # Agrupar por area
    areas=""
    while IFS='|' read -r a n t m f s; do
        case "$areas" in *"$a"*) ;; *) areas="$areas $a" ;; esac
    done < "$tmpfile"

    out="${DOCS_DIR}/INDEX.md"
    {
        echo "---"
        echo "id: INDEX"
        echo "area: doc"
        echo "type: GUIDE"
        echo "module: documentation-index"
        echo "version: 1.0"
        echo "status: ACTIVE"
        echo "summary: \"Indice maestro de documentacion de @Proyecto0. Organizado por AREA_SEMANTICA.\""
        echo "---"
        echo ""
        echo "# Indice de Documentacion"
        echo ""

        total=$(wc -l < "$tmpfile")
        echo "$total documentos organizados por area tematica."
        echo ""

        for a in $areas; do
            count=$(grep -c "^$a|" "$tmpfile" 2>/dev/null || echo 0)
            echo "## Area: $a"
            echo ""
            echo "$count documentos. [Vista parcial](docs/${a}/INDEX.md)"
            echo ""
            echo "| NNN | Tipo | Modulo | Resumen |"
            echo "|-----|------|--------|---------|"
            grep "^$a|" "$tmpfile" | sort -t'|' -k2,2 | while IFS='|' read -r area nnn tipo module fname summ; do
                echo "| $nnn | $tipo | $module | $summ |"
            done
            echo ""
        done

        echo "---"
        echo ""
        echo "## Secuencia completa por NNN"
        echo ""
        echo "| NNN | Archivo | Area | Tipo |"
        echo "|-----|---------|------|------|"
        sort -t'|' -k2,2 "$tmpfile" | while IFS='|' read -r a n t m f s; do
            echo "| $n | \`$f\` | $a | $t |"
        done
    } > "$out"

    log "INDEX.md generado: $out ($total docs)"
    echo "$tmpfile"
}

# --- Escribir INDEX.md para cada area (vista parcial) ---
write_partial_views() {
    tmpfile="$1"

    areas=""
    while IFS='|' read -r a n t m f s; do
        case "$areas" in *"$a"*) ;; *) areas="$areas $a" ;; esac
    done < "$tmpfile"

    for a in $areas; do
        subdir="${DOCS_DIR}/${a}"
        mkdir -p "$subdir"
        out="${subdir}/INDEX.md"
        count=$(grep -c "^$a|" "$tmpfile" 2>/dev/null || echo 0)

        {
            echo "---"
            echo "id: INDEX-${a}"
            echo "area: ${a}"
            echo "type: GUIDE"
            echo "module: documentation-index"
            echo "version: 1.0"
            echo "status: ACTIVE"
            echo "summary: \"Vista parcial de documentacion para area=${a} (${count} documentos).\""
            echo "---"
            echo ""
            echo "# Area: ${a}"
            echo ""
            echo "${count} documentos. [Volver al indice maestro](../INDEX.md)"
            echo ""
            echo "| NNN | Tipo | Modulo | Resumen |"
            echo "|-----|------|--------|---------|"
            grep "^$a|" "$tmpfile" | sort -t'|' -k2,2 | while IFS='|' read -r area nnn tipo module fname summ; do
                echo "| $nnn | $tipo | $module | $summ |"
            done
            echo ""
            echo "## Archivos"
            echo ""
            grep "^$a|" "$tmpfile" | sort -t'|' -k2,2 | while IFS='|' read -r area nnn tipo module fname summ; do
                short=$(echo "$summ" | cut -c1-80)
                echo "- [\`../${fname}\`](../${fname}) — ${short}"
            done
        } > "$out"

        log "  ${a}/INDEX.md generado (${count} docs)"
    done
}

# --- Main ---
main() {
    log "Generando indice de documentacion desde ${DOCS_DIR}..."

    tmpfile=$(write_master_index)
    write_partial_views "$tmpfile"

    total=$(wc -l < "$tmpfile")
    echo ""
    log "Completado: $total documentos indexados en $(ls -d ${DOCS_DIR}/*/INDEX.md ${DOCS_DIR}/INDEX.md 2>/dev/null | wc -l) archivos de indice"
}

main "$@"
