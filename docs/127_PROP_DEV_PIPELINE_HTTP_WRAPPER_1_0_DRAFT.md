---
area: dev
type: prop
module: agentic_pipeline
version: 1.0
status: DRAFT
---
# Propuesta: HTTP Request Handler Wrapper para AgenticPipeline RECPL v2.0

- **ID:** 127_PROP_DEV_PIPELINE_HTTP_WRAPPER_1_0_DRAFT
- **Tipo:** PROP (Propuesta)
- **Área:** DEV
- **Módulo:** agentic_pipeline
- **Versión:** 1.0
- **Estado:** DRAFT
- **Tags:** `http-wrapper`, `request-handler`, `pipeline-adapter`, `serverless`, `fastify`, `express`
- **Changelog:**
  - 1.0 — 2026-06-18: Versión inicial

---

## 1. Contexto

El pipeline `agentic_pipeline` (RECPL v2.0) está diseñado como un **compilador de lenguaje natural a código IR** que ejecuta un StateGraph con 10+ PipelineStages conectados secuencialmente (INTENT → PREPROCESSOR → LEXER → PARSER → SEMANTIC_ANALYZER → IR_GENERATOR → PLANNER → SYNTHESIS → UI_GENERATOR → VALIDATOR).

Actualmente el pipeline se invoca desde:

| Punto de entrada | Tipo | Característica |
|---|---|---|
| `AgentOrchestrator.run(prompt)` | async Python | Retorna `dict`, sin estado externo |
| `AgentLoop.run(prompt)` | async Python | Loop con memoria y herramientas |
| `AgentLoop.run_interactive()` | REPL | CLI interactiva tipo `recpl.sh` |
| `PipelineDebugger.run(prompt)` | async Python | Debug modes (trace/step/timing/inspect) |

**Problema:** No existe un envoltorio estándar que permita ejecutar el pipeline desde un **servidor HTTP** (Fastify, Express, NestJS, Lambda, etc.) con la interfaz universal `function(req, res)`: extraer la entrada de `req`, ejecutar el pipeline, y escribir el resultado en `res`.

---

## 2. Objetivo

Diseñar e implementar un **HTTP Request Handler Wrapper** que envuelva el pipeline RECPL v2.0 en una función con la firma:

```python
async def pipeline_handler(req: Request, res: Response) -> None:
    # 1. Extraer prompt/input de req
    # 2. Ejecutar el pipeline
    # 3. Escribir resultado en res
    # 4. Manejar errores, streaming, CORS, content-type
```

Esta función debe ser **framework-agnostic** pero compatible con los principales servidores HTTP del ecosistema Python/Node.js.

---

## 3. Análisis de la Base de Código

### 3.1 Clases principales y su interfaz

```
AgentOrchestrator        ← StateGraph pipeline (10+ stages)
  ↓ run(prompt: str) -> dict {output, success}

PipelineDebugger         ← Debug wrapper
  ↓ run(prompt: str) -> dict

AgentLoop                ← Loop agente con tools + memoria
  ↓ run(prompt: str) -> AgentOutput {status, data, message, iterations}
  ↓ run_interactive()   ← REPL síncrono

PipelineMacroCommand     ← Command pattern
  ↓ execute() -> CommandResult {success, data, error, duration}

PipelineStage (ABC)      ← Abstract stage
  ↓ execute(input) -> StageOutput {output_data, success, error, metrics}
```

### 3.2 Flujo de datos actual

```
HTTP CLIENT (ninguno hoy)
  ↓
[CLI] agentic_script / AgentLoop.run_interactive()
  ↓ prompt: str
AgentOrchestrator.run(prompt)
  ↓ StageContext / StateGraph
  ↓ etapas: INTENT → PREPROCESSOR → LEXER → ... → VALIDATOR
  ↓ dict {output: {...}, success: True/False}
```

### 3.3 Puntos de integración identificados

1. **`AgentOrchestrator.run()`** — El punto más limpio y directo. No requiere instanciar tools, memoria o bucles adicionales.
2. **`PipelineMacroCommand.execute()`** — Útil si se necesita logging/replay vía Command pattern.
3. **`PipelineDebugger.run()`** — Para entornos de desarrollo/depuración vía HTTP.
4. **`AgentLoop.run()`** — Cuando se necesita el loop completo con tools y recuperación de errores.

