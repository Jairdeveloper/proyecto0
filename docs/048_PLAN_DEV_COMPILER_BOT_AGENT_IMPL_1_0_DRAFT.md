---
id: 048
area: dev
type: PLAN
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - plan
  - implementation
  - agent-robot
  - architecture
  - bridge
  - recpl
  - terminal
summary: "Plan de implementacion detallado para la capa agent-robot sobre RECPL. Define la arquitectura de la nueva capa, el bridge de compatibilidad con el pipeline existente, las herramientas del agente, el plan de fases con tareas concretas, y las reglas de diseno (no tocar codigo existente, modo deterministico como capa inferior, solo terminal)."
keywords:
  - plan
  - implementacion
  - agente
  - agent-robot
  - bridge
  - recpl
  - terminal
  - arquitectura
  - fases
  - tareas
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Plan de implementacion de la capa agent-robot — arquitectura, bridge, herramientas, fases y tareas
---

# Plan de Implementacion: Capa Agent-Robot para Proyecto0(RECPL)

> **Documento de planificacion.** Describe como construir la capa `agent-robot`
> sobre el pipeline RECPL existente, siguiendo las decisiones de diseno
> aprobadas en la revision de `docs/047_PROP_DEV_COMPILER_BOT_AGENT_CONCEPT_1_0_DRAFT.md`.

---

## 0. Decisiones de Diseno Aprobadas

| # | Decision | Implicancia |
|---|----------|-------------|
| 1 | El pipeline RECPL existente se mantiene como patron interno de lectura de input. El agente traduce el input y delega en RECPL y/o `pipeline_debugger.sh` mediante un bucle interno. | No se toca `recpl.sh`, `frontend/`, `middleend/`, `backend/`. Se crea un bridge. |
| 2 | El proyecto se enfoca exclusivamente en **terminal** (CLI + TUI). Se abandona momentaneamente IDE, desktop, y web. | Sin API HTTP, sin extension VS Code, sin desktop app. Solo scripts shell. |
| 3 | La nueva capa se construye dentro de `compiler-bot/agent-robot/`. | Todo el codigo nuevo va ahi. El arbol existente no se modifica. |
| 4 | La implementacion sigue las secciones 1-4 y 6-10 de `047_PROP`. | Las secciones aceptadas guian el diseno. La seccion 5 (mapeo de codigo) se reinterpreta segun el punto 5 de abajo. |
| 5 | La nueva capa se llama `agent-robot`. **No se toca el codigo actual** — solo para crear compatibilidad (adapter/bridge). DRY es explicitamente sacrificable. El "modo deterministico" (RECPL) se maneja en una capa inferior a la del agente. | Bridge de una via: `agent-robot` → `recpl.sh`/`pipeline_debugger.sh`. Nunca al reves. |

---

## 1. Arquitectura de la Capa Agent-Robot

### 1.1 Vista General

```
INPUT (terminal)
     │
     ▼
┌──────────────────────────────────────────────────┐
│              AGENT-ROBOT LAYER                    │
│  (compiler-bot/agent-robot/)                      │
│                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────────┐  │
│  │ agent.sh │──▶│planner.sh│──▶│ tool_*.sh     │  │
│  │ (loop)   │   │(intent→  │   │ (capacidades) │  │
│  │          │   │ acciones)│   │              │  │
│  └────┬─────┘   └──────────┘   └──────┬───────┘  │
│       │                               │          │
│       └───────────┬───────────────────┘          │
│                   ▼                              │
│  ┌──────────────────────────────┐                │
│  │       bridge.sh              │                │
│  │  (adapter a RECPL)           │                │
│  └──────────┬───────────────────┘                │
└─────────────┼────────────────────────────────────┘
              │
              ▼
┌──────────────────────────────────────────────────┐
│              RECPL LAYER (EXISTENTE)              │
│  (modo deterministico — capa inferior)            │
│                                                   │
│  recpl.sh │ pipeline_debugger.sh                  │
│  frontend/ │ middleend/ │ backend/                │
│  providers/ │ tests/ │ templates/                 │
└──────────────────────────────────────────────────┘
```

