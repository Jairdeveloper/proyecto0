---
id: 138
area: dev
type: plan
module: metrics_dashboard_versioning_execution
version: 1.0
status: IMPLEMENTED
tags:
  - plan
  - dashboard
  - metrics
  - versioning
  - ci
  - release
summary: "Plan de ejecucion para implementar todas las secciones de la propuesta 137: dashboard local de metricas, gate diario estable y alineacion de versionado para release/CI confiable."
keywords:
  - execution-plan
  - dashboard
  - metrics-store
  - version-alignment
  - daily-gate
  - release-gate
  - ci
changelog:
  - version: 1.0
    date: 2026-06-19
    author: codex
    description: Creacion del plan de ejecucion derivado de la propuesta 137
---

# Plan de Ejecucion: Dashboard de Metricas y Alineacion de Versionado

**Documento fuente:** `137_PROP_DEV_METRICS_DASHBOARD_AND_VERSION_ALIGNMENT_1_0_DRAFT.md`  
**Fecha:** 2026-06-19  
**Objetivo:** ejecutar todos los requisitos de la propuesta 137 con cambios
incrementales, verificables y compatibles con el estado real del proyecto.

## 1. Alcance

Este plan ejecuta tres lineas de trabajo:

1. Dashboard local de metricas basado en `MetricsStore`.
2. Gate diario estable para trabajo normal.
3. Alineacion de versionado para release/CI confiable.

El orden de ejecucion recomendado prioriza primero versionado y CI porque
reduce ambiguedad antes de implementar la UI.

## 2. Restricciones Operativas

- No modificar lexer, parser, semantic analyzer ni IR para este MVP.
- No introducir Node.js, React, Next.js ni toolchain frontend.
- No depender de `scripts/pipeline_stats.sh` como backend del dashboard.
- No bloquear el gate diario por la suite Python completa, que aun es inestable
  en el entorno documentado.
- Mantener `./compiler-bot/agentic --metrics json|table` como interfaz estable.
- Usar stdlib Python para el servidor HTTP del MVP.
- Mantener el dashboard en `localhost` por defecto.

## 3. Mapa de Entregables

| Entregable | Tipo | Ruta |
|---|---|---|
| Versiones alineadas | cambio | `VERSION`, `compiler-bot/agentic_pipeline/pyproject.toml`, `CHANGELOG.md` |
| Check de versionado | nuevo | `scripts/check_version_alignment.sh` |
| CI actualizado | cambio | `.github/workflows/ci.yml` |
| Servicio dashboard | nuevo | `compiler-bot/agentic_pipeline/dashboard/service.py` |
| Servidor dashboard | nuevo | `compiler-bot/agentic_pipeline/dashboard/app.py` |
| Static UI | nuevo | `compiler-bot/agentic_pipeline/dashboard/static/*` |
| CLI dashboard | cambio | `compiler-bot/agentic` |
| Tests dashboard | nuevo | `compiler-bot/agentic_pipeline/tests/test_dashboard_service.py`, `test_dashboard_app.py` |
| Documentacion operativa | cambio | `README.md` o `docs/136_GUIDE_DEV_PROJECT0_RUNBOOK_1_0_ACTIVE.md` |

## 4. Fase 0: Preparacion

### Objetivo

Confirmar que el repositorio inicia limpio y que los comandos base del runbook
siguen funcionando antes de tocar implementacion.

### Tareas

| ID | Tarea | Comando/Criterio |
|---|---|---|
| P0.1 | Confirmar estado git | `git status --short` sin cambios no relacionados |
| P0.2 | Confirmar lint Python | `ruff check compiler-bot/agentic_pipeline` |
| P0.3 | Confirmar shell RECPL | `bash compiler-bot/tests/run_tests.sh` |
| P0.4 | Confirmar agent-robot shell | `bash compiler-bot/tests/test_agent.sh` |
| P0.5 | Confirmar metricas CLI | `./compiler-bot/agentic --metrics json` |

### Criterio de salida

Los cuatro comandos del gate diario funcionan o cualquier fallo queda registrado
antes de iniciar cambios.

## 5. Fase 1: Alineacion de Versionado

### Objetivo

Hacer que `VERSION`, `pyproject.toml` y la cabecera mas reciente de
`CHANGELOG.md` coincidan.

### Version canonica

Usar la primera cabecera de `CHANGELOG.md` como fuente canonica. Al momento de
este plan, la version esperada es:

```text
2.8.3
```

La version puede cambiar si se agregan entradas nuevas al changelog durante la
ejecucion; el principio es que los tres archivos coincidan al final.

### Tareas

