---
id: 026
area: dev
type: guide
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - recpl
  - loop
  - repl
  - pipeline
  - orchestrator
  - batch
  - interactive
  - state-machine
summary: "Descripcion del bucle principal RECPL (recpl.sh) que envuelve e itera sobre el pipeline compilador. Cubre los dos modos de operacion (interactivo y batch), el ciclo de vida del estado, el manejo de errores por etapa, y la integracion con la maquina de estados del proyecto."
keywords:
  - loop
  - recpl
  - repl
  - batch
  - interactive
  - pipeline
  - orchestrator
  - state
  - error-handling
  - recpl.sh
  - read-eval-print
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Descripcion del bucle principal RECPL
---

# El Bucle RECPL — Wrapper del Pipeline Compilador

> **Archivo:** `compiler-bot/recpl.sh`
>
> El bucle RECPL es la capa externa que envuelve el pipeline compilador.
> No es una etapa mas del compilador, sino el **orquestador** que decide
> cuando y como ejecutar cada etapa, como manejar errores, y como
> mantener el estado entre iteraciones.

---

## 0. Que es el Bucle RECPL

El bucle RECPL implementa el patron **REPL** (Read-Eval-Print Loop)
adaptado a un compilador de lenguaje natural a codigo IR:

```
RECPL = READ (lexer) → EVAL (parser + semantic) → PRINT (synthesis)
         ↑                                              │
         └────────────────── LOOP ───────────────────────┘
```

Pero a nivel arquitectonico, el bucle es mas que eso. Es el
**wrapper** que:

1. Inicializa el estado del compilador
2. Obtiene input (de terminal o tuberia)
3. Decide si el input es un comando de control o una instruccion
4. Si es instruccion: la envia al pipeline completo
5. Captura errores de cada etapa del pipeline
6. Devuelve el resultado al usuario
7. Repite hasta recibir senal de salida
8. Limpia el estado al terminar

```
┌──────────────────────────────────────────────────────────┐
│                     BUCLE RECPL                          │
│                                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐             │
│  │  INIT    │──>│  INPUT   │──>│ DISPATCH │             │
│  │  state   │   │  read    │   │  router  │             │
│  └──────────┘   └──────────┘   └────┬─────┘             │
│                                      │                   │
│              ┌───────────────────────┼─────────┐         │
│              │  COMANDO              │ INSTRUCCION       │
│              │  quit/help/version    │                    │
│              └─────────┬─────────────┼─────────┘         │
│                        │             ▼                   │
│                        │    ┌────────────────┐          │
│                        │    │  PIPELINE      │          │
│                        │    │  preprocess    │          │
│                        │    │  → lexer      │          │
│                        │    │  → parser     │          │
│                        │    │  → semantic   │          │
│                        │    │  → ir_gen     │          │
│                        │    │  → synthesis  │          │
│                        │    └───────┬────────┘          │
│                        │           │                    │
│                        ▼           ▼                    │
│                  ┌──────────────────────┐               │
│                  │      OUTPUT          │               │
│                  │  (JSON response)     │               │
│                  └──────────┬───────────┘               │
│                             │                           │
│                             ▼                           │
│                      ┌──────────┐                       │
│                      │  CLEANUP │  (al salir)           │
│                      └──────────┘                       │
└──────────────────────────────────────────────────────────┘
```

---

## 1. Ciclo de Vida del Bucle

Cada ejecucion del bucle atraviesa tres fases: inicio, operacion,
y termino.

### 1.1 Fase de Inicio (init_state)

```sh
init_state() {
    mkdir -p "$RECPL_STATE_DIR"
}
```

Antes de procesar cualquier instruccion, el bucle crea un directorio
de estado unico (identificado por PID: `/tmp/recpl_state_$$`).

Este directorio contendra:

| Archivo | Proposito |
|---------|-----------|
| `symbols.tmp` | Tabla de simbolos persistente |
| `scope.tmp` | Pila de scopes |

La inicialización ocurre **una sola vez** al arrancar el bucle,
no por instruccion. Esto permite que instrucciones posteriores
vean el estado creado por instrucciones anteriores.

### 1.2 Fase de Operacion (el bucle en si)

