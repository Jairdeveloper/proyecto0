---
id: 137
area: dev
type: PROP
module: METRICS_DASHBOARD_VERSIONING
version: 1.0
status: DRAFT
tags:
  - proposal
  - dashboard
  - metrics
  - versioning
  - release
  - ci
summary: "Propuesta de implementacion para una UI de dashboard de metricas basada en la propuesta 120 y para alinear VERSION, pyproject.toml y CHANGELOG.md como paso previo a release/CI confiable."
keywords:
  - dashboard
  - metrics-store
  - agentic
  - version
  - changelog
  - ci
  - release
changelog:
  - version: 1.0
    date: 2026-06-19
    author: codex
    description: Creacion de propuesta ejecutable para dashboard de metricas y alineacion de versionado
---

# Propuesta de Implementacion: Dashboard de Metricas y Alineacion de Versionado

**Fecha:** 2026-06-19  
**Fuentes analizadas:**  
- `docs/120_PROP_DEV_DASHBOARD_MVP_1_0_DRAFT.md`
- `docs/136_GUIDE_DEV_PROJECT0_RUNBOOK_1_0_ACTIVE.md`

## 1. Resumen Ejecutivo

Se propone implementar un dashboard operativo de metricas para Proyecto0/RECPL
con una UI web local que lea las metricas existentes de `MetricsStore` y exponga
el mismo estado que hoy se consulta por CLI con:

```sh
./compiler-bot/agentic --metrics json
./compiler-bot/agentic --metrics table
```

La propuesta 120 aporta dos ideas utiles:

1. Un dashboard debe tratarse como una UI generable/operable desde features, no
   como una extension rigida de DFA, gramatica e IR para cada widget.
2. El sistema ya tiene infraestructura de metricas, observers y generadores que
   permiten construir un MVP sin redisenar todo el pipeline.

El runbook 136 fija el criterio operativo actual:

- Para trabajo diario son estables `ruff`, los tests shell RECPL, los tests
  shell agent-robot y la inspeccion de metricas por CLI.
- Para release/CI confiable hay que alinear `VERSION`, `pyproject.toml` y
  `CHANGELOG.md`.

Esta propuesta convierte ambos puntos en un plan de implementacion incremental.

## 2. Estado Actual Observado

### 2.1 Metricas disponibles

El proyecto ya tiene:

- `compiler-bot/agentic_pipeline/metrics_store.py`
  - SQLite si `_sqlite3` esta disponible.
  - Fallback JSON en `/tmp/agentic_metrics_json_fallback`.
  - `summary()`, `get_recent()`, metricas por stage y metricas de prompt-chain.
- `compiler-bot/agentic --metrics json|table`
  - Expone resumen agregado.
- `scripts/pipeline_stats.sh`
  - Dashboard shell minimo, pero con riesgos documentados.
- `compiler-bot/agentic_pipeline/observers/dashboard_observer.py`
  - Buffer de eventos recientes y stub de WebSocket.

### 2.2 Riesgos que condicionan el MVP

El runbook 136 documenta riesgos actuales que el MVP debe respetar:

- La suite Python completa no es reproducible en este entorno por `_sqlite3`,
  `torch/CUDA` y referencias antiguas a `HybridPlanner`.
- `scripts/pipeline_stats.sh --json` no emite JSON valido y depende de `bc`.
- Las metricas persistidas son historicas/acumuladas.
- Hay inconsistencia de versionado:
  - `VERSION=2.0.0`
  - `pyproject.toml` declara `0.1.0`
  - `CHANGELOG.md` llega a `2.8.2`

## 3. Objetivos

### 3.1 Dashboard de metricas

Crear una UI local de dashboard que permita:

- Ver resumen global de ejecuciones: total, errores, tasa de exito.
- Ver conteo por stage.
- Ver errores por stage.
- Ver metricas de prompt-chain.
- Ver ultimos eventos/ejecuciones por stage.
- Refrescar manualmente y, en una fase posterior, recibir eventos en vivo.

### 3.2 Trabajo diario estable

Formalizar un gate diario minimo:

```sh
ruff check compiler-bot/agentic_pipeline
bash compiler-bot/tests/run_tests.sh
bash compiler-bot/tests/test_agent.sh
./compiler-bot/agentic --metrics json
```

### 3.3 Release/CI confiable

Alinear el versionado antes de declarar una release:

- `VERSION`
- `compiler-bot/agentic_pipeline/pyproject.toml`
- cabecera mas reciente de `CHANGELOG.md`

## 4. No Objetivos

El MVP no debe:

- Cablear aun `RequirementDecomposer` en el pipeline principal.
- Crear un dashboard generado por el propio RECPL como salida de usuario final.
- Resolver toda la suite Python completa.
- Introducir React/Next.js si eso obliga a una toolchain Node para un panel
  interno.
- Reemplazar `MetricsStore`.

La prioridad es un dashboard interno, local, verificable y de bajo riesgo.

## 5. Arquitectura Propuesta

### 5.1 Componentes nuevos

