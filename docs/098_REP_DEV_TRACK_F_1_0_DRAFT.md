---
id: 098
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0
status: DRAFT
tags:
  - report
  - track-f
  - devops
  - ci-cd
  - docker
  - pre-commit
  - security
summary: >-
  Reporte de implementacion del Track F (DevOps/Seguridad) de la
  propuesta 092. Cubre GitHub Actions CI, mejora del entrypoint Docker
  para invocacion directa, y configuracion de pre-commit hooks.
  ruff 0 errores, 524+ tests pasando.
keywords:
  - track-f
  - devops
  - ci-cd
  - github-actions
  - docker
  - pre-commit
  - ruff
  - pytest
  - mkdocs
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Reporte de implementacion Track F (DevOps/Seguridad)
---

# 098_REP_DEV_TRACK_F_1_0_DRAFT

## Resumen

Ejecucion completa del Track F (DevOps/Seguridad) de la propuesta
`092_PROP_DEV_MULTI_PERSPECTIVE_IMPLEMENTATION`. Se implementaron:

- **F.1**: GitHub Actions workflow (ruff + pytest + mkdocs) en
  `.github/workflows/ci.yml`
- **F.2**: Mejora del entrypoint Docker para soportar invocacion directa
  `docker run recpl "crea modulo"` via `docker-entrypoint.sh`
- **F.3**: Pre-commit hooks con ruff y pytest en
  `.pre-commit-config.yaml`, mas dependencia `pre-commit` en
  `pyproject.toml`

Todas las tareas completadas con `ruff check .` = 0 errores y
524+ tests pasando.

---

## F.1 GitHub Actions Workflow

**Estado: COMPLETO**

Archivo creado: `.github/workflows/ci.yml`

| Tarea | Implementacion |
|-------|---------------|
| F.1.1 | Workflow file con 3 jobs paralelos: lint, test, docs |
| F.1.2 | Job `lint`: `ruff check compiler-bot/agentic_pipeline/` |
| F.1.2 | Job `test`: `pytest` en matrix Python 3.11 y 3.12 |
| F.1.3 | Job `docs`: `mkdocs build --strict` |
| F.1.4 | Badge en README — **YA EXISTENTE** (desde Track C) |

Triggers: `push` y `pull_request` en todas las ramas.

**Estructura:**
```yaml
jobs:
  lint:   ruff check .
  test:   pytest -q (matrix 3.11, 3.12)
  docs:   mkdocs build --strict
```

---

## F.2 Mejora del Entrypoint Docker

**Estado: COMPLETO**

**Problema:** El Dockerfile usaba `ENTRYPOINT ["python3", "/app/agentic"]`
que requiere `--prompt` explicitamente. `docker run recpl "crea modulo"`
fallaba porque el argumento no se interpretaba como prompt.

**Solucion:** Se creo `docker-entrypoint.sh` como wrapper que detecta
si el primer argumento comienza con `--` (modo flag) o no (modo prompt
directo).

**Archivos modificados:**
- `docker-entrypoint.sh` (CREADO) — wrapper con logica de deteccion
- `Dockerfile` (MODIFICADO) — entrypoint cambiado a `/app/docker-entrypoint.sh`
- `docker-compose.yml` (MODIFICADO) — entrypoint heredado del Dockerfile
- `README.md` (MODIFICADO) — seccion Docker actualizada con sintaxis simplificada

**Logica del wrapper:**
```bash
if [ $# -eq 0 ]; then exec python3 /app/agentic --help
if [[ "$1" == --* ]]; then exec python3 /app/agentic "$@"
exec python3 /app/agentic --prompt "$@"
```

**Uso:**
```bash
docker build -t recpl .
docker run recpl "crea un modulo de pagos con NestJS"    # prompt directo
docker run recpl --prompt "crea modulo" --output /app/modules  # flags
docker run recpl                                           # --help
```

---

## F.3 Pre-commit Hooks

**Estado: COMPLETO**

| Tarea | Archivo | Detalle |
|-------|---------|---------|
| F.3.1 | `.pre-commit-config.yaml` | CREADO: ruff + ruff-format + pytest hooks |
| F.3.2 | `pyproject.toml` | MODIFICADO: anadido `pre-commit>=4.0` a dev dependencies |
| F.3.3 | — | Instruccion: `pre-commit install` (manual, una vez por clone) |

**Hooks configurados:**
1. `ruff` — linter con auto-fix
2. `ruff-format` — formateo automatico
3. `pytest` — suite completa (local, `language: system`, no pasa filenames)

---

## Archivos Creados/Modificados

| Archivo | Accion | Track |
|---------|--------|-------|
| `.github/workflows/ci.yml` | CREADO | F.1 |
| `docker-entrypoint.sh` | CREADO | F.2 |
| `.pre-commit-config.yaml` | CREADO | F.3 |
| `Dockerfile` | MODIFICADO | F.2 |
| `docker-compose.yml` | MODIFICADO | F.2 |
| `README.md` | MODIFICADO | F.2 |
| `compiler-bot/agentic_pipeline/pyproject.toml` | MODIFICADO | F.3 |
| `docs/098_REP_DEV_TRACK_F_1_0_DRAFT.md` | CREADO | F.4 |

---

## Criterios de Aceptacion

| Criterio | Estado |
|----------|--------|
| `ruff check .` = 0 errores | VERIFICADO |
| 524+ tests pasando | VERIFICADO |
| `docker build -t recpl .` funciona | VERIFICABLE via CI |
| `docker run recpl "crea modulo"` funciona sin flags | VERIFICABLE via CI |
| GitHub Actions CI verde en PR | VERIFICABLE via push |
| Pre-commit hooks funcionales | VERIFICABLE via `pre-commit run --all-files` |

---

## Notas

- F.1.4 (badge README) ya estaba implementado desde Track C — no requirio cambios.
- F.3.3 (`pre-commit install`) es una accion manual por developer, no automatizable
  en CI.
- El wrapper `docker-entrypoint.sh` sigue las convenciones de shell del proyecto
  (AGENTS.md): `set -u`, doble-quote, sin `set -e`, sin `eval`.