---

## 4. Propuesta de Arquitectura

### 4.1 Capas del wrapper

```
┌─────────────────────────────────────────────────────────────────┐
│  Capa HTTP (Fastify / Express / Lambda / etc.)                  │
│  req → extraer payload → pipeline_handler(req, res)             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  PipelineRequestHandler  ← Clase wrapper principal              │
│  handle(req) -> ResponseData                                    │
│    ├─ parse_request(req)   → PipelineInput                      │
│    ├─ execute(prompt)      → PipelineResult                     │
│    └─ format_response(res) → Serialized output                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│  AgenticPipeline / AgentOrchestrator / PipelineMacroCommand     │
│  (código existente, sin modificaciones)                         │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Contrato PipelineRequestHandler

```python
@dataclass
class PipelineInput:
    prompt: str
    mode: Literal["full", "debug"] = "full"
    debug_mode: str | None = None
    output_dir: str = "modules"
    max_iterations: int = 5
    interactive: bool = False
    session_id: str | None = None

@dataclass
class PipelineResult:
    success: bool
    data: dict
    error: str | None = None
    duration: float = 0.0
    stages: list[StageInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass
class StageInfo:
    name: str
    success: bool
    duration: float
    error: str | None = None

class PipelineRequestHandler:
    """Wrapper framework-agnostic del pipeline RECPL v2.0.

    Uso tipico con Fastify:
        handler = PipelineRequestHandler()
        app.post("/api/pipeline", async (req, reply) => {
            const result = await handler.handle(req);
            reply.send(result);
        });

    Uso tipico con FastAPI:
        handler = PipelineRequestHandler()
        @app.post("/api/pipeline")
        async def run_pipeline(request: Request):
            return await handler.handle(request)
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        tools: ToolRegistry | None = None,
        memory: ConversationalMemory | None = None,
        default_output_dir: str = "modules",
    ):
        self._orchestrator = orchestrator or AgentOrchestrator()
        self._tools = tools or ToolRegistry.build_default()
        self._memory = memory or ConversationalMemory()
        self._default_output_dir = default_output_dir

    async def handle(self, req: Any) -> PipelineResult:
        """Punto de entrada unico. Framework-agnostic."""
        try:
            inp = self._parse_request(req)
            result = await self._execute(inp)
            return result
        except Exception as exc:
            return PipelineResult(
                success=False,
                data={},
                error=f"Handler error: {exc}",
            )

    def _parse_request(self, req: Any) -> PipelineInput:
        """Extrae PipelineInput de cualquier objeto request.
        
        Soporta:
        - dict (fasthtml, lambda, test)
        - Request con .json() (FastAPI, Starlette)
        - Objeto con .body (Fastify, Node.js - via bridge)
        """
        # ... logica de parsing

    async def _execute(self, inp: PipelineInput) -> PipelineResult:
        """Ejecuta el pipeline con el modo seleccionado."""
        t0 = time.time()
        if inp.mode == "debug" and inp.debug_mode:
            debugger = PipelineDebugger(mode=inp.debug_mode)
            raw = await debugger.run(inp.prompt)
            elapsed = time.time() - t0
            return PipelineResult(
                success=raw.get("success", False),
                data=raw.get("output", raw),
                duration=elapsed,
            )
        if inp.mode == "loop":
            loop = AgentLoop(
                orchestrator=self._orchestrator,
                tools=self._tools,
                memory=self._memory,
                max_iterations=inp.max_iterations,
            )
            raw = await loop.run(inp.prompt)
            elapsed = time.time() - t0
            return PipelineResult(
                success=raw.status == "completed",
                data=raw.data,
                error=raw.message if raw.status != "completed" else None,
                duration=elapsed,
            )
        # modo "full" (por defecto) — ejecucion directa del StateGraph
        raw = await self._orchestrator.run(inp.prompt)
        elapsed = time.time() - t0
        return PipelineResult(
            success=raw.get("success", False),
            data=raw.get("output", raw),
            duration=elapsed,
        )

    async def handle_request(
        self,
        req: Any,
        res: Any,
    ) -> None:
        """Interfaz function(req, res) para servidores HTTP.
        
        Escribe directamente en el objeto respuesta.
        Compatible con Fastify reply, Express res, etc.
        """
        result = await self.handle(req)
        self._write_response(res, result)
```

### 4.3 Interfaz function(req, res) universal

```python
async def pipeline_handler(req, res):
    """Wrapper directo function(req, res) -> ejecuta pipeline.
    
    Esta funcion es el producto final: cualquier framework HTTP
    puede llamarla pasando req/res en el formato que espera.
    
    Fastify/Express:
        app.post("/api/pipeline", pipeline_handler)
    
    FastAPI:
        @app.post("/api/pipeline")
        async def handler(request: Request):
            # convertir a dict con await request.json()
            # crear mock res object
            ...
    
    Lambda:
        def handler(event, context):
            result = await pipeline_handler(event, {})
            return {"statusCode": 200, "body": json.dumps(result)}
    """
    handler = PipelineRequestHandler()
    await handler.handle_request(req, res)
```

---

## 5. Estrategia de Implementación (Recomendada)

### Fase 1: Núcleo framework-agnostic

| Paso | Archivo | Descripción |
|------|---------|-------------|
| 1 | `compiler-bot/agentic_pipeline/http_handler.py` | Crear `PipelineRequestHandler`, `PipelineInput`, `PipelineResult`, `StageInfo` |
| 2 | `compiler-bot/agentic_pipeline/http_handler.py` | Implementar `_parse_request()` con soporte para `dict`, `Request` (Starlette/FastAPI), `bytes` |
| 3 | `compiler-bot/agentic_pipeline/http_handler.py` | Implementar `_execute()` con 3 modos: `full`, `loop`, `debug` |
| 4 | `compiler-bot/agentic_pipeline/http_handler.py` | Implementar `handle_request(req, res)` que escribe directo en respuesta |
| 5 | `compiler-bot/agentic_pipeline/http_handler.py` | Manejo de errores, timeouts, CORS headers |

### Fase 2: Integración con servidores HTTP

| Paso | Framework | Archivo |
|------|-----------|---------|
| 6 | FastAPI | `compiler-bot/api/fastapi_app.py` — router `POST /api/pipeline` |
| 7 | Fastify (Node.js bridge) | `compiler-bot/api/bridge_fastify.js` — subprocess + HTTP proxy |
| 8 | Lambda / Serverless | `compiler-bot/api/lambda_handler.py` — entrypoint para AWS Lambda |

### Fase 3: Streaming y SSE

| Paso | Descripción |
|------|-------------|
| 9 | Conectar `stream_callback` del `AgentOrchestrator` a SSE (Server-Sent Events) |
| 10 | Emitir eventos por stage: `{"stage": "lexer", "status": "OK", "duration": 0.123}` |
| 11 | Modo `stream` en `PipelineRequestHandler` para clientes que requieran feedback en vivo |

---

## 6. Formato de Entrada/Salida HTTP

### Request (POST /api/pipeline)

```json
{
  "prompt": "crea un modulo de usuarios en NestJS con autenticacion",
  "mode": "full",
  "output_dir": "modules",
  "max_iterations": 5,
  "session_id": null,
  "debug_mode": null
}
```

### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "generated_files": [
      "modules/users/users.controller.ts",
      "modules/users/users.service.ts",
      "modules/users/users.module.ts"
    ],
    "errors": [],
    "ast_summary": {
      "tokens": 23,
      "intent": "create_module",
      "entities": ["users", "nestjs", "autenticacion"]
    }
  },
  "duration": 1.234,
  "stages": [
    {"name": "intent", "success": true, "duration": 0.100},
    {"name": "preprocessor", "success": true, "duration": 0.050},
    {"name": "lexer", "success": true, "duration": 0.080},
    {"name": "parser", "success": true, "duration": 0.120},
    {"name": "semantic_analyzer", "success": true, "duration": 0.090},
    {"name": "ir_generator", "success": true, "duration": 0.070},
    {"name": "planner", "success": true, "duration": 0.200},
    {"name": "synthesis", "success": true, "duration": 0.400},
    {"name": "ui_generator", "success": true, "duration": 0.050},
    {"name": "validator", "success": true, "duration": 0.074}
  ],
  "warnings": []
}
```

### Response Error (400/500)

```json
{
  "success": false,
  "data": {},
  "error": "Semantic error: entity 'usuarios' undefined in symbol table",
  "duration": 0.450,
  "stages": [
    {"name": "intent", "success": true, "duration": 0.100},
    {"name": "preprocessor", "success": true, "duration": 0.050},
    {"name": "lexer", "success": true, "duration": 0.080},
    {"name": "parser", "success": true, "duration": 0.120},
    {"name": "semantic_analyzer", "success": false, "duration": 0.090, "error": "entity 'usuarios' undefined in symbol table"}
  ],
  "warnings": ["token 'autenticacion' matched as ENTITY but domain 'auth' not loaded"]
}
```

---

## 7. Consideraciones Técnicas

### 7.1 Framework-agnostic vs framework-specific

**Recomendación:** El núcleo (`PipelineRequestHandler`) debe ser completamente framework-agnostic, usando solo tipos estándar de Python (`dict`, `dataclass`, `async def`). Los adaptadores específicos (FastAPI, Fastify bridge, Lambda) son archivos separados de ~30 líneas cada uno.

Esto maximiza:
- **Testeabilidad** — se prueba con requests mock sin servidor HTTP
- **Portabilidad** — mismo handler funciona en FastAPI, Quart, Lambda, etc.
- **Mantenibilidad** — cambios en el pipeline no afectan la capa HTTP

### 7.2 Streaming vs bloqueante

El pipeline actual es **bloqueante por stage**: cada `PipelineStage.execute()` se ejecuta sincrónicamente, pero el StateGraph completo se invoca con `ainvoke()` (async). Esto permite:
- Modo **request-response** (por defecto): esperar resultado completo antes de responder
- Modo **streaming** (future): emitir eventos SSE por stage usando el `stream_callback` existente

### 7.3 Timeout y recursos

Configuración recomendada:

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `pipeline_timeout` | 30s | Timeout máximo para el pipeline completo |
| `stage_timeout` | 10s | Timeout por stage individual |
| `max_prompt_length` | 5000 chars | Protección contra prompts maliciosos |
| `max_output_size` | 10MB | Límite de tamaño de respuesta |

### 7.4 Seguridad

- **Sanitización de input**: el preprocesador existente ya normaliza el texto, pero se debe agregar un filtro de seguridad en `_parse_request()` para bloquear inyección de comandos en el campo `prompt`.
- **Rate limiting**: por sesión/IP, configurable externamente.
- **Validación de output_dir**: restringir a `modules/` y `tmp_modules/` para evitar escritura fuera del sandbox.

### 7.5 Integración con el ecosistema existente

| Componente existente | Cómo se integra |
|---|---|
| `AgentOrchestrator.run()` | Llamado directamente en modo `full` |
| `PipelineDebugger` | Modo `debug` del handler, útil para depuración remota |
| `AgentLoop` | Modo `loop` para prompts complejos que requieren multiple iteración |
| `ConversationalMemory` | Reseteada por defecto; opcionalmente persistente vía `session_id` |
| `ToolRegistry` | Solo en modo `loop` |
| `WorldModel` | Inicializado opcionalmente para consultas de estado |

---

## 8. Implementación Mínima Viable

```python
"""http_handler.py — HTTP Request Handler Wrapper for RECPL v2.0 pipeline."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from .orchestrator import AgentOrchestrator
from .debugger import PipelineDebugger
from .agent_loop import AgentLoop
from .tool_registry import ToolRegistry
from .memory import ConversationalMemory

logger = logging.getLogger(__name__)


@dataclass
class PipelineInput:
    prompt: str
    mode: Literal["full", "loop", "debug"] = "full"
    debug_mode: str | None = None
    output_dir: str = "modules"
    max_iterations: int = 5
    session_id: str | None = None


@dataclass
class StageInfo:
    name: str
    success: bool
    duration: float
    error: str | None = None


@dataclass
class PipelineResult:
    success: bool
    data: dict
    error: str | None = None
    duration: float = 0.0
    stages: list[StageInfo] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class PipelineRequestHandler:
    """Wrapper framework-agnostic del pipeline RECPL v2.0.

    Uso:
        handler = PipelineRequestHandler()
        result = await handler.handle({"prompt": "crea modulo usuarios"})
        # result.success, result.data, result.stages, result.duration
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        tools: ToolRegistry | None = None,
        memory: ConversationalMemory | None = None,
        default_output_dir: str = "modules",
    ):
        self._orchestrator = orchestrator or AgentOrchestrator()
        self._tools = tools or ToolRegistry.build_default()
        self._memory = memory or ConversationalMemory()
        self._default_output_dir = default_output_dir

    def _parse_request(self, req: Any) -> PipelineInput:
        if isinstance(req, dict):
            body = req
        elif hasattr(req, "json") and callable(getattr(req, "json")):
            import asyncio
            body = asyncio.run(req.json()) if asyncio.iscoroutinefunction(req.json) else req.json()
        elif hasattr(req, "body"):
            raw = req.body
            body = json.loads(raw) if isinstance(raw, (str, bytes)) else raw
        else:
            body = {}
        return PipelineInput(
            prompt=body.get("prompt", ""),
            mode=body.get("mode", "full"),
            debug_mode=body.get("debug_mode"),
            output_dir=body.get("output_dir", self._default_output_dir),
            max_iterations=body.get("max_iterations", 5),
            session_id=body.get("session_id"),
        )

    async def _collect_stages(self, output: dict) -> list[StageInfo]:
        """Intenta extraer informacion de stages del output del pipeline."""
        if isinstance(output, dict):
            stages_data = output.get("stages", output.get("stage_info", []))
            return [
                StageInfo(
                    name=s.get("name", s.get("stage", "unknown")),
                    success=s.get("success", True),
                    duration=s.get("duration", 0.0),
                    error=s.get("error"),
                )
                for s in (stages_data if isinstance(stages_data, list) else [])
            ]
        return []

    async def _execute(self, inp: PipelineInput) -> PipelineResult:
        t0 = time.time()
        stages: list[StageInfo] = []
        try:
            if inp.mode == "debug" and inp.debug_mode:
                debugger = PipelineDebugger(mode=inp.debug_mode, output_dir=inp.output_dir)
                raw = await debugger.run(inp.prompt)
                elapsed = time.time() - t0
                stages = await self._collect_stages(raw)
                return PipelineResult(
                    success=raw.get("success", False),
                    data=raw.get("output", raw),
                    duration=elapsed,
                    stages=stages,
                )
            if inp.mode == "loop":
                loop = AgentLoop(
                    orchestrator=self._orchestrator,
                    tools=self._tools,
                    memory=self._memory,
                    max_iterations=inp.max_iterations,
                )
                raw = await loop.run(inp.prompt)
                elapsed = time.time() - t0
                return PipelineResult(
                    success=raw.status == "completed",
                    data=raw.data,
                    error=raw.message if raw.status not in ("completed", "action_executed") else None,
                    duration=elapsed,
                    stages=stages,
                )
            raw = await self._orchestrator.run(inp.prompt)
            elapsed = time.time() - t0
            stages = await self._collect_stages(raw)
            return PipelineResult(
                success=raw.get("success", True),
                data=raw.get("output", raw),
                duration=elapsed,
                stages=stages,
            )
        except Exception as exc:
            elapsed = time.time() - t0
            logger.exception("Pipeline execution failed")
            return PipelineResult(
                success=False,
                data={},
                error=str(exc),
                duration=elapsed,
                stages=stages,
            )

    async def handle(self, req: Any) -> PipelineResult:
        try:
            inp = self._parse_request(req)
            return await self._execute(inp)
        except Exception as exc:
            logger.exception("Request parsing failed")
            return PipelineResult(
                success=False,
                data={},
                error=f"Request error: {exc}",
            )

    async def handle_request(self, req: Any, res: Any) -> None:
        """Interfaz function(req, res) para servidores HTTP."""
        result = await self.handle(req)
        if hasattr(res, "status_code"):
            res.status_code = 200 if result.success else 400
        if hasattr(res, "json"):
            res.json({
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "duration": round(result.duration, 4),
                "stages": [
                    {"name": s.name, "success": s.success, "duration": round(s.duration, 4), "error": s.error}
                    for s in result.stages
                ],
            })
        elif hasattr(res, "send"):
            res.send({
                "success": result.success,
                "data": result.data,
                "error": result.error,
                "duration": round(result.duration, 4),
            })
        elif isinstance(res, dict):
            res.update({
                "statusCode": 200 if result.success else 400,
                "body": json.dumps({
                    "success": result.success,
                    "data": result.data,
                    "error": result.error,
                    "duration": round(result.duration, 4),
                }),
            })
```

---

## 9. Ejemplo de Uso con FastAPI

```python
# api/fastapi_app.py
from fastapi import FastAPI, Request
from agentic_pipeline.http_handler import PipelineRequestHandler

app = FastAPI(title="RECPL Compiler API")
handler = PipelineRequestHandler()

@app.post("/api/pipeline")
async def run_pipeline(request: Request):
    """Ejecuta el pipeline RECPL v2.0 desde una request HTTP."""
    return await handler.handle(request)

@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0"}
```

Ejecución:

```bash
curl -X POST http://localhost:8000/api/pipeline \
  -H "Content-Type: application/json" \
  -d '{"prompt": "crea un modulo de pagos en NestJS"}'
```

---

## 10. Criterios de Éxito

| # | Criterio | Verificación |
|---|----------|-------------|
| 1 | `PipelineRequestHandler.handle(dict)` retorna `PipelineResult` con datos correctos | Test unitario |
| 2 | Modo `full` ejecuta el StateGraph completo sin cambios en `orchestrator.py` | Test de integración |
| 3 | Modo `debug` con `debug_mode="trace"` invoca `PipelineDebugger` correctamente | Test unitario |
| 4 | Modo `loop` invoca `AgentLoop.run()` y retorna el resultado | Test unitario |
| 5 | `handle_request(req, res)` escribe en el objeto respuesta | Test con mock |
| 6 | Error en cualquier modo produce `PipelineResult` con `success=False` y mensaje de error | Test de error |
| 7 | Timeout de 30s aborta la ejecución y retorna error | Test de timeout |
| 8 | `_parse_request()` maneja `dict`, `Request` (Starlette), y objetos con `.body` | Test parametrizado |
| 9 | Sin regresiones en tests existentes (`pytest tests/ -v`) | CI pipeline |
| 10 | Documentación de la API en `docs/` siguiendo ALGP003 | Revisión manual |

---

## 11. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|-------------|------------|
| `asyncio.run()` dentro de `_parse_request()` para `req.json()` | Bloqueante en loops existentes | Media | Usar `await req.json()` directo en el adaptador FastAPI |
| Pipeline lento (>10s) bloquea el worker HTTP | Timeout del cliente | Alta | Implementar SSE streaming o tareas asíncronas con callback URL |
| Estado compartido entre requests (memory, symbol table) | Contaminación entre sesiones | Media | Inicializar nuevo `AgentOrchestrator` por request, o usar `session_id` para memoria aislada |
| `PipelineDebugger` escribe a stderr | Ruido en logs del servidor | Baja | Redirigir stderr en modo producción |
| Dependencia de `langgraph` no async-safe | Race conditions | Baja | Usar `ainvoke()` como ya está implementado |

---

## 12. Conclusión y Recomendación

**Recomendación principal:** Implementar `PipelineRequestHandler` como se describe en la Sección 8, con las siguientes prioridades:

1. **Fase 1 (inmediata):** Crear `compiler-bot/agentic_pipeline/http_handler.py` con el handler framework-agnostic y los contratos `PipelineInput`/`PipelineResult`.
2. **Fase 2 (siguiente sprint):** Integrar con FastAPI (`api/fastapi_app.py`) para exponer el pipeline como API REST.
3. **Fase 3 (futuro):** Streaming SSE y soporte serverless.

Esta aproximación:
- **No modifica** el código existente del pipeline (cero regresiones)
- **Maximiza reutilización** de los 3 modos de ejecución (full/loop/debug)
- **Es testeable** sin servidor HTTP
- **Es portable** a cualquier framework HTTP

El resultado es un envoltorio que transforma el pipeline RECPL v2.0 de una herramienta CLI a un servicio HTTP listo para integrarse en arquitecturas modernas.