El bucle decide el modo de operacion basado en como se invoco:

```
if [ -t 0 ]; then
    interactive_mode
else
    batch_mode
fi
```

`[ -t 0 ]` pregunta: "el file descriptor 0 (stdin) es una terminal?"
Si es terminal → modo interactivo. Si es pipe/redireccion → modo batch.

### 1.3 Fase de Termino (cleanup)

```sh
cleanup() {
    rm -rf "$RECPL_STATE_DIR"
}
```

Cuando el bucle termina (por `quit`, EOF, o senal), elimina el
directorio de estado. Esto asegura que no queden archivos temporales
en el sistema.

La limpieza tambien esta registrada como trap para senales:

```sh
trap 'cleanup; exit 0' INT TERM
```

Esto cubre Ctrl+C (SIGINT) y terminacion normal (SIGTERM).

---

## 2. Modo Interactivo

### 2.1 Comportamiento

El modo interactivo presenta un prompt `> ` y espera entrada del
usuario. Cada linea se procesa como una instruccion independiente.

```
$ ./recpl.sh
RECPL Compiler Bot v1.0.0
Escribe 'quit' para salir.

> crea un modulo de pagos en NestJS
{"tipo_respuesta":"action","mensaje":"Generando modulo Pagos en NestJS...","payload":{...}}

> mostrar usuarios
{"tipo_respuesta":"error","mensaje":"Error semantico al procesar: mostrar usuarios","payload":null}
                                                              ↑
                         (usuarios no existe en la tabla de simbolos)

> crea un modulo de usuarios en Prisma
{"tipo_respuesta":"action","mensaje":"Generando modulo Usuarios en Prisma...","payload":{...}}

> quit
$
```

### 2.2 Diagrama de flujo

```
interactive_mode()
    │
    ├─ mostrar banner
    │
    └─ while true
         │
         ├─ printf "> "          (prompt)
         │
         ├─ read -r input        (esperar entrada)
         │    │
         │    ├─ EOF? → break    (Ctrl+D)
         │    │
         │    └─ OK → dispatcher
         │
         └─ dispatcher(input)
              │
              ├─ "quit"/"salir"/"exit"/"q"
              │    → break (salir del bucle)
              │
              ├─ "help"
              │    → show_help (mostrar ayuda)
              │    → continue (volver al prompt)
              │
              ├─ "version"/"--version"
              │    → show_version
              │    → continue
              │
              ├─ "" (linea vacia)
              │    → continue (silencioso)
              │
              └─ cualquier otra cosa
                   → process_instruction(input)
                   → echo (linea en blanco despues del output)
                   → continue
```

### 2.3 Comandos especiales

| Comando | Accion |
|---------|--------|
| `quit`, `salir`, `exit`, `q` | Termina el bucle y limpia el estado |
| `help` | Muestra la ayuda completa |
| `version`, `--version` | Muestra la version del bot |
| Ctrl+D | Envia EOF, termina el bucle |
| Ctrl+C | Envia SIGINT, termina el bucle (via trap) |

---

## 3. Modo Batch

### 3.1 Comportamiento

El modo batch lee instrucciones de stdin (una por linea) y las
procesa secuencialmente. No muestra prompt ni banner.

```sh
echo "crea un modulo de pagos en NestJS" | ./recpl.sh
```

### 3.2 Diagrama de flujo

```
batch_mode()
    │
    └─ while read -r line
         │
         ├─ linea vacia? → continue
         │
         ├─ "quit"/"salir"/"exit"/"q"
         │    → break
         │
         ├─ "help"
         │    → show_help
         │    → break (en batch, help termina)
         │
         └─ cualquier otra cosa
              → process_instruction(line)
              → continue
```

### 3.3 Diferencia clave con el modo interactivo

| Aspecto | Interactivo | Batch |
|---------|-------------|-------|
| Prompt | `> ` | No |
| Banner | Si | No |
| `help` | Muestra ayuda y continua | Muestra ayuda y termina |
| Linea vacia | Silencioso, continua | Silencioso, continua |
| Estado | Persiste entre instrucciones | Persiste entre instrucciones |
| Terminacion | `quit` o Ctrl+D | `quit` o EOF |

---

