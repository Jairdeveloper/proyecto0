---
id: 028
area: dev
type: PROP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - prop
  - composite-pattern
  - interactive
  - batch
  - recpl
  - architecture
  - state-sharing
summary: "Propuesta de diseno para implementar un patron composite que permita al modo interactivo de RECPL invocar modos batch, comando y archivo de forma dinamica, compartiendo el mismo estado y retornando al loop principal. Traduce el comportamiento de herramientas como source (bash), \i (psql) y .read (sqlite3) al contexto del compilador RECPL."
keywords:
  - composite
  - patron
  - interactive
  - batch
  - source
  - exec
  - recpl
  - shell
  - state
  - pipeline
  - proposal
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Propuesta de patron composite para invocacion dinamica de modos desde el modo interactivo
---

# Patron Composite: Modo Batch Dinamico desde el Modo Interactivo

> **Propuesta:** Permitir que el modo interactivo de RECPL invoque los modos
> comando (`-c`) y archivo (`-f`) como comandos internos, compartiendo el
> estado de la sesion y retornando al prompt al terminar.

---

## 0. Resumen Ejecutivo

Actualmente RECPL tiene 4 modos de operacion independientes:

```
recpl.sh
  ├── interactivo  (sin args, stdin terminal)
  ├── batch        (sin args, stdin pipe)
  ├── comando      (-c "instruccion")
  └── archivo      (-f instrucciones.txt)
```

Cada modo es **excluyente**: una vez elegido, no se puede cambiar al otro
sin reiniciar el proceso. Esto es normal para herramientas simples, pero
limita el flujo de trabajo del usuario en el modo interactivo.

**Lo que falta:** Poder ejecutar instrucciones desde un archivo o desde
un string inline **dentro** de una sesion interactiva, compartiendo la
tabla de simbolos y el historial de estado.

Este documento propone un **patron composite** que convierte al modo
interactivo en un contenedor capaz de delegar a los otros modos como
subrutinas, manteniendo el estado compartido.

---

## 1. Comportamiento Deseado

### 1.1 Escenario de uso

```
$ ./compiler-bot/recpl.sh
RECPL Compiler Bot v1.1.0
Escribe 'quit' para salir.

> crea un modulo de pagos en NestJS
Generando modulo Pagos en NestJS...

> source seed.txt          ← NUEVO: ejecuta instrucciones desde un archivo
Generando modulo Usuarios en NestJS...
Generando modulo Productos en Prisma...
Generando entidad Carrito...

> exec listar usuarios     ← NUEVO: ejecuta una instruccion inline
Mostrando entity usuarios...

> mostrar pagos
Mostrando module pagos...  ← El estado de seed.txt persiste!

> source seed.txt          ← Error semantico: todo ya existe (duplicados)
Error: modulo Usuarios ya existe

> quit
```

### 1.2 Analogia con herramientas existentes

| Herramienta | Comando interno | Equivalente RECPL propuesto |
|-------------|----------------|-----------------------------|
| `bash` | `source script.sh` o `. script.sh` | `source instrucciones.txt` |
| `bash` | `eval "comando"` | `exec crear modulo pagos en NestJS` |
| `psql` | `\i archivo.sql` | `source archivo.txt` |
| `psql` | `\! comando` | `exec comando` |
| `sqlite3` | `.read archivo.sql` | `source archivo.txt` |
| `redis-cli` | `EVAL "script" 0` | `exec "instruccion"` |
| `gdb` | `source script.gdb` | `source archivo.txt` |
| `python` | `exec(open('file.py').read())` | `source archivo.txt` |

---

## 2. Patron Composite: Diseno Arquitectonico

### 2.1 Estructura actual (jerarquia plana)

```
recpl.sh
  ├── main()
  │   ├── command_mode()   ← independiente, init+process+cleanup propio
  │   ├── file_mode()      ← independiente, init+process+cleanup propio
  │   ├── interactive_mode() ← loop propio, estado compartido
  │   └── batch_mode()     ← loop propio, estado compartido
  └── process_instruction()  ← nucleo compartido
```

Cada modo gestiona su propio init/cleanup. No hay forma de que
interactive_mode() llame a file_mode() o command_mode() compartiendo
estado porque esas funciones hacen init+cleanup internamente.

### 2.2 Estructura propuesta (composite)

