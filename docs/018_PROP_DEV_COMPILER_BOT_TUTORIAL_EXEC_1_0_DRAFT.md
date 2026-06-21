---
id: 018
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - proposal
  - compiler-bot
  - recpl
  - tutorial
  - executor
  - markdown
  - step-by-step
  - automation
  - doc-processor
  - nlp
  - intent
  - scaffolding
summary: "Propuesta de sistema Ejecutor de Tutoriales para el bot RECPL. Extiende la capa NLP (014) con capacidad de leer, comprender y ejecutar tutoriales .md paso a paso, integrando el procesador de documentos (003/004) con el pipeline de scaffolding existente."
keywords:
  - propuesta
  - tutorial-executor
  - recpl
  - compiler-bot
  - markdown
  - paso-a-paso
  - automatizacion
  - scaffolding
  - ejecucion
  - estado
  - progreso
  - django
  - graphql
  - integracion
  - pipeline
  - multi-paso
changelog:
  - version: 1.0
    date: 2026-06-08
    author: workflow-agent
    description: Creacion de la propuesta de Ejecutor de Tutoriales para RECPL, integrando doc-processor (003/004) y NLP layer (014)
---

# Propuesta: Sistema Ejecutor de Tutoriales para RECPL

> **Referencias:**
> `003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md` (procesador de documentos, scan/parse/index),
> `004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md` (especificacion de herramientas doc),
> `014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md` (capa NLP, clasificador de intenciones, dialog manager),
> `013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` (nucleo C nativo),
> `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` (multi-tech-stack + UI web)
>
> **Continuacion de:** 014 (NLP + Intent Layer)
>
> Mientras 014 define como el bot **entiende** lenguaje natural, esta propuesta define
> como el bot **aprende y ejecuta** secuencias de instrucciones a partir de tutoriales .md:
> un sistema que lee documentacion estructurada, la descompone en pasos ejecutables,
> y los ejecuta automaticamente con seguimiento de estado.

---

## 1. Resumen Ejecutivo

### 1.1 Problema

El bot RECPL actual puede procesar comandos simples como "crea modulo X en Y" y,
gracias a 014, entiende intenciones y mantiene contexto multi-turno. Sin embargo,
hay un vacio funcional importante:

| Limitacion | Ejemplo | Impacto |
|------------|---------|---------|
| **No entiende tutoriales** | Darle un `.md` con 10 pasos para configurar Django+GraphQL | El bot no sabe leerlo ni ejecutarlo |
| **No ejecuta secuencias** | "Instala dependencias, crea proyecto, configura schema..." | Cada paso hay que darselo manualmente |
| **No rastrea progreso** | "¿En que paso voy del tutorial?" | No hay estado de avance |
| **No adapta pasos al contexto** | "Ya tienes Django instalado, salta al paso 3" | Repite pasos innecesarios |
| **No detecta errores en medio de una secuencia** | "Fallo al instalar graphene-django" | No sabe si reintentar, saltar, o abortar |
| **No genera resumen de ejecucion** | "¿Que se hizo?" | No hay trazabilidad |

### 1.2 Solucion Propuesta

Un **Ejecutor de Tutoriales** que se situa como una nueva capacidad del bot,
utilizando la capa NLP (014) para entender el lenguaje natural dentro de los tutoriales
y el pipeline de scaffolding (RECPL) para ejecutar las acciones:

```
INPUT: tutorial.md (archivo markdown estructurado)
  ↓
[ DOC PROCESSOR LAYER ] (003/004)
  ├── scan_md.sh           → detecta frontmatter y estructura
  ├── parse_frontmatter    → extrae metadatos (title, desc, tags)
  └── generate_index       → identifica secciones y pasos
  ↓
[ TUTORIAL PARSER ]
  ├── extract_steps()      → divide en pasos ejecutables
  ├── classify_step()      → shell_cmd | file_edit | manual_action | scaffold
  └── build_dag()          → grafo de dependencias entre pasos
  ↓
[ TUTORIAL EXECUTOR ]
  ├── state_manager        → tracking de progreso (que paso, que falta)
  ├── step_runner          → ejecuta cada paso segun su tipo
  ├── error_handler        → reintentar/saltar/abortar en fallo
  └── rollback_manager     → deshacer pasos fallidos si es posible
  ↓
[ NLP LAYER ] (014)
  ├── intent_classifier    → "siguiente paso", "repetir", "resumen", "estado"
  ├── context_manager      → mantiene estado multi-turno de la ejecucion
  └── dialog_manager       → pregunta si algo no esta claro
  ↓
OUTPUT: "Paso 3/10 completado. ¿Ejecuto el paso 4?"
       + estado actual del proyecto
       + resumen de acciones realizadas
```

### 1.3 Beneficios Esperados

| Escenario | Sin Ejecutor | Con Ejecutor | Mejora |
|-----------|-------------|--------------|--------|
| Tutorial de 10 pasos | Hay que leer y ejecutar cada paso manualmente | `recpl ejecuta tutorial.md` y lo hace solo | **Automation** |
| Fallo en paso intermedio | Hay que diagnosticar y reparar manualmente | Detecta, pregunta si reintentar o saltar | **Resiliencia** |
| Reanudar tutorial | Hay que recordar donde se quedo | `recpl estado` muestra progreso exacto | **Continuidad** |
| Tutorial con scaffolding | No aprovecha el generador de modulos | Traduce pasos de "crea modulo X" a scaffolding del bot | **Sinergia** |
| Documentacion como ejecutable | Los .md solo se leen | Los .md son programas que el bot ejecuta | **Doc-as-code** |
| Errores de version | Tutorial desactualizado vs entorno real | El bot detecta versiones y adapta comandos | **Adaptabilidad** |

---

## 2. Arquitectura del Sistema

### 2.1 Vision General

```
┌──────────────────────────────────────────────────────────────────────┐
│                        EJECUTOR DE TUTORIALES                         │
│                                                                      │
│  ┌─────────────────────┐    ┌───────────────────────────────────┐   │
│  │   TUTORIAL INPUT     │    │         DOC PROCESSOR (003)       │   │
│  │   (.md file o URL)   │───▶│  scan_md → parse_frontmatter     │   │
│  └─────────────────────┘    │  → split_sections → index         │   │
│                             └───────────────┬───────────────────┘   │
│                                             │                        │
│                             ┌───────────────▼───────────────────┐   │
│                             │        TUTORIAL PARSER            │   │
│                             │  ┌─────────────────────────────┐  │   │
│                             │  │  step_extractor.sh          │  │   │
│                             │  │  step_classifier.sh         │  │   │
│                             │  │  dependency_builder.sh      │  │   │
│                             │  └─────────────────────────────┘  │   │
│                             └───────────────┬───────────────────┘   │
│                                             │                        │
│                             ┌───────────────▼───────────────────┐   │
│                             │        TUTORIAL EXECUTOR          │   │
│                             │  ┌─────────────────────────────┐  │   │
│                             │  │  state_manager.sh           │  │   │
│                             │  │  step_runner.sh             │  │   │
│                             │  │  error_handler.sh           │  │   │
│                             │  │  rollback_manager.sh        │  │   │
│                             │  └─────────────────────────────┘  │   │
│                             └───────────────┬───────────────────┘   │
│                                             │                        │
└─────────────────────────────────────────────┼────────────────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────┐
                    │         NLP LAYER (014)   │                      │
                    │  ┌────────────────┐  ┌───▼──────────┐          │
                    │  │ Intent Classif │  │ Context Mgr  │          │
                    │  └────────────────┘  └──────────────┘          │
                    └──────────────────────────┬──────────────────────┘
                                               │
                    ┌──────────────────────────▼──────────────────────┐
                    │         PIPELINE EXISTENTE (recpl)              │
                    │  preprocess → lexer → parser → semantic → IR    │
                    │  → synthesis → scaffold                         │
                    └─────────────────────────────────────────────────┘
```

