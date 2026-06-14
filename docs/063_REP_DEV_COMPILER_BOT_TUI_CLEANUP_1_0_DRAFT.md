---
id: 063
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0.0
status: DRAFT
tags:
  - tui
  - maintenance
  - baja-prioridad
  - cleanup
summary: Implementacion de 5 tareas de prioridad Baja del plan TUI (documento 062)
keywords: [tui_check, tui_menu, tui_help, mktemp, memory_warning]
changelog:
  - 2026-06-13: Documento creado
---

# Reporte: Implementacion de Tareas Baja Prioridad — TUI Cleanup

## Resumen

Se implementaron 5 tareas de prioridad **Baja** identificadas en la
propuesta `062_PROP_DEV_COMPILER_BOT_TUI_IMPLEMENTACION_1_0_DRAFT.md`:

| # | Archivo | Cambio | Estado |
|---|---------|--------|--------|
| 1 | `tui.sh` | Mensaje multi-package-manager en `tui_check()` | COMPLETED |
| 2 | `tui.sh` | Titulo dinamico en `tui_menu()` con proveedor activo | COMPLETED |
| 9 | `tui.sh` | Texto de ayuda compartido via `show_help()` o archivo externo | COMPLETED |
| 13 | `test_agent.sh` | Refactorizar `_prepare_whiptail_mock_choice()` con `mktemp` | COMPLETED |
| 19 | `agent.sh` | Warning si `AGENT_MEMORY_DIR` es `/tmp/` | COMPLETED |

## Detalle de Cambios

### Tarea #1 — `tui_check()` multi-package-manager

**Archivo:** `compiler-bot/agent-robot/tui.sh:17-27`

**Motivacion:** El mensaje de error solo mencionaba `apt`, ignorando
usuarios de otros package managers.

**Cambio:** Detectar el OS via archivos de release y `uname`:

```
/etc/debian_version   → sudo apt install whiptail
/etc/redhat-release   → sudo yum install whiptail
/etc/arch-release     → sudo pacman -S whiptail
$(uname) = "Darwin"   → brew install whiptail
```

### Tarea #2 — `tui_menu()` con titulo dinamico

**Archivo:** `compiler-bot/agent-robot/tui.sh:29-43`

**Motivacion:** El titulo del menu no reflejaba que proveedor LLM
estaba activo, dificultando la depuracion.

**Cambio:**
- Nueva variable `TUI_MENU_TITLE` que incluye `AGENT_LLM_PROVIDER`
  (default: "claude")
- Opcion 3 del menu ahora muestra el proveedor activo:
  `Configurar LLM (claude)`

### Tarea #9 — Texto de ayuda compartido en `tui_help()`

**Archivo:** `compiler-bot/agent-robot/tui.sh:89-115`

**Motivacion:** `tui_help()` y `show_help()` tenian texto hardcodeado
inconsistente entre si. Cambiar uno requeria cambiar el otro.

**Cambio:** Refactorizar `tui_help()` para usar el mismo formato de
texto que `show_help()`, incluyendo:
- Version dinamica via `AGENT_VERSION`
- Secciones de USO DESDE CLI, MODOS, EJEMPLOS
- Uso de `--scrolltext` en lugar de `--msgbox` para mejor navegacion
- Ancho aumentado de 60 a 70 columnas

### Tarea #13 — Refactorizar `_prepare_whiptail_mock_choice()` con `mktemp`

**Archivo:** `compiler-bot/tests/test_agent.sh:369-385`

**Motivacion:** Los mocks usaban `/tmp/` con `mkdir -p` y nombres fijos
basados en `$$`, lo que podia causar conflictos entre tests paralelos.

**Cambio:**
- Reemplazar `mkdir -p /tmp/tui_mock2_$$` con `mktemp -d`
- Agregar archivo contador via `mktemp` para evitar colisiones
- Agregar manejo de `--msgbox` en el mock
- Agregar logica secuencial: primera llamada al menu retorna `_choice`,
  llamadas subsiguientes retornan "6" (Salir)

### Tarea #19 — Warning si `AGENT_MEMORY_DIR` apunta a `/tmp/`

**Archivo:** `compiler-bot/agent-robot/agent.sh:28-32`

**Motivacion:** La memoria por defecto esta en `/tmp/agent_memory` y se
pierde al reiniciar el sistema. Usuarios novatos podian no saberlo.

**Cambio:** Agregar verificacion despues de cargar `config.sh`:
```sh
if echo "$AGENT_MEMORY_DIR" | grep -q "^/tmp/"; then
    echo "⚠️  Memoria en /tmp/ (se pierde al reiniciar). Usa AGENT_MEMORY_DIR para cambiarlo." >&2
fi
```

## Verificacion

- Syntax check (`bash -n`) pasado en los 3 archivos modificados
- Test suite `test_agent.sh` ejecutado: FAIL=0 (ningun fallo)
- 3 warnings esperados (TUI sin terminal, bridge sin RECPL state)

## Acciones Recomendadas

- Verificar que el mensaje de warning en `agent.sh` no interfiera con
  pipes o scripts que consuman stdout
- Considerar migrar tambien `_prepare_whiptail_mock()` a `mktemp`
  (tarea no listada pero analogo a #13)