```text
compiler-bot/agentic_pipeline/dashboard/
├── __init__.py
├── app.py              # servidor HTTP local
├── service.py          # adaptador de MetricsStore a view models
├── static/
│   ├── index.html      # UI dashboard
│   ├── dashboard.css
│   └── dashboard.js
└── README.md
```

### 5.2 CLI

Agregar flag al ejecutable existente:

```sh
./compiler-bot/agentic --dashboard
./compiler-bot/agentic --dashboard --host 127.0.0.1 --port 8765
```

El servidor debe abrir solo en localhost por defecto.

### 5.3 API minima

El MVP puede implementarse con `http.server` de stdlib para evitar dependencias
nuevas. Endpoints:

| Metodo | Ruta | Descripcion |
|---|---|---|
| `GET` | `/` | Sirve `static/index.html` |
| `GET` | `/api/summary` | Resumen de `MetricsStore.summary()` + prompt-chain |
| `GET` | `/api/stages` | Conteo, errores y tasa por stage |
| `GET` | `/api/stages/<stage>/recent?limit=20` | Ultimos registros del stage |
| `GET` | `/api/health` | Estado del dashboard y backend de metricas |

Fase posterior opcional: migrar a FastAPI si se necesita OpenAPI, WebSockets o
autenticacion. No es requisito para el MVP.

### 5.4 UI

La UI debe ser una herramienta operativa, no una landing page:

- Barra superior compacta: version, backend de metricas, timestamp.
- KPIs: total records, total errors, success rate, prompt-chain success rate.
- Tabla por stage: runs, errors, success rate, ultima actualizacion.
- Panel de detalle: ultimos registros de un stage seleccionado.
- Estados vacios claros: sin metricas, sin stage, backend JSON fallback.

No requiere build step. `index.html`, `dashboard.css` y `dashboard.js` son
artefactos estaticos servidos por Python.

## 6. Relacion con la Propuesta 120

La propuesta 120 defiende un enfoque adaptativo para dashboards: no extender el
lenguaje formal por cada tipo de widget, sino derivar features y generar UI segun
necesidad. Para este MVP se aplica el mismo principio, pero acotado:

- Las "features" del dashboard son fijas y salen de `MetricsStore`.
- La UI se construye como dashboard operativo interno.
- No se modifica lexer, parser, semantic analyzer ni IR.
- Se deja preparado un camino posterior para que RECPL pueda generar dashboards
  externos usando el enfoque adaptativo de la propuesta 120.

Decision: implementar primero un dashboard de metricas como producto interno; no
mezclarlo con el pipeline generativo hasta que el dashboard sea observable y
testeable.

## 7. Plan de Implementacion

### Fase 1: Servicio de metricas para UI

| ID | Tarea | Archivos | Criterio |
|---|---|---|---|
| D1.1 | Crear `dashboard/service.py` | nuevo | Expone `get_summary()`, `get_stages()`, `get_recent(stage)` |
| D1.2 | Calcular success rate sin `bc` ni shell | `service.py` | Tasas correctas con cero registros |
| D1.3 | Detectar backend SQLite/JSON fallback | `service.py` | `/api/health` reporta backend |
| D1.4 | Tests unitarios con `tmp_path` | `tests/test_dashboard_service.py` | No toca `/tmp` real |

### Fase 2: Servidor HTTP local

| ID | Tarea | Archivos | Criterio |
|---|---|---|---|
| D2.1 | Crear `dashboard/app.py` con stdlib HTTP server | nuevo | Sirve `/` y `/api/summary` |
| D2.2 | Manejar 404 y errores JSON | `app.py` | Respuestas deterministicamente JSON |
| D2.3 | Agregar `--dashboard`, `--host`, `--port` | `compiler-bot/agentic` | CLI arranca servidor local |
| D2.4 | Tests de endpoints con puerto efimero | `tests/test_dashboard_app.py` | No requiere red externa |

### Fase 3: UI estatica

| ID | Tarea | Archivos | Criterio |
|---|---|---|---|
| D3.1 | Crear layout HTML operativo | `static/index.html` | Render inicial sin datos |
| D3.2 | Crear CSS responsive | `static/dashboard.css` | Desktop y mobile sin solapes |
| D3.3 | Crear JS fetch/render | `static/dashboard.js` | Lee `/api/summary` y `/api/stages` |
| D3.4 | Estados vacios/error/loading | archivos static | UI no queda en blanco |

### Fase 4: Integracion con workflow diario

| ID | Tarea | Archivos | Criterio |
|---|---|---|---|
| D4.1 | Agregar comando al README o runbook | docs | Operador sabe iniciar dashboard |
| D4.2 | Agregar smoke test dashboard al gate diario opcional | docs/CI | Endpoint `/api/health` responde |
| D4.3 | Mantener `./compiler-bot/agentic --metrics` como fuente estable | CLI | No rompe comandos existentes |

## 8. Alineacion de Versionado

### 8.1 Version canonica propuesta

