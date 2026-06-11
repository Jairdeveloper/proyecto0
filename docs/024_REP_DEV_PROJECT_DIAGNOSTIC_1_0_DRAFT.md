---
id: 024
area: dev
type: REP
module: project-diagnostic
version: 1.0
status: DRAFT
tags:
  - report
  - diagnostic
  - analysis
  - risks
  - roadmap
  - strategy
summary: "Diagnostico integral del proyecto @Proyecto0 basado exclusivamente en los archivos existentes en el directorio de trabajo. Identifica el objetivo implicito del proyecto, objetivos alcanzados, debilidades, riesgos de abandono, y genera un plan de accion pragmatico a corto, medio y largo plazo para asegurar que el proyecto llegue a produccion."
keywords:
  - diagnostico
  - proyecto
  - riesgos
  - debilidades
  - plan-de-accion
  - estrategia
  - sostenibilidad
  - produccion
  - recpl
  - compiler-bot
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Creacion del diagnostico integral del proyecto basado en los archivos existentes
---

# Diagnostico Integral de @Proyecto0

> **Fecha:** 2026-06-11
> **Base del analisis:** Unicamente los archivos existentes en `/home/john/proyects/proyect0`
> **Metodo:** Lo que el proyecto ES se deduce de lo que contiene, no de lo que dice querer ser.

---

## 0. Objetivo Implicito del Proyecto

El objetivo real del proyecto no esta declarado en un unico documento.
Se deduce de la suma de archivos existentes:

| Evidencia | Que indica |
|-----------|------------|
| `compiler-bot/` con 9 scripts funcionales | El nucleo del proyecto es el pipeline RECPL |
| `templates/` (module-nestjs, entity-nestjs, module-prisma) | El output del pipeline es codigo NestJS/Prisma |
| `recpl.sh` con modo interactivo y batch | El producto es un bot shell, no una API |
| `tests/run_tests.sh` con 47 tests | El pipeline esta validado y funciona |
| `README.md` titulo "RECPL Compiler Bot" | La identidad del proyecto es el bot |
| Ausencia de `src/`, `apps/`, `package.json` | No hay codigo NestJS escrito a mano |

**Objetivo implicito del proyecto:**

> Construir un **RECPL Compiler Bot** — un compilador de lenguaje natural a codigo.
> Toma instrucciones en espanol ("crea un modulo de pagos en NestJS") y genera
> scaffolding de modulos NestJS, entidades y modelos Prisma.
>
> El pipeline compilador (preprocess → lexer → parser → semantic → IR → synthesis)
> es el producto. NestJS/Prisma es el **formato de salida**, no un proyecto separado.

Esto corrige el analisis previo (doc 023) que asumia que el objetivo era
"construir una API NestJS". La API NestJS es lo que el bot **genera**,
no lo que se construye manualmente.

---

## 1. Objetivos Alcanzados

### 1.1 Pipeline RECPL (COMPLETO)

| Componente | Archivo | Lineas | Funcionalidad |
|-----------|---------|--------|--------------|
| Preprocesador | `frontend/preprocessor.sh` | 94 | Normaliza input: lowercase, colapsa puntuacion, segmenta oraciones |
| Lexer (DFA) | `frontend/lexer.sh` | 165 | Tokeniza con maximal munch. 24 tipos de token |
| Parser (LL1) | `frontend/parser.sh` | 340 | Recursive descent. Grammar: comando → accion modulo_espec opcional_tech |
| Semantico | `frontend/semantic.sh` | 245 | Tabla de simbolos persistente, type checking |
| IR Generator | `middleend/ir_generator.sh` | 183 | AST validado → IR canonico JSON |
| Synthesis | `backend/synthesis.sh` | 199 | IR → respuesta JSON del bot |
| Scaffold | `backend/scaffold.sh` | 91 | Templates → archivos en disco |
| LOOP principal | `recpl.sh` | 197 | Modo interactivo + batch, estado persistente |

**Pipeline completo funcional y testeado.**

### 1.2 Tests (COMPLETO)

- 47 tests automatizados en `tests/run_tests.sh`
- Cobertura: sintaxis, preprocesador, lexer, parser, pipeline, scaffolding, loop batch, errores, persistencia