### 2.2 Integracion con Doc Processor (003/004)

El Doc Processor define herramientas para escanear, parsear e indexar documentos `.md`.
El Ejecutor de Tutoriales reutiliza estas mismas herramientas pero con un objetivo
distinto: no solo indexar, sino **ejecutar**:

| Herencia de 003/004 | Adaptacion para Tutoriales |
|---------------------|---------------------------|
| `scan_md.sh` — escanea .md con frontmatter | Reutilizado: detecta tutoriales por frontmatter + estructura de pasos |
| `parse_frontmatter.sh` — extrae YAML | Reutilizado: extrae titulo, descripcion, tags, prerequisitos |
| `generate_index.sh` — produce indice | Adaptado: en vez de indice, produce lista ordenada de pasos |
| `spellcheck.sh` — valida ortografia | Reutilizado: verifica que el tutorial no tenga errores tipograficos |
| Pipeline modular por fases | Reutilizado: cada paso del tutorial es una "fase" del pipeline |

**Diferencia clave:** Mientras el Doc Processor produce **artefactos de documentacion**
(indices, reportes), el Ejecutor de Tutoriales produce **acciones ejecutadas**
(archivos creados, comandos ejecutados, scaffolding generado).

### 2.3 Integracion con NLP Layer (014)

La capa NLP (014) proporciona la "interfaz conversacional" del Ejecutor de Tutoriales:

| Componente 014 | Uso en Tutorial Executor |
|----------------|-------------------------|
| `classify_intent.sh` | Nuevas intenciones: `RUN_TUTORIAL`, `NEXT_STEP`, `TUTORIAL_STATUS`, `TUTORIAL_SUMMARY`, `SKIP_STEP`, `RETRY_STEP` |
| `extract_entities.sh` | Nuevas entidades: `TUTORIAL` (nombre de tutorial), `STEP` (numero de paso), `SECTION` (seccion) |
| `dialog_manager.sh` | Gestiona dialogo durante ejecucion: "Fallo el paso 5. ¿Reintentar, saltar, o abortar?" |
| `context_manager.sh` | Mantiene estado de ejecucion entre turnos: paso actual, pasos completados, errores |
| `fill_slots.sh` | Nuevos slots: `tutorial_path`, `current_step`, `start_step`, `end_step`, `mode` (auto|interactive) |

**Nuevas intenciones especificas:**

| Intencion | Descripcion | Ejemplo |
|-----------|-------------|---------|
| `RUN_TUTORIAL` | Ejecutar un tutorial completo | "ejecuta el tutorial de django" |
| `NEXT_STEP` | Avanzar al siguiente paso | "siguiente paso", "continua" |
| `TUTORIAL_STATUS` | Mostrar progreso actual | "en que paso voy?", "estado" |
| `TUTORIAL_SUMMARY` | Resumir lo ejecutado | "que se hizo hasta ahora?" |
| `SKIP_STEP` | Saltar un paso | "salta el paso de instalacion" |
| `RETRY_STEP` | Reintentar un paso fallido | "reintenta el paso 3" |
| `ABORT_TUTORIAL` | Cancelar ejecucion | "cancela", "deten el tutorial" |
| `TUTORIAL_HELP` | Explicar el tutorial | "de que trata este tutorial?" |

### 2.4 Modos de Operacion

| Modo | Descripcion | Activacion |
|------|-------------|------------|
| **Auto** | Ejecuta todos los pasos sin preguntar | `--mode=auto` o `ejecuta tutorial.md --auto` |
| **Interactive** | Pregunta antes de cada paso | `--mode=interactive` (defecto) |
| **Step-by-step** | Espera confirmacion en cada paso | `--mode=step` o `siguiente paso` |
| **Dry-run** | Muestra que haria sin ejecutar | `--mode=dry-run` o `ensaya tutorial.md` |
| **Resume** | Reanuda desde el ultimo paso exitoso | `--mode=resume` o `continua tutorial` |
| **Validate** | Verifica prerequisitos sin ejecutar | `--mode=validate` o `verifica tutorial.md` |

---

## 3. Componentes Detallados

### 3.1 Tutorial Parser

#### 3.1.1 Estructura esperada de un tutorial .md

El parser espera tutoriales con una estructura consistente. El formato de referencia
es `misc/tutorial.md` (Tutorial de GraphQL con Django y Graphene):

```markdown
---
title: "Tutorial de GraphQL con Django y Graphene"
description: "Creacion de un backend para un servicio acortador de URL..."
tags: [graphql, django, graphene, python, tutorial]
---

# Titulo del Tutorial

## Introduccion

Texto descriptivo...

## Requisitos previos

Lista de prerequisitos...

## Paso 1: Configurar el proyecto Django

Texto explicativo...

```sh
comando shell a ejecutar
```

## Paso 2: Configurar una aplicacion y modelos Django

...
```

**Reglas de parseo:**

1. Cada `## Paso N:` es un paso ejecutable
2. Cada `##` sin "Paso" es una seccion informativa (no ejecutable)
3. Los bloques ` ```sh ` contienen comandos a ejecutar
4. Los bloques ` ```python ` contienen archivos a crear
5. Los bloques ` ```json ` o ` ```graphql ` contienen ejemplos (no ejecutar)
6. Las lineas de texto entre pasos son contexto informativo
7. El frontmatter YAML contiene metadatos del tutorial

#### 3.1.2 step_extractor.sh

