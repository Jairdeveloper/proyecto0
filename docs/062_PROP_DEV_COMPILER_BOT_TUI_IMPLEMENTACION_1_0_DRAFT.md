---
id: 062
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - proposal
  - tui
  - implementation
  - agent-robot
  - whiptail
  - testing
summary: "Propuesta de implementacion para respaldar cada seccion de la guia de comportamiento TUI (061_GUIDE). Cubre 12 areas: whiptail, menu, ejecucion de instrucciones, modo interactivo, configuracion LLM, historial, ayuda, salida, bucle principal, tests, mocks y comportamiento real. Identifica brechas entre el comportamiento esperado y el codigo actual, y propone cambios concretos."
keywords:
  - proposal
  - implementation
  - tui
  - whiptail
  - agent
  - interactive-mode
  - llm-config
  - validation
  - plan-flag
  - tests
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Propuesta de implementacion TUI — 12 secciones, 5 brechas identificadas, cambios concretos por seccion
---

# Propuesta de Implementacion: Capa TUI del Agente

## Proposito

Este documento analiza cada seccion de la guia de comportamiento TUI
(`docs/061_GUIDE_DEV_COMPILER_BOT_TUI_BEHAVIOR_1_0_DRAFT.md`) y
propone implementaciones concretas para respaldar la funcionalidad
esperada. Por cada seccion se identifican:

- El **codigo existente** que ya implementa el comportamiento
- Las **brechas** entre el comportamiento esperado y el codigo actual
- Los **cambios propuestos** con archivos, lineas y pseudocodigo

---

## Seccion 1: Requisito Base (whiptail)

### Estado Actual

`tui_check()` en `agent-robot/tui.sh:17-22` ya implementa la
verificacion de whiptail:

```sh
tui_check() {
    command -v whiptail >/dev/null 2>&1 || {
        echo "whiptail no instalado. Ejecuta: sudo apt install whiptail" >&2
        return 1
    }
}
```

En `agent.sh:371` se llama `tui_check || return 1` antes de iniciar el
bucle TUI.

### Brechas

1. **Sin mensaje de instalacion para otros package managers** — El
   mensaje solo menciona `apt`, no `brew`, `yum`, `dnf`, `pacman`.
2. **No hay verificacion de version minima** — whiptail existe pero
   podria ser muy antiguo.

### Propuesta

**Archivo:** `agent-robot/tui.sh`

```sh
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
```

**Tests:** `test_tui_whiptail_available`, `test_tui_check_fail` ya
cubren este comportamiento.

---

## Seccion 2: Menu Principal

### Estado Actual

`tui_menu()` en `agent-robot/tui.sh:25-35` presenta 6 opciones via
`whiptail --menu` con redireccion `3>&1 1>&2 2>&3`.

### Brechas

1. **Las opciones del menu estan hardcodeadas** — No hay manera de
   extenderlas sin modificar `tui.sh`.
2. **El menu no muestra el proveedor LLM activo** — El usuario no ve
   que proveedor esta configurado actualmente.

### Propuesta

**Archivo:** `agent-robot/tui.sh`

Refactorizar `tui_menu()` para leer opciones de un array o permitir
personalizacion via variable de entorno:

```sh
# Opciones por defecto (sobreescribible via AGENT_TUI_MENU_ITEMS)
TUI_MENU_TITLE="${AGENT_TUI_MENU_TITLE:-Proyecto0(RECPL) - ${AGENT_LLM_PROVIDER:-claude}}"

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
```

**Tests:** `test_tui_menu_mocked` ya cubre. Agregar test que verifique
que el titulo incluya el proveedor activo.

---

## Seccion 3: Opcion 1 — Ejecutar Instruccion RECPL

### Estado Actual

`agent-robot/agent.sh` implementa:
- `tui_input()` en `tui.sh:38-42` — cuadro de dialogo
- `classify_intent()` en `agent.sh:102-192` — 9 tipos de intencion
- `execute_intent()` en `agent.sh:195-278` — ejecuta segun intencion
- `format_response()` en `agent.sh:283-322` — formatea salida

