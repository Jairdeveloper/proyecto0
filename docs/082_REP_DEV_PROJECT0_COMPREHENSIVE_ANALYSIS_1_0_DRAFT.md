---
area: dev
type: rep
module: project
version: 1.0
status: IMPLEMENTED
---
# Comprehensive Analysis of Proyecto0 (RECPL Compiler Bot)

**Document ID:** 082_REP_DEV_PROJECT0_COMPREHENSIVE_ANALYSIS_1_0_DRAFT  
**Area:** DEV (Development)  
**Type:** REP (Report)  
**Module:** Project Analysis  
**Version:** 1.0 — DRAFT  
**Tags:** `project-analysis`, `risks`, `strategy`, `roadmap`, `sustainability`  
**Summary:** Análisis integral del proyecto Proyecto0, identificando objetivos alcanzados, debilidades estructurales, riesgos técnicos y recomendaciones estratégicas para asegurar su finalización y sostenibilidad.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Objetivos Alcanzados](#2-objetivos-alcanzados)
3. [Debilidades Encontradas](#3-debilidades-encontradas)
4. [Mejoras Concretas de Implementación](#4-mejoras-concretas-de-implementación)
5. [Mejoras de Estructura](#5-mejoras-de-estructura)
6. [Riesgos Técnicos que Podrían Abortar el Proyecto](#6-riesgos-técnicos-que-podrían-abortar-el-proyecto)
7. [Estrategia de Sostenibilidad](#7-estrategia-de-sostenibilidad)
8. [Plan de Acción Pragmático](#8-plan-de-acción-pragmático)
9. [Qué Haría para Asegurar que Este Proyecto Llegue a Producción](#9-qué-haría-para-asegurar-que-este-proyecto-llegue-a-producción)

---

## 1. Executive Summary

Proyecto0 es un **RECPL Compiler Bot** — un compilador de lenguaje natural a código IR que toma instrucciones en lenguaje natural y produce una representación intermedia canónica. Generadores opcionales traducen el IR a código específico (NestJS, Prisma, React, etc.). El pipeline sigue el patrón clásico de compiladores (Aho, Dragon Book): preprocess → lexer → parser → semantic → IR → synthesis.

El proyecto tiene **tres implementaciones paralelas**:

| Capa | Stack | Estado | Tests |
|------|-------|--------|-------|
| **v1.0 Shell** | Shell scripts (pipeline compilador) | COMPLETO | 72 tests (PASS) |
| **Agent layer** | Shell scripts (agente + herramientas) | COMPLETO | 13 tests (PASS) |
| **v2.0 Python** | LangGraph + Pydantic + LangChain | PARCIAL (skeleton) | Sin tests |
| **C Core** | C11 experimental | PARCIAL (stubs) | No integrado |

El shell pipeline es funcional y está probado. El agente (agent-robot) es una capa adicional que clasifica intenciones y enruta a RECPL o a herramientas. La v2.0 en Python es un esqueleto con modelos definidos pero implementación parcial.

---

## 2. Objetivos Alcanzados

### Pipeline Shell (v1.0) — COMPLETO

- [x] **Preprocesador** — Normalización de input (trim, lowercase, collapse punct, split sentences)
- [x] **Lexer DFA** — Tokenización con maximal munch (ACTION_CREATE/DELETE/UPDATE/READ, MODULE, ENTITY, TECH_NESTJS/PRISMA, PREP_IN, SEPARATOR)
- [x] **Parser LL(1) recursivo descendente** — Gramática BNF completa (comando → accion modulo_espec opcional_tech)
- [x] **Analizador Semántico** — Tabla de símbolos persistente (disk-based), type checking
- [x] **Generador IR** — AST validado → IR.json canónico
- [x] **Synthesis/PRINT** — IR.json → respuesta JSON con mensaje y payload
- [x] **Scaffolding** — Generación de archivos desde templates (NestJS module/entity, Prisma model)
- [x] **Router** — 3 modos (auto/llm/deterministic)
- [x] **Integración LLM** — Providers Claude y OpenAI
- [x] **Pipeline debugger** — 5 modos (trace, step, timing, inspect, xtrace)
- [x] **CLI flags** — `-c`/`--command`, `-f`/`--file`, `--llm`, `--provider`
- [x] **Patrón composite** — `source`/`exec` con estado compartido

### Agent-Robot Layer — COMPLETO

- [x] **Clasificador de intención** — Heurística basada en regex, 14 patrones
- [x] **Bridge RECPL** — Comunicación unidireccional agent → RECPL
- [x] **Herramientas**: read_file, write_file, run_command, search_code, respond
- [x] **Planificador multi-paso** — Descomposición de instrucciones complejas
- [x] **Memoria persistente** — Historial multi-sesión en JSON
- [x] **TUI** — Interfaz whiptail
- [x] **Provider apifreellm** — Capa gratuita
- [x] **System prompts** — Agent, planner, tools

### Documentación — COMPLETO (81+ documentos)

- [x] Convetion de nombrado ALGP003 implementada en todos los documentos
- [x] INDEX.md maestro + índices por área
- [x] Guías de estilo (Shell, Python, C)
- [x] Reportes de implementación por sprint (Sprint 1-12)
- [x] Propuestas técnicas, planes de ejecución, runbooks

---

## 3. Debilidades Encontradas

### 3.1 Dualidad Shell/Python sin Estrategia de Migración Clara

**Problema crítico.** El proyecto mantiene dos implementaciones paralelas del mismo pipeline:

- **Shell (v1.0)**: 10 scripts, 72 tests, funcional y probado
- **Python (v2.0)**: LangGraph skeleton con 9 nodos, pero implementaciones reales son stubs o están vacías

No hay una estrategia documentada de cómo migrar de Shell a Python. Tampoco hay un criterio para decidir qué implementación usar en producción. Esto crea **deuda técnica por diseño**: cada bug o feature request debe implementarse en ambos stacks.

### 3.2 Python v2.0: Skeleton Sin Carne

El directorio `agentic_pipeline/` contiene:

| Archivo | Estado |
|---------|--------|
| `orchestrator.py` | Framework LangGraph completo con enrutamiento |
| `state_models.py` | Modelos Pydantic (Stage, StageContext, etc.) |
| `config.py` | Config básica |
| `feedback_loop.py` | Parcial |
| `metrics_store.py` | Stub |
| `generators/` | Vacío |
| `grammars/` | Vacío |
| `nodes/` | 10 subdirectorios, la mayoría con stubs |
| `providers/` | Vacío |
| `tests/` | Sin tests |
| `tools/` | Vacío |

Los nodos implementados (preprocessor, lexer, parser, etc.) probablemente contienen lógica real, pero la orquestación LangGraph no tiene tests, dependencias de producción no instaladas, y `pyproject.toml` usa dependencias alpha/beta de langchain.

### 3.3 C Core: Muerto al Llegar

El directorio `core/` contiene una implementación C11 experimental con:

- `Makefile` funcional (release/debug/test)
- `main.c`, `token.h`, `ast.h`
- `hash_table.c/h`, `json_builder.c/h`, `common.c/h`

Pero:

- **No hay integración** con el pipeline Shell o Python
- **No se menciona** en ninguna estrategia de despliegue
- El `main.c` probablemente es un dispatch vacío
- No hay tests en C
- Requeriría compilación nativa, empaquetado y distribución separada

Este componente representa **esfuerzo hundido** (sunk cost) que distrae del objetivo principal.

### 3.4 Escasez de Tests de Integración

Los 72 tests de Shell y 13 de agent-robot son unitarios/funcionales. No hay:

- **Tests de integración** que validen el pipeline completo con escenarios reales
- **Tests de rendimiento** (tiempo de respuesta del pipeline completo)
- **Tests de regresión** automatizados en CI
- **Tests de carga** para el modo LLM (latencias, costos)
- **Tests de seguridad** (inyección de comandos, path traversal)

### 3.5 Gestión de Estado Frágil

- `RECPL_STATE_DIR` usa `/tmp/` por defecto — **se pierde al reiniciar**
- `AGENT_MEMORY_DIR` también usa `/tmp/` — advertencia explícita en agent.sh
- Estado compartido via archivos JSON en disco → race conditions en concurrencia
- No hay mecanismo de lock o transacciones

### 3.6 Dependencia Hardcodeada a `jq`

- `jq` es crítico para todo el pipeline JSON del agente
- El instalador descarga un binario estático, pero no verifica suma de verificación
- No hay fallback a `python3 -m json.tool` o similares
- `npm jq` (Node.js wrapper) **no es compatible** — documentado pero fácil de instalar por error

### 3.7 Documentación Excesiva, Código Insuficiente

81 documentos para ~30 scripts funcionales. Proporción ~2.7 docs por script. Muchos documentos son reportes de implementación redundantes (Sprint 1-12, Fase 1-4, etc.) que documentan el proceso de desarrollo pero no son útiles para un nuevo desarrollador.

**Síntoma**: el proyecto prioriza documentar sobre construir.

---

## 4. Mejoras Concretas de Implementación

### 4.1 Shell Pipeline

1. **Reemplazar parsing JSON con awk por `jq`**: synthesis.sh y parser.sh usan awk para extraer campos JSON, que es frágil con espacios, comillas escapadas, etc. Usar `jq` en todos los lugares donde esté disponible.

2. **Añadir timeouts configurables**: El modo LLM no tiene timeout; llamadas a API externa pueden colgar el pipeline indefinidamente.

3. **Sanitización de nombres de archivo**: `scaffold.sh` recibe nombres del usuario sin sanitizar. Riesgo de path traversal en `output_dir`.

4. **Manejo de errores consistente**: Algunos scripts devuelven exit code 0 incluso en error (e.g., preprocessor.sh devuelve input original — no hay forma de distinguir éxito de fallo).

5. **Reemplazar `date +%s` por `date +%s%3N`** para medición de tiempo en milisegundos (actualmente truncado a segundos).

### 4.2 Agent Layer

6. **Parser de `write_file` más robusto**: El parsing actual "crea archivo \<ruta\> con contenido \<contenido\>" rompe si la ruta contiene "con contenido".

7. **Timeout global configurable**: `timeout_run()` tiene timeout hardcodeado. Debería ser configurable via variable de entorno.

8. **Logging estructurado**: Actualmente logs a archivos de texto plano. Migrar a JSON logging para facilitar análisis.

### 4.3 Python v2.0

9. **Decidir: completar o descartar**: No hay término medio. O se completa la implementación Python (prioridad alta) o se elimina del repositorio. Mantener el esqueleto es deuda técnica.

10. **Añadir pytest antes de más código**: Todo nuevo nodo Python debe tener tests primero (TDD).

### 4.4 Tests

11. **Script de CI**: Un `ci.sh` que corra syntax check → shellcheck → tests Shell → tests agent → (si Python, pytest). Debe fallar si cualquier etapa falla.

12. **Test de inyección**: Probar que `"crea modulo $(rm -rf /)"` no ejecute comandos.

---

## 5. Mejoras de Estructura

### 5.1 Arquitectura Jerárquica

```
proyecto0/
  docs/                    # Documentación (reducir a 40-50 docs clave)
  compiler-bot/
    recpl.sh               # Entrypoint público
    pipeline_debugger.sh   # Debugger
    agent-robot.sh         # Entrypoint agente
    
    # Pipeline Shell (v1.0) — mantenedor
    frontend/
    middleend/
    backend/
    templates/
    providers/
    
    # Pipeline Python (v2.0) — futuro, solo si se completa
    agentic_pipeline/
    
    # C Core — eliminar o mover a contrib/
    core/
    
    tests/                 # Tests consolidados
    agent-robot/           # Agente capa superior
```

### 5.2 Separar Conceptualmente "Pipeline" de "Agente"

- `compiler-bot/` debe contener solo el pipeline compilador Shell
- `agent-robot/` debe ser un paquete separado que *consume* el pipeline
- La línea es borrosa actualmente: agent-robot está dentro de compiler-bot

### 5.3 Reducir Documentación a lo Esencial

Conservar:
- Guías de estilo (Shell, Python, C)
- Guía de arquitectura (059)
- Runbook de operación (010)
- Especificaciones técnicas (core)

Descartar o archivar:
- Reportes de sprints individuales (mantener solo resúmenes)
- Propuestas rechazadas o superadas
- Documentos de planificación ya ejecutados

### 5.4 Convención de Versiones

El proyecto usa versionado semántico pero no hay consistencia:
- CHANGELOG.md: v1.8.0
- recpl.sh: v1.2.0
- agent-robot: v1.0.0
- Python: v0.1.0

Unificar versión del proyecto en un solo lugar (root `VERSION` file o `version.sh`).

---

## 6. Riesgos Técnicos que Podrían Abortar el Proyecto

### 🔴 R1: Abandono por Fatiga de Mantenimiento (Alta Probabilidad)

**Causa**: Mantener 3 implementaciones paralelas (Shell + Python + C) con un solo desarrollador. Cada cambio requiere modificaciones en múltiples stacks.

**Síntomas**: Commits espaciados, funcionalidades incompletas en Python, C Core abandonado.

**Mitigación**: Elegir un stack primario (Shell ya funcional) y posponer/descartar los otros hasta tener equipo.

### 🔴 R2: Dependencia de APIs Externas sin Control (Alta Probabilidad)

**Causa**: El modo LLM depende de Claude (Anthropic), OpenAI, o apifreellm. Cualquier cambio en API, precio, o disponibilidad deja el modo LLM inoperativo.

**Síntomas**: Tests LLM que fallan por rate limiting, cambios de API, keys expiradas.

**Mitigación**: 
- Modo deterministico debe ser siempre funcional (ya lo es)
- Mock de LLM en tests
- Cache de respuestas LLM para reducir costos y dependencia

### 🔴 R3: Inconsistencia Shell/Python Divide la Base de Código (Media Probabilidad)

**Causa**: Sin decisión clara, features se implementan en Shell (rápido) pero la documentación asume Python (futuro). Nuevos desarrolladores no saben dónde contribuir.

**Mitigación**: Decisión ejecutiva: Shell es producción, Python es experimental hasta que tenga paridad de tests.

### 🟡 R4: Seguridad por Diseño Insuficiente

**Causa**: 
- `run_command` ejecuta `sh -c` con input del usuario
- Scaffold escribe a rutas derivadas del input
- `eval` está prohibido en shell style guide, pero `sh -c` en tool_run_command.sh es equivalente funcional

**Mitigación**: 
- Lista blanca de comandos permitidos para run_command
- Validación de rutas contra path traversal
- Sandboxing de ejecución

### 🟡 R5: Escalabilidad Vertical del Estado en Disco

**Causa**: Estado persistente via archivos JSON en disco. Con muchas sesiones/operaciones, el directorio de estado crece sin límite.

**Mitigación**:
- `memory_export()` ya existe — usarlo para backups
- Añadir rotación/reseteo de memoria
- Límite de entradas en historial (e.g., últimas 1000)

### 🟢 R6: Compatibilidad `dash` vs `bash`

**Causa**: El proyecto usa `#!/bin/sh` pero tiene dependencia en `bash-isms`:
- `[[ ]]` en algunos scripts y tests
- `echo` con escape sequences

**Mitigación**: Ya se corrigió en v1.7.0 para agent.sh. Verificar que todos los scripts usen `printf` en vez de `echo` y `[ ]` en vez de `[[ ]]`.

---

## 7. Estrategia de Sostenibilidad

### 7.1 Principio Rector: Una sola fuente de verdad

> El código funcional y probado es la única fuente de verdad. La documentación describe lo que el código *hace*, no lo que el código *debería hacer*.

### 7.2 Decisiones Arquitectónicas

| Decisión | Opción Elegida | Justificación |
|----------|---------------|---------------|
| Stack de producción | Shell (v1.0) | Funcional, probado, completo |
| Stack futuro | Python (v2.0) | Solo si hay recursos para completarlo |
| C Core | Archivar/eliminar | Esfuerzo no dirigido al objetivo |
| Almacenamiento persistente | Directorio configurable via env var (`RECPL_STATE_DIR`, `AGENT_MEMORY_DIR`) | Ya implementado, documentar mejor |
| LLM | Capa optional, modo deterministico siempre funcional | Ya implementado |

### 7.3 Prácticas para Sostenibilidad

1. **Un solo entrypoint público**: `recpl.sh` es el entrypoint. `agent-robot.sh` es una capa opcional. Documentar claramente.

2. **CI/CD mínimo**: Un script `ci.sh` que ejecute:
   ```bash
   bash -n script.sh          # Syntax check
   shellcheck script.sh        # Linting
   tests/run_tests.sh          # Tests pipeline (72 tests)
   tests/test_agent.sh         # Tests agente (13 tests)
   ```

3. **Versionado centralizado**: Archivo `VERSION` en la raíz del proyecto, leído por todos los componentes.

4. **CHANGELOG por feature, no por documento**: Cada entrada en CHANGELOG debe corresponder a un cambio de código, no a un nuevo documento.

5. **Pruebas antes de documentar**: Invertir la proporción actual. Primero código y tests, luego documento de reporte si es necesario.

---

## 8. Plan de Acción Pragmático

### 8.1 Corto Plazo (Sprint actual — 1 semana)

**Objetivo**: Estabilizar el pipeline Shell existente y cerrar tareas pendientes.

| # | Acción | Criterio de Éxito | Prioridad |
|---|--------|--------------------|-----------|
| 1 | `TASK-009`: Implementar Tracer (three-address code) | `compiler-bot/tracer.sh` funcional, tests PASS | Alta |
| 2 | `TASK-012`: Implementar Scorer (pattern matching) | `compiler-bot/scorer.sh` funcional, tests PASS | Alta |
| 3 | Añadir `ci.sh` con validación completa | `./ci.sh` exit 0 en repo limpio | Alta |
| 4 | Sanitizar nombres de archivo en scaffold.sh | Path traversal bloqueado | Alta |
| 5 | Añadir timeout configurable en modo LLM | `RECPL_LLM_TIMEOUT` env var respetado | Media |
| 6 | Test de inyección de comandos en test suite | Test específico PASS | Media |
| 7 | CI: syntax check + shellcheck + tests Shell | GitHub Actions o script local | Alta |

### 8.2 Medio Plazo (2-4 semanas)

**Objetivo**: Reducir deuda técnica, mejorar robustez, decidir futuro de Python/C.

| # | Acción | Criterio de Éxito | Prioridad |
|---|--------|--------------------|-----------|
| 8 | Decisión sobre Python v2.0 | Documento de decisión: completar O archivar | Alta |
| 9 | Decisión sobre C Core | Eliminar del repo o mover a `contrib/` | Alta |
| 10 | Reemplazar awk JSON parsing por `jq` en synthesis.sh | Cero dependencia de awk para JSON | Media |
| 11 | Logging estructurado en pipeline (JSON) | Logs parseables por `jq` | Media |
| 12 | Tests de integración end-to-end | 5+ escenarios reales automatizados | Alta |
| 13 | Reducir documentación a 40-50 docs clave | Archivar reportes de sprint redundantes | Baja |

### 8.3 Largo Plazo (1-3 meses)

**Objetivo**: Preparar para producción, expandir capacidades.

| # | Acción | Criterio de Éxito | Prioridad |
|---|--------|--------------------|-----------|
| 14 | Dockerizar el pipeline | `Dockerfile` produciendo imagen < 100MB | Media |
| 15 | API HTTP Server (Propuesta 055) | Servidor Fastify/Express con endpoints REST | Baja |
| 16 | Si se completa Python v2.0: migración gradual | Pipeline Python con 100% paridad de tests Shell | Baja |
| 17 | Web UI básica | Interfaz web para probar el pipeline | Baja |
| 18 | Documentación de onboarding | README.md que un nuevo dev pueda seguir en 30 min | Media |

---

## 9. Qué Haría para Asegurar que Este Proyecto Llegue a Producción

Esta es la sección más importante del análisis. He visto muchos proyectos prometedores morir por las mismas razones. Aquí están mis recomendaciones concretas:

### 9.1 Parar de construir, empezar a terminar

El proyecto tiene 3 implementaciones paralelas + 81 documentos. **La principal razón por la que este proyecto moriría es porque el desarrollador se abruma con el tamaño y no sabe por dónde seguir.**

**Acción concreta**: Este sprint, el objetivo no es añadir nada nuevo. Es:
1. Cerrar TASK-009 (Tracer) y TASK-012 (Scorer) — son los únicos pendientes del pipeline Shell
2. Decidir si Python v2.0 sigue o se archiva
3. Eliminar C Core del árbol principal
4. Ejecutar `ci.sh` y verificar que todo pasa

Cuando un proyecto tiene 81 documentos y 30 scripts, el 90% de la energía debería ir a **consolidar**, no a expandir.

### 9.2 Elegir un stack y matar los otros

**Shell (v1.0) funciona.** Tiene 72 tests y pasa todos. Está completo.

- **Si el objetivo es producción**: Shell ya está listo. No necesitas Python v2.0. No necesitas C Core. Enfócate en pulir Shell.
- **Si el objetivo es aprender LangGraph**: Python v2.0 es un proyecto de aprendizaje, no un reemplazo de producción. Trátalo como tal.

**El error fatal sería mantener ambos** — porque entonces cada bug hay que arreglarlo dos veces, y el desarrollador se quema.

### 9.3 CI/CD desde el día 1 (literalmente)

No importa si eres el único desarrollador. Un `ci.sh` que ejecute:

```bash
#!/bin/bash
set -e
echo "=== Syntax check ==="
bash -n compiler-bot/frontend/*.sh compiler-bot/backend/*.sh ...
echo "=== ShellCheck ==="
shellcheck compiler-bot/**/*.sh
echo "=== Shell tests ==="
compiler-bot/tests/run_tests.sh
echo "=== Agent tests ==="
compiler-bot/tests/test_agent.sh
echo "✅ All checks passed"
```

Este script, ejecutado antes de cada commit, mantiene el proyecto verde y evita regresiones. Es la red de seguridad que permite avanzar rápido.

### 9.4 El "Modo Demo" como Norte

Un proyecto vive o muere por su capacidad de demostrar valor. Define el "Modo Demo":

```
$ ./recpl.sh
> crea un modulo de pagos en NestJS
✅ Generando modulo Pagos en nestjs...
  → modules/pagos/pagos.module.ts
  → modules/pagos/pagos.controller.ts
  → modules/pagos/pagos.service.ts
```

Si esto funciona de manera confiable, el proyecto tiene valor. Todo lo demás (TUI, agent-robot, Web UI, API HTTP) es bonus.

**Prioriza que el demo funcione siempre.**

### 9.5 Medir lo que importa

| Métrica | Por qué importa | Objetivo |
|---------|----------------|----------|
| Tests Shell: FAIL count | Regresiones | 0 |
| Tiempo de pipeline completo | UX | < 2s (modo deterministico) |
| Cobertura LLM fallback | Robustez | > 90% de instrucciones resueltas |
| Días sin commits rotos | Salud del proyecto | 0 (siempre verde) |

### 9.6 Regla de las 3 preguntas antes de escribir código

Antes de cualquier tarea nueva, responder:

1. **¿Esto acerca el proyecto a producción?** Si la respuesta es "no" o "tal vez", no hacerlo.
2. **¿Hay algo más importante que debería estar haciendo?** (bugs, tests, CI, deuda técnica)
3. **¿Puedo hacerlo en menos de 2 horas?** Si no, dividirlo.

### 9.7 El plan de rescate (si el proyecto se estanca)

Si en 2 semanas no hay commits, ejecutar:

```bash
# 1. Verificar estado
compiler-bot/tests/run_tests.sh

# 2. Arreglar lo que esté roto
# 3. Hacer un commit con el arreglo
# 4. Repetir
```

El proyecto no muere mientras los tests pasen. Si están rotos, arreglarlos es la prioridad #1.

---

## Appendix A: Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| Documentos en `docs/` | 81+ |
| Scripts Shell funcionales | ~30 |
| Tests Shell v1.0 | 72 (PASS) |
| Tests Agent | 13 (PASS) |
| Líneas de código Shell (aprox.) | ~3000 |
| Líneas de Python (aprox.) | ~500 (mayoría stubs) |
| Documentos por script | 2.7 |
| Versiones paralelas | 3 (Shell, Python, C) |
| Commit inicial | 2026-06-07 |
| Último commit | 2026-06-13 |
| Días de desarrollo activo | ~7 |

## Appendix B: Dependencias Externas

| Dependencia | Uso | Riesgo |
|-------------|-----|--------|
| `jq` (binario estático) | Parsing JSON en agent-robot | Crítico — sin fallback |
| `whiptail` (o `dialog`) | TUI (agent-robot) | Bajo — fallback textual |
| `curl` | API calls LLM | Medio — rate limiting |
| `timeout` (GNU coreutils) | Timeout wrapper | Bajo — fallback a ejecución directa |
| `awk` | Parsing JSON en pipeline Shell | Medio — frágil con JSON complejo |
| `grep` / `sed` | Procesamiento de texto | Bajo — ampliamente disponible |
| `python3` (>=3.11) | Pipeline v2.0 | Medio — no instalado por defecto |
| langchain/langgraph | Pipeline v2.0 | Alto — APIs cambiantes, dependencias pesadas |

---

*Documento generado el 2026-06-14. Próxima revisión sugerida: 2026-07-14.*