### 1.2 Relacion entre capas

```
agent-robot layer     ← NUEVA: inteligencia, decision, herramientas
     │ llama via bridge.sh
     ▼
RECPL deterministic   ← EXISTENTE: pipeline compilador rapido y sin costo
```

- `agent-robot` **nunca** modifica archivos de RECPL.
- `agent-robot` se comunica con RECPL exclusivamente via `bridge.sh`.
- RECPL no sabe que existe `agent-robot`. Es transparente.
- El "modo deterministico" es RECPL. El agente decide CUANDO usarlo.

### 1.3 Arbol de directorios resultante

```
compiler-bot/
├── agent-robot/                        # NUEVO: capa agente
│   ├── agent.sh                        # Entrypoint + loop del agente
│   ├── bridge.sh                       # Adapter/bridge a RECPL
│   ├── config.sh                       # Configuracion del agente
│   ├── memory.sh                       # Memoria del agente (historial, estado)
│   ├── planner.sh                      # Planificador multi-paso
│   ├── tools/                          # Capacidades/herramientas del agente
│   │   ├── tool_registry.sh            # Registro de herramientas disponibles
│   │   ├── tool_recpl.sh               # Delega en RECPL via bridge
│   │   ├── tool_read_file.sh           # Lee archivos del sistema
│   │   ├── tool_write_file.sh          # Escribe/edita archivos
│   │   ├── tool_run_command.sh         # Ejecuta comandos del sistema
│   │   ├── tool_search_code.sh         # Busca en codigo fuente
│   │   └── tool_respond.sh             # Responde textualmente
│   └── prompts/                        # System prompts del agente
│       ├── system_agent.txt            # Prompt base del agente
│       ├── system_planner.txt          # Prompt del planificador
│       └── system_tools.txt            # Prompt de descripcion de herramientas
│
├── frontend/                           # EXISTENTE: sin cambios
├── middleend/                          # EXISTENTE: sin cambios
├── backend/                            # EXISTENTE: sin cambios
├── providers/                          # EXISTENTE: sin cambios
├── templates/                          # EXISTENTE: sin cambios
├── tests/                              # EXISTENTE: se agregaran tests de agent-robot
├── recpl.sh                            # EXISTENTE: se modifica SOLO para delegar
├── pipeline_debugger.sh                # EXISTENTE: sin cambios
│
└── agent-robot.sh                      # NUEVO: symlink o entrypoint global
                                        # (delega en agent-robot/agent.sh)
```

---

## 2. Componentes del Bridge

### 2.1 bridge.sh — Adapter entre Agent-Robot y RECPL

El bridge es el **unico punto de contacto** entre el agente y el pipeline RECPL
existente. Su proposito es aislar al agente de los detalles internos de RECPL.

```
agent-robot → bridge.sh → recpl.sh (o pipeline_debugger.sh)
                          → respuesta JSON estandarizada
```

**Contrato del bridge:**

```sh
# bridge.sh

# --- Ejecutar instruccion en RECPL y devolver respuesta estructurada ---
# Uso: bridge_recpl "instruccion"
# Output: JSON con { exito, tipo_respuesta, mensaje, payload, raw }
bridge_recpl() {
    instruction="$1"

    # 1. Llamar a recpl.sh en modo comando
    # 2. Capturar stdout y stderr por separado
    # 3. Normalizar la respuesta a JSON estandar
    # 4. Devolver { exito, tipo_respuesta, mensaje, payload, raw }
}

# --- Ejecutar instruccion con debugger y devolver trazabilidad ---
# Uso: bridge_debug "instruccion"
bridge_debug() {
    instruction="$1"

    # 1. Llamar a pipeline_debugger.sh --output
    # 2. Capturar la traza completa
    # 3. Devolver JSON con { etapas, tiempos, output_final }
}

# --- Consultar estado interno de RECPL ---
# Uso: bridge_state
# Output: JSON con tabla de simbolos, modulos generados, etc.
bridge_state() {
    # Lee RECPL_STATE_DIR y devuelve snapshot
}
```