| ID | Tarea | Archivos | Criterio |
|---|---|---|---|
| V1.1 | Actualizar `VERSION` | `VERSION` | Contiene solo `2.8.3` o version canonica vigente |
| V1.2 | Actualizar paquete Python | `compiler-bot/agentic_pipeline/pyproject.toml` | `[project].version` coincide con `VERSION` |
| V1.3 | Confirmar cabecera changelog | `CHANGELOG.md` | Primera cabecera `## [x.y.z]` coincide |
| V1.4 | No tocar versiones legacy shell | `compiler-bot/recpl.sh` | `VERSION="1.2.0"` queda como version shell legacy |

### Verificacion

```sh
cat VERSION
python - <<'PY'
import tomllib
from pathlib import Path
data = tomllib.loads(Path("compiler-bot/agentic_pipeline/pyproject.toml").read_text())
print(data["project"]["version"])
PY
awk '/^## \\[[0-9]+\\.[0-9]+\\.[0-9]+\\]/ {print $2; exit}' CHANGELOG.md
```

## 6. Fase 2: Script de Verificacion de Versionado

### Objetivo

Agregar un check reproducible sin dependencias externas.

### Archivo nuevo

```text
scripts/check_version_alignment.sh
```

### Reglas funcionales

1. Leer `VERSION`.
2. Leer `version = "x.y.z"` de `compiler-bot/agentic_pipeline/pyproject.toml`.
3. Leer la primera cabecera `## [x.y.z]` de `CHANGELOG.md`.
4. Fallar con mensaje claro si una version falta.
5. Fallar con mensaje claro si las tres versiones no coinciden.
6. Salir `0` si coinciden.

### Convenciones shell

- No usar `set -e`.
- No usar `eval`.
- Variables siempre entre comillas.
- Funciones `snake_case()`.
- Validar con `bash -n` y, si esta disponible, `shellcheck`.

### Tareas

| ID | Tarea | Criterio |
|---|---|---|
| V2.1 | Crear script ejecutable | `test -x scripts/check_version_alignment.sh` |
| V2.2 | Implementar extraccion con `awk`/`sed` | No requiere Python, jq ni toml parser |
| V2.3 | Caso positivo | Script sale `0` cuando coinciden |
| V2.4 | Caso negativo manual | Script falla si una copia temporal diverge |

### Verificacion

```sh
bash -n scripts/check_version_alignment.sh
./scripts/check_version_alignment.sh
```

## 7. Fase 3: Integracion CI

### Objetivo

Ejecutar el check de versionado en CI antes de instalar dependencias Python.

### Tarea

Modificar `.github/workflows/ci.yml`:

```yaml
- run: bash scripts/check_version_alignment.sh
```

Ubicacion recomendada: job `lint`, inmediatamente despues de `actions/checkout`.

### Criterios

- El check corre antes de `pip install`.
- Un desalineamiento de version falla rapido.
- No se modifican los jobs existentes de lint/test/docs salvo el nuevo paso.

### Verificacion local

```sh
bash scripts/check_version_alignment.sh
ruff check compiler-bot/agentic_pipeline
```

## 8. Fase 4: Servicio de Metricas para Dashboard

### Objetivo

Crear una capa de servicio que transforme `MetricsStore` en view models seguros
para UI/API.

### Archivos

```text
compiler-bot/agentic_pipeline/dashboard/__init__.py
compiler-bot/agentic_pipeline/dashboard/service.py
compiler-bot/agentic_pipeline/tests/test_dashboard_service.py
```

### Contrato de `service.py`

Funciones o clase recomendada:

```python
class DashboardService:
    def get_health(self) -> dict: ...
    def get_summary(self) -> dict: ...
    def get_stages(self) -> list[dict]: ...
    def get_recent(self, stage: str, limit: int = 20) -> list[dict]: ...
```

### Requisitos

- Calcular `success_rate` sin `bc` ni shell.
- Soportar cero registros sin division por cero.
- Usar `MetricsStore` directamente, no `scripts/pipeline_stats.sh`.
- Reportar backend observado:
  - `sqlite` si `metrics_store.HAS_SQLITE`.
  - `json_fallback` si no hay `_sqlite3`.
- Limitar `limit` a un rango seguro, por ejemplo `1..100`.
- No escribir metricas durante lectura.

### Tests minimos

| Test | Criterio |
|---|---|
| `test_summary_empty_store` | total `0`, success rate `0.0` |
| `test_summary_with_errors` | tasa calculada correctamente |
| `test_stages_shape` | cada stage tiene `name`, `runs`, `errors`, `success_rate` |
| `test_recent_limit` | respeta limite |
| `test_health_reports_backend` | incluye backend y timestamp |