```sh
# step_extractor.sh - Extrae pasos ejecutables de un tutorial .md
#
# Entrada: archivo .md (stdin o --file)
# Salida: JSON con lista de pasos clasificados
#
# Algoritmo:
#   1. Leer frontmatter YAML → metadatos
#   2. Dividir por ## headings
#   3. Identificar secciones "Paso N:" → paso ejecutable
#   4. Dentro de cada paso:
#      a. Extraer bloques ```sh → tipo SHELL_CMD
#      b. Extraer bloques ```python → tipo FILE_CREATE
#      c. Extraer bloques ``` (otros) → tipo EXAMPLE (no ejecutable)
#      d. Extraer bloques ```graphql → tipo GRAPHQL_QUERY
#      e. Texto explicativo → tipo INFO (mostrar al usuario)
#   5. Numerar pasos secuencialmente
#   6. Asignar ID a cada paso: "tutorial_nombre_paso_N"
#   7. Detectar prerequisitos dentro del paso
```

**Salida del extractor:**

```json
{
  "tutorial": {
    "title": "Tutorial de GraphQL con Django y Graphene",
    "description": "Creacion de un backend para un servicio acortador de URL...",
    "tags": ["graphql", "django", "graphene", "python", "tutorial"],
    "total_steps": 8,
    "prereqs": ["python >= 3.5", "pip", "entorno virtual"],
    "techs_detectadas": ["django", "graphene", "python", "graphql"]
  },
  "pasos": [
    {
      "id": "paso_1",
      "numero": 1,
      "titulo": "Configurar el proyecto Django",
      "acciones": [
        {
          "tipo": "SHELL_CMD",
          "comando": "pip install \"django==2.1.7\" \"graphene-django>==2.2.0\"",
          "cwd": "shorty",
          "esperar": true,
          "check_exit": 0
        },
        {
          "tipo": "SHELL_CMD",
          "comando": "django-admin startproject shorty .",
          "cwd": "shorty",
          "esperar": true
        },
        {
          "tipo": "SHELL_CMD",
          "comando": "python manage.py migrate",
          "cwd": "shorty",
          "esperar": true
        },
        {
          "tipo": "SHELL_CMD",
          "comando": "python manage.py runserver",
          "cwd": "shorty",
          "esperar": false,
          "daemon": true
        },
        {
          "tipo": "FILE_EDIT",
          "archivo": "shorty/settings.py",
          "accion": "append_line",
          "seccion": "INSTALLED_APPS",
          "contenido": "'graphene_django',"
        },
        {
          "tipo": "FILE_EDIT",
          "archivo": "shorty/settings.py",
          "accion": "append_to_end",
          "contenido": "\nGRAPHENE = {\n    'SCHEMA': 'shorty.schema.schema',\n}"
        }
      ],
      "dependencias": [],
      "tiempo_estimado": "5 min",
      "verificable": true,
      "verificacion": "python -c \"import django; print(django.VERSION)\""
    },
    {
      "id": "paso_2",
      "numero": 2,
      "titulo": "Configurar una aplicacion y modelos Django",
      "acciones": [
        {
          "tipo": "SHELL_CMD",
          "comando": "python manage.py startapp shortener",
          "cwd": "shorty"
        },
        {
          "tipo": "FILE_CREATE",
          "archivo": "shortener/models.py",
          "contenido": "...",
          "sobrescribir": true
        }
      ],
      "dependencias": ["paso_1"],
      "tiempo_estimado": "10 min"
    }
  ]
}
```

#### 3.1.3 step_classifier.sh

Clasifica cada accion dentro de un paso segun su tipo:

| Tipo | Deteccion | Ejecucion |
|------|-----------|-----------|
| `SHELL_CMD` | Bloque ` ```sh ` | Ejecuta comando, captura stdout/stderr |
| `FILE_CREATE` | Bloque ` ```python ` + instruccion "Cree un nuevo archivo" | Crea archivo con el contenido del bloque |
| `FILE_EDIT` | Texto "abra el archivo", "anada la linea" + bloque de codigo | Edita archivo existente (insertar linea, reemplazar seccion, append) |
| `SHELL_CMD_DAEMON` | Comando que inicia servidor (`runserver`, `start`) | Ejecuta en background, registra PID |
| `MANUAL_ACTION` | Instrucciones sin bloque de codigo | Muestra mensaje al usuario, espera confirmacion |
| `GRAPHQL_QUERY` | Bloque ` ```graphql ` | (Opcional futuro) Ejecutar contra endpoint GraphQL |
| `SCAFFOLD` | Accion que coincide con patron RECPL | Delegar a `recpl-core --mode=full` |
| `INFO` | Texto explicativo no accionable | Mostrar al usuario |
| `VERIFY` | Instruccion de verificacion | Ejecutar comando de verificacion, comparar output |

#### 3.1.4 dependency_builder.sh

Construye un grafo de dependencias entre pasos:

```sh
# dependency_builder.sh - Construye DAG de dependencias entre pasos
#
# Algoritmo:
#   1. Cada paso depende del anterior por defecto (secuencia lineal)
#   2. Detectar dependencias explicitas:
#      - "En el paso anterior..." → depende del paso N-1
#      - "Una vez que tenga X..." → depende del paso que crea X
#      - "Abra el archivo creado en el paso N" → depende del paso N
#   3. Detectar prerequisitos compartidos:
#      - Dos pasos que usan el mismo archivo → orden secuencial
#      - Pasos que crean archivos vs pasos que los modifican → orden
#   4. Detectar pasos paralelizables:
#      - Pasos sin dependencias entre si → pueden ejecutarse en paralelo
```

**Salida:**

```json
{
  "dag": {
    "paso_1": {"deps": [], "paralelizable": false},
    "paso_2": {"deps": ["paso_1"], "paralelizable": false},
    "paso_3": {"deps": ["paso_2"], "paralelizable": false},
    "paso_4": {"deps": ["paso_3"], "paralelizable": false},
    "paso_5": {"deps": ["paso_4"], "paralelizable": false},
    "paso_6": {"deps": ["paso_5"], "paralelizable": false},
    "paso_7": {"deps": ["paso_6"], "paralelizable": false},
    "paso_8": {"deps": ["paso_7"], "paralelizable": false}
  },
  "orden_topologico": ["paso_1", "paso_2", "paso_3", "paso_4", "paso_5", "paso_6", "paso_7", "paso_8"],
  "paralelizables": []
}
```

### 3.2 Tutorial Executor

#### 3.2.1 state_manager.sh

Mantiene el estado de ejecucion del tutorial en disco (via `RECPL_STATE_DIR`):

```sh
# state_manager.sh - Gestiona el estado de ejecucion del tutorial
#
# Estado persistido en: $RECPL_STATE_DIR/tutorials/<tutorial_id>.state
#
# Formato del archivo de estado:
#   TUTORIAL_ID="graphql-django-graphene"
#   TUTORIAL_FILE="/path/to/tutorial.md"
#   STARTED_AT="2026-06-08T10:00:00Z"
#   CURRENT_STEP=3
#   TOTAL_STEPS=8
#   STATUS="in_progress"  # pending | in_progress | completed | failed | aborted
#   COMPLETED_STEPS="paso_1 paso_2"
#   FAILED_STEPS=""
#   SKIPPED_STEPS=""
#   STEP_3_STATUS="completed"
#   STEP_3_OUTPUT="..."
#   STEP_3_ERROR=""
#   PROJECT_DIR="/home/user/projects/shorty"
```

**Funciones:**

```sh
# init_tutorial(tutorial_file) — inicia estado de un tutorial
# get_state() — devuelve estado actual
# set_step_status(step_id, status, output) — marca paso como completado/fallido
# get_current_step() — devuelve el paso actual
# advance_step() — avanza al siguiente paso
# can_resume() — verifica si se puede reanudar
# get_summary() — devuelve resumen de lo ejecutado
# reset_tutorial() — reinicia el estado
```

**Estados de cada paso:**

```
pending → running → completed
                 → failed → retrying → running
                 → skipped
                 → blocked (dependencia fallida)
```

#### 3.2.2 step_runner.sh

Ejecuta un paso individual segun su tipo:

```sh
# step_runner.sh - Ejecuta un paso del tutorial
#
# Uso: step_runner.sh <step_json> [--mode=auto|interactive]
#
# Para SHELL_CMD:
#   1. Verificar cwd (crear si no existe)
#   2. Ejecutar comando con timeout (default: 5 min)
#   3. Capturar stdout/stderr a archivo temporal
#   4. Verificar exit code (si check_exit != 0, marcar fallo)
#   5. Si daemon=true: ejecutar en background, guardar PID
#
# Para FILE_CREATE:
#   1. Verificar que el directorio existe
#   2. Escribir archivo con el contenido del bloque
#   3. Verificar que se escribio correctamente
#
# Para FILE_EDIT:
#   1. Leer archivo existente
#   2. Aplicar la edicion (append_line, replace_section, insert_at)
#   3. Verificar que la edicion fue aplicada
#   4. Crear backup .orig antes de modificar (herencia de spellcheck.sh)
#
# Para MANUAL_ACTION:
#   1. Mostrar instrucciones al usuario
#   2. En modo interactive: preguntar "Listo?" y esperar confirmacion
#   3. En modo auto: mostrar y continuar (asumir que el usuario lo hara)
#
# Para SCAFFOLD:
#   1. Traducir la accion a un comando RECPL
#   2. Ejecutar recpl-core --mode=full o recpl.sh
#
# Toda accion registra: timestamp, duracion, exit_code, output_size
```

#### 3.2.3 error_handler.sh

Maneja errores durante la ejecucion de pasos:

```sh
# error_handler.sh - Maneja errores de ejecucion
#
# Estrategias por tipo de error:
#
# | Error | Deteccion | Accion por defecto | Configurable |
# |-------|-----------|-------------------|--------------|
# | Comando no encontrado | exit code 127 | Abortar | --skip-on-not-found |
# | Permiso denegado | exit code 126 | Abortar con mensaje | -- |
# | Timeout | Senal ALRM | Reintentar 1 vez, luego saltar | --retry=N |
# | Error de red (pip, npm) | stderr con "connection", "timeout" | Reintentar hasta 3 veces | --retry-network=N |
# | SyntaxError Python | stderr con "SyntaxError" | Abortar, paso critico | -- |
# | ImportError Python | stderr con "ImportError" | Sugerir pip install | -- |
# | Archivo no encontrado | File not found | Saltar paso, warning | -- |
# | Version incorrecta | Deteccion en verificacion | Preguntar si continuar | --force |
#
# Flujo:
#   1. Detectar tipo de error por exit code + stderr
#   2. Aplicar estrategia segun configuracion
#   3. Si es AUTO: aplicar estrategia sin preguntar
#   4. Si es INTERACTIVE: preguntar "Fallo paso N. [R]eintentar, [S]altar, [A]bortar, [D]epurar?"
#   5. Registrar decision en el estado
```

#### 3.2.4 rollback_manager.sh

Deshace cambios de pasos fallidos cuando es posible:

```sh
# rollback_manager.sh - Deshace pasos fallidos
#
# Capacidad de rollback por tipo:
#
# | Tipo | Rollback posible | Metodo |
# |------|-----------------|--------|
# | SHELL_CMD | Depende del comando | No automatico (el comando puede tener efectos secundarios) |
# | FILE_CREATE | Si | Eliminar archivo creado |
# | FILE_EDIT | Si | Restaurar backup .orig |
# | SCAFFOLD | Si | recpl-core --mode=delete |
# | SHELL_CMD_DAEMON | Si | kill PID guardado |
# | pip install | Depende | pip uninstall (futuro) |
#
# Limitaciones:
#   - No todos los comandos shell son reversible
#   - Rollback solo si se ejecuto en modo interactivo o se configuro --rollback
#   - Acciones destructivas (DROP TABLE, rm -rf) no tienen rollback
```

### 3.3 Integracion con NLP (014) - Comandos de Usuario

El usuario interactua con el Ejecutor de Tutoriales a traves de la capa NLP:

```
USR> ejecuta el tutorial de graphql con django
  ↓
INTENT: RUN_TUTORIAL
ENTITIES: tutorial="graphql django", techs=[django, graphql, python]
  ↓
Buscar tutorial: misc/tutorial.md
  ↓
"Encontre el tutorial 'GraphQL con Django y Graphene' (8 pasos).
 ¿En que modo quieres ejecutarlo?
 [A]uto: ejecuta todo sin preguntar
 [I]nteractivo: pregunta antes de cada paso
 [D]ry-run: solo muestra que se hara
 [V]alidar: solo verifica prerequisitos"

USR> interactivo
  ↓
MODE: interactive
  ↓
"OK. Modo interactivo.
Paso 1/8: Configurar el proyecto Django
  → pip install django==2.1.7 graphene-django==2.2.0
  → django-admin startproject shorty .
  → python manage.py migrate
  → (editar shorty/settings.py)
 ¿Ejecuto el paso 1? (s/n/mostrar)"

USR> s
  ↓
Ejecutando pip install...
...
"Paso 1/8 completado (timestamp, duracion: 45s)
 ¿Ejecuto el paso 2: Configurar una aplicacion y modelos Django?"

USR> estado
  ↓
INTENT: TUTORIAL_STATUS
  ↓
"Progreso: 1/8 pasos completados
 - Paso 1: Configurar proyecto Django ✓
 - Paso 2: Configurar app y modelos   ⏳ pendiente
 - Paso 3: Crear consultas           ⏳ pendiente
 - Paso 4: Crear mutaciones          ⏳ pendiente
 - Paso 5: Endpoint de acceso        ⏳ pendiente
 - Paso 6: Manejo de errores         ⏳ pendiente
 - Paso 7: Filtros                   ⏳ pendiente
 - Paso 8: Paginacion                ⏳ pendiente
 Tiempo transcurrido: 45s
 Proyecto: /home/user/shorty/"

USR> salta al paso 4
  ↓
INTENT: SKIP_STEP
ENTITIES: step=4
  ↓
"Saltando pasos 2 y 3...
Paso 4/8: Crear mutaciones
  → (editar shortener/schema.py)
  → (editar shorty/schema.py)
 ¿Ejecuto el paso 4? (s/n)"

USR> resume despues
  ↓
"OK. Estado guardado. Puedes reanudar con 'continua tutorial'"
```

### 3.4 Integracion con RECPL Scaffolding

Cuando un paso del tutorial coincide con una accion que RECPL sabe hacer
(crear modulos, entidades, etc.), se delega al pipeline de scaffolding:

```sh
# Deteccion de patron RECPL en pasos del tutorial:
#
# "crear una aplicacion llamada shortener"
#   → RECPL detecta: accion=CREATE, tipo=module, nombre=shortener
#   → Pero NO ejecuta recpl porque no es un modulo NestJS
#   → En vez de eso, ejecuta: python manage.py startapp shortener
#   → (El tutorial especifica el comando exacto)
#
# "crea un modulo de pagos en nestjs"
#   → RECPL detecta: coincide con su dominio
#   → Ejecuta: recpl-core --mode=full "crea modulo pagos en nestjs"
#   → Esto genera el scaffold del modulo NestJS
#
# El tutorial puede contener instrucciones en lenguaje natural que RECPL
# ya sabe interpretar gracias a la capa NLP (014):
#
# "Crea un nuevo proyecto Django llamado shorty"
#   → NLP entiende: SCAFFOLD + tech=django + nombre=shorty
#   → Pero si el tutorial especifica "django-admin startproject shorty .",
#     se usa el comando exacto (lo especifico prima sobre lo generico)

# Regla de decision:
#   Si el paso contiene un bloque ```sh → ejecutar el comando exacto
#   Si el paso contiene texto suelto que coincide con patron RECPL → usar NLP+RECPL
#   Si hay ambos → preguntar: "El tutorial dice ejecutar 'X'. Yo puedo hacer 'Y'. ¿Cual prefieres?"
```

---

## 4. Flujo Detallado: Escenarios

### 4.1 Ejecucion Completa de Tutorial

```
USR> ejecuta misc/tutorial.md --mode=auto
  ↓
