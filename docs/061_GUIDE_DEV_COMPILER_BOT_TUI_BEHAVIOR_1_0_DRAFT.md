---
id: 061
area: dev
type: guide
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - tui
  - whiptail
  - behavior
  - specification
  - agent-robot
  - tests
summary: "Guia de comportamiento esperado del agente en modo TUI. Describe las 6 opciones del menu, el flujo de cada una, los tipos de instruccion soportados, y como se mapean a las acciones del agente. Sirve como modelo de especificacion basado en los tests TUI existentes (FAIL=0)."
keywords:
  - guide
  - tui
  - whiptail
  - behavior
  - specification
  - agent
  - menu
  - llm
  - history
  - recpl
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Guia de comportamiento TUI — 6 opciones, clasificador de intencion, 14 tests de cobertura
---

# Guia de Comportamiento del Agente TUI

## Proposito

Este documento describe el comportamiento esperado del agente
Proyecto0(RECPL) cuando opera en **modo TUI** (`--tui`). La interfaz
TUI usa `whiptail` para presentar menus, cuadros de dialogo y mensajes
al usuario.

El comportamiento se deduce de:
- El codigo fuente (`tui.sh`, `agent.sh`)
- Los tests TUI en `tests/test_agent.sh` (14 tests, FAIL=0)
- Las especificaciones del proyecto RECPL Compiler Bot

---

## 1. Requisito Base: whiptail

### 1.1 Disponibilidad

El sistema **debe** tener `whiptail` instalado para usar el modo TUI.

**Test:** `test_tui_whiptail_available`
```sh
command -v whiptail >/dev/null 2>&1
```
- Si whiptail existe → el test reporta disponible
- Si no existe → reporta advertencia (el resto de tests se saltan)

### 1.2 Deteccion de ausencia

La funcion `tui_check()` verifica whiptail y falla con mensaje claro:

```sh
tui_check() {
    command -v whiptail >/dev/null 2>&1 || {
        echo "whiptail no instalado. Ejecuta: sudo apt install whiptail" >&2
        return 1
    }
}
```

**Test:** `test_tui_check_fail` — simula PATH sin whiptail, verifica que
`tui_check()` retorna exit code != 0 y produce mensaje con "whiptail" e
"instal".

**Comportamiento esperado en entorno real:**
- Sin whiptail: `tui_check()` retorna 1, `agent.sh --tui` termina con
  `return 1`, no se muestra ningun menu
- Con whiptail: `tui_check()` retorna 0, el bucle TUI se inicia

---

## 2. Menu Principal

`tui_menu()` presenta 6 opciones via `whiptail --menu`:

```
Proyecto0(RECPL)
Selecciona una opcion:
  1. Ejecutar instruccion RECPL
  2. Modo interactivo
  3. Configurar LLM
  4. Ver historial
  5. Ayuda
  6. Salir
```

**Tecnica de redireccion:** `whiptail` devuelve la opcion seleccionada
por el usuario a traves de fd3 mediante `3>&1 1>&2 2>&3`. El resultado
se captura en `_choice` y se imprime via `echo "$_choice"`.

**Test:** `test_tui_menu_mocked` — mock whiptail que escanea argumentos
buscando `--menu` y escribe "1" a fd3. Verifica que `tui_menu()`
retorna "1".

**Comportamiento esperado en entorno real:**
- El usuario selecciona una opcion numerica (1-6)
- Si el usuario cancela (ESC/Cancelar), la opcion retorna vacio `""`
  y el bucle termina (`exit 0`)

---

## 3. Opcion 1: Ejecutar Instruccion RECPL

### Flujo

```
Menu → opcion 1 → tui_input() → main(instruccion)
```

1. `tui_input()` presenta un cuadro `--inputbox` con titulo
   "Instruccion" y texto "Escribe tu instruccion:"
2. El usuario escribe cualquier texto y presiona Enter
3. Si el texto no esta vacio, se pasa a `main()`
4. `main()` clasifica la intencion y ejecuta la accion

