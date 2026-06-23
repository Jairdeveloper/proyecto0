#!/bin/sh
# ============================================================================
# spellscheck.sh — Corrector ortografico interactivo (adaptado)
# ============================================================================
#
# PROPOSITO:
#   Corrector ortografico interactivo para archivos de texto.
#   Adaptacion del clasico spellcheck.awk de Dale Dougherty
#   (O'Reilly, "UNIX Text Processing", 1990).
#
# ORIGINAL:
#   spellcheck.awk — Dale Dougherty, O'Reilly & Associates, 1990
#   Uso: nawk -f spellcheck.awk [+dict] file
#
# ADAPTACION:
#   Shell script que preserva la interfaz original y delega en
#   scripts/spellcheck_docs.sh (motor aspell moderno).
#
# USO (interfaz original):
#   spellscheck.sh [+dict] <archivo>     # Revisar archivo con diccionario
#   spellscheck.sh <archivo>             # Revisar archivo
#   spellscheck.sh --help                # Ayuda detallada
#
# RESPUESTAS INTERACTIVAS:
#   C - Cambiar cada ocurrencia
#   G - Cambio global
#   A - Agregar al diccionario
#   H - Ayuda
#   Q - Salir
#   ENTER - Ignorar
#
# PATRON DE DISEÑO (heredado):
#   Temp files + confirm-before-save + .orig backups + make_change()
#   (ver docs/archive/002_GUIDE_DOC_SPELLCHECK_1.0_DRAFT.md)
#
# REQUIERE:
#   scripts/spellcheck_docs.sh, aspell
# ============================================================================

SCRIPT_NAME="spellscheck.sh"
SCRIPT_DIR="$(dirname "$0")"
MODERN_TOOL="${SCRIPT_DIR}/scripts/spellcheck_docs.sh"

# ============================================================================
# AYUDA
# ============================================================================

show_help() {
    cat <<HELP
spellscheck.sh — Corrector ortografico interactivo (adaptado)

USO:
  $SCRIPT_NAME [+dict] <archivo>        Revision interactiva
  $SCRIPT_NAME --help                   Esta ayuda

ORIGEN:
  Adaptacion de spellcheck.awk (Dale Dougherty, O'Reilly 1990)

ADAPTACION:
  Delega en scripts/spellcheck_docs.sh con motor aspell.
  Preserva el flujo interactivo original (C/G/A/H/Q),
  copias .orig, y confirmacion antes de guardar.

RESPUESTAS INTERACTIVAS:
  C   Cambiar cada ocurrencia
  G   Cambio global
  A   Agregar al diccionario
  H   Ayuda
  Q   Salir
  ENTER  Ignorar

EJEMPLOS:
  $SCRIPT_NAME docs/INDEX.md
  $SCRIPT_NAME +docs/.aspell.pws docs/INDEX.md   (con diccionario)
  $SCRIPT_NAME --help

REQUIERE:
  scripts/spellcheck_docs.sh, aspell
HELP
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        '')
            echo "Error: falta el archivo a revisar"
            echo "Uso: $SCRIPT_NAME [+dict] <archivo>"
            echo "     $SCRIPT_NAME --help"
            exit 1
            ;;
    esac

    # Detectar notacion original +dict (prefijo '+' para diccionario)
    dict_file=""
    target_file=""

    for arg in "$@"; do
        case "$arg" in
            +*)
                dict_file="${arg#+}"
                [ ! -f "$dict_file" ] && dict_file=""
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                target_file="$arg"
                ;;
        esac
    done

    if [ -z "$target_file" ]; then
        echo "Error: no se especifico archivo a revisar"
        echo "Uso: $SCRIPT_NAME [+dict] <archivo>"
        exit 1
    fi

    echo "[spellscheck.sh] Adaptacion de spellcheck.awk (Dougherty 1990)"
    echo "[spellscheck.sh] Motor: aspell (moderno)"
    echo ""

    # Delegar en el tool moderno
    if [ -f "$MODERN_TOOL" ]; then
        if [ -n "$dict_file" ]; then
            echo "[spellscheck.sh] Diccionario: ${dict_file}"
            exec "$MODERN_TOOL" -d "$dict_file" "$target_file"
        else
            exec "$MODERN_TOOL" "$target_file"
        fi
    else
        echo "[spellscheck.sh] ERROR: ${MODERN_TOOL} no encontrado."
        echo "[spellscheck.sh] Instalacion incompleta — asegurese de que"
        echo "[spellscheck.sh] scripts/spellcheck_docs.sh exista."
        exit 1
    fi
}

main "$@"