[1. DOC PROCESSOR] scan_md → parse_frontmatter
  Titulo: "GraphQL con Django y Graphene"
  Pasos: 8 detectados
  Techs: [django, graphene, python, graphql]
  ↓
[2. TUTORIAL PARSER] extract_steps → classify → build_dag
  8 pasos, 24 acciones totales
  Tipos: 12 SHELL_CMD, 8 FILE_EDIT, 2 FILE_CREATE, 2 MANUAL_ACTION
  ↓
[3. PRE-CHECK]
  ✓ python3 --version (3.8.10 >= 3.5)
  ✓ pip disponible
  ✗ django-admin no encontrado → pip install django (lo instalara en paso 1)
  ↓
[4. EJECUCION AUTO]
  Paso 1/8: "Configurar proyecto Django"
    → pip install django==2.1.7 graphene-django==2.2.0  ✓ (32s)
    → django-admin startproject shorty .                 ✓ (1s)
    → python manage.py migrate                           ✓ (3s)
    → Editando shorty/settings.py:
      - Anadiendo 'graphene_django' a INSTALLED_APPS     ✓
      - Anadiendo GRAPHENE config al final              ✓
    ✓ Paso 1 completado (36s)
  ↓
  Paso 2/8: "Configurar app y modelos"
    → python manage.py startapp shortener                 ✓ (1s)
    → Creando shortener/models.py con modelo URL         ✓
    → python manage.py makemigrations                     ✓ (1s)
    → python manage.py migrate                            ✓ (2s)
    ✓ Paso 2 completado (4s)
  ...
  ↓
[5. POST-CHECK]
  ✓ python -c "import django; print(django.VERSION)" → 2.1.7
  ✓ python manage.py check --deploy → 0 issues
  ✓ http://localhost:8000/graphql responde
  ↓
"Tutorial completado (8/8 pasos, duracion total: 12m 34s)
 Resumen:
   - Proyecto Django: shorty/
   - App: shortener/
   - Modelo URL con acortador MD5
   - GraphQL endpoint en /graphql
   - 8 mutaciones y queries configuradas
   - Filtro y paginacion implementados
   - Manejo de errores con GraphQLError
 ¿Quieres que persista este proyecto o lo limpiamos?"
```

### 4.2 Fallo y Recuperacion

```
Paso 6/8: "Implementar gestion de errores"
  → Editando shortener/models.py...                     ✓
  → Ejecutando verificación...                          ✗
    Error: ImportError: cannot import name 'GraphQLError' from 'graphql'
  ↓
[ERROR HANDLER]
  Tipo: ImportError (dependencia Python)
  Estrategia: Sugerir pip install
  ↓
"Error en paso 6: Falta el paquete 'graphql-core' o version incorrecta.
 [R]eintentar: voy a instalar graphql-core y reintentar
 [S]altar: omito este paso y continuo
 [A]bortar: detengo el tutorial
 [D]epurar: abro una terminal para que arregles manualmente"

USR> reintentar
  ↓
  → pip install graphql-core                             ✓ (5s)
  → Re-ejecutando verificacion...                        ✓
  ↓
"Paso 6/8 completado (2do intento)"
```

### 4.3 Dry-run y Validacion

```
USR> ensaya tutorial de graphql
  ↓
MODE: dry-run
  ↓
"Simulacion de 'GraphQL con Django y Graphene' (8 pasos):

Paso 1: Configurar proyecto Django
  📦 pip install django==2.1.7 graphene-django==2.2.0
  📁 django-admin startproject shorty .
  ⚙️  python manage.py migrate
  ✏️  Editar shorty/settings.py (+2 cambios)
  ⚠️  Crea archivos: 3 nuevos, modifica: 1
  💾 Espacio estimado: 45MB

Paso 2: Configurar app y modelos
  📁 python manage.py startapp shortener
  ✏️  Crear shortener/models.py
  ⚙️  python manage.py makemigrations
  ⚙️  python manage.py migrate
  💾 Espacio estimado: 12MB
  ...

Resumen:
  Total: 8 pasos, 24 acciones
  Comandos shell: 12 | Ediciones: 8 | Archivos nuevos: 4
  Tiempo estimado: 30-45 min
  Dependencias a instalar: django, graphene-django, graphql-core
  
  ¿Ejecuto el tutorial? (s/n)"
```

### 4.4 Tutorial Discovery

```
USR> que tutoriales tienes?
  ↓
INTENT: TUTORIAL_HELP
ENTITIES: (ninguna)
  ↓
"Tutoriales disponibles:
  1. GraphQL con Django y Graphene (misc/tutorial.md)
     Tags: graphql, django, graphene, python
     Pasos: 8 | Duracion est: 30-45 min
     
 ¿Quieres ejecutar alguno o ver mas detalles?"
```

```
USR> busca tutoriales de graphql
  ↓
INTENT: TUTORIAL_HELP
ENTITIES: tech=graphql
  ↓
"Tutoriales sobre graphql:
  1. GraphQL con Django y Graphene (misc/tutorial.md)
     Tags: graphql, django, graphene, python
     Stack: Django + Graphene + Python
     Pasos: 8 | Duracion est: 30-45 min
     Descripcion: Creacion de un backend acortador de URL usando GraphQL
```

---

## 5. Componentes de Deteccion y Clasificacion de Pasos

### 5.1 Ejemplos de clasificacion sobre misc/tutorial.md

```
# Fragmento del tutorial (Paso 2):
#
#   "A continuacion, creara una app llamada shortener..."
#   ```sh
#   python manage.py startapp shortener
#   ```
#   "Para terminar de crear la app, abra el archivo..."
#   "Anada el nombre de la app a INSTALLED_APPS..."
#   ```python
#   INSTALLED_APPS = [
#       ...
#       'shortener',
#   ]
#   ```
#
# Clasificacion:
#   Texto: "creara una app llamada shortener" → INFO
#   ```sh → SHELL_CMD: "python manage.py startapp shortener"
#   Texto: "Para terminar de crear la app..." → INFO
#   Texto: "Anada el nombre de la app..." → FILE_EDIT (append_line)
#   ```python con INSTALLED_APPS → FILE_EDIT (reemplazar seccion)
```

```
# Fragmento del tutorial (Paso 4):
#
#   "Para crear su primera Mutation, abra shortener/schema.py..."
#   "Al final del archivo, anada una nueva clase CreateURL..."
#   ```python
#   class CreateURL(graphene.Mutation):
#       url = graphene.Field(URLType)
#   ```
#
# Clasificacion:
#   Texto: "abra shortener/schema.py" → FILE_EDIT objetivo:shortener/schema.py
#   Texto: "Al final del archivo, anada..." → FILE_EDIT accion:append
#   ```python → FILE_EDIT contenido a anadir
```

### 5.2 Patrones de Deteccion

```sh
# Patrones para clasificar acciones en texto de tutorial:

# Archivos a crear
PATRON_FILE_CREATE="Cree un nuevo archivo|crea.*archivo|Create a new file|crear.*en la ruta"

# Archivos a editar
PATRON_FILE_EDIT="abra el archivo|open|edite|modifique|anada la linea|anada el siguiente|sustituya|altere|reemplace|cambie"

# Comandos shell
PATRON_SHELL_CMD="^```sh$"

# Bloques de codigo (con lenguaje)
PATRON_CODE_BLOCK="^```[a-zA-Z]+$"

# Accion manual
PATRON_MANUAL_ACTION="visite|abra su navegador|navegue a|pulse|ejecute el siguiente comando en su terminal|acceda a"

# Scaffolding RECPL
PATRON_SCAFFOLD="crea modulo|crea entidad|genera modulo|scaffold|make module"
```

---

## 6. Tabla de Tareas

### Convenciones

| ID | Tarea | Modulo | Depende de | Esfuerzo | Estado |
|----|-------|--------|------------|----------|--------|
| TUT-001 | Crear `step_extractor.sh` — extrae pasos de .md estructurado | parser | — | L | pending |
| TUT-002 | Implementar deteccion de frontmatter y metadatos del tutorial | parser | TUT-001 | M | pending |
| TUT-003 | Implementar extraccion de bloques ```sh, ```python, ```graphql, ```json | parser | TUT-001 | L | pending |
| TUT-004 | Implementar deteccion de instrucciones textuales (patrones de edicion) | parser | TUT-001 | L | pending |
| TUT-005 | Crear `step_classifier.sh` — clasifica acciones por tipo | parser | TUT-001 | L | pending |
| TUT-006 | Implementar clasificacion SHELL_CMD con deteccion de daemon | parser | TUT-005 | M | pending |
| TUT-007 | Implementar clasificacion FILE_CREATE con contenido from code block | parser | TUT-005 | M | pending |
| TUT-008 | Implementar clasificacion FILE_EDIT con deteccion de tipo de edicion | parser | TUT-005 | L | pending |
| TUT-009 | Implementar clasificacion MANUAL_ACTION con mensajes al usuario | parser | TUT-005 | S | pending |
| TUT-010 | Implementar clasificacion SCAFFOLD (delegar a RECPL) | parser | TUT-005 | M | pending |
| TUT-011 | Crear `dependency_builder.sh` — construye DAG de dependencias | parser | TUT-001 | M | pending |
| TUT-012 | Implementar deteccion de dependencias explicitas entre pasos | parser | TUT-011 | M | pending |
| TUT-013 | Crear `state_manager.sh` — estado persistente de ejecucion | executor | — | L | pending |
| TUT-014 | Implementar get_state/set_state con archivos en RECPL_STATE_DIR | executor | TUT-013 | M | pending |
| TUT-015 | Implementar tracking de progreso (paso actual, completados, fallidos) | executor | TUT-013 | M | pending |
| TUT-016 | Crear `step_runner.sh` — ejecuta un paso segun su tipo | executor | TUT-013 | XL | pending |
| TUT-017 | Implementar runner SHELL_CMD con timeout y captura de output | executor | TUT-016 | L | pending |
| TUT-018 | Implementar runner FILE_CREATE con escritura y verificacion | executor | TUT-016 | M | pending |
| TUT-019 | Implementar runner FILE_EDIT con backup .orig y aplicacion de cambios | executor | TUT-016 | L | pending |
| TUT-020 | Implementar runner MANUAL_ACTION con confirmacion del usuario | executor | TUT-016 | M | pending |
| TUT-021 | Implementar runner SCAFFOLD que delega a recpl-core | executor | TUT-016 | M | pending |
| TUT-022 | Crear `error_handler.sh` — manejo de errores en ejecucion | executor | TUT-016 | L | pending |
| TUT-023 | Implementar deteccion de tipo de error por exit code + stderr | executor | TUT-022 | M | pending |
| TUT-024 | Implementar estrategias: reintentar, saltar, abortar, depurar | executor | TUT-022 | L | pending |
| TUT-025 | Crear `rollback_manager.sh` — deshace cambios de pasos fallidos | executor | TUT-016 | M | pending |
| TUT-026 | Implementar rollback de FILE_CREATE (eliminar archivo) | executor | TUT-025 | S | pending |
| TUT-027 | Implementar rollback de FILE_EDIT (restaurar .orig) | executor | TUT-025 | S | pending |
| TUT-028 | Implementar rollback de SHELL_CMD_DAEMON (kill PID) | executor | TUT-025 | S | pending |
| TUT-029 | Crear `tutorial_discovery.sh` — busca tutoriales en el proyecto | discovery | — | M | pending |
| TUT-030 | Implementar busqueda por tags, techs, nombre parcial | discovery | TUT-029 | M | pending |
| TUT-031 | Crear `tutorial_orchestrator.sh` — orquestador principal | orchestrator | TUT-001..TUT-031 | XL | pending |
| TUT-032 | Implementar modo AUTO (ejecutar todo sin preguntar) | orchestrator | TUT-031 | M | pending |
| TUT-033 | Implementar modo INTERACTIVE (preguntar antes de cada paso) | orchestrator | TUT-031 | M | pending |
| TUT-034 | Implementar modo DRY-RUN (mostrar sin ejecutar) | orchestrator | TUT-031 | M | pending |
| TUT-035 | Implementar modo RESUME (reanudar desde ultimo paso exitoso) | orchestrator | TUT-031 | M | pending |
| TUT-036 | Implementar modo VALIDATE (verificar prerequisitos) | orchestrator | TUT-031 | M | pending |
| TUT-037 | Integrar con NLP (014): nuevas intenciones RUN_TUTORIAL, NEXT_STEP, etc. | nlp-integration | TUT-031, 014-FASE-N3 | L | pending |
| TUT-038 | Integrar con Doc Processor (003): reutilizar scan_md y parse_frontmatter | doc-integration | TUT-031, 003-FASE-1 | M | pending |
| TUT-039 | Agregar comando `recpl ejecuta <tutorial>` a recpl.sh | recpl-integration | TUT-031 | M | pending |
| TUT-040 | Integrar scaffolding: cuando un paso coincide con RECPL, delegar | scaffold-integration | TUT-031 | L | pending |
| TUT-041 | Tests unitarios: step_extractor (10 casos con diferentes formatos de .md) | testing | TUT-003 | L | pending |
| TUT-042 | Tests unitarios: step_classifier (15 casos, todos los tipos de accion) | testing | TUT-005 | L | pending |
| TUT-043 | Tests unitarios: step_runner (10 casos, un tipo por test) | testing | TUT-016 | L | pending |
| TUT-044 | Tests unitarios: error_handler (10 casos, diferentes tipos de error) | testing | TUT-022 | M | pending |
| TUT-045 | Tests unitarios: state_manager (5 casos, ciclo de vida completo) | testing | TUT-013 | M | pending |
| TUT-046 | Tests de integracion: tutorial completo de 3 pasos (mock) | testing | TUT-031 | L | pending |
| TUT-047 | Tests de integracion: fallo y recuperacion en paso intermedio | testing | TUT-031 | L | pending |
| TUT-048 | Tests de integracion: dry-run vs ejecucion real (mismo output) | testing | TUT-031 | L | pending |
| TUT-049 | Validar con `bash -n` y `shellcheck` todos los scripts nuevos | quality | TUT-031 | S | pending |
| TUT-050 | Documentar API del Ejecutor de Tutoriales | docs | TUT-031 | M | pending |
| TUT-051 | Documentar formato esperado de tutoriales .md | docs | TUT-031 | M | pending |
| TUT-052 | Actualizar AGENTS.md con estado del proyecto | docs | TUT-050 | S | pending |

---

## 7. Fases de Implementacion

| Fase | Nombre | Descripcion | Tareas | Depende de | Duracion est. |
|------|--------|-------------|--------|------------|---------------|
| **FASE-T1** | Parseo de Tutoriales | Extractor de pasos, clasificador, DAG de dependencias | TUT-001 al TUT-012 | — | 5-7 dias |
| **FASE-T2** | Ejecucion y Estado | State manager, step runner para todos los tipos | TUT-013 al TUT-021 | FASE-T1 | 5-7 dias |
| **FASE-T3** | Robustez | Error handler, rollback manager | TUT-022 al TUT-028 | FASE-T2 | 3-4 dias |
| **FASE-T4** | Discovery y Orquestacion | Tutorial discovery, orquestador, modos de ejecucion | TUT-029 al TUT-036 | FASE-T3 | 4-5 dias |
| **FASE-T5** | Integracion | NLP, Doc Processor, RECPL, scaffolding | TUT-037 al TUT-040 | FASE-T4, 014-FASE-N3, 003-FASE-1 | 4-5 dias |
| **FASE-T6** | Tests y Hardening | Tests unitarios, integracion, shellcheck | TUT-041 al TUT-049 | FASE-T5 | 4-5 dias |
| **FASE-T7** | Documentacion | API, formato esperado, AGENTS.md | TUT-050 al TUT-052 | FASE-T6 | 1-2 dias |

### Grafo de Dependencias

```
FASE-T1 (Parseo)
  │
  ▼