## 4. Procesamiento de Instrucciones

### 4.1 Pipeline completo

`process_instruction()` es la funcion que encadena todas las etapas
del compilador:

```sh
process_instruction(raw_input)
    │
    ├── 1. PREPROCESSOR
    │     preprocessor.sh "$raw_input"
    │     │ exito → continuar
    │     │ fallo → usar input original (fallo silencioso)
    │
    ├── 2. LEXER (READ)
    │     lexer.sh "$preprocessed"
    │     │ exito → continuar
    │     │ fallo → devolver JSON de error y retornar
    │
    ├── 3. PARSER (EVAL)
    │     echo "$tokens" | parser.sh
    │     │ exito → continuar
    │     │ fallo → devolver JSON de error y retornar
    │
    ├── 4. SEMANTIC (EVAL)
    │     echo "$ast" | RECPL_STATE_DIR=... semantic.sh
    │     │ exito → continuar
    │     │ fallo → devolver JSON de error y retornar
    │
    ├── 5. IR GENERATOR
    │     echo "$validated" | ir_generator.sh
    │     │ exito → continuar
    │     │ fallo → devolver JSON de error y retornar
    │
    └── 6. SYNTHESIS (PRINT)
          echo "$ir" | synthesis.sh
          │ siempre produce JSON de respuesta
```

### 4.2 Manejo de errores por etapa

Cada etapa del pipeline se protege individualmente con un `if`
que verifica el codigo de salida (`$?`) y que la salida no este
vacia:

```sh
output=$(etapa input 2>/dev/null)
if [ $? -ne 0 ] || [ -z "$output" ]; then
    echo '{"tipo_respuesta":"error","mensaje":"Error en etapa: ...","payload":null}'
    return
fi
```

Cuando una etapa falla:

1. Se descarta la salida de esa etapa
2. Se produce un JSON de error con el mensaje descriptivo
3. La funcion retorna (no sale del bucle)
4. El bucle continua con la siguiente instruccion

### 4.3 Flujo de datos entre etapas

Cada etapa recibe datos por stdin y produce datos por stdout.
El bucle conecta las etapas usando pipes y sustitucion de comandos:

```
Etapa 1 → stdout → variable → echo | Etapa 2 → stdout → variable → ...
```

Las variables intermedias (`preprocessed`, `tokens`, `ast`,
`validated`, `ir`) contienen el JSON producido por cada etapa.
Esto permite:

- Inspeccionar el estado en cualquier punto (para depuracion)
- Reintentar desde una etapa anterior si es necesario
- Loggear la entrada y salida de cada etapa

---

## 5. Estado Persistente Entre Iteraciones

### 5.1 Como funciona

El bucle crea un directorio de estado al iniciar (`init_state`) y
pasa su ruta a las etapas que necesitan persistencia (semantic.sh)
mediante la variable de entorno `RECPL_STATE_DIR`:

```sh
validated=$(echo "$ast" | RECPL_STATE_DIR="$RECPL_STATE_DIR" "$SCRIPT_DIR/frontend/semantic.sh" 2>/dev/null)
```

Esto significa que:

```
Iteracion 1: "crea modulo pagos en nestjs"
    → semantic.sh escribe "pagos" en la tabla de simbolos
    → la tabla queda en disco

Iteracion 2: "mostrar pagos"
    → semantic.sh lee "pagos" de la tabla de simbolos
    → existe → OK
```

### 5.2 Ciclo de vida del estado

```
recpl.sh start
    │
    ├─ init_state() → crea /tmp/recpl_state_12345/
    │
    ├─ Iteracion 1 → RECPL_STATE_DIR=/tmp/recpl_state_12345
    │                    semantic.sh escribe symbols.tmp
    │
    ├─ Iteracion 2 → RECPL_STATE_DIR=/tmp/recpl_state_12345
    │                    semantic.sh lee y escribe symbols.tmp
    │
    ├─ ... (mas iteraciones)
    │
    ├─ "quit" → cleanup() → rm -rf /tmp/recpl_state_12345/
    │
    └─ recpl.sh end
```

### 5.3 Transferencia entre etapas del pipeline