**Principios del bridge:**
- Solo llama a RECPL via `recpl.sh -c` y `pipeline_debugger.sh --output`
- No conoce ni depende de `frontend/`, `middleend/`, `backend/` internamente
- Normaliza las respuestas de RECPL a un formato uniforme para el agente
- Si RECPL falla, el bridge devuelve un error estructurado (no se cuelga)

### 2.2 Formato de respuesta normalizado

Toda respuesta del bridge sigue este esquema:

```json
{
  "exito": true,
  "origen": "recpl",
  "tipo_respuesta": "action",
  "mensaje": "Generando module Payments en nestjs...",
  "payload": {
    "accion": "scaffold:module",
    "params": { "nombre": "Payments", "tech": "nestjs" },
    "archivos": ["modules/payments/"]
  },
  "raw": { ... },
  "tiempo_ms": 45
}
```

En caso de error:

```json
{
  "exito": false,
  "origen": "recpl",
  "tipo_respuesta": "error",
  "mensaje": "Error lexico: token no reconocido en col 1: 'xyzzy'",
  "payload": null,
  "raw": { ... },
  "tiempo_ms": 12
}
```

---

## 3. Componentes del Agente

### 3.1 agent.sh — Bucle principal del agente

```
agent.sh "instruccion"
   │
   ├── 1. Preprocesar instruccion (trim, normalizar)
   ├── 2. Clasificar intencion (LLM via provider chain)
   │      ├── Si es comando RECPL → bridge_recpl()
   │      ├── Si es tool call     → ejecutar herramienta
   │      ├── Si es multi-paso    → planner.sh
   │      └── Si es pregunta      → tool_respond()
   ├── 3. Ejecutar accion
   ├── 4. Formatear respuesta
   └── 5. Devolver resultado
```

**Modos de operacion (heredados de recpl.sh pero envueltos por el agente):**

| Modo | Comportamiento | Implementacion |
|------|---------------|----------------|
| `auto` | Intenta RECPL deterministico → si falla, usa LLM | `agent.sh` (default) |
| `llm` | Envia directamente al LLM, saltea RECPL | `agent.sh --llm` |
| `deterministic` | Solo RECPL via bridge, sin LLM | `agent.sh --deterministic` |

### 3.2 planner.sh — Planificador multi-paso

Para instrucciones complejas que requieren multiples acciones:

```
Instruccion: "crea un proyecto con modulo auth y modulo payments en nestjs"

Planner:
  1. bridge_recpl("crea modulo auth en nestjs")
  2. bridge_recpl("crea modulo payments en nestjs")
  3. tool_respond("Proyecto creado con 2 modulos")
```

**Funcionamiento:**
1. El planificador recibe la instruccion y el contexto actual
2. Usa el LLM para descomponerla en una secuencia de pasos
3. Cada paso se ejecuta secuencialmente (o en paralelo si es posible)
4. Los resultados se consolidan en una unica respuesta

### 3.3 memory.sh — Memoria del agente

Gestiona el estado del agente entre interacciones:

| Funcion | Proposito |
|---------|-----------|
| `memory_init()` | Inicializa el archivo de memoria |
| `memory_save(key, value)` | Guarda un valor en la memoria |
| `memory_get(key)` | Recupera un valor |
| `memory_history()` | Devuelve el historial de instrucciones |
| `memory_context()` | Devuelve el contexto actual (modulos, archivos) |

**Almacenamiento:** Archivo JSON en `$RECPL_STATE_DIR/agent_memory.json`.

### 3.4 config.sh — Configuracion del agente

Variables de entorno y configuracion:

```sh
# --- Variables de configuracion del agente ---
AGENT_LLM_MODE="${AGENT_LLM_MODE:-auto}"         # auto | llm | deterministic
AGENT_LLM_PROVIDER="${AGENT_LLM_PROVIDER:-}"      # provider preferido
AGENT_LLM_TIER="${AGENT_LLM_TIER:-auto}"          # free | paid | auto
AGENT_MEMORY_DIR="${AGENT_MEMORY_DIR:-/tmp/agent_memory}"
AGENT_LOG_FILE="${AGENT_LOG_FILE:-/tmp/agent.log}"
```