### 1.3 Templates de generacion de codigo (COMPLETO)

| Template | Archivos | Placeholders |
|----------|----------|-------------|
| Modulo NestJS | controller, module, service | `__NAME__`, `__LOWERNAME__` |
| Entidad NestJS | entity class | `__NAME__`, `__LOWERNAME__` |
| Modelo Prisma | schema `.prisma` | `__LOWERNAME__` |

### 1.4 Infraestructura de agente (COMPLETO)

- 3 orquestadores OpenCode en `.opencode/agents/`
- Pipeline de delegacion: Orq1 (mapa) → Orq3 (prompt) → Orq2 (ejecucion)

### 1.5 Documentacion del pipeline (COMPLETO)

- `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — Propuesta y especificacion
- `007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` — Plan de accion detallado
- `009_GUIDE_DEV_COMPILER_BOT_IMPL_REPORT_1_0_DRAFT.md` — Reporte de implementacion
- `010_GUIDE_DEV_COMPILER_BOT_RUNBOOK_1_0_DRAFT.md` — Runbook operativo

### 1.6 Guias de estilo (COMPLETO)

- `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Convenciones shell
- `015_GUIDE_DEV_C_STYLE_1_0_DRAFT.md` — Convenciones C

### 1.7 Experimentos laterales (EN CURSO / PARCIAL)

| Componente | Estado | Archivos |
|-----------|--------|----------|
| Core C (recpl-core) | Compila pero stubs sin implementar | 6 .c + 4 .h + Makefile, 733 lineas |
| NLP / Intent | Propuesta documentada sin implementacion | `014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md` |
| Tutorial executor | Propuesta documentada sin implementacion | `018_PROP_DEV_COMPILER_BOT_TUTORIAL_EXEC_1_0_DRAFT.md` |

---

## 2. Debilidades Encontradas

### 2.1 Estructurales

| Debilidad | Impacto | Donde |
|-----------|---------|-------|
| **Sin commit de todo el proyecto** | Solo 2 commits parciales. Archivos sueltos sin seguimiento | `git status` muestra 7 modified + 19 untracked |
| **Codigo objeto compilado en el repo** | (`*.o`, `recpl-core`) inflan el repo sin necesidad | `compiler-bot/core/*.o`, `recpl-core` |
| **Sin `.gitignore` para artefactos de compilacion** | `.o` y binarios trackeables | `compiler-bot/core/` |
| **Sin `package.json` para el output NestJS** | No hay forma de validar que el codigo generado compile | No existe en raiz |
| **Sin CI/CD** | 47 tests solo se ejecutan manualmente | — |
| **Docs sin frontmatter YAML** | Violan la convencion declarada en AGENTS.md | `001_DOC_*`, `002_DOC_*`, `005_SPEC_*` |
| **3 doc IDs duplicados o fuera de secuencia** | `008` tiene id `018` en frontmatter; inconsistencia | `008_PRM_BUILD_AGENT_1_0_DRAFT.md` |

### 2.2 Tecnicas del Pipeline

| Debilidad | Impacto |
|-----------|---------|
| **Parser shell sin recuperacion de errores** | Un token inesperado rompe el pipeline completo |
| **JSON pasa como strings sin validacion** | Errores de formato silenciosos entre etapas |
| **Sin cache de IR** | Cada invocacion reprocesa todo desde cero |
| **Estado en `/tmp/`** | Se pierde al reiniciar el sistema |
| **Solo 2 techos soportados** | NestJS y Prisma. El lexer reconoce mas techs (Express, React, etc.) pero no hay templates |
| **Sin validacion de templates generados** | `scaffold.sh` copia archivos pero no verifica que el resultado compile |

### 2.3 De Proceso

| Debilidad | Impacto |
|-----------|---------|
| **Proporcion docs/codigo desbalanceada** | ~15,600 lineas de documentacion vs ~2,500 de codigo (6:1) |
| **Experimentos laterales sin decision tomada** | C core, NLP, tutorial executor, FrameMaker — consumen atencion sin avanzar el objetivo principal |
| **Sin roadmap publicado** | No hay criterio para decidir que se hace ahora y que despues |
| **Sin hitos medibles** | No se puede responder "el proyecto esta al N% de completarse" |

