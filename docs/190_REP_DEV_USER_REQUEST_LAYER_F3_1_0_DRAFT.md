---
id: 190
area: DEV
type: REP
module: USER_REQUEST_LAYER
version: 1.0
status: DRAFT
tags:
  - user-request
  - nlg
  - natural-language-generation
  - formatters
  - adapters
  - templates
summary: Reporte de implementacion de la Fase 3 — NLG Pipeline (generacion de lenguaje natural)
keywords:
  - NLG
  - formatters
  - adapters
  - translator
  - pipeline
  - templates
changelog:
  - 2026-06-22: Creacion del reporte Fase 3
---

# Reporte Fase 3 — NLG Pipeline

## Resumen

Se implemento el pipeline NLG (Natural Language Generation) para la capa
User Request. El pipeline transforma un `ResponseObject` en texto formateado,
traducido y adaptado al canal de salida (CLI, API, WebUI, Editor, Agent).

**Commits:** Ninguno aun (pendiente).

## Componentes Implementados

### 1. Formatters (`user_request/nlg/formatters/`)

Patron Strategy + Factory para seleccionar el formateador segun el tipo de
respuesta.

| Componente | Archivo | Proposito |
|-----------|---------|-----------|
| `NLGFormatter` (ABC) | `base.py` | Interfaz comun: `format(response) -> str` |
| `SuccessFormatter` | `success.py` | Formatea respuestas exitosas (mensaje + datos + sugerencias) |
| `ErrorFormatter` | `error.py` | Formatea errores con nivel de detalle y sugerencias |
| `IRFormatter` | `ir_display.py` | Renderiza IR en formato jerarquico legible |
| `MetricFormatter` | `metrics.py` | Muestra metricas del pipeline (stages, errores, duracion) |
| `resolve_formatter()` | `__init__.py` | Factory que inspecciona el `ResponseObject` y elige el formatter adecuado |

### 2. Translator (`user_request/nlg/translator.py`)

Templates de respuestas en espanol e ingles con formato `{placeholder}`.

| Metodo | Proposito |
|--------|-----------|
| `render_template()` | Renderiza una plantilla con argumentos |
| `translate()` | Traduce texto con detector de idioma heuristico |
| `available_templates()` | Lista templates disponibles por idioma |

11 templates por idioma cubriendo: success, success_with_data, error,
error_with_suggestions, ir_display, ask_clarify, confirm, metrics,
files_created, file_created, greeting.

### 3. Adapters (`user_request/nlg/adapters/`)

Patron Strategy + Factory para adaptar la salida al formato del canal.

| Componente | Archivo | Formato de salida |
|-----------|---------|-------------------|
| `ChannelAdapter` (ABC) | `base.py` | Interfaz comun: `adapt(content, response) -> str` |
| `CLIAdapter` | `cli.py` | Texto plano sin adornos |
| `APIAdapter` | `api.py` | JSON (`{"content": ..., "type": ..., "data": ...}`) |
| `WebUIAdapter` | `webui.py` | HTML con clases CSS |
| `EditorAdapter` | `editor.py` | Texto truncado a 500 chars con marcador `[...truncated...]` |
| `AgentAdapter` | `agent.py` | JSON estructurado para consumo por otros agentes |
| `resolve_adapter()` | `__init__.py` | Factory que resuelve el adaptador por `RequestChannel` |

### 4. Pipeline (`user_request/nlg/pipeline.py`)

Orquestador que conecta las 3 etapas:

```
ResponseObject
    │
    ▼
Formatter  →  content (str)
    │
    ▼
Translator  →  translated (str)
    │
    ▼
ChannelAdapter  →  output (str segun canal)
```

- `process()`: retorna el string final
- `process_with_metadata()`: retorna `NLGPipelineResult` con cada etapa intermedia
- `set_channel()`: cambia el canal por defecto

## Tests (51 nuevos)

| Test file | Tests | Proposito |
|-----------|-------|-----------|
| `test_formatters.py` | 15 | Success, Error, IR, Metric formatters + resolve_formatter() |
| `test_translator.py` | 8 | Templates, traduccion, templates por idioma |
| `test_adapters.py` | 18 | CLI, API, WebUI, Editor, Agent adapters + resolve_adapter() |
| `test_nlg_pipeline.py` | 10 | Pipeline completo, overrides, metadata |

**Estado:** 51/51 PASS

## Verificacion de Calidad

- **ruff check:** 0 errores (4 corregidos: imports no usados y `import json` fuera de lugar)
- **ruff format:** sin cambios necesarios
- **Tests legacy (backward compat):** 782 passed, 21 skipped (CUDA pre-existente), 0 fallos nuevos
- **DeprecationWarning:** 1 pre-existente (no introducido por F3)

## Arquitectura

El diseno sigue los mismos patrones que la Fase 2 (NLU):

- **Strategy Pattern:** Formatters y Adapters intercambiables
- **Factory Method:** `resolve_formatter()` y `resolve_adapter()` para seleccion automatica
- **Chain of Responsibility:** Pipeline de 3 etapas secuenciales
- **Dataclasses:** `NLGPipelineResult` para resultados con trazabilidad

## Backward Compatibility

Sin cambios en codigo legacy. Todos los componentes NLG son nuevos y
totalmente independientes.

## Proximos Pasos

1. **Fase 4:** Integracion en CLI — modificar `agentic` entrypoint para
   usar `NLUPipeline` + `NLGPipeline`, flags `--json`, `--ir-only`,
   modo dialogo interactivo
2. **Fase 5:** Canales adicionales — endpoints HTTP
3. **Fase 6:** Limpieza — deprecar legacy, actualizar imports en toda la
   base de codigo
