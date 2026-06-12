---
id: 039
area: dev
type: PROP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - prop
  - tui
  - whiptail
  - interactive
  - ui
  - shell
  - user-experience
summary: "Propuesta para agregar una capa TUI (Terminal UI) al RECPL Compiler Bot. Analiza si el proyecto esta maduro para este paso y propone dos enfoques: liviano (whiptail wrapper) vs. completo (terminal rendering externo). Recomienda el enfoque liviano como unica opcion viable en el estado actual."
keywords:
  - tui
  - whiptail
  - terminal-ui
  - interactive
  - propuesta
  - shell
  - experiencia-de-usuario
  - recpl
changelog:
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Propuesta de capa TUI para RECPL — analisis de madurez y enfoque recomendado
---
# Propuesta: Capa TUI (Terminal UI) para RECPL Compiler Bot

> **Archivo afectado:** `compiler-bot/recpl.sh` (+ nuevo `compiler-bot/tui.sh`)
> **Depende de:** Fases 1-3 del patron composite (completadas)
> **Herramienta base disponible en el sistema:** `whiptail` (0.52.24)

---

## 0. Verdict

> **Agregar una TUI ahora NO es prematuro, pero solo si se hace como
> wrapper liviano (whiptail). Un TUI completo con terminal rendering
> (Ratatui/BubbleTea) SI seria prematuro en el estado actual del
> proyecto.**

---

## 1. Analisis de madurez del proyecto

Para decidir si es asertado agregar una TUI en este punto, evaluemos
el estado actual contra los criterios que tipicamente definen a un
proyecto "listo para UI".

### 1.1 Lo que esta solido

| Aspecto | Estado | Por que importa para una TUI |
|---------|--------|------------------------------|
| Pipeline RECPL | 72 tests, probado extremo a extremo | La TUI no necesita inventar logica de negocio, solo delegar |
| Modos de operacion | 4 modos (interactivo, batch, -c, -f) | La TUI puede envolver cualquiera de ellos |
| Estado compartido | Funciona via RECPL_STATE_DIR | La TUI puede mantener sesiones largas |
| Manejo de errores | JSON estructurado en todas las respuestas | La TUI puede parsear y mostrar errores graficamente |
| Comandos internos | source, exec implementados y probados | La TUI puede ofrecerlos como opciones de menu |

### 1.2 Lo que esta fragil o ausente

| Aspecto | Estado | Riesgo si se agrega TUI ahora |
|---------|--------|-------------------------------|
| Tests del modo interactivo | **Cero.** Solo se testea batch mode | No sabemos si el loop interactivo tiene bugs que la TUI ocultaria |
| CI/CD | No existe | Sin automatizacion, la TUI sera otro componente que probar manualmente |
| Validacion post-scaffold | No existe | La TUI mostraria "modulo creado" pero no podria verificar que compila |
| Nucleo C experimental | Stubs, sin uso real | Si a futuro el pipeline migra a C, una TUI shell habra que reescribirla |
| Documentacion de UX | No existe | No hay principios de diseno definidos para la interaccion con el usuario |

### 1.3 Conclusión del análisis

El proyecto tiene un **nucleo solido (el pipeline)** y una **periferia
fragil (tests de interaccion, CI/CD, validacion)**. Una TUI liviana
que sea solo un wrapper del pipeline existente es de bajo riesgo.
Una TUI pesada que intente reemplazar el pipeline o agregar logica
propia seria prematura porque:

1. No tenemos tests del modo interactivo actual — no sabemos que comportamientos preservar
2. No tenemos CI/CD — cualquier TUI nueva se convertiria en otro componente que mantener sin red de seguridad
3. El nucleo C experimental sugiere que el pipeline podria migrar de shell a C, lo que invalidaria una TUI shell pesada

---

## 2. Dos enfoques

### 2.1 Enfoque A: Wrapper liviano con whiptail (RECOMENDADO)

```
recpl.sh (backend) ←── tui.sh (frontend whiptail)
                           ├── Menu principal
                           ├── Formulario de instruccion
                           ├── Selector de archivo (source)
                           ├── Historial de comandos
                           └── Visor de estado (tabla de simbolos)
```

**Mecanica:** `tui.sh` es un script independiente que llama a
`recpl.sh` internamente (via `-c` o via batch mode) y muestra los
resultados con ventanas `whiptail`.

**Herramienta base:** `whiptail` (ya instalado en el sistema).
Alternativa: agregar `dialog` como dependencia opcional si se quiere
mayor sofisticacion (menus con checklist, progress bars, etc.).

#### Ventajas

- **Bajo riesgo:** No toca una sola linea del pipeline existente
- **Desacoplado:** `tui.sh` depende de `recpl.sh`, pero no al reves
- **Rapido de implementar:** ~2 horas para un MVP funcional
- **Probable con las herramientas existentes:** whiptail ya esta en el sistema
- **Reutiliza el parser JSON:** `jq` ya se usa en recpl.sh

#### Desventajas

- Limitado a lo que whiptail ofrece: dialogos de texto, menus, yes/no
- Sin colores, sin sintaxis resaltada, sin autocompletado predictivo
- La experiencia no se acerca a una TUI moderna (Ratatui, BubbleTea, etc.)

### 2.2 Enfoque B: TUI completa con terminal rendering (NO RECOMENDADO ahora)

Consiste en escribir un programa independiente (Go, Rust, Python) que
consuma el pipeline RECPL como libreria o subproceso y pinte una
interfaz rica en la terminal: paneles, colores 24-bit, autocompletado,
historial navegable, etc.

#### Por que NO ahora