---

## 4. Herramientas del Agente (Tools)

### 4.1 tool_registry.sh — Registro central de herramientas

Cada herramienta se registra con metadatos:

```sh
# Formato: nombre:script:descripcion:parametros
TOOL_REGISTRY='recpl:tool_recpl.sh:Ejecuta instrucciones RECPL:{"instruction":"string"}
read_file:tool_read_file.sh:Lee el contenido de un archivo:{"path":"string"}
write_file:tool_write_file.sh:Escribe contenido en un archivo:{"path":"string","content":"string"}
run_command:tool_run_command.sh:Ejecuta un comando del sistema:{"command":"string"}
search_code:tool_search_code.sh:Busca texto en el codigo fuente:{"pattern":"string","path":"string"}
respond:tool_respond.sh:Responde directamente al usuario:{"message":"string"}'
```

### 4.2 tool_recpl.sh — Bridge a RECPL

```sh
# tool_recpl.sh - Delega en el pipeline RECPL via bridge
#
# Esta herramienta permite al agente usar RECPL como una capacidad mas.
# El agente decide cuando invocar RECPL segun la intencion detectada.

tool_recpl() {
    instruction="$1"

    # Cargar bridge y delegar
    . "$AGENT_DIR/bridge.sh"
    bridge_recpl "$instruction"
}
```

### 4.3 Catalogo completo de herramientas (Fase 1)

| Herramienta | Descripcion | Depende de | Prioridad |
|-------------|-------------|------------|-----------|
| `recpl` | Ejecuta instrucciones RECPL via bridge | bridge.sh | **Fase 1** |
| `respond` | Responde textualmente al usuario | — | **Fase 1** |
| `read_file` | Lee archivos del sistema | — | Fase 2 |
| `write_file` | Escribe/edita archivos | — | Fase 2 |
| `run_command` | Ejecuta comandos shell | — | Fase 2 |
| `search_code` | Busca en codigo fuente | — | Fase 3 |

---

## 5. Plan de Implementacion por Fases

### 5.1 Fase 1: Fundacion del agente (Semana 1)

**Objetivo:** Tener un agente funcional que recibe instrucciones, clasifica
intencion, y delega en RECPL o responde textualmente.

| # | Tarea | Archivo | Estimacion | Depende de |
|---|-------|---------|------------|------------|
| 1.1 | Crear `compiler-bot/agent-robot/` con esquema de directorios | — | 5 min | — |
| 1.2 | Implementar `bridge.sh` — adapter a RECPL via `recpl.sh -c` | `agent-robot/bridge.sh` | 45 min | — |
| 1.3 | Implementar `config.sh` — variables de entorno del agente | `agent-robot/config.sh` | 15 min | — |
| 1.4 | Implementar `tool_registry.sh` con herramientas basicas (recpl, respond) | `agent-robot/tools/tool_registry.sh` | 20 min | 1.1 |
| 1.5 | Implementar `tool_recpl.sh` — llama a bridge | `agent-robot/tools/tool_recpl.sh` | 15 min | 1.2, 1.4 |
| 1.6 | Implementar `tool_respond.sh` — respuesta textual | `agent-robot/tools/tool_respond.sh` | 10 min | 1.4 |
| 1.7 | Implementar `agent.sh` — bucle principal con clasificador de intencion | `agent-robot/agent.sh` | 60 min | 1.2, 1.3, 1.5, 1.6 |
| 1.8 | Implementar `memory.sh` — memoria basica (historial de instrucciones) | `agent-robot/memory.sh` | 30 min | 1.1 |
| 1.9 | Crear `agent-robot.sh` symlink global en raiz de `compiler-bot/` | `compiler-bot/agent-robot.sh` | 5 min | 1.7 |
| 1.10 | Agregar flag `--agent` a `recpl.sh` que delega en agent-robot | `recpl.sh` (MODIFICAR) | 10 min | 1.9 |
| 1.11 | Tests de la Fase 1 (bridge, agent loop, tools basicas) | `tests/test_agent.sh` | 30 min | 1.2-1.8 |