```
recpl.sh
  ├── main()
  │   ├── command_mode()     ← wrapper: init + composite_exec + cleanup
  │   ├── file_mode()        ← wrapper: init + composite_file + cleanup
  │   ├── composite_exec()   ← ejecuta una instruccion (comparte estado)
  │   ├── composite_file()   ← ejecuta archivo (comparte estado)
  │   ├── interactive_mode() ← COMPOSITE: loop + delegacion
  │   └── batch_mode()       ← loop simple (usa composite internamente)
  └── process_instruction()  ← nucleo compartido (sin cambios)
```

### 2.3 Diagrama composite

```
┌─────────────────────────────────────────────────────────────┐
│                    interactive_mode()                        │
│                        (COMPOSITE)                           │
│                                                              │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────────────┐  │
│  │ PROMPT   │   │ DISPATCHER   │   │ STATE               │  │
│  │ "> "     │──>│              │──>│ RECPL_STATE_DIR     │  │
│  └──────────┘   │              │   │ (persiste entre     │  │
│                 │  ┌─────────┐ │   │  llamadas)          │  │
│                 │  │ quit    │ │   └─────────────────────┘  │
│                 │  ├─────────┤ │                            │
│                 │  │ help    │ │   ┌─────────────────────┐  │
│                 │  ├─────────┤ │   │ process_instruction │  │
│                 │  │ source  │─┼──>│ (nucleo compartido) │  │
│                 │  ├─────────┤ │   └─────────────────────┘  │
│                 │  │ exec    │ │                            │
│                 │  ├─────────┤ │   ┌─────────────────────┐  │
│                 │  │ texto   │─┼──>│ composite_file()    │  │
│                 │  │ normal  │ │   │ (source "archivo")  │  │
│                 │  └─────────┘ │   └─────────────────────┘  │
│                 └──────────────┘                            │
│                                                              │
│  Cada iteracion puede invocar:                               │
│    • process_instruction()   → instruccion unica             │
│    • composite_file()        → archivo completo              │
│    • composite_exec()        → instruccion inline            │
│                                                              │
│  Las 3 comparten el mismo RECPL_STATE_DIR.                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 Relacion composite-estrategia

```
         ┌──────────────┐
         │  COMPOSITE   │  ← interactive_mode()
         │  (contiene)  │
         └──────┬───────┘
                │ delega a
        ┌───────┼───────────────┐
        │       │               │
        ▼       ▼               ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ STRATEGY │ │ STRATEGY │ │ STRATEGY │
│ simple   │ │ file     │ │ exec     │
│ instruc. │ │ source   │ │ inline   │
└──────────┘ └──────────┘ └──────────┘
    │            │            │
    └────────────┼────────────┘
                 ▼
        ┌────────────────┐
        │ process_       │
        │ instruction()  │  ← nucleo comun del pipeline
        └────────────────┘
```

---

## 3. Especificacion de Comportamiento

### 3.1 Comandos internos nuevos

Se agregan al dispatcher del modo interactivo:

| Comando | Formato | Funcion |
|---------|---------|---------|
| `source` | `source <ruta>` | Ejecuta cada linea del archivo como instruccion independiente |
| `exec` | `exec <instruccion>` | Ejecuta una instruccion inline (equivalente a `-c`) |
| (texto normal) | cualquier cosa | Se procesa como instruccion individual (igual que hoy) |

### 3.2 Reglas de composite_file (source)

```
composite_file(ruta)
    │
    ├─ Validar que ruta existe y es legible
    │  └─ fallo → mensaje de error, retornar al prompt
    │
    ├─ Abrir archivo
    │
    └─ Por cada linea:
         │
         ├─ linea vacia → saltar
         │
         ├─ "quit" → cerrar archivo, retornar al prompt
         │
         └─ cualquier otra → process_instruction(linea)
                              │ mismo RECPL_STATE_DIR
                              │ (NO hacer init/cleanup)
                              ▼
                         Estado compartido con la sesion interactiva
```

### 3.3 Reglas de composite_exec (exec)

```
composite_exec(instruccion)
    │
    └─ process_instruction(instruccion)
         │ mismo RECPL_STATE_DIR
         │ (NO hacer init/cleanup)
         ▼
    Estado compartido con la sesion interactiva
```

### 3.4 Reglas de estado compartido

| Aspecto | Modos independientes (-c, -f) | Modos composite (source, exec) |
|---------|------------------------------|-------------------------------|
| init_state() | Si, cada invocacion | No, ya existe desde interactive_mode() |
| cleanup() | Si, al terminar | No, lo gestiona interactive_mode() |
| RECPL_STATE_DIR | Propio (por llamada) | Compartido (el de la sesion) |
| Tabla de simbolos | Nueva cada vez | Acumulativa |
| Persistencia | Solo durante la llamada | Durante toda la sesion interactiva |

### 3.5 Manejo de errores en composite

```
source archivo_con_error.txt
    │
    ├─ Linea 1: "crea modulo A en NestJS" → OK (simbolo A creado)
    ├─ Linea 2: "crea modulo A en NestJS" → ERROR (duplicado)
    │   └─ Se muestra el error, pero NO se aborta el archivo
    ├─ Linea 3: "crea modulo B en NestJS" → OK
    └─ Linea 4: "quit" → fin del source, vuelve al prompt