### Verificacion

```sh
cd compiler-bot/agentic_pipeline
python -m pytest tests/test_dashboard_service.py -q -o addopts=
ruff check .
```

## 9. Fase 5: Servidor HTTP Local

### Objetivo

Exponer el servicio por HTTP local usando stdlib.

### Archivos

```text
compiler-bot/agentic_pipeline/dashboard/app.py
compiler-bot/agentic_pipeline/tests/test_dashboard_app.py
```

### Endpoints requeridos

| Metodo | Ruta | Respuesta |
|---|---|---|
| `GET` | `/` | HTML |
| `GET` | `/api/health` | JSON health |
| `GET` | `/api/summary` | JSON summary |
| `GET` | `/api/stages` | JSON stages |
| `GET` | `/api/stages/<stage>/recent?limit=20` | JSON recent |

### Requisitos tecnicos

- Bind por defecto: `127.0.0.1`.
- Puerto por defecto: `8765`.
- Respuestas JSON con `Content-Type: application/json`.
- 404 deterministico para rutas desconocidas.
- Errores internos con JSON, no traceback HTML.
- No abrir navegador automaticamente.

### Tests minimos

| Test | Criterio |
|---|---|
| `test_health_endpoint` | HTTP 200 + JSON |
| `test_summary_endpoint` | HTTP 200 + campos esperados |
| `test_stages_endpoint` | HTTP 200 + lista |
| `test_recent_endpoint` | HTTP 200 + lista |
| `test_not_found` | HTTP 404 + JSON |

### Verificacion

```sh
cd compiler-bot/agentic_pipeline
python -m pytest tests/test_dashboard_app.py -q -o addopts=
```

## 10. Fase 6: CLI `--dashboard`

### Objetivo

Arrancar el dashboard desde el entrypoint existente.

### Archivo

```text
compiler-bot/agentic
```

### Flags nuevos

```text
--dashboard
--host
--port
```

### Comportamiento

- Si `--dashboard` esta presente, arrancar servidor y no requerir `--prompt`.
- `--host` default `127.0.0.1`.
- `--port` default `8765`.
- Mensaje a stdout/stderr con URL:

```text
Dashboard listening on http://127.0.0.1:8765
```

- Mantener intactos:
  - `--prompt`
  - `--file`
  - `--metrics`
  - `--debug`
  - `--chain`
  - `--offline`

### Verificacion manual

```sh
./compiler-bot/agentic --dashboard --host 127.0.0.1 --port 8765
curl http://127.0.0.1:8765/api/health
```

## 11. Fase 7: UI Estatica

### Objetivo

Crear dashboard visual operativo sin build step.

### Archivos

```text
compiler-bot/agentic_pipeline/dashboard/static/index.html
compiler-bot/agentic_pipeline/dashboard/static/dashboard.css
compiler-bot/agentic_pipeline/dashboard/static/dashboard.js
```

### Requisitos UI

- Primera pantalla debe ser el dashboard, no una landing page.
- Layout sobrio, denso y operativo.
- KPIs visibles:
  - total records
  - total errors
  - success rate
  - prompt-chain success rate
- Tabla por stage:
  - stage
  - runs
  - errors
  - success rate
  - ultima actualizacion si esta disponible
- Panel de detalle:
  - registros recientes del stage seleccionado
  - metricas crudas resumidas
- Estados:
  - loading
  - sin datos
  - error de API
- Refresco manual con boton.
- Sin texto explicativo largo dentro de la app.

### Criterios frontend

- Sin solapes en mobile y desktop.
- Sin cartas anidadas.
- Sin hero ni marketing copy.
- No depender de CDN externo.
- Usar HTML/CSS/JS locales.

### Verificacion manual

```sh
./compiler-bot/agentic --dashboard
# Abrir http://127.0.0.1:8765
```

## 12. Fase 8: Documentacion Operativa

### Objetivo

Documentar uso, comandos y limitaciones.

### Archivos candidatos

- `README.md`
- `docs/136_GUIDE_DEV_PROJECT0_RUNBOOK_1_0_ACTIVE.md`
- `compiler-bot/agentic_pipeline/dashboard/README.md`

### Contenido minimo

```sh
./compiler-bot/agentic --dashboard
./compiler-bot/agentic --dashboard --host 127.0.0.1 --port 8765
./compiler-bot/agentic --metrics json
```

Incluir nota:

- Las metricas son acumuladas.
- El dashboard usa `MetricsStore`.
- Si `_sqlite3` no existe, se usa JSON fallback.

## 13. Fase 9: Gate Diario

### Objetivo

Formalizar el gate diario estable de la propuesta 137.