**Test:** `test_tui_input_mocked` — mock whiptail que detecta
`--inputbox` y escribe "test_input" a fd3. Verifica que
`tui_input()` retorna "test_input".

### 3.1 Clasificador de Intencion

`classify_intent()` determina que accion ejecutar segun la instruccion:

| Intencion | Patron | Ejemplo | Accion |
|-----------|--------|---------|--------|
| `respond` | Saludo, "quien eres", "gracias", "adios" | "hola", "quien eres?" | `tool_respond` con mensaje predefinido |
| `help` | "ayuda", "--help" | "ayuda" | `show_help` |
| `read_file` | "lee", "muestra", "cat", "abre", "read" | "lee README.md" | `tool_read_file` |
| `write_file` | "crea archivo", "escribe", "write", "genera archivo" | "crea archivo test.txt con contenido hola" | `tool_write_file` |
| `run_command` | "ejecuta", "corre", "run", "executa", "lanza" | "ejecuta ls -la" | `tool_run_command` |
| `recpl` | "crea", "genera", "elimina", "lista", "actualiza", "modifica", "source", "exec" | "crea modulo pagos en nestjs" | `bridge_recpl` |
| `plan` | Multiples acciones RECPL (detectado por planner) | "crea modulo auth y modulo payments en nestjs" | `planner` (planifica y ejecuta multi-paso) |
| `llm` | Default en modo `auto`, o forzado con `--llm` | cualquier otra cosa | `bridge_llm` |
| `error` | Instruccion vacia | `""` | Mensaje de error |

### 3.2 Respuestas Esperadas

#### Saludos (`respond`)

```
Usuario: "hola"
Agente: "Hola! Soy Proyecto0(RECPL). En que puedo ayudarte?..."

Usuario: "quien eres?"
Agente: "Soy Proyecto0(RECPL) v1.0, un agente de codigo abierto..."

Usuario: "gracias"
Agente: "De nada! Estoy aqui para ayudarte con tu codigo."

Usuario: "adios"
Agente: "Hasta luego! Vuelve cuando necesites ayuda con tu codigo."
```

**Test:** `test_agent_greeting` — "hola" → respuesta contiene
"hola|ayudar|proyecto0". `test_agent_identity` — "quien eres?" →
respuesta contiene "proyecto0|agente|recpl".

#### Creacion de Modulos/Entidades (`recpl`)

```
Usuario: "crea modulo pagos en nestjs"
Agente: JSON con exito, tipo_respuesta, payload del scaffold

Usuario: "crea entidad usuario en prisma"
Agente: JSON con exito, tipo_respuesta, payload del modelo Prisma
```

**Test:** `test_bridge_recpl` — "crea modulo testbridge en nestjs" →
`exito=true, origen=recpl`.

#### Multi-create (`plan`)

```
Usuario: "crea modulo auth y modulo payments en nestjs"
Agente: Plan multi-paso, ejecuta cada paso secuencialmente
```

**Test:** `test_planner_multi_create` — verifica `tipo=multi_create`,
`total_pasos >= 2`.

#### LLM (fallback)

```
Usuario: "cual es el sentido de la vida?"
Agente: Respuesta del LLM configurado
```

**Test:** `test_agent_llm_mode` — "--llm hola" → respuesta contiene
"respuesta|llm|proyecto0".

#### Instruccion Vacia

```
Usuario: ""
Agente: "No se recibio ninguna instruccion."
```

**Test:** `test_agent_error_empty` — respuesta contiene
"error|no se recibio|vacia".

---

## 4. Opcion 2: Modo Interactivo

Actualmente no implementado via TUI.

```
Al seleccionar opcion 2:
  tui_output("Modo interactivo no implementado via TUI aun")
```

---

## 5. Opcion 3: Configurar LLM

`tui_llm_config()` presenta dos cuadros de entrada secuenciales:

### 5.1 Proveedor LLM