```
recpl.sh crea RECPL_STATE_DIR
    │
    └─ process_instruction()
         │
         └─ semantic.sh
              │ RECPL_STATE_DIR apunta al directorio del bucle
              │
              ├─ Crea archivo symbols.tmp (si no existe)
              ├─ Inserta o consulta simbolos
              └─ symbol table disponible para ir_generator.sh
```

---

## 6. Integracion con la Maquina de Estados (AGENTS.md)

El bucle RECPL implementa los estados de la maquina de estados
definida en AGENTS.md:

| Estado AGENTS.md | Implementacion en recpl.sh |
|-----------------|---------------------------|
| `analyze` | `process_instruction()` recibe el input |
| `execute` | Pipeline: preprocessor → lexer → parser → semantic → IR |
| `verify` | Cada etapa verifica su salida y codigo de error |
| `error` | Fallo en cualquier etapa → JSON de error |

El ciclo completo por instruccion es:

```
analyze → execute → verify → (exito → PRINT) | (error → JSON error)
```

Y el bucle itera este ciclo mientras haya input:

```
while (hay input):
    analyze(input)
    execute(pipeline)
    verify(salida)
    PRINT(resultado)
```

---

## 7. El Bucle como Wrapper

### 7.1 Que "envuelve" el bucle

El bucle no es una etapa del compilador. Es un **wrapper** que:

1. **Aisla** al usuario de la complejidad del pipeline
2. **Coordina** la ejecucion secuencial de las etapas
3. **Protege** contra fallos en cualquier etapa
4. **Persiste** el estado entre invocaciones
5. **Adapta** su comportamiento al contexto (terminal o tuberia)

### 7.2 Capas de abstraccion

```
┌──────────────────────────────────────────────────────┐
│                    USUARIO                           │
│  "crea un modulo de pagos en NestJS"                 │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              CAPA 1: BUCLE RECPL                      │
│              (recpl.sh)                               │
│                                                       │
│  - Interpreta comandos (quit, help)                   │
│  - Decide modo (interactivo/batch)                    │
│  - Inicializa/limpia estado                          │
│  - Captura errores del pipeline                      │
└────────────────────────┬─────────────────────────────┘
                         │
┌────────────────────────▼─────────────────────────────┐
│              CAPA 2: PIPELINE COMPILADOR              │
│                                                       │
│  preprocess → lexer → parser → semantic → IR → synth │
└──────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────┐
│                    SALIDA                             │
│  JSON con tipo_respuesta + payload                   │
│  + archivos generados en modules/                    │
└──────────────────────────────────────────────────────┘
```

### 7.3 El bucle como funcion pura

Conceptualmente, el bucle RECPL se comporta como una funcion
de orden superior que recibe un pipeline y lo ejecuta en un
entorno controlado:

```
recpl(pipeline, input_stream, options)
    → (output_stream, exit_code)
```

Donde:

| Parametro | Descripcion |
|-----------|-------------|
| `pipeline` | Secuencia de stages (preprocess → lexer → ...) |
| `input_stream` | stdin (terminal o pipe) |
| `options` | Modo, flags, directorio de estado |
| `output_stream` | Respuestas JSON a stdout |
| `exit_code` | 0 si termino normalmente, 1 si hubo error |

Esta abstraccion permite que el mismo bucle pueda ejecutar
diferentes pipelines en el futuro, simplemente cambiando la
cadena de stages.

---

## 8. Logging

El bucle escribe un log de todas sus operaciones:

| Archivo | Contenido |
|---------|-----------|
| `/tmp/recpl_loop.log` | Eventos del bucle (inicio, instrucciones, errores, fin) |

Formato del log:

```
[2026-06-11 10:00:00] OK: estado inicializado en /tmp/recpl_state_12345
[2026-06-11 10:00:05] OK: procesando instruccion: crea un modulo de pagos en NestJS
[2026-06-11 10:00:05] OK: preprocess completado
[2026-06-11 10:00:05] OK: lexer produjo 5 tokens
[2026-06-11 10:00:05] OK: parser produjo AST
[2026-06-11 10:00:05] OK: semantico: insertado simbolo pagos
[2026-06-11 10:00:05] OK: IR generado
[2026-06-11 10:00:05] OK: synthesis completada
[2026-06-11 10:00:10] OK: comando quit recibido
[2026-06-11 10:00:10] OK: estado limpiado
```