---

## 3. Mejoras Concretas de Implementacion y Estructura

### 3.1 Repositorio

```
1. git add . && git commit -m "feat: RECPL pipeline complete with 47 tests"
2. Agregar al .gitignore:
   - compiler-bot/core/*.o
   - compiler-bot/core/recpl-core
   - modules/
3. Crear package.json raiz con scripts:
   - "test": "cd compiler-bot && bash tests/run_tests.sh"
   - "start": "bash compiler-bot/recpl.sh"
4. Agregar .editorconfig
5. Setup GitHub Actions para ejecutar tests en cada push
```

### 3.2 Estructura propuesta

```
proyect0/
├── compiler-bot/              # Pipeline RECPL (nucleo del proyecto)
│   ├── frontend/
│   ├── middleend/
│   ├── backend/
│   ├── templates/
│   └── tests/
├── docs/                      # Documentacion
├── scripts/                   # Utilidades (masterindex.sh, spellscheck.sh)
├── .github/workflows/         # CI/CD
├── .editorconfig
├── .gitignore
├── package.json               # Scripts de orquestacion
├── Makefile                   # Alternativa portable
└── README.md
```

### 3.3 Mejoras al pipeline

| Mejora | Por que | Esfuerzo |
|--------|---------|----------|
| Validacion de JSON entre etapas | Evita errores silenciosos | 1 dia |
| Cache de IR en archivo | Evita reprocesar entrada identica | 0.5 dia |
| Mas templates (Express, FastAPI, etc.) | El lexer ya reconoce los tokens | 2-3 dias |
| Modo servidor (HTTP) | Permite integracion con web/IDE | 3-5 dias |
| Validacion de templates compilables | `npm init` + `npx tsc --noEmit` en el output | 1 dia |
| Estado persistente en archivo del proyecto | No depender de `/tmp/` | 0.5 dia |

---

## 4. Riesgos Tecnicos que Podrian Hacer que el Proyecto se Abandone

### Riesgo #1: Paralisis por expansion lateral (ALTO)

**Sintoma:** Cada semana aparece un nuevo tema (C core, NLP, FrameMaker,
tutorial executor) que desvia atencion del pipeline base.

**Consecuencia:** El pipeline RECPL queda functional pero incompleto
(faltan templates, falta cache, falta validacion) mientras se invierte
esfuerzo en areas que no generan valor inmediato.

**Mitigacion:** Congelar todo experimento que no sea el pipeline RECPL
hasta que el bot pueda generar codigo NestJS compilable y testeable.

### Riesgo #2: El bot genera codigo que nadie valida (ALTO)

**Sintoma:** `scaffold.sh` escribe archivos en `modules/` pero nadie
ejecuta `npm install` ni `npx tsc` para verificar que el codigo generado
es correcto.

**Consecuencia:** El pipeline produce output que no se sabe si funciona.

**Mitigacion:** Agregar paso de validacion post-scaffold que compile el
codigo generado y ejecute tests basicos.

### Riesgo #3: Dependencia total de OpenCode (MEDIO)

**Sintoma:** Sin el agente AI, nadie sabe como continuar el proyecto.

**Consecuencia:** Si OpenCode deja de estar disponible, el proyecto se
congela.

**Mitigacion:** Mantener scripts ejecutables sin OpenCode. La
documentacion debe ser suficiente para que un humano continue.

### Riesgo #4: Proporcion docs/codigo insostenible (MEDIO)

**Sintoma:** 6 lineas de documentacion por cada linea de codigo.

**Consecuencia:** El mantenimiento de docs consume mas tiempo que la
implementacion. El proyecto se siente "pesado" y se abandona.

**Mitigacion:** Regla: no escribir un nuevo doc sin haber implementado
el anterior. La documentacion se actualiza DESPUES del codigo.

### Riesgo #5: Sin commit completo (ALTO)

**Sintoma:** Archivos sueltos, 19 untracked, riesgo de perdida.