### Brechas

1. **`format_response()` usa `printf` con emojis** — La salida JSON de
   las tools internas se formatea con `printf` y emojis Unicode. No hay
   un flag `--json` para obtener la respuesta cruda.
2. **Las respuestas de saludo no se traducen en modo TUI** — En modo
   TUI, la salida de `main()` (via `format_response()`) se pierde en
   stdout porque el bucle TUI no la captura. El usuario nunca ve el
   resultado de su instruccion en el mismo panel TUI.
3. **No hay timeout configurable** — `timeout_run()` esta definido pero
   no se usa en `execute_intent()`.

### Propuesta

**Archivo:** `agent-robot/agent.sh`

Modificar el case de opcion 1 en el bucle TUI para capturar y mostrar
el resultado:

```sh
1)
    _inst=$(tui_input)
    if [ -n "$_inst" ]; then
        _result=$(main "$_inst" 2>&1)
        echo "$_result" | while IFS= read -r _line; do
            tui_output "$_line"
        done
    fi
    ;;
```

**Archivo:** `agent-robot/tui.sh`

Agregar `tui_result()` para mostrar respuestas largas en un msgbox:

```sh
tui_result() {
    _json="$1"
    _mensaje=$(printf '%s' "$_json" | jq -r '.mensaje // .output // ""' 2>/dev/null)
    [ -z "$_mensaje" ] && _mensaje="$(printf '%s' "$_json" | head -c 500)"
    whiptail --title "Resultado" --scrolltext "$_mensaje" 20 80 2>/dev/null || \
        whiptail --title "Resultado" --msgbox "$_mensaje" 20 80
}
```

**Tests existentes:** `test_tui_input_mocked`, `test_agent_greeting`,
`test_agent_identity`, `test_bridge_recpl`, `test_planner_multi_create`.

---

## Seccion 4: Opcion 2 — Modo Interactivo

### Estado Actual

**NO IMPLEMENTADO.** Actualmente muestra:

```sh
tui_output "Modo interactivo no implementado via TUI aun"
```

### Brecha

El modo interactivo CLI (`./agent.sh` sin argumentos, lee de stdin en
bucle) existe pero no tiene equivalente TUI.

### Propuesta

Crear `tui_interactive()` en `agent-robot/tui.sh`:

```sh
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
```

**Archivo:** `agent-robot/agent.sh` — Cambiar el case 2:

```sh
2) . "$SCRIPT_DIR/tui.sh" && tui_interactive ;;
```

**Tests nuevos:**

```sh
test_tui_interactive_exit() {
    # Mock que retorna "salir" en inputbox
    _mock_dir="/tmp/tui_mock_int_$$"
    mkdir -p "$_mock_dir"
    cat > "$_mock_dir/whiptail" << 'MOCK'
#!/bin/sh
for _arg in "$@"; do
    case "$_arg" in
        --inputbox) echo "salir" >&3; exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    _exit=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" \
        sh -c '. agent-robot/tui.sh && tui_interactive >/dev/null 2>&1; echo $?')
    rm -rf "$_mock_dir"
    if echo "$_exit" | grep -q "^0$"; then
        echo "  ✅ tui_interactive: 'salir' termina el bucle"
    else
        echo "  ❌ tui_interactive: falla (exit: $_exit)"
    fi
}
```

---

## Seccion 5: Opcion 3 — Configurar LLM

### Estado Actual

`tui_llm_config()` en `tui.sh:51-65`:
1. Pide proveedor con default `${AGENT_LLM_PROVIDER:-claude}`
2. Pide modo con default `${AGENT_LLM_MODE:-auto}`
3. Exporta las variables y muestra confirmacion

### Brechas

1. **Sin validacion de proveedor** — Acepta cualquier string, incluso
   "invalid_provider_xyz" o "apifreellm" (que no existe).