Resultado: A y B existen en la tabla. El error de la linea 2 se reporto
           pero no interrumpio el procesamiento del archivo.
```

---

## 4. Implementacion Propuesta

### 4.1 Cambios en recpl.sh

```sh
# --- Funciones composite (comparten estado con el llamante) ---

composite_exec() {
    instruction="$1"
    process_instruction "$instruction"
}

composite_file() {
    filepath="$1"

    if [ ! -f "$filepath" ]; then
        echo "Error: archivo no encontrado: $filepath"
        return 1
    fi

    if [ ! -r "$filepath" ]; then
        echo "Error: archivo sin permisos de lectura: $filepath"
        return 1
    fi

    while IFS= read -r line <&3; do
        [ -z "$line" ] && continue
        case "$line" in
            quit|salir|exit|q) break ;;
            *) process_instruction "$line" ;;
        esac
    done 3< "$filepath"
}

# --- Modo interactivo modificado ---

interactive_mode() {
    echo "RECPL Compiler Bot v${VERSION}"
    echo "Escribe 'quit' para salir."
    echo "Comandos: source <archivo>, exec <instruccion>"
    echo

    while true; do
        printf "> "
        if ! read -r input; then
            echo
            break
        fi

        case "$input" in
            quit|salir|exit|q) break ;;
            help) show_help; continue ;;
            version|--version) show_version; continue ;;
            "") continue ;;

            # NUEVOS: comandos composite
            source\ *)
                filepath="${input#source }"
                [ -z "$filepath" ] && echo "Uso: source <archivo>" && continue
                composite_file "$filepath"
                continue
                ;;

            exec\ *)
                instruction="${input#exec }"
                [ -z "$instruction" ] && echo "Uso: exec <instruccion>" && continue
                composite_exec "$instruction"
                echo
                continue
                ;;
        esac

        process_instruction "$input"
        echo
    done

    cleanup
}

# --- Modo comando (-c): usar composite_exec si hay estado activo ---

command_mode() {
    instruction="$1"
    init_state
    process_instruction "$instruction"
    cleanup
}

# --- Modo archivo (-f): usar composite_file si hay estado activo ---

file_mode() {
    filepath="$1"
    init_state
    composite_file "$filepath"
    cleanup
}
```

### 4.2 No duplicacion de logica

`file_mode()` (independiente) y `composite_file()` (compartido) comparten
la misma logica de lectura de archivo. La diferencia es que:

- `file_mode()` hace init + composite_file + cleanup
- `composite_file()` solo lee y procesa (el init/cleanup lo hace el llamante)

Esto sigue el principio **DRY**: la logica de "leer archivo y procesar
lineas" esta en `composite_file()`, y ambos modos la usan.

### 4.3 Integracion con los modos existentes

```
main()
  │
  ├─ -c "instruccion" → command_mode("instruccion")
  │                      └─ init_state + composite_exec + cleanup
  │
  ├─ -f archivo       → file_mode("archivo")
  │                      └─ init_state + composite_file + cleanup
  │
  ├─ interactivo      → interactive_mode()
  │                      └─ init_state + LOOP:
  │                           ├─ process_instruction (directa)
  │                           ├─ composite_exec     (via comando exec)
  │                           └─ composite_file     (via comando source)
  │                      └─ cleanup
  │
  └─ batch            → batch_mode()
                         └─ init_state + LOOP:
                              └─ process_instruction (directa)
                         └─ cleanup
