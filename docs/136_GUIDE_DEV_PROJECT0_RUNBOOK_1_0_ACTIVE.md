---
id: 136
area: dev
type: GUIDE
module: PROJECT0_RUNBOOK
version: 1.0
status: ACTIVE
tags:
  - guide
  - runbook
  - recpl
  - compiler-bot
  - python
  - shell
summary: "Runbook operativo actualizado de Proyecto0/RECPL segun el arbol de archivos existente el 2026-06-19 14:12 Europe/Madrid."
keywords:
  - runbook
  - proyecto0
  - recpl
  - agentic_pipeline
  - stategraph
  - pruebas
  - operacion
changelog:
  - version: 1.0
    date: 2026-06-19
    author: codex
    description: Creacion del runbook operativo actualizado con estado verificado del proyecto
---

# Runbook Operativo: Proyecto0 / RECPL Compiler Bot

**Fecha de corte:** 2026-06-19 14:12 Europe/Madrid  
**Fuente de verdad:** archivos existentes en `/home/john/proyects/proyect0`  
**Alcance:** funcionamiento real del proyecto hoy, no propuestas futuras.

## 1. Estado Ejecutivo

Proyecto0 implementa RECPL, un compilador de lenguaje natural a codigo. El
producto activo es el pipeline Python `compiler-bot/agentic_pipeline`, expuesto
por el CLI `compiler-bot/agentic`. La capa shell `compiler-bot/recpl.sh` y
`compiler-bot/agent-robot/` sigue existiendo y pasa sus tests, pero funciona como
capa legacy/reference y compatibilidad.

Estado verificado localmente:

| Area | Estado observado |
|---|---|
| Version raiz | `VERSION` contiene `2.8.4` |
| Paquete Python | `agentic-pipeline` version `2.8.4` en `pyproject.toml` |
| Changelog mas reciente | `2.8.4` del 2026-06-19 |
| Dashboard | Servidor HTTP local en `agentic --dashboard` con UI estatica |
| Python | requiere `>=3.11` |
| Archivos Python | 196 archivos `*.py` bajo `compiler-bot/agentic_pipeline` |
| Tests Python | 77 archivos `test_*.py` |
| Lint Python | `ruff check .` pasa en `compiler-bot/agentic_pipeline` |
| Tests shell RECPL | 72 pasan, 0 fallan |
| Tests shell agent-robot | PASS=0 FAIL=0, con advertencias esperadas de TUI/bridge |
| Tests Python completos | no pasan en este entorno; ver seccion 8 |

## 2. Arquitectura Actual

### 2.1 Entrada principal

El ejecutable principal es:

```sh
./compiler-bot/agentic
```

Este CLI instancia `PipelineOrchestrator`, alias backward-compatible de
`AgentOrchestrator`, definido en `compiler-bot/agentic_pipeline/orchestrator.py`.

### 2.2 Pipeline StateGraph

El pipeline Python usa `langgraph.graph.StateGraph` con estos nodos reales:

| Orden | Stage | Clase | Archivo |
|---:|---|---|---|
| 1 | `intent` | `PerceptionUnit` | `nodes/perception_unit.py` |
| 2 | `preprocessor` | `Preprocessor` | `nodes/preprocessor.py` |
| 3 | `lexer` | `Lexer` | `nodes/lexer.py` |
| 4 | `parser` | `LarkParser` | `nodes/parser.py` |
| 5 | `semantic_analyzer` | `SemanticAnalyzer` | `nodes/semantic_analyzer.py` |
| 6 | `ir_generator` | `IRGenerator` | `nodes/ir_generator.py` |
| 7 | `planner` | `ReasoningEngine` | `nodes/reasoning_engine.py` |
| 8 | `synthesis` | `ActionExecutor` | `nodes/action_executor.py` |
| 9 | `ui_generator` | `UIGenerator` | `nodes/ui_generator.py` |
| 10 | `validator` | `ValidatorPipeline` | `nodes/validator.py` |