FASE-T2 (Ejecucion y Estado)
  │
  ▼
FASE-T3 (Robustez)
  │
  ▼
FASE-T4 (Discovery y Orquestacion)
  │
  ├──────────────────────────┐
  ▼                          ▼
FASE-T5a (NLP 014)     FASE-T5b (Doc 003)
  │                          │
  └──────────┬───────────────┘
             ▼
        FASE-T5c (Integracion RECPL)
             │
             ▼
        FASE-T6 (Tests)
             │
             ▼
        FASE-T7 (Docs)
```

### Relacion con Fases Externas

| Fase externa | Relacion | Tareas |
|--------------|----------|--------|
| 003-FASE-1 (masterindex) | Reutiliza scan_md.sh, parse_frontmatter.sh para leer tutoriales | TUT-038 |
| 014-FASE-N1 (Intent Classifier) | Anade nuevas intenciones: RUN_TUTORIAL, NEXT_STEP, etc. | TUT-037 |
| 014-FASE-N3 (Dialog Manager) | Dialog Manager gestiona interaccion durante ejecucion | TUT-037 |
| 014-FASE-N5 (Integracion pipeline) | enriched_input incluye tutorial_id y step context | TUT-037 |
| 013-FASE-C6 (Modo Full) | Step runner deleg a recpl-core para acciones SCAFFOLD | TUT-040 |
| 011-FASE-E1 (Stack Registry) | Tutorial discovery filtra por techs del registry | TUT-029 |

---

## 8. Estructura de Directorios (Nuevos Archivos)

```
compiler-bot/
├── tutorial/                          # NUEVO: Ejecutor de Tutoriales
│   ├── tutorial_orchestrator.sh       # Orquestador principal
│   ├── step_extractor.sh              # Extrae pasos de .md
│   ├── step_classifier.sh             # Clasifica acciones
│   ├── dependency_builder.sh          # DAG de dependencias
│   ├── state_manager.sh               # Estado persistente
│   ├── step_runner.sh                 # Ejecuta pasos
│   ├── error_handler.sh               # Manejo de errores
│   ├── rollback_manager.sh            # Rollback de cambios
│   ├── tutorial_discovery.sh          # Busca tutoriales
│   ├── lib/
│   │   ├── patterns_tutorial.sh       # Patrones de deteccion
│   │   ├── file_utils.sh              # Utilidades de archivos
│   │   └── verify_utils.sh            # Verificaciones post-paso
│   └── tests/
│       ├── test_step_extractor.sh
│       ├── test_step_classifier.sh
│       ├── test_step_runner.sh
│       ├── test_error_handler.sh
│       ├── test_state_manager.sh
│       ├── test_orchestrator.sh
│       ├── fixtures/                  # Tutoriales de prueba
│       │   ├── tutorial_simple.md     # 3 pasos, solo shell
│       │   ├── tutorial_mixed.md      # shell + file_edit + scaffold
│       │   └── tutorial_graphql.md    # Copia de misc/tutorial.md
│       └── run_tutorial_tests.sh
├── nlp/                               # Existente (014)
│   └── ... (nuevas intenciones)
├── recpl.sh                           # MODIFICADO: nuevo comando "ejecuta"
└── doc/                               # Existente (003)
    └── lib/                           # Reutilizado
        ├── scan_md.sh
        └── parse_yaml.sh
```

---

## 9. Stack Tecnologico

| Tecnologia | Uso | Version | Nota |
|------------|-----|---------|------|
| Shell POSIX | Todos los scripts del ejecutor | Cualquier Unix | Misma convencion que proyecto |
| awk | Procesamiento de patrones, extraccion de bloques de codigo | nawk/gawk | Sin cambios |
| sed | Edicion de archivos (FILE_EDIT), insercion de lineas | POSIX sed | Refuerza seguridad: backup .orig |
| RECPL_STATE_DIR | Persistencia de estado de tutoriales | — | Misma variable que semantic.sh y 014 |
| `timeout` (coreutils) | Timeout en ejecucion de comandos shell | GNU coreutils | Alternativa: `timelimit` |
| `diff` | Verificacion de cambios en archivos | POSIX diff | Para validar ediciones |
| `bash -n` | Validacion de sintaxis | Bash 3+ | Convocion existente |
| shellcheck | Analisis estatico | 0.7+ | Convocion existente |

**Dependencias opcionales:**

| Herramienta | Uso | Si no esta disponible |
|-------------|-----|----------------------|
| `inotifywait` | Detectar cambios en archivos durante ejecucion | Modo manual |
| `jq` | Procesar JSON de estado | awk + grep (fallback) |
| `timeout` | Limitar tiempo de ejecucion de comandos | `ulimit -t` o manual |

---

## 10. Formato Esperado de Tutoriales .md

Para que un tutorial sea procesable por el Ejecutor, debe seguir estas reglas:

### 10.1 Reglas de Formato

1. **Frontmatter YAML obligatorio** con `title`, `description`, `tags`
2. **Titulo principal** (`#`) al inicio
3. **Secciones** con `##`: cada `## Paso N:` es un paso ejecutable
4. **Bloques de codigo** con lenguaje especificado: ` ```sh `, ` ```python `, etc.
5. **Instrucciones textuales** en lenguaje natural ANTES del bloque de codigo
6. **Paso 1** debe incluir prerequisitos/instalacion si aplica
7. **Verificacion** opcional al final de cada paso

