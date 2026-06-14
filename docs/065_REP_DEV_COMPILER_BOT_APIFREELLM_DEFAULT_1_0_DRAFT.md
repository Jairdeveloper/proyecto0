---
id: 065
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0.0
status: DRAFT
tags:
  - config
  - provider
  - apifreellm
summary: Configuracion de apifreellm como proveedor LLM por defecto
keywords: [apifreellm, default_provider, AGENT_LLM_PROVIDER, config]
changelog:
  - 2026-06-13: Documento creado
---

# Reporte: Configuracion de apifreellm como Proveedor por Defecto

## Resumen

Se configuro `apifreellm` como el proveedor LLM por defecto del sistema,
reemplazando el valor vacio anterior y agregandolo a la lista de
proveedores validos en el menu TUI.

## Archivos Modificados

### `compiler-bot/agent-robot/config.sh:19-21`

- `AGENT_LLM_PROVIDER` ahora por defecto es `apifreellm` en lugar de
  vacio (`""`)
- Comentario actualizado para reflejar que `apifreellm` requiere la
  variable de entorno `API_FREE_KEY`

```sh
# Antes:
AGENT_LLM_PROVIDER="${AGENT_LLM_PROVIDER:-}"

# Despues:
AGENT_LLM_PROVIDER="${AGENT_LLM_PROVIDER:-apifreellm}"
```

### `compiler-bot/agent-robot/tui.sh`

- Agregado `apifreellm` a la lista de proveedores validos en
  `tui_llm_config()`: `_valid_providers="claude openai apifreellm"`
- Actualizados todos los fallbacks de `:-claude` a `:-apifreellm`:
  - `TUI_MENU_TITLE` (linea 30)
  - Opcion 3 del menu (linea 38)
  - Default del inputbox de proveedor (linea 80)
  - Mensaje de confirmacion (linea 106)

### `compiler-bot/agent-robot/agent.sh:20`

- Comentario de cabecera actualizado para indicar que `apifreellm` es
  el valor por defecto: `(default: apifreellm)`

## Uso

Una vez configurada la variable de entorno `API_FREE_KEY`, el sistema
usara automaticamente `apifreellm` como proveedor LLM sin necesidad de
configuracion adicional:

```sh
export API_FREE_KEY="tu-api-key"
./agent.sh "hola"
```

El proveedor puede cambiarse en cualquier momento:
- Via variable de entorno: `AGENT_LLM_PROVIDER=claude ./agent.sh ...`
- Via menu TUI (opcion 3): `./agent.sh --tui` → Configurar LLM

## Verificacion

- Syntax check (`bash -n`) pasado en los 3 archivos
- Test suite `test_agent.sh`: **FAIL=0** (sin regresiones)
- `apifreellm` es seleccionable desde el menu TUI
- `claude` y `openai` siguen siendo proveedores validos
