#!/bin/sh
# ============================================================================
# tui.sh - Capa TUI (whiptail) para Proyecto0(RECPL)
# ============================================================================
#
# PROPOSITO:
#   Proporciona una interfaz de usuario basada en whiptail para el
#   agent-robot. Permite ejecutar instrucciones, configurar el LLM,
#   ver historial y acceder a ayuda sin usar la linea de comandos.
#
# USO:
#   . tui.sh
#   tui_check && tui_menu
# ============================================================================

# --- Verificar whiptail ---
tui_check() {
    command -v whiptail >/dev/null 2>&1 || {
        _os=""
        [ -f /etc/debian_version ] && _os="apt install whiptail"
        [ -f /etc/redhat-release ] && _os="yum install whiptail"
        [ -f /etc/arch-release ]   && _os="pacman -S whiptail"
        [ "$(uname)" = "Darwin" ]  && _os="brew install whiptail"
        echo "whiptail no instalado. Ejecuta: sudo $_os" >&2
        return 1
    }
}

# --- Titulo dinamico del menu ---
TUI_MENU_TITLE="${AGENT_TUI_MENU_TITLE:-Proyecto0(RECPL) - ${AGENT_LLM_PROVIDER:-claude}}"

# --- Menu principal ---
tui_menu() {
    _choice=$(whiptail --title "$TUI_MENU_TITLE" \
        --menu "Selecciona una opcion:" 20 60 10 \
        "1" "Ejecutar instruccion RECPL" \
        "2" "Modo interactivo" \
        "3" "Configurar LLM (${AGENT_LLM_PROVIDER:-claude})" \
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

# --- Modo interactivo ---
tui_interactive() {
    tui_output "Modo interactivo — escribe 'salir' para volver al menu"
    while true; do
        _inst=$(whiptail --title "Modo Interactivo" \
            --inputbox "Instruccion (o 'salir' para volver):" 10 60 \
            3>&1 1>&2 2>&3)
        [ $? -ne 0 ] && break
        [ -z "$_inst" ] && continue
        echo "$_inst" | grep -qiE '^(salir|exit|menu|volver)$' && break
        main "$_inst"
    done
}

# --- Output box ---
tui_output() {
    _msg="$1"
    whiptail --title "Resultado" --msgbox "$_msg" 20 60
}

# --- Configurar LLM ---
tui_llm_config() {
    _valid_providers="claude openai"
    _valid_modes="auto llm deterministic"

    while true; do
        _provider=$(whiptail --title "Configurar LLM" \
            --inputbox "Proveedor LLM ($(echo $_valid_providers | tr ' ' ', ')):" 10 60 \
            "${AGENT_LLM_PROVIDER:-claude}" 3>&1 1>&2 2>&3)
        [ -z "$_provider" ] && return
        _found=0
        for _p in $_valid_providers; do
            [ "$_provider" = "$_p" ] && _found=1
        done
        [ "$_found" -eq 1 ] && break
        tui_output "Proveedor no soportado. Validos: $(echo $_valid_providers | tr ' ' ', ')"
    done
    export AGENT_LLM_PROVIDER="$_provider"

    while true; do
        _mode=$(whiptail --title "Configurar LLM" \
            --inputbox "Modo LLM ($(echo $_valid_modes | tr ' ' ', ')):" 10 60 \
            "${AGENT_LLM_MODE:-auto}" 3>&1 1>&2 2>&3)
        [ -z "$_mode" ] && return
        _found=0
        for _m in $_valid_modes; do
            [ "$_mode" = "$_m" ] && _found=1
        done
        [ "$_found" -eq 1 ] && break
        tui_output "Modo no soportado. Validos: $(echo $_valid_modes | tr ' ' ', ')"
    done
    export AGENT_LLM_MODE="$_mode"

    tui_output "Configuracion actualizada para esta sesion:
  Proveedor: ${AGENT_LLM_PROVIDER:-claude}
  Modo:      ${AGENT_LLM_MODE:-auto}"
}

# --- Ver historial ---
tui_history() {
    . "$SCRIPT_DIR/memory.sh"
    _history=$(memory_history 2>/dev/null || echo "No hay historial disponible")
    if [ -z "$_history" ] || [ "$_history" = "[]" ]; then
        tui_output "No hay entradas en el historial."
    else
        _formatted=$(echo "$_history" | jq -r '.[] | "\(.timestamp // "?"): \(.instruction // "")"' 2>/dev/null | head -20)
        tui_output "Historial (ultimas 20):
$_formatted"
    fi
}

# --- Ayuda ---
tui_help() {
    _help_text=$(cat <<HELP
RECPL Compiler Bot v${AGENT_VERSION:-1.0.0}

USO DESDE CLI:
  ./agent.sh "instruccion"                Modo normal
  ./agent.sh --llm "instruccion"          Fuerza uso de LLM
  ./agent.sh --deterministic "instruc"    Solo RECPL deterministico
  ./agent.sh --tui                        Modo TUI (whiptail)

MODOS (via AGENT_LLM_MODE):
  auto          Intenta RECPL deterministico, luego LLM si falla
  llm           Usa LLM directamente
  deterministic Solo RECPL deterministico

EJEMPLOS:
  - crea modulo pagos en nestjs
  - crea entidad usuario en prisma
  - hola
  - quien eres?
  - ayuda

Mas informacion: ./agent.sh --help
HELP
)
    whiptail --title "Ayuda - Proyecto0(RECPL)" --scrolltext "$_help_text" 20 70
}