**Total Fase 1:** ~4 horas

**Criterio de exito:**
```sh
# El agente responde comandos RECPL
./compiler-bot/agent-robot/agent.sh "crea modulo pagos en nestjs"
# Output: ✅ Generando module Payments...

# El agente responde textualmente
./compiler-bot/agent-robot/agent.sh "hola"
# Output: Hola! Soy Proyecto0, tu agente de codigo abierto...

# El flag --agent funciona desde recpl.sh
./compiler-bot/recpl.sh --agent -c "crea modulo pagos en nestjs"
```

### 5.2 Fase 2: Herramientas del sistema (Semana 2)

**Objetivo:** El agente puede leer y escribir archivos, ejecutar comandos.

| # | Tarea | Archivo | Estimacion | Depende de |
|---|-------|---------|------------|------------|
| 2.1 | Implementar `tool_read_file.sh` | `agent-robot/tools/tool_read_file.sh` | 20 min | 1.4 |
| 2.2 | Implementar `tool_write_file.sh` | `agent-robot/tools/tool_write_file.sh` | 25 min | 1.4 |
| 2.3 | Implementar `tool_run_command.sh` | `agent-robot/tools/tool_run_command.sh` | 20 min | 1.4 |
| 2.4 | Integrar nuevas herramientas en `tool_registry.sh` | `agent-robot/tools/tool_registry.sh` | 10 min | 2.1-2.3 |
| 2.5 | Actualizar `agent.sh` para detectar y usar las nuevas herramientas | `agent-robot/agent.sh` | 30 min | 2.4 |
| 2.6 | Tests de la Fase 2 (read, write, command) | `tests/test_agent.sh` | 30 min | 2.1-2.5 |

**Total Fase 2:** ~2 horas

**Criterio de exito:**
```sh
# El agente lee archivos
./agent-robot/agent.sh "lee el archivo README.md"

# El agente escribe archivos
./agent-robot/agent.sh "crea un archivo test.txt con el texto 'hola mundo'"

# El agente ejecuta comandos
./agent-robot/agent.sh "ejecuta ls -la"
```

### 5.3 Fase 3: Planificador y memoria avanzada (Semana 3)

**Objetivo:** El agente puede ejecutar tareas multi-paso y recordar contexto
entre instrucciones.

| # | Tarea | Archivo | Estimacion | Depende de |
|---|-------|---------|------------|------------|
| 3.1 | Implementar `planner.sh` — descomposicion de instrucciones en pasos | `agent-robot/planner.sh` | 60 min | 1.7 |
| 3.2 | Mejorar `memory.sh` — memoria persistente entre sesiones (archivo JSON) | `agent-robot/memory.sh` | 30 min | 1.8 |
| 3.3 | Implementar `tool_search_code.sh` — busqueda en codigo fuente | `agent-robot/tools/tool_search_code.sh` | 25 min | 1.4 |
| 3.4 | Integrar planner en `agent.sh` — loop detecta multi-paso | `agent-robot/agent.sh` | 30 min | 3.1 |
| 3.5 | Tests de la Fase 3 (planner, memoria, search) | `tests/test_agent.sh` | 30 min | 3.1-3.4 |

**Total Fase 3:** ~3 horas

**Criterio de exito:**
```sh
# El agente ejecuta tareas multi-paso
./agent-robot/agent.sh "crea modulo auth y modulo payments en nestjs"
# Output: ✅ Modulo Auth creado... ✅ Modulo Payments creado...

# El agente recuerda contexto entre instrucciones
./agent-robot/agent.sh "crea modulo users en nestjs"
./agent-robot/agent.sh "que modulos tengo?"
# Output: Tienes 1 modulo: Users

# Memoria persiste entre sesiones
AGENT_MEMORY_DIR=/tmp/mi_sesion ./agent-robot/agent.sh "que modulos tengo?"
```