Usar como fuente canonica inicial la ultima entrada de `CHANGELOG.md`.
Actualmente, tras registrar esta propuesta:

```text
2.8.2
```

### 8.2 Cambios requeridos

| Archivo | Estado actual | Cambio propuesto |
|---|---|---|
| `VERSION` | `2.0.0` | `2.8.2` |
| `compiler-bot/agentic_pipeline/pyproject.toml` | `version = "0.1.0"` | `version = "2.8.2"` |
| `CHANGELOG.md` | llega a `2.8.2` | se mantiene como referencia canonica |
| `README.md` | badge/tests posiblemente desfasados | actualizar solo si se modifica release |

### 8.3 Script de verificacion

Agregar script:

```text
scripts/check_version_alignment.sh
```

Reglas:

1. Leer `VERSION`.
2. Leer `project.version` de `compiler-bot/agentic_pipeline/pyproject.toml`.
3. Leer la primera cabecera `## [x.y.z]` de `CHANGELOG.md`.
4. Fallar si las tres versiones no coinciden.

No usar dependencias externas. Puede implementarse con `awk`/`sed`.

### 8.4 Integracion CI

Agregar paso al workflow existente `.github/workflows/ci.yml`:

```sh
bash scripts/check_version_alignment.sh
```

Ubicacion recomendada: job `lint`, despues de checkout y antes de instalar
dependencias Python.

## 9. Gate Diario y Gate de Release

### 9.1 Gate diario estable

Este gate es el minimo recomendado por el runbook 136:

```sh
ruff check compiler-bot/agentic_pipeline
bash compiler-bot/tests/run_tests.sh
bash compiler-bot/tests/test_agent.sh
./compiler-bot/agentic --metrics json
```

Debe documentarse como `make daily-check` o script equivalente en una fase
posterior. No requiere arreglar la suite Python completa.

### 9.2 Gate de release confiable

Antes de tag/release:

```sh
bash scripts/check_version_alignment.sh
ruff check compiler-bot/agentic_pipeline
bash compiler-bot/tests/run_tests.sh
bash compiler-bot/tests/test_agent.sh
./compiler-bot/agentic --metrics json
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
```

Nota: el ultimo comando todavia no es estable en el entorno documentado. La
release debe bloquearse hasta resolver `_sqlite3`, `torch/CUDA` y los tests que
importan `HybridPlanner`, o hasta marcar/aislar esos tests correctamente.

## 10. Criterios de Aceptacion

### Dashboard MVP

- `./compiler-bot/agentic --dashboard` arranca un servidor local.
- `GET /api/health` responde JSON.
- `GET /api/summary` devuelve `total_records`, `total_errors`, `success_rate`.
- `GET /api/stages` devuelve lista ordenable por stage.
- La UI muestra KPIs y tabla por stage sin depender de Node.js.
- La UI maneja estado sin metricas.
- Tests unitarios cubren servicio y API.

### Versionado

- `VERSION`, `pyproject.toml` y primera cabecera de `CHANGELOG.md` coinciden.
- `scripts/check_version_alignment.sh` falla con mensaje claro si no coinciden.
- CI ejecuta el check de versionado.

### Trabajo diario

- Los cuatro comandos del gate diario se ejecutan y quedan documentados.
- `./compiler-bot/agentic --metrics json` sigue funcionando despues del dashboard.

## 11. Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| `_sqlite3` no disponible | MetricsStore cae a JSON fallback | Dashboard debe soportar ambos backends |
| Metricas historicas acumuladas | Tasas confusas | UI debe indicar backend, timestamp y total acumulado |
| `pipeline_stats.sh` JSON invalido | No usarlo como backend del dashboard | Leer `MetricsStore` directamente |
| Tests Python completos inestables | Release bloqueada | Separar gate diario de gate release |
| Agregar FastAPI aumenta dependencias | Mayor superficie de fallo | MVP con stdlib HTTP server |
| Versionado divergente | Releases ambiguas | Script de alineacion en CI |

## 12. Orden Recomendado

1. Alinear versionado y agregar `scripts/check_version_alignment.sh`.
2. Integrar el check de versionado en CI.
3. Crear `dashboard/service.py` y tests.
4. Crear `dashboard/app.py` y flag `--dashboard`.
5. Crear UI estatica.
6. Documentar uso en runbook/README.
7. Evaluar fase posterior con WebSocket usando `DashboardObserver`.

## 13. Estimacion

| Bloque | Esfuerzo |
|---|---:|
| Version alignment + script + CI | 2h |
| Servicio dashboard | 3h |
| Servidor HTTP local | 3h |
| UI estatica | 5h |
| Tests y documentacion | 4h |
| Total | 17h |

## 14. Resultado Esperado

Al finalizar, Proyecto0 tendra:

- Una UI local de dashboard de metricas basada en datos reales de `MetricsStore`.
- Un camino operativo diario claro y estable.
- Versionado consistente entre `VERSION`, `pyproject.toml` y `CHANGELOG.md`.
- Un check automatizable para evitar nuevas divergencias de version.