El logging esta implementado con una funcion simple que escribe
con timestamp a un archivo configurable via `LOG_FILE`:

```sh
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}
```

---

## 9. Ejemplos de Ejecucion

### 9.1 Sesion interactiva completa

```
$ ./compiler-bot/recpl.sh
RECPL Compiler Bot v1.0.0
Escribe 'quit' para salir.

> crea un modulo de pagos en NestJS
{"tipo_respuesta":"action","mensaje":"Generando modulo Pagos en NestJS...","payload":{...}}

> listar usuarios
{"tipo_respuesta":"error","mensaje":"Error semantico al procesar: listar usuarios","payload":null}
                    ↑ El LOOP captura el error y CONTINUA

> crea un modulo de usuarios en Prisma
{"tipo_respuesta":"action","mensaje":"Generando modulo Usuarios en Prisma...","payload":{...}}

> mostrar usuarios
{"tipo_respuesta":"info","mensaje":"Mostrando entity usuarios...","payload":{...}}

> help
RECPL Compiler Bot v1.0.0
...

> quit
$
```

### 9.2 Sesion batch

```sh
$ echo -e "crea modulo pagos en nestjs\nmostrar pagos\nquit" | ./compiler-bot/recpl.sh
{"tipo_respuesta":"action","mensaje":"Generando modulo Pagos en NestJS...","payload":{...}}
{"tipo_respuesta":"info","mensaje":"Mostrando entity pagos...","payload":{...}}
$ 
```

### 9.3 Recuperacion de errores

```sh
$ echo -e "crea modulo pagos en nestjs\nlistar nonexistent\ncrea modulo users\nquit" | ./compiler-bot/recpl.sh
{"tipo_respuesta":"action","mensaje":"Generando modulo Pagos en NestJS...","payload":{...}}
{"tipo_respuesta":"error","mensaje":"Error semantico al procesar: listar nonexistent","payload":null}
{"tipo_respuesta":"action","mensaje":"Generando modulo Users...","payload":{...}}
```

Notese que la instruccion erronea (`listar nonexistent`) no rompe
el bucle. La tercera instruccion (`crea modulo users`) se procesa
normalmente.

---

## 10. Seguridad y Robustez

### 10.1 Sin `set -e`

El bucle sigue la convencion del proyecto de NO usar `set -e`.
Cada comando potencialmente fallible se protege con `if`.

### 10.2 Stderr silenciado

Todas las llamadas a las etapas del pipeline redirigen stderr
a `/dev/null`:

```sh
output=$(etapa input 2>/dev/null)
```

Esto evita que mensajes de error internos de las etapas se filtren
al output visible del usuario. El bucle produce mensajes de error
propios en formato JSON.

### 10.3 Directorio de estado unico por proceso

Usar `$$` (PID del proceso) en el nombre del directorio de estado
previene colisiones cuando multiples instancias del bucle se
ejecutan simultaneamente:

```sh
RECPL_STATE_DIR="/tmp/recpl_state_$$"
```

### 10.4 Captura de senales

El bucle captura SIGINT y SIGTERM para asegurar limpieza incluso
en terminacion forzada:

```sh
trap 'cleanup; exit 0' INT TERM
```

---

## 11. Limitaciones del Bucle Actual

| Limitacion | Descripcion | Mejora propuesta |
|-----------|-------------|------------------|
| Sin historial | No se puede navegar instrucciones anteriores con flechas | Integrar `rlwrap` o `readline` |
| Sin modo silencioso | No hay flag para suprimir el banner | Agregar `--quiet` |
| Sin timeout | Una instruccion puede colgar el bucle indefinidamente | Agregar `timeout` con `alarm` |
| Sin persistencia entre ejecuciones | El estado se pierde al salir | Permitir `RECPL_STATE_DIR` persistente (no en `/tmp/`) |
| Sin pipeline configurable | Las etapas estan fijas en codigo | Hacer el pipeline configurable por archivo |
| Sin validacion de entrada batch larga | stdin sin fin puede saturar el bucle | Agregar limite de iteraciones (`-n`) |