**Consecuencia:** Un `rm -rf` accidental o un cambio de disco destruye
semanas de trabajo.

**Mitigacion:** Commitear todo el proyecto HOY.

---

## 5. Estrategia para Mantener el Proyecto Sostenible

### 5.1 Principio rector

> El proyecto ES el pipeline RECPL. Todo lo que no mejore el pipeline
> es ruido hasta nuevo aviso.

### 5.2 Reglas de operacion

| Regla | Explicacion |
|-------|-------------|
| **Un solo frente activo** | No trabajar en C core + NLP + tutorial executor simultaneamente |
| **Commit diario** | Al final de cada sesion, todo el trabajo debe estar commiteado |
| **Tests verdes siempre** | `bash tests/run_tests.sh` debe pasar antes de cada commit |
| **Docs post-codigo** | Primero se implementa, luego se documenta lo implementado |
| **Validacion del output** | Todo codigo generado debe poder compilarse |

### 5.3 Que preservar

| Componente | Por que |
|-----------|---------|
| Pipeline RECPL shell (9 scripts) | Es unico, funcional, y resuelve un problema real |
| 47 tests | Base de regresion para cualquier cambio |
| Templates NestJS/Prisma | Formato de salida del pipeline |
| Guias de estilo (shell, C) | Mantienen consistencia |
| Agentes OpenCode | Aceleran desarrollo si se usan como herramienta |

### 5.4 Que congelar o archivar

| Tema | Accion |
|------|--------|
| Core C (`compiler-bot/core/`) | Mover a rama `experiment/c-core` |
| NLP intent (`014_*`) | Mantener como referencia, no implementar hasta que el pipeline base este completo |
| Tutorial executor (`018_*`) | Idem |
| FrameMaker (`019_*`, `020_*`, `021_*`) | Mover a rama `archive/framemaker` |
| Docs sin frontmatter (`001_*`, `002_*`, `005_*`) | Agregar frontmatter cuando se editen por otras razones |

---

## 6. Plan de Accion Pragmatico

### Corto Plazo (Semana 1)

| # | Accion | Duracion | Dependencia |
|---|--------|----------|-------------|
| 1 | `git add . && git commit -m "feat: RECPL pipeline + 47 tests + docs"` | 5 min | — |
| 2 | Agregar `*.o`, `recpl-core` a `.gitignore` | 2 min | 1 |
| 3 | Mover `core/` a rama `experiment/c-core` | 5 min | 1 |
| 4 | Crear `package.json` raiz con script `test` | 5 min | 1 |
| 5 | Crear `.github/workflows/test.yml` (GitHub Actions) | 20 min | 4 |
| 6 | Agregar validacion post-scaffold al pipeline | 1 dia | 1 |
| 7 | Hacer commit del CI funcionando | 5 min | 5,6 |

**Resultado:** Repositorio limpio, CI verde, pipeline validado.

### Mediano Plazo (Semanas 2-4)

| # | Accion | Duracion |
|---|--------|----------|
| 8 | Agregar cache de IR (`ir_cache.sh`) | 0.5 dia |
| 9 | Agregar validacion de JSON entre etapas del pipeline | 1 dia |
| 10 | Templates para mas techos (Express, FastAPI) | 2-3 dias |
| 11 | Modo servidor HTTP basico para RECPL | 3-5 dias |
| 12 | Tests de integracion: pipeline completo → codigo compilable | 1 dia |
| 13 | Documentar lo implementado (actualizar README y runbook) | 1 dia |

**Resultado:** Pipeline RECPL robusto, con cache, mas techos soportados,
y modo servidor.

### Largo Plazo (Meses 2-3)

| # | Accion |
|---|--------|
| 14 | Sistema de plugins para agregar nuevos lenguajes/techos |
| 15 | Interfaz web para el bot (REST + UI basica) |
| 16 | NLP avanzado: clasificador de intenciones (basado en `014_*`) |
| 17 | Evaluar si el C core mejora el rendimiento (benchmark) |
| 18 | Despliegue del bot como servicio |

---

## 7. Que Haria para Asegurar que Este Proyecto Llegue a Produccion y No Muera a Mitad del Desarrollo