### Opcion A: Solo documentacion

Agregar al runbook/README:

```sh
ruff check compiler-bot/agentic_pipeline
bash compiler-bot/tests/run_tests.sh
bash compiler-bot/tests/test_agent.sh
./compiler-bot/agentic --metrics json
```

### Opcion B: Script ejecutable

Crear:

```text
scripts/daily_check.sh
```

Reglas:

- Ejecuta los cuatro comandos.
- No ejecuta la suite Python completa.
- Imprime resumen PASS/FAIL.
- Sale `1` si falla cualquiera.

La opcion B es recomendada si se quiere repetir el gate con menos friccion.

## 14. Fase 10: Gate de Release

### Objetivo

Definir gate mas estricto para release/CI confiable.

### Comandos

```sh
bash scripts/check_version_alignment.sh
ruff check compiler-bot/agentic_pipeline
bash compiler-bot/tests/run_tests.sh
bash compiler-bot/tests/test_agent.sh
./compiler-bot/agentic --metrics json
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
```

### Nota critica

El ultimo comando todavia esta marcado como inestable en el runbook 136. No debe
ser obligatorio para trabajo diario, pero si debe bloquear release hasta que se
resuelvan:

- `_sqlite3` ausente en el Python local.
- `torch/CUDA` con `libcudart.so.13` corrupto o incompleto.
- tests que importan `HybridPlanner` cuando la clase real actual es
  `ReasoningEngine`.

## 15. Matriz de Dependencias

| Fase | Depende de | Puede ejecutarse en paralelo |
|---|---|---|
| Fase 0 | ninguna | no |
| Fase 1 | Fase 0 | no |
| Fase 2 | Fase 1 | no |
| Fase 3 | Fase 2 | no |
| Fase 4 | Fase 0 | Fase 1-3 parcialmente |
| Fase 5 | Fase 4 | no |
| Fase 6 | Fase 5 | no |
| Fase 7 | Fase 5 | parcialmente con Fase 6 |
| Fase 8 | Fase 6-7 | no |
| Fase 9 | Fase 0 | si |
| Fase 10 | Fase 1-3 | si, salvo pytest completo |

## 16. Secuencia Recomendada de Commits

| Commit | Contenido |
|---|---|
| 1 | version alignment + `check_version_alignment.sh` + CI |
| 2 | `dashboard/service.py` + tests |
| 3 | `dashboard/app.py` + API tests |
| 4 | CLI `--dashboard` |
| 5 | UI estatica |
| 6 | docs + daily/release gate |

Mantener commits pequenos permite revertir UI sin perder version alignment.

## 17. Criterios de Aceptacion Globales

La ejecucion se considera completa cuando:

- `VERSION`, `pyproject.toml` y `CHANGELOG.md` coinciden.
- `scripts/check_version_alignment.sh` pasa localmente y esta en CI.
- `./compiler-bot/agentic --dashboard` arranca servidor local.
- `/api/health`, `/api/summary`, `/api/stages` y `/api/stages/<stage>/recent`
  responden correctamente.
- La UI muestra KPIs, tabla por stage y detalle de registros recientes.
- El gate diario queda documentado o automatizado.
- `./compiler-bot/agentic --metrics json|table` no cambia su contrato existente.
- `ruff check compiler-bot/agentic_pipeline` pasa.
- Tests nuevos de dashboard pasan con `-o addopts=`.
- Tests shell RECPL y agent-robot siguen pasando.

## 18. Riesgos de Ejecucion

| Riesgo | Probabilidad | Impacto | Mitigacion |
|---|---:|---:|---|
| Changelog avanza durante implementacion | Media | Bajo | Usar siempre primera cabecera como version canonica |
| `http.server` queda incomodo para tests | Baja | Medio | Aislar handler factory y usar puerto efimero |
| MetricsStore con fallback JSON contiene datos historicos grandes | Media | Medio | Limitar registros recientes y ordenar por stage |
| UI estatica crece demasiado | Media | Medio | Mantener MVP: KPIs, tabla, detalle, refresh |
| CI falla por pytest completo | Alta | Alto | Separar gate diario de release; no mezclar con MVP dashboard |

## 19. Checklist Final

- [ ] Versiones alineadas.
- [ ] Script de versionado ejecutable.
- [ ] CI con check de versionado.
- [ ] Servicio dashboard implementado.
- [ ] API dashboard implementada.
- [ ] CLI `--dashboard` implementado.
- [ ] UI estatica implementada.
- [ ] Tests dashboard agregados.
- [ ] Runbook/README actualizado.
- [ ] Gate diario documentado o automatizado.
- [ ] Changelog actualizado.