2. **Sin validacion de modo** — Acepta cualquier string.
3. **`apifreellm` listado como opcion** pero no hay implementacion.

### Propuesta

**Archivo:** `agent-robot/tui.sh`

```sh
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
```

**Tests:** Modificar `test_tui_llm_config_invalid_provider` para que
verifique que un proveedor invalido **no** se acepta y produce mensaje
de error. Agregar `test_tui_llm_config_valid_provider` que verifique
que "claude" se acepta.

---

## Seccion 6: Opcion 4 — Ver Historial

### Estado Actual

`tui_history()` en `tui.sh:68-78`:
- Sourcea `$SCRIPT_DIR/memory.sh`
- Llama a `memory_history()`
- Si vacio o `[]`, muestra "No hay entradas en el historial."
- Si hay datos, formatea con `jq` y muestra ultimas 20.

### Brechas

1. **`tui_history()` se llama a si mismo via `main()` recursivo** —
   Cuando el usuario selecciona opcion 4 desde el menu TUI, el historial
   se muestra. Pero si el usuario ejecuta `tui_history` desde el bucle,
   no hay recursion. Sin embargo, `tui_history` sourcea `memory.sh`
   cada vez, lo cual es ineficiente.
2. **No hay Paginacion** — `head -20` funciona pero no hay
   "siguiente pagina" para ver mas.

### Propuesta

**Archivo:** `agent-robot/tui.sh`

Optimizar agregando paginacion y cache:

```sh
tui_history() {
    . "$SCRIPT_DIR/memory.sh"
    _history=$(memory_history 2>/dev/null || echo "[]")
    if [ -z "$_history" ] || [ "$_history" = "[]" ]; then
        tui_output "No hay entradas en el historial."
        return
    fi
    _total=$(echo "$_history" | jq 'length' 2>/dev/null || echo 0)
    _page=0
    _page_size=10
    while true; do
        _start=$((_page * _page_size))
        _formatted=$(echo "$_history" | jq -r ".[$_start:$_start+$_page_size][] | \"\(.timestamp // \"?\"): \(.instruction // "")\"" 2>/dev/null)
        [ -z "$_formatted" ] && _formatted="(no hay mas entradas)"
        _header="Historial (pagina $((_page+1)), $_total totales):"
        tui_output "$_header
$_formatted"
        _choice=$(whiptail --title "Historial" \
            --menu "Pagina $((_page+1)) de $(( (_total + _page_size - 1) / _page_size ))" 20 60 3 \
            "n" "Siguiente pagina" \
            "p" "Pagina anterior" \
            "v" "Volver al menu" 3>&1 1>&2 2>&3)
        case "$_choice" in
            n) [ $(( (_page+1) * _page_size )) -lt "$_total" ] && _page=$((_page+1)) ;;
            p) [ "$_page" -gt 0 ] && _page=$((_page-1)) ;;
            *) break ;;
        esac
    done
}
```

**Tests existentes:** `test_tui_history_empty`,
`test_tui_history_with_data`.

---

## Seccion 7: Opcion 5 — Ayuda

### Estado Actual

`tui_help()` en `tui.sh:81-101` muestra informacion del proyecto via
`whiptail --msgbox`.

### Brechas

1. **El texto de ayuda esta hardcodeado** — No se sincroniza con
   `show_help()` en `agent.sh:69-97`. Cambiar uno requiere cambiar el
   otro.

### Propuesta

**Archivo:** `agent-robot/tui.sh`

Refactorizar para compartir el texto de ayuda:

```sh
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
```

Alternativa: Extraer el texto de ayuda a un archivo compartido
(`agent-robot/prompts/help_text.txt`) y que tanto `show_help()` como
`tui_help()` lo lean.

**Tests existentes:** `test_tui_help_mocked`,
`test_agent_tui_menu_help`.

---

## Seccion 8: Opcion 6 — Salir

### Estado Actual

```sh
6)  exit 0 ;;
"") exit 0 ;;
```

ya implementado en `agent.sh:391-396`.