```
Titulo: "Configurar LLM"
Texto: "Proveedor LLM (claude, openai, apifreellm):"
Valor por defecto: ${AGENT_LLM_PROVIDER:-claude}
```

Si el usuario ingresa un valor no vacio, se exporta como
`AGENT_LLM_PROVIDER`.

**Nota:** Aunque el menu ofrece `apifreellm`, este proveedor **no esta
implementado** (no existe `providers/apifreellm.sh`). Seleccionarlo
produce error silencioso en `llm_classifier.sh`.

### 5.2 Modo LLM

```
Titulo: "Configurar LLM"
Texto: "Modo LLM (auto, llm, deterministic):"
Valor por defecto: ${AGENT_LLM_MODE:-auto}
```

Si el usuario ingresa un valor no vacio, se exporta como
`AGENT_LLM_MODE`.

### 5.3 Confirmacion

```sh
tui_output "Configuracion actualizada para esta sesion:
  Proveedor: ${AGENT_LLM_PROVIDER:-claude}
  Modo:      ${AGENT_LLM_MODE:-auto}"
```

**Tests:**
- `test_tui_llm_config_exports` — verifica que `AGENT_LLM_PROVIDER` y
  `AGENT_LLM_MODE` se exportan con valores no vacios
- `test_tui_llm_config_invalid_provider` — verifica que cualquier valor
  (incluso "invalid_provider_xyz") se acepta y exporta sin validacion

---

## 6. Opcion 4: Ver Historial

`tui_history()` fuentea `memory.sh` y muestra el historial de
instrucciones previas.

### 6.1 Historial Vacio

```sh
if [ -z "$_history" ] || [ "$_history" = "[]" ]; then
    tui_output "No hay entradas en el historial."
```

**Test:** `test_tui_history_empty` — memoria con `{"historial":[]}` →
`tui_history()` termina con exit code 0.

### 6.2 Historial con Datos

```sh
_formatted=$(echo "$_history" | jq -r '.[] | "\(.timestamp // "?"): \(.instruction // "")"' 2>/dev/null | head -20)
tui_output "Historial (ultimas 20):\n$_formatted"
```

Formatea cada entrada como `TIMESTAMP: INSTRUCCION` y muestra las
ultimas 20 entradas.

**Test:** `test_tui_history_with_data` — memoria con 1 entrada →
`tui_history()` termina con exit code 0.

---

## 7. Opcion 5: Ayuda

`tui_help()` muestra informacion del proyecto via `whiptail --msgbox`:

```
RECPL Compiler Bot v1.0

Un compilador de lenguaje natural a codigo NestJS/Prisma.

EJEMPLOS:
  - crea modulo pagos en nestjs
  - crea entidad usuario en prisma
  - hola
  - quien eres?
  - ayuda

MODOS:
  auto:   RECPL deterministico, luego LLM
  llm:    solo LLM
  deterministic: solo RECPL

Mas informacion:
  ./agent.sh --help
```

**Test:** `test_tui_help_mocked` — mock whiptail → `tui_help()` no
falla. `test_agent_tui_menu_help` — `agent.sh --tui` con opcion 5 →
salida contiene "proyecto0|nestjs|prisma|ayuda".

---

## 8. Opcion 6: Salir

Seleccionar "6" o cancelar el menu (`""`) ejecuta `exit 0`.

```sh
6)  exit 0 ;;
"") exit 0 ;;
```

**Test:** `test_agent_tui_flag` — mock retorna "6" (Salir) →
`agent.sh --tui` termina inmediatamente, salida contiene
"proyecto0|agente|recpl" (banner de inicio).

---

## 9. Bucle Principal TUI

```sh
if [ "$_mode" = "tui" ]; then
    . "$SCRIPT_DIR/tui.sh"
    tui_check || return 1
    while true; do
        _choice=$(tui_menu)
        case "$_choice" in
            1) _inst=$(tui_input); [ -n "$_inst" ] && main "$_inst" ;;
            2) tui_output "Modo interactivo no implementado via TUI aun" ;;
            3) tui_llm_config ;;
            4) tui_history ;;
            5) tui_help ;;
            6) exit 0 ;;
            "") exit 0 ;;
        esac
    done
fi
```