### 10.2 Ejemplo Minimo

```markdown
---
title: "Ejemplo minimo"
description: "Tutorial de 3 pasos para demostrar el formato"
tags: [ejemplo, demo]
---

# Ejemplo Minimo

## Requisitos previos

- Python 3

## Paso 1: Instalar dependencias

Instala los paquetes necesarios:

```sh
pip install requests
```

## Paso 2: Crear script

Crea un archivo `app.py`:

```python
import requests
print("OK")
```

## Paso 3: Ejecutar

Ejecuta el script:

```sh
python app.py
```

Verifica que imprime "OK".
```

### 10.3 Reglas para Acciones FILE_EDIT

Para que el parser detecte correctamente ediciones de archivos:

1. **Indicar el archivo**: "abra el archivo `path/to/file.py`"
2. **Indicar la accion**: "anada la linea", "reemplace el contenido", "anada al final"
3. **El bloque de codigo** debe contener SOLO el fragmento a anadir/reemplazar

Ejemplo:
```markdown
Abra `settings.py` y añada al final:

```python
GRAPHENE = {
    'SCHEMA': 'shorty.schema.schema',
}
```
```

### 10.4 Reglas para Acciones SCAFFOLD

Si el paso contiene texto que coincide con el dominio de RECPL:

```markdown
## Paso 4: Crear modulo de usuarios

Crea un modulo para gestion de usuarios en Django:

```sh
# Esto se ejecuta como shell command directamente
python manage.py startapp users
```

O, si quieres que RECPL lo interprete:

Crea un modulo usuarios en Django
```

---

## 11. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| Tutorial mal formateado (no sigue reglas 10.1-10.4) | Alto (no se puede ejecutar) | Media | Modo VALIDATE detecta problemas de formato antes de ejecutar |
| Comando shell destructivo en tutorial | Muy alto (rm -rf, drop table) | Baja | Lista negra de comandos peligrosos; modo dry-run obligatorio antes de auto |
| Tutorial desactualizado (versiones de paquetes) | Medio (pasos fallan) | Alta | Detectar versiones instaladas y sugerir adaptaciones |
| Dependencia externa no disponible (pip, npm) | Medio (paso falla) | Media | Verificar prerequisitos al inicio; error_handler reintenta con mensaje claro |
| Estado corrupto por crash | Alto (pierde progreso) | Baja | Backup periodico del estado; verificacion de integridad al reanudar |
| Edicion de archivo falla por cambio de estructura | Medio (diff no matchea) | Media | Mostrar diff actual y pedir intervencion manual |
| Tiempo de ejecucion excesivo (tutorial largo) | Bajo (usuario espera) | Alta | Timeout por paso; modo resume para continuar despues |
| Conflicto con archivos existentes del usuario | Medio | Media | Preguntar antes de sobrescribir; backup .orig siempre |
| Tutorial en idioma no soportado | Medio (patrones no matchean) | Baja | Detectar idioma del frontmatter; patrones en ingles y español |

---

## 12. Metricas de Exito

| KPI | Target | Como se mide |
|-----|--------|-------------|
| Precision de extraccion de pasos | > 95% | Tests con 10 tutoriales etiquetados manualmente |
| Precision de clasificacion de acciones | > 90% | Tests con todos los tipos de accion |
| Tasa de exito en modo auto | > 80% de tutoriales completan sin intervencion | Logging de ejecuciones |
| Tiempo medio por paso | < 2x el tiempo manual estimado | Comparar con ejecucion manual del mismo tutorial |
| Tasa de recuperacion de errores | > 70% se recuperan sin abortar | Logging de error_handler |
| Cobertura de rollback | 100% de FILE_CREATE y FILE_EDIT | Tests de rollback |
| Tutoriales detectables | 100% de los .md con frontmatter en el proyecto | Tutorial discovery scan |
| Tests pasando | 100% (50+ tests) | run_tutorial_tests.sh |
| shellcheck | 0 warnings | shellcheck tutorial/*.sh |

---

## 13. Casos de Uso

| ID | Descripcion | Input | Output esperado |
|----|-------------|-------|-----------------|
| CU-T01 | Ejecutar tutorial completo en auto | "ejecuta misc/tutorial.md --auto" | 8/8 pasos completados, proyecto creado |
| CU-T02 | Ejecutar paso a paso interactivo | "ejecuta tutorial.md" | Pregunta antes de cada paso |
| CU-T03 | Ver progreso | "en que paso voy?" | "Paso 3/8: Crear consultas (completado: 2/8)" |
| CU-T04 | Saltar paso | "salta el paso de instalacion" | Paso marcado como skipped, continua en paso 2 |
| CU-T05 | Reintentar paso fallido | "reintenta paso 5" | Re-ejecuta paso 5, si falla de nuevo pregunta |
| CU-T06 | Reanudar tutorial | "continua tutorial" | Carga estado, continua desde ultimo paso exitoso |
| CU-T07 | Dry-run | "ensaya tutorial.md" | Muestra que haria sin ejecutar |
| CU-T08 | Validar tutorial | "verifica tutorial.md" | Checkea prerequisitos y formato |
| CU-T09 | Buscar tutoriales | "que tutoriales hay?" | Lista tutoriales disponibles con tags y pasos |
| CU-T10 | Tutorial con scaffolding | Paso que dice "crea modulo X" | RECPL interpreta y ejecuta scaffold |
| CU-T11 | Tutorial con error de red | Paso con `pip install` falla por timeout | Reintenta hasta 3 veces |
| CU-T12 | Tutorial con edicion de archivo | "anade linea a settings.py" | Edita archivo, backup .orig, verifica cambio |
| CU-T13 | Multi-tutorial | "ejecuta paso 3 del tutorial de auth" | Busca tutorial "auth", ejecuta solo paso 3 |
| CU-T14 | Abortar y limpiar | "cancela y limpia" | Detiene ejecucion, pregunta si revertir cambios |

---

## 14. Referencias

- `003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md` — Procesador de documentos: scan, parse, index
- `004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md` — Especificacion del procesador de documentos
- `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` — Multi-tech-stack + UI web
- `012_PROP_DEV_COMPILER_BOT_FLOW_REFINE_1_0_DRAFT.md` — Flujo de datos y ciclo de refinamiento
- `013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` — Nucleo C nativo (recpl-core)
- `014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md` — Capa NLP e Intent
- `015_GUIDE_DEV_C_STYLE_1_0_DRAFT.md` — Guia de estilo C
- `016_PLAN_DEV_C_CORE_EXECUTION_1_0_DRAFT.md` — Plan de ejecucion del C core
- `017_GUIDE_DEV_C_CORE_LEARNING_1_0_DRAFT.md` — Guia de aprendizaje de C
- `000_DEV_GUIDE_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
- `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md` — Convencion de documentacion
- `misc/tutorial.md` — Tutorial de GraphQL con Django y Graphene (tutorial de referencia)
