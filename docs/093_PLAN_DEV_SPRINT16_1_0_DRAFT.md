---
id: 093
area: DEV
type: PLAN
module: COMPILER_BOT
version: 1.0
status: DRAFT
tags:
  - plan
  - sprint
  - generators
  - integration
summary: >-
  Plan de ejecucion del Sprint 16. Objetivo unico: integrar los 6 generadores
  de codigo con el pipeline de compilacion, validando que `execute("crea un
  modulo de pagos")` produzca scaffolding real en modules/.
keywords:
  - sprint-16
  - generators
  - synthesis
  - integration
  - scaffolding
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Plan Sprint 16 — integracion de generators
---

# 093_PLAN_DEV_SPRINT16_1_0_DRAFT

## Objetivo del Sprint

**Integrar los 6 generadores de codigo (NestJS, Prisma, React, NextJS,
Tailwind, Docker) con el pipeline de compilacion RECPL v2.0**, de modo que
un prompt como "crea un modulo de pagos con NestJS y Prisma" produzca
archivos reales en `modules/pagos/`.

## Alcance

| Componente | Estado entrada | Estado salida esperado |
|------------|---------------|----------------------|
| GeneratorFactory | 6 generadores registrados | Misma interfaz, sin cambios |
| SynthesisOrchestrator | Llama a generators via `_get_generator()` | Misma interfaz, validada |
| Parser (Lark) | AST jerarquico con Lark + fallback | Misma interfaz, 37 tests |
| Enriched propagation | Todos los stages propagan enriched | Misma interfaz, validada |
| Tests | 516 pasando | 530+ pasando |

## Priorizacion

| Prioridad | Tarea | Dependencia | Esfuerzo |
|-----------|-------|-------------|----------|
| P0 | Validar que `execute("crea modulo pagos")` genera archivos | A.3 completo | 1 dia |
| P1 | Tests de integracion: 3 escenarios end-to-end | P0 verificado | 1 dia |
| P2 | Pipeline stats script + CLI --metrics flag | — | 0.5 dias |
| P3 | RELEASE.md + git tag v2.0.0 | — | 0.5 dias |

## MVP v2.1.0 — Criterios

- [ ] Pipeline genera scaffolding NestJS + Prisma funcional
- [ ] Comando `agentic --prompt "crea un modulo de pagos"` produce archivos en `modules/`
- [ ] 530+ tests pasando (`pytest -q`)
- [ ] `ruff check .` = 0 errores
- [ ] CI/CD pasando en cada PR (GitHub Actions)

## Proyeccion Sprints 17-20

| Sprint | Objetivo | Dependencia | Tracks involucrados |
|--------|----------|-------------|---------------------|
| S17 | Performance benchmarks + snapshot testing | A.3, D.1, D.2 | QA |
| S18 | Docker demo + README renovado | C.1, C.2, F.2 | Marketing, DevOps |
| S19 | Archivar docs obsoletos + API docs | E.1, E.3 | Documentacion |
| S20 | Onboarding tutorial + release v2.1.0 | E.2, B.2 | Documentacion, Gerencia |

## Riesgos

- **Generator incompleto**: si algun generator (e.g. Docker) no produce
  archivos validos, el pipeline reporta error pero no bloquea.
- **Tests insuficientes**: si no se alcanzan 530 tests, el MVP se considera
  parcial y se difiere a S17.
- **Sin CI/CD**: F.1 (GitHub Actions) es independiente pero necesario para
  el criterio de MVP. Puede ejecutarse en paralelo.

## Criterios de Aceptacion del Sprint

1. `ruff check .` = 0 errores
2. `pytest tests/ -q` = 530+ pasando
3. `agentic --prompt "crea un modulo de pagos con NestJS y Prisma"` produce
   `modules/pagos/pagos.controller.ts` y `modules/pagos/schema.prisma`
4. `agentic --metrics` imprime resumen JSON de metricas del pipeline
5. `RELEASE.md` publicado con proceso de release de 5 pasos