### Brechas

Ninguna. El comportamiento es simple y esta completo.

### Propuesta

Ninguna. Mantener como esta.

**Tests existentes:** `test_agent_tui_flag` (mock retorna "6", TUI
termina).

---

## Seccion 9: Bucle Principal TUI

### Estado Actual

El bucle en `agent.sh:368-400`:
```sh
if [ "$_mode" = "tui" ]; then
    . "$SCRIPT_DIR/tui.sh"
    tui_check || return 1
    while true; do
        _choice=$(tui_menu)
        case "$_choice" in ...
```

### Brechas

1. **El resultado de `main()` no se muestra en TUI** — Cuando el
   usuario ejecuta una instruccion (opcion 1), `main()` imprime a
   stdout pero el bucle TUI no captura esa salida para mostrarla en un
   msgbox. El usuario debe cambiar al terminal para ver el resultado.
2. **No hay manejo de errores en `tui_check`** — Si whiptail no esta
   disponible, `return 1` termina `main()`. En modo `--tui` desde CLI,
   esto es correcto. Pero si `agent.sh` es sourceado, `return` podria
   no funcionar como se espera.

### Propuesta

**Archivo:** `agent-robot/agent.sh`

```sh
if [ "$_mode" = "tui" ]; then
    . "$SCRIPT_DIR/tui.sh"
    tui_check || { echo "Error: whiptail no instalado. Usa ./agent.sh sin --tui"; return 1; }
    while true; do
        _choice=$(tui_menu)
        case "$_choice" in
            1)
                _inst=$(tui_input)
                if [ -n "$_inst" ]; then
                    _result=$(main "$_inst" 2>&1)
                    echo "$_result" | head -20 | while IFS= read -r _line; do
                        [ -n "$_line" ] && tui_output "$_line"
                    done
                fi
                ;;
            2) . "$SCRIPT_DIR/tui.sh" && tui_interactive ;;
            3) tui_llm_config ;;
            4) tui_history ;;
            5) tui_help ;;
            6) exit 0 ;;
            "") exit 0 ;;
        esac
    done
fi
```

**Tests:** Los tests `test_agent_tui_flag`,
`test_agent_tui_menu_history`, `test_agent_tui_menu_help` ya cubren
el bucle a nivel de integracion.

---

## Seccion 10: Tabla de Tests TUI

### Estado Actual

14 tests en `tests/test_agent.sh:389-675`. 11 pasan (✅), 3 son
warnings (⚠️) por depender de terminal real.

### Brechas

1. **Tests 12-14 son ⚠️** — `test_agent_tui_flag`,
   `test_agent_tui_menu_history`, `test_agent_tui_menu_help` dependen
   de `agent.sh --tui` que requiere whiptail real.
2. **No hay tests para `tui_interactive()`** — Porque no existe.
3. **No hay tests de validacion de proveedor LLM** — Solo existe
   `test_tui_llm_config_invalid_provider` que verifica que acepta
   cualquier valor (comportamiento actual, no el deseado).

### Propuesta

**Tests nuevos a agregar en `tests/test_agent.sh`:**