### 5.4 Fase 4: System prompts y robustez (Semana 4)

**Objetivo:** El agente tiene personalidad, system prompts claros, y manejo
de errores robusto.

| # | Tarea | Archivo | Estimacion | Depende de |
|---|-------|---------|------------|------------|
| 4.1 | Escribir `system_agent.txt` — prompt base del agente | `agent-robot/prompts/system_agent.txt` | 20 min | — |
| 4.2 | Escribir `system_planner.txt` — prompt del planificador | `agent-robot/prompts/system_planner.txt` | 15 min | — |
| 4.3 | Escribir `system_tools.txt` — descripcion de herramientas para el LLM | `agent-robot/prompts/system_tools.txt` | 15 min | — |
| 4.4 | Mejorar manejo de errores en `agent.sh` (timeouts, fallos de bridge) | `agent-robot/agent.sh` | 30 min | 1.7 |
| 4.5 | Agregar logging completo en `agent.sh` | `agent-robot/agent.sh` | 15 min | 1.7 |
| 4.6 | Tests de la Fase 4 (errores, prompts, logging) | `tests/test_agent.sh` | 30 min | 4.1-4.5 |

**Total Fase 4:** ~2 horas

**Criterio de exito:**
```sh
# Errores de bridge se manejan gracefulmente
./agent-robot/agent.sh "comando que no existe"
# Output: No entendi la instruccion. Puedes intentar: ...

# El agente tiene personalidad consistente
./agent-robot/agent.sh "quien eres?"
# Output: Soy Proyecto0(RECPL), tu agente de codigo abierto...

# Logging captura todas las interacciones
cat /tmp/agent.log
```

---

## 6. Reglas de Diseno para la Implementacion

### 6.1 Reglas estrictas

1. **NO modificar archivos existentes de RECPL** excepto `recpl.sh` para agregar
   el flag `--agent` (un cambio minimal de ~3 lineas).
2. **NO depender de internals de RECPL** — el bridge solo llama a `recpl.sh -c`
   y `pipeline_debugger.sh --output`. No llama a `frontend/` ni `middleend/`
   directamente.
3. **Bridge de una via** — `agent-robot` → RECPL. RECPL nunca llama a
   `agent-robot`.
4. **DRY es opcional** — si hay duplicacion entre `agent-robot` y RECPL, se
   acepta. La prioridad es el aislamiento.
5. **Modo deterministico es RECPL** — el agente NO reimplementa el pipeline
   deterministico. Lo invoca via bridge.
6. **Todo el codigo nuevo va en `agent-robot/`** — nada fuera de ese directorio
   excepto `agent-robot.sh` (symlink) y el flag en `recpl.sh`.

### 6.2 Convenciones de codigo

- Seguir `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` (sin `set -e`, sin `eval`,
  double-quote variables, 4-space indent, snake_case funciones)
- `agent-robot` usa `#!/bin/sh` (POSIX) como el resto del proyecto
- Las herramientas (`tools/tool_*.sh`) implementan la funcion `tool_<nombre>()`
- El registro de herramientas esta en `tools/tool_registry.sh`

### 6.3 Interaccion con el usuario

```
$ recpl --agent "crea modulo pagos en nestjs"
🤖 Proyecto0(RECPL) v1.0.0
   Usando modo deterministico (RECPL)...

✅ Generando module Payments en nestjs...
   Archivos: modules/payments/

$ recpl --agent "que modulos tengo?"
🤖 Tienes 1 modulo:
   - Payments (NestJS)
```

El prefijo `🤖` distingue visualmente la salida del agente de la salida
directa de RECPL.

---

## 7. Integracion con el Codigo Existente

### 7.1 Modificaciones minimas a `recpl.sh`

Unicamente se agrega un flag `--agent` que delega en `agent-robot/agent.sh`:

```sh
# En recpl.sh, dentro del case de argumentos:
--agent)
    exec "$SCRIPT_DIR/agent-robot/agent.sh" "$@"
    ;;
```