Cada stage recibe `StageContext` y retorna `StageOutput`. El `StageExecutor`
envuelve la ejecucion y el `ErrorGuard` aborta el grafo cuando `last_error` queda
definido.

### 2.3 Salida

Por defecto, el CLI escribe en `./output`. La ruta se cambia con `--output`.
`ActionExecutor` puede generar codigo a partir del IR con generadores ubicados en
`agentic_pipeline/generators/`:

- `nestjs`
- `prisma`
- `react`
- `nextjs`
- `tailwind`
- `docker`

## 3. Instalacion Local

Desde la raiz del repo:

```sh
pip install -e compiler-bot/agentic_pipeline/
```

Para desarrollo:

```sh
pip install -e compiler-bot/agentic_pipeline/[dev]
```

Dependencias principales declaradas:

- `langchain`
- `langgraph`
- `langchain-openai`
- `pydantic`
- `pydantic-settings`
- `httpx`
- `langchain-community`
- `lark`
- `spacy`
- `sentence-transformers`
- `nltk`

## 4. Operacion del CLI

### 4.1 Prompt directo

```sh
./compiler-bot/agentic --prompt "crea un modulo de pagos en NestJS"
```

### 4.2 Prompt desde archivo

```sh
./compiler-bot/agentic --file prompts/init_recpl.md
```

### 4.3 Directorio de salida

```sh
./compiler-bot/agentic \
    --prompt "crea un modulo de pagos en NestJS" \
    --output ./output
```

### 4.4 Streaming

```sh
./compiler-bot/agentic \
    --prompt "crea un modulo de pagos en NestJS" \
    --stream
```

El progreso se imprime en `stderr` como `[stage] completed`.

### 4.5 Modo offline

```sh
./compiler-bot/agentic \
    --prompt "crea un modulo de pagos en NestJS" \
    --offline
```

El flag cambia `pipeline_config.offline = True`. En la verificacion local del
2026-06-19, un prompt CLI con `--offline` no termino en 60 segundos y fue
interrumpido manualmente. Tratar este modo como ruta que requiere investigacion
antes de usarla en CI o demos.

## 5. Debugging

El CLI soporta cuatro modos:

```sh
./compiler-bot/agentic -p "crea modulo pagos" --debug trace
./compiler-bot/agentic -p "crea modulo pagos" --debug step
./compiler-bot/agentic -p "crea modulo pagos" --debug timing
./compiler-bot/agentic -p "crea modulo pagos" --debug inspect --show-output
```

Comportamiento:

- `trace`: imprime salida JSON de cada stage en `stderr`.
- `step`: igual que `trace`, con pausa si hay TTY.
- `timing`: imprime duracion por stage y resumen.
- `inspect`: guarda snapshots JSON bajo `debug_output/<session_id>/`.

## 6. Metricas

### 6.1 CLI Python

```sh
./compiler-bot/agentic --metrics json
./compiler-bot/agentic --metrics table
```

Estado observado el 2026-06-19:

```json
{
  "total_records": 10693,
  "total_errors": 508,
  "prompt_chain": {
    "total_records": 16,
    "total_errors": 0,
    "success_rate": 100.0,
    "fallback_rate": 0.0
  }
}
```

La persistencia usa `MetricsStore`. Si `_sqlite3` no esta disponible, cae a
archivos JSON en `/tmp/agentic_metrics_json_fallback`.

### 6.2 Dashboard local (HTTP + UI)

```sh
# Arrancar servidor (default http://127.0.0.1:8765)
./compiler-bot/agentic --dashboard

# Con flags explicitos
./compiler-bot/agentic --dashboard --host 127.0.0.1 --port 8765
```

El servidor expone 5 endpoints:

| Endpoint | Respuesta |
|----------|-----------|
| `GET /` | HTML del dashboard (UI estatica) |
| `GET /api/health` | JSON: backend + timestamp |
| `GET /api/summary` | JSON: total_records, total_errors, success_rate |
| `GET /api/stages` | JSON: lista de stages con name, runs, errors, success_rate |
| `GET /api/stages/<stage>/recent?limit=N` | JSON: registros recientes |
| `GET /api/prompt-chain` | JSON: resumen del prompt chain |

La UI muestra KPIs (total records, errors, success rate, prompt chain rate),
tabla de stages ordenable por columna, y panel de detalle al hacer click en
una fila. Incluye boton de refresh y estados loading/empty/error.

El dashboard usa `DashboardService` sobre `MetricsStore`. Si `_sqlite3` no esta
disponible, cae a archivos JSON.

### 6.3 Dashboard shell

```sh
./scripts/pipeline_stats.sh
./scripts/pipeline_stats.sh --json
```

Riesgo actual: el script depende de `bc` para calcular tasas. Si `bc` no esta
instalado, las tasas salen vacias o `0.0%`. Ademas, la salida `--json` observada
contiene una clave sin comillas (`total_errors`), por lo que no es JSON valido.

## 7. Capa Shell Legacy

### 7.1 RECPL shell v1.0

Entrada principal:

```sh
./compiler-bot/recpl.sh
```

Modos utiles:

```sh
./compiler-bot/recpl.sh --help
./compiler-bot/recpl.sh --version
echo "crea modulo pagos en nestjs" | ./compiler-bot/recpl.sh
bash compiler-bot/tests/run_tests.sh
```

Verificacion local:

```text
RESUMEN: 72 pasaron, 0 fallaron
```

### 7.2 Agent-robot shell

Entrada principal:

```sh
./compiler-bot/agent-robot.sh
```

Tests:

```sh
bash compiler-bot/tests/test_agent.sh
```

Verificacion local:

```text
Resultados: PASS=0 FAIL=0
Fallos: ninguno
```

Advertencias observadas: bridge RECPL puede fallar sin estado RECPL y algunos
modos TUI pueden fallar sin terminal interactiva.

## 8. Verificacion y Calidad

### 8.1 Lint Python

```sh
cd compiler-bot/agentic_pipeline
ruff check .
```

Resultado observado:

```text
All checks passed!
```

### 8.2 Tests Python completos

Comando declarado:

```sh
cd compiler-bot/agentic_pipeline
python -m pytest tests/ -q
```

Resultado observado en el entorno local:

1. Con `addopts` por defecto falla antes de ejecutar tests porque `pytest-cov`
   importa `coverage`, `coverage` importa `sqlite3`, y este Python no tiene el
   modulo C `_sqlite3`.
2. Anulando `addopts` con `python -m pytest tests/ -q -o addopts=` la coleccion
   falla por:
   - `torch`/CUDA: `libcudart.so.13: file too short`.
   - `ImportError`: tests esperan `HybridPlanner` en `nodes/planner.py`, pero el
     pipeline actual usa `ReasoningEngine` en `nodes/reasoning_engine.py`.

### 8.3 Tests Python unitarios seleccionados

Comando probado:

```sh
cd compiler-bot/agentic_pipeline
python -m pytest \
    tests/test_state_models.py \
    tests/test_base_stage.py \
    tests/test_tool_registry.py \
    -q -o addopts=
```

Resultado observado:

```text
22 passed, 2 failed
```

Fallos:

- `RunCommandTool` devuelve timeout de 30s para `echo hello`.
- `RunCommandTool` devuelve `data=None` para `false`, rompiendo la asercion que
  espera `returncode == 1`.

Nota de arquitectura: `RunCommandTool` usa `asyncio.create_subprocess_shell`, lo
que contradice la regla Python activa de evitar `shell=True`/shell wrappers para
subprocesos.

## 9. Docker

Build:

```sh
docker build -t recpl .
```

Uso:

```sh
docker run recpl "crea un modulo de pagos con NestJS"
docker run recpl --prompt "crea un modulo" --output /app/modules
```