```sh
# Test: validacion de proveedor LLM (comportamiento futuro)
test_tui_llm_config_validation() {
    _mock_dir="/tmp/tui_mock_val_$$"
    mkdir -p "$_mock_dir"
    cat > "$_mock_dir/whiptail" << MOCK
#!/bin/sh
_f="/tmp/tui_val_cnt_$$"
if [ ! -f "\$_f" ]; then echo "0" > "\$_f"; fi
read _c < "\$_f"
for _arg in "\$@"; do
    case "\$_arg" in
        --inputbox)
            _c=\$((_c + 1)); echo "\$_c" > "\$_f"
            # Primera llamada: provider invalido
            # Segunda llamada: mode invalido
            # Tercera llamada: provider valido
            if [ "\$_c" -eq 1 ] || [ "\$_c" -eq 2 ]; then
                echo "invalid" >&3
            else
                echo "claude" >&3
            fi
            exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    rm -f /tmp/tui_val_cnt_$$
    _result=$(cd "$SCRIPT_DIR" && PATH="$_mock_dir:$PATH" sh -c '
        . agent-robot/tui.sh
        unset AGENT_LLM_PROVIDER
        unset AGENT_LLM_MODE
        tui_llm_config >/dev/null 2>&1
        echo "PROVIDER=${AGENT_LLM_PROVIDER:-}"
        echo "MODE=${AGENT_LLM_MODE:-}"
    ')
    rm -rf "$_mock_dir" /tmp/tui_val_cnt_$$
    _provider=$(echo "$_result" | grep "^PROVIDER=" | sed 's/^PROVIDER=//')
    if [ "$_provider" = "claude" ]; then
        echo "  ✅ tui_llm_config: rechaza invalido, acepta valido"
    else
        echo "  ⚠️  tui_llm_config: validacion (depende de implementacion)"
    fi
}
```

**Agregar al MAIN:** despues de la linea 720
(`test_tui_llm_config_invalid_provider`):

```sh
test_tui_llm_config_validation
```

---

## Seccion 11: Mocks de whiptail para Tests

### Estado Actual

Dos helpers en `tests/test_agent.sh:345-387`:
- `_prepare_whiptail_mock()` — mock simple (--menu → "1",
  --inputbox → "test_input", --msgbox → exit 0)
- `_prepare_whiptail_mock_choice()` — mock parametrizable con archivo
  contador para secuencias

### Brechas

1. **Los mocks usan `/tmp/` para archivos contador** — Podria haber
   conflictos entre tests paralelos.
2. **`_prepare_whiptail_mock_choice()` no maneja `--msgbox`** — El loop
  termina sin hacer nada, pero no es un problema porque `exit 0` se
  ejecuta al final.

### Propuesta

**Archivo:** `tests/test_agent.sh`

Refactorizar `_prepare_whiptail_mock_choice()` para usar `mktemp`:

```sh
_prepare_whiptail_mock_choice() {
    _choice="$1"
    _mock_dir="$(mktemp -d /tmp/tui_mock2_$$_XXXXXX)"
    _cnt_file="$(mktemp /tmp/tui_cnt_$$_XXXXXX)"
    cat > "$_mock_dir/whiptail" << MOCK
#!/bin/sh
_f="$_cnt_file"
if [ ! -f "\$_f" ]; then echo "0" > "\$_f"; fi
read _c < "\$_f"
for _arg in "\$@"; do
    case "\$_arg" in
        --menu)
            _c=\$((_c + 1)); echo "\$_c" > "\$_f"
            if [ "\$_c" -eq 1 ]; then echo "$_choice" >&3; else echo "6" >&3; fi
            exit 0 ;;
        --inputbox) echo "test_input" >&3; exit 0 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
MOCK
    chmod +x "$_mock_dir/whiptail"
    echo "$_mock_dir"
}
```

---

## Seccion 12: Comportamiento en Entorno Real

### 12.1 Modos de Operacion

### Estado Actual

| Modo | Flag | Implementado? |
|------|------|---------------|
| Normal | (sin flag) | ✅ `agent.sh:402-416` |
| LLM forzado | `--llm` | ✅ `agent.sh:332-333` |
| Deterministico | `--deterministic` | ✅ `agent.sh:336-337` |
| TUI | `--tui` | ✅ `agent.sh:340-342` |
| Batch | stdin | ✅ `agent.sh:405-407` |
| Plan | `--plan` | ❌ **No implementado** |

### Propuesta

**Archivo:** `agent-robot/agent.sh`

Agregar `--plan` al parser de argumentos en `main()`:

```sh
# Linea 338, despues de --deterministic)
--plan)
    _mode="plan"
    shift
    ;;
```

Y en el flujo principal, despues del bloque TUI:

```sh
# Antes de la seccion de instruccion (linea 402)
if [ "$_mode" = "plan" ]; then
    . "$SCRIPT_DIR/tui.sh"
    _inst="$*"
    if [ -z "$_inst" ]; then
        read -r _inst || true
    fi
    if [ -n "$_inst" ]; then
        . "$SCRIPT_DIR/planner_llm.sh" 2>/dev/null || . "$SCRIPT_DIR/planner.sh"
        _plan=$(planificar "$_inst")
        ejecutar_plan "$_plan"
    fi
    return
fi
```

**Tests nuevos:**

```sh
test_agent_plan_flag() {
    _result=$(cd "$SCRIPT_DIR" && ./agent.sh --plan "crea modulo testplan y modulo testplan2 en nestjs" 2>/dev/null)
    if echo "$_result" | grep -qi "plan\|multi\|paso"; then
        echo "  ✅ agent.sh --plan: flag reconocido y plan ejecutado"
    else
        echo "  ⚠️  agent.sh --plan: puede fallar sin RECPL configurado"
    fi
}
```

### 12.2 Variables de Entorno

**Estado actual:** `config.sh` define defaults para todas las variables
listadas. `AGENT_LLM_TIER` esta definida pero no se usa (ver reporte
`060_REP_DEV_COMPILER_BOT_INCONSISTENCIAS_1_0_DRAFT.md` seccion 3c).

**Propuesta:** Remover `AGENT_LLM_TIER` de `config.sh` o implementar
su logica en `classify_intent()`:

```sh
# En classify_intent(), antes del fallback a LLM:
if [ "$AGENT_LLM_TIER" = "deterministic" ]; then
    echo "recpl"
    return
fi
```

### 12.3 Ejemplos de Uso Real

**Estado actual:** Todos los ejemplos funcionan excepto `--plan`.

**Propuesta:** Agregar `--plan` (ver seccion 12.1).

### 12.4 Limitaciones Conocidas

#### Limitacion 1: `apifreellm` no implementado

**Estado:** No existe `providers/apifreellm.sh`. Aparece en menu TUI y
documentacion.

**Propuesta:** Crear `providers/apifreellm.sh` siguiendo el patron de
`claude.sh`:

```sh
#!/bin/sh
# apifreellm.sh - Provider para API Free LLM
# Sigue el patron de providers/claude.sh
API_FREE_URL="${API_FREE_URL:-https://api.apifreellm.example.com/v1}"

apifreellm_call() {
    _prompt="$1"
    _api_key="${API_FREE_KEY:-}"
    [ -z "$_api_key" ] && { echo '{"error":"API_FREE_KEY no configurada"}'; return 1; }
    # ... implementacion de llamada HTTP ...
}

apifreellm_available() {
    [ -n "${API_FREE_KEY:-}" ]
}
```

O, alternativamente, **remover `apifreellm` del menu TUI** y de la
documentacion hasta que se implemente.

#### Limitacion 2: Modo interactivo no implementado

**Estado:** Opcion 2 del menu TUI muestra placeholder.

**Propuesta:** Ver seccion 4.

#### Limitacion 3: Sin validacion de proveedor

**Estado:** `tui_llm_config()` acepta cualquier texto.

**Propuesta:** Ver seccion 5.

#### Limitacion 4: Dependencia de `jq`

**Estado:** Todo el parsing JSON usa `jq`.

**Propuesta:** Agregar verificacion de `jq` al inicio y mensaje claro:

```sh
# En agent.sh, antes de usar jq:
tui_check_jq() {
    command -v jq >/dev/null 2>&1 || {
        echo "Error: jq no instalado. Ejecuta: sudo apt install jq" >&2
        return 1
    }
}
```

Y verificar al inicio de `memory.sh`, `tool_registry.sh`, `tui.sh`.

#### Limitacion 5: Memoria en `/tmp/`

**Estado:** `AGENT_MEMORY_DIR` default es `/tmp/agent_memory`.

**Propuesta:** No cambiar el default (es estandar para herramientas
POSIX), pero documentar que puede sobreescribirse:

```sh
export AGENT_MEMORY_DIR="${AGENT_MEMORY_DIR:-/tmp/agent_memory}"
```

Agregar mensaje de advertencia si se usa el default:

```sh
# En agent.sh, despues de cargar config.sh:
if echo "$AGENT_MEMORY_DIR" | grep -q "^/tmp/"; then
    echo "⚠️  Memoria en /tmp/ (se pierde al reiniciar). Usa AGENT_MEMORY_DIR para cambiarlo." >&2
fi
```

---

## Resumen de Cambios Propuestos

| # | Seccion | Archivo | Cambio | Prioridad |
|---|---------|---------|--------|-----------|
| 1 | 1 | `tui.sh` | Mensaje multi-package-manager en `tui_check()` | Baja |
| 2 | 2 | `tui.sh` | Titulo dinamico en `tui_menu()` con proveedor activo | Baja |
| 3 | 3 | `agent.sh` | Capturar stdout de `main()` en bucle TUI y mostrar via `tui_output()` | **Alta** |
| 4 | 3 | `tui.sh` | Nueva funcion `tui_result()` para respuestas largas | Media |
| 5 | 4 | `tui.sh` | Nueva funcion `tui_interactive()` | **Alta** |
| 6 | 4 | `agent.sh` | Case 2 → llama a `tui_interactive()` | Media |
| 7 | 5 | `tui.sh` | Validacion de proveedor y modo en `tui_llm_config()` | **Alta** |
| 8 | 6 | `tui.sh` | Paginacion en `tui_history()` | Media |
| 9 | 7 | `tui.sh` | Texto de ayuda compartido vía `show_help()` o archivo externo | Baja |
| 10 | 9 | `agent.sh` | Capturar y mostrar resultado de `main()` en bucle TUI | **Alta** |
| 11 | 10 | `test_agent.sh` | Nuevo test `test_tui_llm_config_validation` | Media |
| 12 | 10 | `test_agent.sh` | Nuevo test `test_tui_interactive_exit` | Media |
| 13 | 11 | `test_agent.sh` | Refactorizar `_prepare_whiptail_mock_choice()` con `mktemp` | Baja |
| 14 | 12.1 | `agent.sh` | Implementar flag `--plan` | **Alta** |
| 15 | 12.1 | `test_agent.sh` | Nuevo test `test_agent_plan_flag` | Media |
| 16 | 12.2 | `config.sh` | Remover o implementar `AGENT_LLM_TIER` | Media |
| 17 | 12.4 | `providers/apifreellm.sh` | Crear provider o remover del menu | **Alta** |
| 18 | 12.4 | `agent.sh` | Verificacion de `jq` al inicio | Media |
| 19 | 12.4 | `agent.sh` | Warning si `AGENT_MEMORY_DIR` es `/tmp/` | Baja |

### Prioridades

- **Alta** (5): Afectan funcionalidad core del TUI
  3, 5, 7, 10, 14, 17
- **Media** (6): Mejoras de UX o testing
  4, 6, 8, 11, 12, 15, 16, 18
- **Baja** (5): Limpieza y mantenimiento
  1, 2, 9, 13, 19

---

## Referencias

- `docs/061_GUIDE_DEV_COMPILER_BOT_TUI_BEHAVIOR_1_0_DRAFT.md` — Guia de
  comportamiento que origina esta propuesta
- `docs/060_REP_DEV_COMPILER_BOT_INCONSISTENCIAS_1_0_DRAFT.md` —
  Reporte de inconsistencias (apifreellm, AGENT_LLM_TIER, etc.)
- `docs/058_REP_DEV_COMPILER_BOT_TUI_1_0_DRAFT.md` — Reporte de
  implementacion TUI original
- `agent-robot/tui.sh` — Capa TUI (7 funciones, 102 lineas)
- `agent-robot/agent.sh` — Bucle principal y clasificador
- `tests/test_agent.sh` — Tests existentes (34 tests, FAIL=0)