| Razón | Detalle |
|-------|---------|
| Duplicacion de logica | El programa tendria que reimplementar o embeber el pipeline (hoy en shell) |
| Sin tests de interaccion | No hay forma de validar que la TUI se comporte igual que el CLI actual |
| El C core es una incognita | Si el pipeline migra a C, la TUI en otro lenguaje tendria que cambiar de interfaz |
| Esfuerzo estimado | ~2-4 semanas para un MVP decente vs. ~2 horas del wrapper whiptail |
| Dependencias nuevas | Habria que agregar Go/Rust/Python al stack del proyecto |

#### Cuando tendria sentido

1. Cuando el pipeline este disponible como libreria (C core funcional o API HTTP)
2. Cuando existan tests de integracion para el modo interactivo
3. Cuando haya CI/CD para validar la TUI en cada cambio
4. Cuando el equipo/proyecto justifique una experiencia de usuario premium

---

## 3. Propuesta de implementacion: Enfoque A (whiptail)

### 3.1 Arquitectura

```
tui.sh (menu loop)
  │
  ├── [1] Ejecutar instruccion  →  recpl.sh -c "<input>"  →  muestra JSON con whiptail --msgbox
  ├── [2] Source archivo        →  recpl.sh -f "<archivo>" →  muestra resultado
  ├── [3] Ver estado            →  cat $RECPL_STATE_DIR/*  →  whiptail --textbox
  ├── [4] Historial             →  cat /tmp/recpl_history  →  whiptail --textbox
  ├── [5] Configuracion         →  selector LLM/provider   →  export vars
  └── [6] Salir
```

### 3.2 Funciones propuestas

```sh
# tui.sh (nuevo archivo)

tui_menu() {
    whiptail --title "RECPL Compiler Bot" \
             --menu "Selecciona una opcion" 20 60 6 \
             "1" "Ejecutar instruccion" \
             "2" "Source archivo" \
             "3" "Ver tabla de simbolos" \
             "4" "Historial" \
             "5" "Configuracion" \
             "6" "Salir" \
             3>&1 1>&2 2>&3
}

tui_exec() {
    input=$(whiptail --inputbox "Instruccion:" 8 60 3>&1 1>&2 2>&3)
    [ -z "$input" ] && return
    result=$(recpl.sh -c "$input" 2>/dev/null)
    mensaje=$(echo "$result" | jq -r '.mensaje // "Sin respuesta"')
    whiptail --msgbox "$mensaje" 10 60
}

tui_source() {
    filepath=$(whiptail --inputbox "Ruta del archivo:" 8 60 3>&1 1>&2 2>&3)
    [ -z "$filepath" ] && return
    if [ ! -f "$filepath" ]; then
        whiptail --msgbox "Error: archivo no encontrado" 8 40
        return
    fi
    recpl.sh -f "$filepath" 2>/dev/null
    whiptail --msgbox "Archivo procesado. Revisa la salida arriba." 8 40
}
```

### 3.3 Integracion con recpl.sh

`tui.sh` se invoca con una nueva bandera:

```sh
./recpl.sh --tui     # → ejecuta tui.sh en lugar del modo interactivo
```

O como script independiente:

```sh
./tui.sh             # → llama a recpl.sh internamente
```

La integracion via `--tui` implica agregar un flag en `main()`:

```sh
--tui)
    exec "$SCRIPT_DIR/tui.sh"
    ;;
```

### 3.4 Dependencias

| Dependencia | Uso | Estado |
|-------------|-----|--------|
| `whiptail` | Dialogos TUI (menu, inputbox, msgbox, textbox) | Ya instalado |
| `jq` | Parseo de JSON respuesta | Ya se usa en recpl.sh |
| `recpl.sh` | Backend de procesamiento | Existente |

### 3.5 Plan de implementacion

| Fase | Descripcion | Estimacion |
|------|-------------|------------|
| 1 | Crear `tui.sh` con menu principal y opcion "Ejecutar instruccion" | 30 min |
| 2 | Agregar opciones: Source archivo, Ver estado, Historial | 30 min |
| 3 | Agregar flag `--tui` a recpl.sh y configuracion LLM/proveedor | 20 min |
| 4 | Pruebas manuales y documentacion | 40 min |
| **Total** | | **~2 horas** |

---

## 4. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| whiptail no disponible en algun entorno | La TUI no arranca | Mostrar error claro y sugerir usar modo interactivo |
| JSON de respuesta muy largo para msgbox | Texto truncado | Usar `--textbox` con scroll en vez de `--msgbox` |
| El usuario acostumbrado a TUI modernas se frustre | Expectativas no cumplidas | Documentar que es un wrapper liviano, no una terminal UI completa |
| Mantener dos interfaces (CLI + TUI) | Duplicacion de esfuerzo | tui.sh es delgado (~100 lineas), el CLI sigue siendo el interfaz principal |

---

## 5. Conclusion

| Pregunta | Respuesta |
|----------|-----------|
| ¿Es asertado agregar una TUI ahora? | **Si, pero solo la liviana (whiptail).** |
| ¿Por que no la completa? | El proyecto no tiene tests de interaccion, CI/CD, ni un core estable. Agregar una TUI pesada ahora seria construir sobre arena. |
| ¿Que ganamos con la liviana? | Mejor UX inmediato con bajo riesgo, cero deuda tecnica, y experiencia para disenar la TUI completa cuando el proyecto este listo. |
| ¿Cuando estaria lista la completa? | Cuando el pipeline exista como libreria (C core funcional), haya tests de interaccion, y CI/CD automatizado. |
