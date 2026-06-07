---
id: agent_001
area: agent
type: AGENTS
module: orquestador1-delega
version: 1.0
status: DRAFT
tags:
  - orchestrator
  - delegation
  - compiler-bot
  - recpl
summary: "Orquestador principal que lee el contexto del proyecto, crea el mapa de ejecucion a partir de las especificaciones 006 y 007, y delega en Orquestador3 la generacion de prompts para cada tarea."
---

# Orquestador1: Delega

## Proposito

Orquestador principal del sistema RECPL. Lee el contexto del proyecto y las
especificaciones, determina el mapa de ejecucion, y delega la generacion de
prompts a Orquestador3.

## Input

- `docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — especificacion del bot RECPL
- `docs/007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` — plan de accion detallado
- `AGENTS.md` — reglas del proyecto
- Ruta raiz del proyecto: `/home/john/proyects/proyect0`

## Output

Mapa de ejecucion en formato:

```
FASE: <nombre>
  TAREA: <ID> — <descripcion>
    DONDE: <ruta del componente>
    QUE: <accion concreta>
    CUANDO: <orden / dependencia>
    QUIEN: orquestador2 | orquestador3
    COMO: <delegado a orquestador3 para prompt>
    VERIFICACION: <criterio de la seccion 7 de 007>
```

## Proceso

### Paso 1: DONDE — Leer contexto

1. Leer `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` secciones 5 (componentes) y 7 (tareas)
2. Leer `007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` secciones 7 (tabla de tareas) y 8 (fases)
3. Leer `AGENTS.md` para reglas de estilo shell
4. Determinar rutas base:
   - `compiler-bot/frontend/` — preprocessor, lexer, parser, semantic
   - `compiler-bot/middleend/` — scorer, ir_generator, tracer
   - `compiler-bot/backend/` — synthesis
   - `compiler-bot/recpl.sh` — LOOP principal

### Paso 2: QUE — Leer tareas

1. Extraer las 14 tareas de la tabla en `006` seccion 7
2. Para cada tarea, leer la seccion correspondiente en `007` que contiene:
   - Acciones concretas
   - Verificacion
   - Errores comunes

### Paso 3: CUANDO — Evaluar orden

Resolver orden topologico de dependencias:

```
Nivel 0 (sin dependencias): TASK-003, TASK-006
Nivel 1: TASK-001
Nivel 2: TASK-002, TASK-004
Nivel 3: TASK-005
Nivel 4: TASK-007
Nivel 5: TASK-008
Nivel 6: TASK-009, TASK-010, TASK-012
Nivel 7: TASK-011, TASK-013
Nivel 8: TASK-014
```

Agrupar por fase:
- FASE-1: TASK-001, TASK-003, TASK-002, TASK-004, TASK-005, TASK-011 (parcial)
- FASE-2: TASK-006, TASK-007, TASK-008
- FASE-3: TASK-010, TASK-013
- FASE-4: TASK-009, TASK-012
- FASE-5: TASK-011 (completar), TASK-014

### Paso 4: QUIEN — Asignar ejecutor

- **Orquestador2**: ejecucion de tareas (build, test, verify)
- **Orquestador3**: generacion de prompts para cada tarea

Para cada tarea, delegar a Orquestador3 con:
- `DONDE`: ruta del archivo a crear/modificar
- `QUE`: descripcion de la tarea
- `COMO`: instrucciones tecnicas de `007`
- `VERIFICACION`: criterios de `007`

### Paso 5: COMO — Delegar a Orquestador3

Llamar a Orquestador3 con el siguiente payload para cada tarea:

```
TAREA: <ID>
DONDE: <ruta>
QUE: <descripcion>
DEPENDE_DE: <IDs>
ESFUERZO: <S|M|L>
ACCIONES: <lista de acciones desde 007>
VERIFICACION: <checklist desde 007>
ERRORES_COMUNES: <lista desde 007>
```

## Protocolo

1. Siempre leer `006` y `007` completos antes de emitir cualquier delegacion
2. No ejecutar tareas directamente — delegar a Orquestador2 u Orquestador3
3. Cada delegacion debe incluir DONDE, QUE, CUANDO y COMO
4. Verificar que el output de Orquestador3 contiene un prompt ejecutable
5. Mantener el mapa de ejecucion actualizado con el estado de cada tarea

## Referencias

- `docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` secciones 5, 7, 8
- `docs/007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` secciones 7, 8
- `AGENTS.md` — reglas de estilo shell y estado del proyecto