El resto de `recpl.sh` permanece intacto.

### 7.2 Sin cambios en `frontend/`, `middleend/`, `backend/`, `providers/`

| Directorio | Cambio | Justificacion |
|------------|--------|---------------|
| `frontend/` | **NINGUNO** | El agente llama a RECPL via bridge, no directamente |
| `middleend/` | **NINGUNO** | Idem |
| `backend/` | **NINGUNO** | Idem |
| `providers/` | **NINGUNO** | El agente usa los providers existentes via `llm_classifier.sh` o los llama directamente si necesita |
| `templates/` | **NINGUNO** | RECPL los usa, el agente no los toca |
| `tests/` | **AGREGAR** `tests/test_agent.sh` | Nuevos tests para agent-robot |
| `pipeline_debugger.sh` | **NINGUNO** | El agente lo usa via bridge con `--output` |

### 7.3 Bridge vs. llamada directa a providers

El agente necesita acceso a LLM para clasificar intencion y planificar. Puede:

a) **Usar el `llm_classifier.sh` existente via bridge** (recomendado para Fase 1)
b) **Llamar a los providers directamente** desde `agent-robot` (si se necesita
   control fino, Fase 2+)

**Decision:** Para Fase 1, el agente usa `llm_classifier.sh` via bridge. Esto
mantiene el aislamiento y reutiliza la logica existente de provider chain,
rate limiting, y manejo de errores.

---

## 8. Cronograma Resumido

| Fase | Semana | Horas | Entregable |
|------|--------|-------|------------|
| Fase 1: Fundacion del agente | Semana 1 | ~4h | `agent.sh` funcional + bridge a RECPL + tools basicas (recpl, respond) + `--agent` flag |
| Fase 2: Herramientas del sistema | Semana 2 | ~2h | Agente puede leer/escribir archivos y ejecutar comandos |
| Fase 3: Planificador y memoria | Semana 3 | ~3h | Agente ejecuta tareas multi-paso y recuerda contexto |
| Fase 4: Prompts y robustez | Semana 4 | ~2h | System prompts, manejo de errores, logging |
| **Total** | **4 semanas** | **~11h** | **Capa agent-robot completa** |

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| **El bridge es un cuello de botella** (cada llamada al agente pasa por RECPL) | Latencia adicional | El bridge llama a `recpl.sh -c` que ya es rapido (~50ms deterministico). Aceptable para Fase 1. |
| **Duplicacion de logica entre agent-robot y RECPL** | Inconsistencia | Aceptado explicitamente (DRY es opcional). Si crece, refactorizar. |
| **El agente depende de RECPL pero RECPL no sabe del agente** | Dependencia circular no, pero acoplamiento unidireccional | Disenado asi. Si RECPL cambia su interfaz, solo hay que actualizar `bridge.sh`. |
| **El clasificador de intencion (LLM) es lento** | ~1-3s por instruccion | El modo deterministico (sin LLM) es el default. El LLM solo se usa cuando el deterministico falla. |
| **System prompts crecen y son dificiles de mantener** | Deriva de comportamiento | Separar en archivos `.txt` dentro de `agent-robot/prompts/`. Versionar los cambios. |

---

## 10. Referencias

- `docs/047_PROP_DEV_COMPILER_BOT_AGENT_CONCEPT_1_0_DRAFT.md` — Propuesta de concepto (documento rector)
- `docs/046_PROP_DEV_COMPILER_BOT_TIER_ARCHITECTURE_1_0_DRAFT.md` — Arquitectura free/paid (provider chain)
- `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` — Provider gratuito
- `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` — Propuesta TUI (futuro)
- `docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — Propuesta original del compilador
- `docs/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
- `compiler-bot/recpl.sh` — Entrypoint actual (modificar solo flag --agent)
- `compiler-bot/pipeline_debugger.sh` — Debugger (usado por bridge)
- `compiler-bot/frontend/llm_classifier.sh` — Fachada LLM (usado por bridge para clasificar intencion)
- `compiler-bot/providers/` — Adapters de proveedores