### Flujo completo:

```
inicio → whiptail disponible?
  │
  ├── NO → error → return 1
  │
  └── SI → bucle infinito:
         │
         ├── whiptail --menu (6 opciones)
         │
         ├── 1 → whiptail --inputbox → main(instruccion)
         │       ├── respond → tool_respond (texto)
         │       ├── help → show_help
         │       ├── read_file → tool_read_file
         │       ├── write_file → tool_write_file
         │       ├── run_command → tool_run_command
         │       ├── recpl → bridge_recpl (scaffolding NestJS/Prisma)
         │       ├── plan → planner multi-paso
         │       ├── llm → bridge_llm
         │       └── error → mensaje de error
         │
         ├── 2 → tui_output "no implementado"
         │
         ├── 3 → tui_llm_config (provider + mode)
         │
         ├── 4 → tui_history (muestra historial)
         │
         ├── 5 → tui_help (muestra ayuda)
         │
         ├── 6 → exit 0
         │
         └── "" → exit 0
```

---

## 10. Tabla de Tests TUI

| # | Test | Que verifica | Resultado |
|---|------|-------------|-----------|
| 1 | `test_tui_whiptail_available` | whiptail existe en PATH | ✅ |
| 2 | `test_tui_check_ok` | `tui_check()` retorna 0 con whiptail | ✅ |
| 3 | `test_tui_check_fail` | `tui_check()` retorna != 0 sin whiptail | ✅ |
| 4 | `test_tui_menu_mocked` | `tui_menu()` retorna "1" | ✅ |
| 5 | `test_tui_input_mocked` | `tui_input()` retorna "test_input" | ✅ |
| 6 | `test_tui_output_mocked` | `tui_output()` termina con codigo 0 | ✅ |
| 7 | `test_tui_help_mocked` | `tui_help()` termina con codigo 0 | ✅ |
| 8 | `test_tui_llm_config_exports` | exporta PROVIDER y MODE | ✅ |
| 9 | `test_tui_history_empty` | historial vacio → exit 0 | ✅ |
| 10 | `test_tui_history_with_data` | historial con datos → exit 0 | ✅ |
| 11 | `test_tui_llm_config_invalid_provider` | acepta cualquier valor sin validacion | ✅ |
| 12 | `test_agent_tui_flag` | `--tui` flag reconocido | ⚠️ |
| 13 | `test_agent_tui_menu_history` | opcion 4: historial desde `--tui` | ⚠️ |
| 14 | `test_agent_tui_menu_help` | opcion 5: ayuda desde `--tui` | ⚠️ |

**Leyenda:** ✅ = pasa, ⚠️ = warning (depende de terminal/disponibilidad de whiptail)

Tests 12-14 son ⚠️ porque usan `agent.sh --tui` que requiere terminal
real con whiptail. Los mocks simulan whiptail pero el comportamiento
exacto puede variar segun el entorno.

---

## 11. Mocks de whiptail para Tests

Los tests que no requieren whiptail real usan un mock que reemplaza
el binario `whiptail` en PATH. El mock escanea todos los argumentos con
un bucle `for` (no confia en `$1`) para detectar:

- `--menu` → escribe opcion a `>&3`
- `--inputbox` → escribe texto a `>&3`
- `--msgbox` → solo sale con 0

**Patron del mock:**

```sh
#!/bin/sh
for _arg in "$@"; do
    case "$_arg" in
        --menu) echo "1" >&3 ;;
        --inputbox) echo "test_input" >&3 ;;
        --msgbox) exit 0 ;;
    esac
done
exit 0
```

Para tests secuenciales (varias llamadas a whiptail en el mismo
proceso, como el bucle TUI), se usa un **archivo contador**:

```sh
_f="/tmp/tui_seq_$$"
if [ ! -f "$_f" ]; then echo "0" > "$_f"; fi
read _c < "$_f"
for _arg in "$@"; do
    case "$_arg" in
        --menu)
            _c=$((_c + 1)); echo "$_c" > "$_f"
            if [ "$_c" -eq 1 ]; then echo "OPCION" >&3; else echo "6" >&3; fi
            exit 0 ;;
    esac
done
exit 0
```

---

## 12. Comportamiento en Entorno Real

### 12.1 Modos de Operacion

| Modo | Flag | Comportamiento |
|------|------|---------------|
| Normal | (sin flag) | Clasifica intencion, ejecuta RECPL o LLM segun `AGENT_LLM_MODE` |
| LLM forzado | `--llm` | Fuerza uso de LLM para toda instruccion |
| Deterministico | `--deterministic` | Solo RECPL, sin LLM |
| TUI | `--tui` | Interfaz grafica con whiptail |
| Batch | stdin | `echo "instruccion" | ./agent.sh` |
| Plan | `--plan` | Descompone instrucciones multi-paso |

### 12.2 Variables de Entorno

| Variable | Default | Valores | Proposito |
|----------|---------|---------|-----------|
| `AGENT_LLM_MODE` | `auto` | `auto`, `llm`, `deterministic` | Modo de clasificacion |
| `AGENT_LLM_PROVIDER` | `claude` | `claude`, `openai`, `apifreellm` | Proveedor LLM |
| `AGENT_MEMORY_DIR` | `/tmp/agent_memory` | cualquier ruta | Directorio de memoria persistente |
| `AGENT_LOG_FILE` | `/tmp/agent.log` | cualquier ruta | Archivo de log |
| `AGENT_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARN`, `ERROR` | Nivel de log |
| `AGENT_VERSION` | `1.0.0` | version semantica | Version del agente |

### 12.3 Ejemplos de Uso Real

```bash
# Modo TUI interactivo
./agent.sh --tui

# Instruccion directa
./agent.sh "crea modulo payments en nestjs"

# Forzar LLM
./agent.sh --llm "explicame que hace este proyecto"

# Modo deterministico (solo RECPL)
./agent.sh --deterministic "crea entidad usuario en prisma"

# Batch desde stdin
echo "hola" | ./agent.sh

# Plan multi-paso
./agent.sh --plan "crea modulo auth y modulo payments en nestjs"
```

### 12.4 Limitaciones Conocidas

1. **`apifreellm` no implementado** — Aunque aparece en el menu TUI y
   en la documentacion, no existe el archivo `providers/apifreellm.sh`.
   Seleccionar este proveedor produce error silencioso.

2. **Modo interactivo no implementado** — Opcion 2 del menu TUI muestra
   mensaje "no implementado".

3. **Sin validacion de proveedor** — `tui_llm_config()` acepta cualquier
   texto, incluso valores no soportados.

4. **Dependencia de `jq`** — Todo el parsing JSON depende de `jq`.
   Asegurar que sea el binario oficial de jqlang/jq, no el wrapper npm
   incompleto.

5. **Memoria en `/tmp/`** — Por defecto, la memoria del agente se
   almacena en `/tmp/agent_memory`, que se pierde al reiniciar.

---

## Referencias

- `tests/test_agent.sh` — 14 tests TUI, 34 tests total, FAIL=0
- `agent-robot/tui.sh` — Implementacion de la capa TUI (7 funciones, 102 lineas)
- `agent-robot/agent.sh` — Bucle principal, clasificador de intencion, ejecutor
- `agent-robot/memory.sh` — Memoria persistente del agente
- `agent-robot/bridge.sh` — Bridge hacia el pipeline RECPL
- `docs/058_REP_DEV_COMPILER_BOT_TUI_1_0_DRAFT.md` — Reporte de implementacion TUI
- `docs/059_GUIDE_DEV_COMPILER_BOT_ARCHITECTURE_1_0_DRAFT.md` — Guia de arquitectura
