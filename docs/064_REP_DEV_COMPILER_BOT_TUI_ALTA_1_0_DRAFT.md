---
id: 064
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0.0
status: DRAFT
tags:
  - tui
  - alta-prioridad
  - plan-flag
  - apifreellm
summary: Implementacion de 6 tareas de prioridad Alta del plan TUI (documento 062)
keywords: [tui_interactive, tui_llm_config, validation, plan_flag, apifreellm]
changelog:
  - 2026-06-13: Documento creado
---

# Reporte: Implementacion de Tareas Alta Prioridad — TUI Core

## Resumen

Se implementaron 6 tareas de prioridad **Alta** identificadas en la
propuesta `062_PROP_DEV_COMPILER_BOT_TUI_IMPLEMENTACION_1_0_DRAFT.md`:

| # | Archivo | Cambio | Estado |
|---|---------|--------|--------|
| 3 | `agent.sh` | Capturar stdout de `main()` en bucle TUI y mostrar via `tui_output()` | COMPLETED |
| 5 | `tui.sh` | Nueva funcion `tui_interactive()` | COMPLETED |
| 7 | `tui.sh` | Validacion de proveedor y modo en `tui_llm_config()` | COMPLETED |
| 10 | `agent.sh` | Capturar y mostrar resultado de `main()` en bucle TUI | COMPLETED |
| 14 | `agent.sh` | Implementar flag `--plan` | COMPLETED |
| 17 | `providers/apifreellm.sh` | Crear provider o remover del menu | COMPLETED |

## Detalle de Cambios

### Tarea #3 / #10 — Capturar resultado de `main()` en bucle TUI

**Archivo:** `compiler-bot/agent-robot/agent.sh:386-396`

**Motivacion:** Cuando el usuario ejecutaba una instruccion desde la
opcion 1 del menu TUI, la salida de `main()` se imprimia a stdout pero
no se mostraba en un msgbox. El usuario debia cambiar al terminal para
ver el resultado.

**Cambio:** El case 1 del bucle TUI ahora captura la salida de
`main()` via sustitucion de comando y la muestra linea por linea usando
`tui_output()`:

```sh
1)
    _inst=$(tui_input)
    if [ -n "$_inst" ]; then
        _result=$(main "$_inst" 2>&1)
        echo "$_result" | head -20 | while IFS= read -r _line; do
            [ -n "$_line" ] && tui_output "$_line"
        done
    fi
    ;;
```

### Tarea #5 — Nueva funcion `tui_interactive()`

**Archivo:** `compiler-bot/agent-robot/tui.sh:56-68`

**Motivacion:** La opcion 2 del menu TUI solo mostraba un placeholder.
No habia forma de ejecutar multiples instrucciones secuencialmente desde
el TUI sin volver al menu cada vez.

**Cambio:** Nueva funcion que implementa un bucle interactivo:
- Muestra un inputbox donde el usuario escribe instrucciones
- Cada instruccion se delega a `main()` para clasificar y ejecutar
- El usuario escribe "salir", "exit", "menu" o "volver" para regresar
  al menu principal

**Archivo relacionado:** `agent.sh` case 2 actualizado para llamar a
`tui_interactive()` en lugar del placeholder.

### Tarea #7 — Validacion de proveedor y modo en `tui_llm_config()`

**Archivo:** `compiler-bot/agent-robot/tui.sh:71-108`

**Motivacion:** `tui_llm_config()` aceptaba cualquier string como
proveedor o modo, incluso valores invalidos o no implementados como
"apifreellm". Esto causaba errores dificiles de diagnosticar.

**Cambio:**
- Lista blanca de proveedores validos: `claude`, `openai`
- Lista blanca de modos validos: `auto`, `llm`, `deterministic`
- Bucle `while` que rechaza valores invalidos con mensaje de error y
  vuelve a pedir el valor
- Si el usuario cancela (entrada vacia), retorna sin cambiar nada

### Tarea #14 — Flag `--plan` en `agent.sh`

**Archivo:** `compiler-bot/agent-robot/agent.sh`

**Motivacion:** No existia forma de ejecutar el planificador
directamente desde linea de comandos. El modo "plan" solo se activaba
via clasificacion de intencion.

**Cambio:**
- Nuevo flag `--plan` en el parser de argumentos
- Bloque de ejecucion directa del planificador que:
  1. Toma la instruccion de args o stdin
  2. Carga `planner_llm.sh` (fallback a `planner.sh`)
  3. Llama a `planificar()` y `ejecutar_plan()`
- Documentado en `show_help()`

### Tarea #17 — Provider `apifreellm.sh`

**Archivo:** `compiler-bot/agent-robot/providers/apifreellm.sh` (NUEVO)

**Motivacion:** El proveedor `apifreellm` estaba referenciado en el
menu TUI y documentacion pero no existia implementacion. No habia
directorio `providers/` ni patron de provider establecido.

**Cambio:**
- Creado directorio `providers/`
- Creado `providers/apifreellm.sh` con implementacion funcional via
  `curl` para llamadas API compatibles con OpenAI
- Funciones: `apifreellm_call(prompt)` y `apifreellm_available()`
- Dependencia: `curl`, `jq` y variable de entorno `API_FREE_KEY`
- `apifreellm` removido de la lista de proveedores validos en
  `tui_llm_config()` hasta que se configure apropiadamente

## Cambios Adicionales

### Tests actualizados

- **`test_tui_llm_config_exports`** — Actualizado para usar valores
  validos ("claude", "auto") en lugar de "test_input"
- **`test_tui_llm_config_invalid_provider`** — Refactorizado para
  verificar que el proveedor invalido es **rechazado** (antes esperaba
  que fuera aceptado). Usa mock con contador para simular cancelacion
  del usuario tras el error.
- **`test_files_exist`** — Agregado `providers/apifreellm.sh` a la lista
- **`test_bash_syntax`** — Agregado `providers/apifreellm.sh` a la lista

## Verificacion

- Syntax check (`bash -n`) pasado en los 4 archivos modificados
- Test suite `test_agent.sh`: **FAIL=0** (34 tests, sin regresiones)
- 4 warnings esperados (TUI sin terminal, bridge sin RECPL state)

## Riesgos

- El modo interactivo (`tui_interactive`) llama a `main()` que a su vez
  imprime banner y logs. En modo TUI esto puede generar salida
  redundante en el msgbox.
- El flag `--plan` usa `planificar()` y `ejecutar_plan()` de planner.sh,
  que esperan un formato JSON especifico. Cambios en planner.sh podrian
  afectar este flujo.
- `apifreellm.sh` es funcional pero requiere configurar `API_FREE_KEY`.
  La URL base por defecto (`api.apifreellm.example.com`) es un lugar
  comun y debe actualizarse a la URL real del servicio.
