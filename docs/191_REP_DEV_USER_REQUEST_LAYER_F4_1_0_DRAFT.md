---
id: 191
area: DEV
type: REP
module: USER_REQUEST_LAYER
version: 1.0
status: DRAFT
tags:
  - user-request
  - nlu
  - nlg
  - cli
  - integration
  - facade
  - dialog
summary: Reporte de implementacion de la Fase 4 — Integracion en CLI (UserRequestLayer facade + entrypoint agentic)
keywords:
  - UserRequestLayer
  - CLI
  - entrypoint
  - flags
  - dialog-mode
  - NLG-integration
  - output-formatting
changelog:
  - 2026-06-22: Creacion del reporte Fase 4
---

# Reporte Fase 4 — Integracion en CLI

## Resumen

Se integro la capa User Request (NLU + NLG) con el entrypoint `agentic`.
Se creo la facade `UserRequestLayer` que unifica los pipelines NLU y NLG,
y se modifico el entrypoint para producir mensajes en lenguaje natural
(no JSON crudo) por defecto.

**Commits:** Ninguno aun (pendiente).

## Componentes Implementados

### T4.1 — UserRequestLayer facade (`user_request/layer.py`)

| Metodo | Proposito |
|--------|-----------|
| `process_input(raw)` | Procesa texto via NLUPipeline → `RequestObject` |
| `format_output(response, channel, force_ir)` | Formatea via NLGPipeline → string |
| `resolve_ambiguity(request)` | Genera preguntas para resolver ambiguedades |
| `set_channel(channel)` | Cambia canal de salida (propaga a NLG) |

La facade mantiene los pipelines como atributos publicos (`layer.nlu`,
`layer.nlg`) para acceso directo si es necesario.

`format_output()` soporta `force_ir=True` que fuerza el uso de
`IRFormatter` envolviendo los datos bajo la clave `"ir"`.

### T4.2 — Entrypoint `agentic` modificado

**Nuevos flags:**

| Flag | Tipo | Descripcion |
|------|------|-------------|
| `--json` | flag | Salida JSON (fuerza APIAdapter) |
| `--output-format {text,json}` | opcion | Formato de salida explicito |
| `--no-dialog` | flag | Desactiva modo dialogo interactivo |

**Cambios en el flujo de salida:**

Antes:
```
orchestrator.run(prompt) → dict → json.dumps → print
```

Despues:
```
orchestrator.run(prompt) → dict → ResponseObject → NLGPipeline → print
```

- `--json` o `--output-format json` → canal `RequestChannel.API` → `APIAdapter` produce JSON
- `--ir-only` → `force_ir=True` → `IRFormatter` muestra IR formateado
- defecto → `SuccessFormatter` + `CLIAdapter` → texto legible

### T4.3 — Modo dialogo interactivo

Cuando no se pasa `--no-dialog`, el entrypoint ejecuta:

1. `UserRequestLayer.process_input(prompt)` → detecta ambiguedades
2. `resolve_ambiguity()` → genera preguntas si hay slots faltantes
3. Por cada pregunta: imprime `? {pregunta}` a stderr, lee respuesta de stdin
4. Las respuestas se concatenan al prompt original

El modo dialogo es **no-blocking**: si falla (stdin no disponible), se
captura la excepcion y se continua sin dialogo.

### T4.4 — Tests (23 nuevos)

| Test file | Tests | Proposito |
|-----------|-------|-----------|
| `test_layer.py` | 23 | UserRequestLayer: init, process_input, format_output, resolve_ambiguity, set_channel, edge cases, integracion por canal |

### Verificacion de Calidad

| Gate | Resultado |
|------|-----------|
| `ruff check` — Fase 4 archivos | **0 errores** (2 corregidos: imports no usados) |
| `ruff check` — `agentic` entrypoint | **0 errores** |
| `bash -n agentic` | N/A (es Python) |
| `python -c "compile(...)"` | **Syntax OK** |
| Test Fase 4 (23 tests) | **23/23 PASS** |
| Suite completa `user_request/` (167 tests) | **167/167 PASS** |
| Backward compat (legacy suite) | **782 PASS**, 21 skipped (CUDA), **0 regresiones** |
| `agentic --help` | Muestra nuevos flags `--json`, `--no-dialog`, `--output-format` |

## Arquitectura

```
UserRequestLayer (facade)
  ├── nlu: NLUPipeline
  │     normalizer → classifier → extractor → slot_filler → ambiguity → enricher
  └── nlg: NLGPipeline
        formatter → translator → adapter

agentic entrypoint:
  prompt → [dialog mode] → orchestrator.run(prompt) → dict
    → ResponseObject → UserRequestLayer.format_output() → print
```

## Backward Compatibility

- El entrypoint `agentic` sigue aceptando los mismos flags de siempre
- Los nuevos flags son adicionales, no rompen compatibilidad
- `--ir-only` y `--offline` mantienen su comportamiento exacto
- `--chain` y `--debug` tambien usan NLG output formatting (consistente)
- `--dashboard` y `--metrics` no se modifican (salida directa)

## Proximos Pasos

1. **Fase 5:** Canales adicionales — endpoints HTTP (`/api/nlu`, `/api/chat`)
2. **Fase 6:** Limpieza — deprecar `nlp/` legacy, actualizar imports en
   toda la base de codigo
