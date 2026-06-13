---
id: agent_003
area: agent
type: AGENTS
module: orquestador3-generador
version: 1.0
status: DRAFT
tags:
  - prompt-generator
  - delegation
  - compiler-bot
  - recpl
summary: "Generador de prompts. Recibe el COMO de Orquestador1 (que incluye DONDE, QUE, CUANDO, acciones y verificacion) y produce un prompt completo y ejecutable para que Orquestador2 implemente la tarea."
---

# Orquestador3: Generador de Prompt

## Proposito

Recibe las instrucciones tecnicas de Orquestador1 y genera un prompt completo
y estructurado que Orquestador2 pueda ejecutar directamente.

## Input

Desde Orquestador1 recibe:

```
TAREA: <ID>
DONDE: <ruta del archivo a crear/modificar>
QUE: <descripcion de la tarea>
DEPENDE_DE: <IDs de tareas previas>
ESFUERZO: <S|M|L>
ACCIONES: <lista de acciones desde 007>
VERIFICACION: <checklist desde 007>
ERRORES_COMUNES: <lista desde 007>
COMPONENTE: <lexer | parser | semantic | ir | tracer | synthesis | preproc | recpl>
```

## Output

Prompt estructurado listo para ejecutar por Orquestador2:

```
## Tarea: <ID> — <descripcion>

### Contexto
Proyecto: RECPL Compiler Bot (@tienda/api)
Componente: <nombre>
Ruta: <ruta>
Depende de: <IDs>

### Instrucciones

<acciones detalladas>

### Formato de salida esperado

<formato que debe producir el script>

### Verificacion

<checklist de criterios>

### Errores comunes a evitar

<lista de errores>

### Reglas de estilo

- No usar `set -e`
- No usar `eval`
- Variables con dobles comillas
- 4 espacios de indentacion
- Funciones snake_case con ()
- Constantes SCREAMING_SNAKE_CASE
- Pasar `bash -n` y `shellcheck`

### Referencias

- docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md
- docs/007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md
```

## Proceso

### Paso 1: Recibir payload de Orquestador1

Extraer: TAREA, DONDE, QUE, ACCIONES, VERIFICACION, ERRORES_COMUNES, COMPONENTE.

### Paso 2: Resolver referencias cruzadas

Para cada accion, buscar en `docs/007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` la
seccion correspondiente al COMPONENTE y extraer:
- Algoritmo (pseudocodigo)
- Formato de datos de entrada/salida
- Ejemplos
- Errores comunes

### Paso 3: Generar prompt

Armar el prompt siguiendo la plantilla de Output.
Cada prompt debe ser autocontenido (no requerir leer otros documentos).

### Paso 4: Devolver prompt a Orquestador1

Orquestador1 puede entonces pasar el prompt a Orquestador2 para su ejecucion.

## Template de generacion

```
## Tarea: {ID} — {QUE}

### Contexto
Proyecto: RECPL Compiler Bot (@tienda/api)
Componente: {COMPONENTE}
Ruta: {DONDE}
Depende de: {DEPENDE_DE}
Esfuerzo: {ESFUERZO}

### Instrucciones

{ACCIONES formateadas como lista ordenada}

### Especificacion del componente

{Extracto de docs/006 seccion 5 correspondiente al componente}

### Formato de entrada

{tipo de datos que recibe este componente}

### Formato de salida

{tipo de datos que produce este componente}

### Verificacion

{VERIFICACION formateada como checklist}

### Errores comunes

{ERRORES_COMUNES formateados como lista}

### Reglas de estilo

- No usar `set -e`
- No usar `eval`
- Variables con dobles comillas
- 4 espacios de indentacion
- Funciones snake_case con ()
- Constantes SCREAMING_SNAKE_CASE
- Pasar `bash -n` y `shellcheck`
```

## Referencias

- `docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` secciones 5 (especificacion de componentes)
- `docs/007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` — acciones, verificacion, errores
- `docs/008_PRM_BUILD_AGENT_1_0_DRAFT.md` — template de prompt
- `docs/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — reglas de estilo shell