```

---

## 5. Analisis Comparativo

### 5.1 Antes vs Despues

| Capacidad | Antes | Despues |
|-----------|-------|---------|
| Ejecutar instruccion inline en interactivo | Solo texto normal | Tambien `exec "..."` |
| Ejecutar archivo desde interactivo | No existia | `source archivo.txt` |
| Estado compartido entre modos | No (cada modo es independiente) | Si (composite usa el estado de la sesion) |
| Reutilizacion de logica | file_mode() tiene su propio loop | file_mode() y composite_file() comparten logica |
| Claridad de la interfaz | 2 modos + 2 banderas | `source` y `exec` como comandos naturales |

### 5.2 Ventajas del patron composite

1. **Estado unificado:** El usuario no pierde la tabla de simbolos al
   cambiar de modo dentro de la sesion

2. **Composicion natural:** `source` ejecuta N instrucciones como si
   se hubieran escrito manualmente en el prompt

3. **Separacion de responsabilidades:** Cada funcion hace una cosa:
   - `composite_file()` solo lee y delega
   - `composite_exec()` solo delega
   - `process_instruction()` solo procesa

4. **Testeabilidad:** `composite_file()` y `composite_exec()` se pueden
   probar independientemente del modo interactivo

5. **Preparado para el futuro:** El mismo patron permite agregar:
   - `pipe "comando externo | recpl"` (procesar salida de otros comandos)
   - `include "config.recpl"` (archivos de configuracion)
   - `eval $(comando)` (evaluacion dinamica)

### 5.3 Desventajas y riesgos

| Riesgo | Mitigacion |
|--------|------------|
| `source` de archivos grandes puede saturar el prompt | No hay mitigacion (es el mismo comportamiento que bash) |
| `exec` puede confundirse con texto normal | El prefijo `exec ` es explicito |
| Archivos con errores pueden dejar estado inconsistente | El manejo de errores ya existe en process_instruction() |
| El usuario puede olvidar que `source` comparte estado | Documentar explicitamente |

---

## 6. Plan de Traduccion a Codigo

### Fase 1: Crear funciones composite (estimacion: 15 min)

1. Crear `composite_exec()`: 3 lineas (wrapper de process_instruction)
2. Crear `composite_file()`: extraer logica actual de `file_mode()` sin init/cleanup
3. Refactorizar `file_mode()` para que llame a `composite_file()`

### Fase 2: Modificar interactive_mode (estimacion: 15 min)

1. Agregar caso `source\ *)` al case del dispatcher
2. Agregar caso `exec\ *)` al case del dispatcher
3. Actualizar banner con los nuevos comandos disponibles

### Fase 3: Pruebas (estimacion: 10 min)

1. Test: `source` con archivo valido
2. Test: `source` con archivo inexistente
3. Test: `exec` con instruccion valida
4. Test: `exec` con instruccion invalida
5. Test: Estado compartido (CREATE en source, READ manual despues)

### Fase 4: Documentacion (estimacion: 10 min)

1. Actualizar `show_help()` con los nuevos comandos
2. Este documento

**Total estimado: ~50 minutos**

---

## 7. Ejemplos de Uso del Patron Composite

### 7.1 Script de inicializacion (seed)

```sh
# seed.txt
crea modulo usuarios en NestJS
crea modulo productos en NestJS
crea modulo pedidos en Prisma
```

```
$ ./recpl.sh
> source seed.txt
Generando modulo Usuarios en NestJS...
Generando modulo Productos en NestJS...
Generando modulo Pedidos en Prisma...

> mostrar usuarios
Mostrando module usuarios...

> exec crear modulo pagos en NestJS
Generando modulo Pagos en NestJS...
```

### 7.2 Scripts anidados

```
$ ./recpl.sh
> source config/init.recpl
Generando modulo Base en NestJS...

> source config/seed.recpl
Generando modulo Usuarios...
Generando modulo Productos...

> source config/seed.recpl
Error: modulo Usuarios ya existe  ← idempotencia?
Error: modulo Productos ya existe
```

### 7.3 Integracion con herramientas externas

Modo pipe (futuro, no implementado en esta propuesta):

```
> pipe ls modules/
pagos/
usuarios/

> pipe cat modules/pagos/pagos.controller.ts
import ...
```

---

## 8. Checklist de Implementacion

- [ ] `composite_exec()`: wrapper simple de `process_instruction()`
- [ ] `composite_file()`: loop de lectura de archivo SIN init/cleanup
- [ ] Refactor: `file_mode()` usa `composite_file()` internamente
- [ ] `interactive_mode()`: caso `source\ *)` en el dispatcher
- [ ] `interactive_mode()`: caso `exec\ *)` en el dispatcher
- [ ] Banner actualizado con nuevos comandos
- [ ] `show_help()` actualizado
- [ ] Validacion: archivo no encontrado en `source`
- [ ] Validacion: instruccion vacia en `exec`
- [ ] Test: estado compartido entre source y comandos manuales
- [ ] Test: errores dentro de source no rompen la sesion
- [ ] `bash -n recpl.sh` pasa
- [ ] `bash tests/run_tests.sh` pasa (47 tests)
- [ ] Este documento actualizado con resultados de implementacion