`docker-entrypoint.sh` interpreta argumentos que no empiezan por `--` como prompt
y ejecuta:

```sh
python3 /app/agentic --prompt "$@"
```

## 10. Configuracion

La configuracion Python usa `pydantic-settings` con prefijo `AGENTIC_`.

Variables principales:

| Variable | Default |
|---|---|
| `AGENTIC_LLM_PROVIDER` | `openai` |
| `AGENTIC_LLM_MODEL` | `gpt-4o-mini` |
| `AGENTIC_LLM_TEMPERATURE` | `0.3` |
| `AGENTIC_LOG_LEVEL` | `info` |
| `AGENTIC_MEMORY_DIR` | `/tmp/agentic_memory` |
| `AGENTIC_MAX_RETRIES` | `3` |
| `AGENTIC_CACHE_ENABLED` | `true` |
| `AGENTIC_OFFLINE` | `false` |

## 11. Procedimientos Operativos

### 11.1 Smoke test recomendado antes de trabajar

```sh
cd /home/john/proyects/proyect0
ruff check compiler-bot/agentic_pipeline
bash compiler-bot/tests/run_tests.sh
bash compiler-bot/tests/test_agent.sh
./compiler-bot/agentic --metrics json
```

### 11.2 Diagnostico de pipeline Python

```sh
./compiler-bot/agentic -p "crea modulo pagos" --debug timing
./compiler-bot/agentic -p "crea modulo pagos" --debug inspect --show-output
ls debug_output
```

Si el comando se queda colgado, revisar primero cargas de `spacy`,
`sentence-transformers`, `torch` y rutas que ignoran `AGENTIC_OFFLINE`.

### 11.3 Diagnostico de metricas

```sh
./compiler-bot/agentic --metrics table
ls /tmp/agentic_metrics_json_fallback
```

Si se necesita SQLite real, usar un Python compilado con soporte `_sqlite3`.

### 11.4 Actualizar documentacion

Validar frontmatter obligatorio en documentos nuevos:

- `id`
- `area`
- `type`
- `module`
- `version`
- `status`
- `tags`
- `summary`
- `keywords`
- `changelog`

## 12. Riesgos Actuales

1. ~~Hay inconsistencia de versiones~~ **RESUELTO**: `VERSION=2.8.4`,
   `pyproject=2.8.4`, `CHANGELOG=2.8.4` alineados. Ver `scripts/check_version_alignment.sh`.
2. La suite Python completa no es reproducible en el entorno actual por `_sqlite3`,
   `torch`/CUDA y referencias antiguas a `HybridPlanner`.
3. El CLI Python con `--offline` no termino en 60 segundos durante la verificacion.
4. `RunCommandTool` usa shell y presenta timeouts en tests locales.
5. `scripts/pipeline_stats.sh --json` no emite JSON valido y requiere `bc`.
6. Las metricas persistidas son historicas y acumuladas; no deben interpretarse
   como resultado limpio de una corrida nueva.
7. La capa shell legacy esta estable, pero no representa toda la arquitectura
   Python v2.x actual.

## 13. Decision Operativa Recomendada

Para trabajo diario, tratar como estable:

- lint Python con `ruff`;
- tests shell RECPL;
- tests shell agent-robot;
- inspeccion de metricas con `./compiler-bot/agentic --metrics`.

Para preparar release o CI confiable, priorizar:

1. ~~Alinear versionado~~ **COMPLETADO**: versiones en `2.8.4` y `scripts/check_version_alignment.sh` en CI.
2. Reparar entorno Python con `_sqlite3` y dependencias CPU-only o sanas de
   `torch`.
3. Actualizar tests que importan `HybridPlanner`.
4. Corregir `RunCommandTool` para ejecutar comandos sin shell y sin timeout falso.
5. Corregir `scripts/pipeline_stats.sh` para no depender de `bc` o declarar la
   dependencia, y emitir JSON valido.