### 7.1 La meta es tener un bot que genere codigo que compile

Produccion para este proyecto significa:

> Un usuario escribe "crea un modulo de pagos en NestJS" y recibe
> archivos `.ts` que compilan y pasan tests basicos.

No significa "tener una API NestJS en la nube". El producto es el bot.

### 7.2 Estrategia de supervivencia

```
Reglas para no abandonar:

1. HOY: git commit. No hay excusa.
   → 19 archivos sin trackear = 19 oportunidades de perder trabajo.

2. CADA SEMANA: el pipeline debe generar al menos UN tipo nuevo de output
   o corregir UN bug.
   → Progreso semanal medible.

3. NADA de nuevos experimentos hasta que el pipeline base este completo:
   - Cache de IR
   - Validacion de JSON entre etapas
   - Validacion de que el codigo generado compila
   - Tests de integracion

4. SI aparece una idea nueva:
   - Documentarla en 10 lineas como maximo
   - Crear un issue en GitHub
   - VOLVER al pipeline base
   - Solo retomarla cuando el pipeline este en produccion

5. MEDIR progreso en templates funcionales:
   | Template | Estado |
   |----------|--------|
   | module-nestjs (controller + service + module) | COMPLETO |
   | entity-nestjs | COMPLETO |
   | module-prisma | COMPLETO |
   | module-express | PENDIENTE |
   | module-fastapi | PENDIENTE |
   | +validacion post-generacion | PENDIENTE |

6. CADA COMMIT debe:
   - Pasar los 47 tests existentes
   - Agregar codigo nuevo O documentacion de lo ya implementado
   - No agregar experimentos laterales

7. SI EL PROYECTO SE SIENTE PESADO:
   - Reducir alcance: el pipeline RECPL shell ya funciona
   - Publicarlo como herramienta CLI aunque falten features
   - Un bot que genera modulos NestJS basicos ya es util
```

### 7.3 Escenario de fracaso mas probable

```
El proyecto tiene 24 docs de propuestas y 0 commits completos.
El autor no sabe que esta construyendo realmente.
Cada semana aparece un "y si mejor hacemos X" que desvia el foco.
A los 3 meses, el pipeline sigue siendo el mismo que el dia 1.
El proyecto se abandona por agotamiento de opciones sin ejecutar.
```

Para evitarlo:

> **El proyecto es el pipeline RECPL. No es una API NestJS.
> No es un core en C. No es un analisis de FrameMaker.
> Es un bot shell que convierte lenguaje natural en codigo.
> Todo lo demas es accesorio.**

### 7.4 Checklist semanal de viabilidad

- [ ] El pipeline RECPL tiene al menos una mejora respecto a la semana anterior?
- [ ] Los 47 tests pasan?
- [ ] El codigo generado por el bot compila (o hubo avance hacia eso)?
- [ ] Hay un commit de esta semana?
- [ ] Se empezo algun experimento nuevo que no sea el pipeline?

Si la respuesta a "se empezo un experimento nuevo" es "si" y el pipeline
no esta completo, el proyecto esta en riesgo.

---

## 8. Resumen Ejecutivo

**Que es @Proyecto0:** Un compilador de lenguaje natural a codigo (RECPL).
Toma instrucciones en espanol y genera scaffolding de modulos NestJS, entidades
y modelos Prisma.

**Que NO es:** Una API NestJS construida manualmente. El codigo NestJS es el
output del bot, no un proyecto separado.

**Estado actual:** Pipeline shell funcional (9 scripts, 47 tests, 5 templates).
El nucleo del proyecto esta construido. Faltan validaciones, cache, mas
templates, y modo servidor.

**Riesgo principal:** Dispersion en experimentos laterales (C core, NLP,
FrameMaker, tutorial executor) que desvian atencion del pipeline base.

**Prioridad inmediata:**
1. Commit completo del proyecto
2. Mover experimentos a ramas separadas
3. Validacion post-scaffold (que el codigo generado compile)
4. CI/CD para los tests

**Metrica de exito:** El bot recibe "crea un modulo de pagos en NestJS"
y genera archivos `.ts` que compilan y pasan tests.
