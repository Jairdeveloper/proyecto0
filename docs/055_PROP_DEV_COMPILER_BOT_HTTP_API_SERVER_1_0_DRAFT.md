---
id: 055
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - proposal
  - http-api
  - server
  - web
  - api-rest
  - python
  - agent-robot
summary: "Propuesta de implementacion para un servidor HTTP que exponga el pipeline RECPL y la capa agent-robot como API REST. Analiza 3 enfoques (Python, Node.js, C core), selecciona Python por minima dependencia, y define 4 fases con especificacion de endpoints, autenticacion, rate limiting, y sandboxing."
keywords:
  - proposal
  - http-api
  - server
  - rest-api
  - python
  - endpoints
  - authentication
  - rate-limiting
  - sandbox
  - websocket
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Propuesta de servidor HTTP para exponer RECPL como API REST — 3 enfoques, 4 fases, especificacion completa de endpoints
---

# Propuesta: Servidor HTTP para API Web

> **Documentos de referencia:**
> - `docs/013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` — propuesta original de daemon server en C
> - `docs/011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` — propuesta de API NestJS + React (FASE-E4)
> - `docs/048_PLAN_DEV_COMPILER_BOT_AGENT_IMPL_1_0_DRAFT.md` — Decision #2: enfoque terminal-only (ahora revisada)
> - `docs/053_REP_DEV_COMPILER_BOT_FASE4_AGENT_PROMPTS_ROBUSTEZ_1_0_DRAFT.md` — reporte Fase 4, seccion "Modo servidor"
> - `docs/054_PLAN_DEV_COMPILER_BOT_NEXT_STEPS_1_0_DRAFT.md` — plan de proximos pasos (descarta servidor, ahora revisado)
>
> **Estado:** DRAFT — pendiente de aprobacion

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Analisis de la Situacion Actual](#2-analisis-de-la-situacion-actual)
3. [Enfoques Considerados](#3-enfoques-considerados)
4. [Enfoque Seleccionado: Python wrapper](#4-enfoque-seleccionado-python-wrapper)
5. [Especificacion de la API](#5-especificacion-de-la-api)
6. [Plan de Implementacion](#6-plan-de-implementacion)
7. [Seguridad](#7-seguridad)
8. [Riesgos y Mitigaciones](#8-riesgos-y-mitigaciones)
9. [Referencias](#9-referencias)

---

## 1. Resumen Ejecutivo

### Que se propone

Construir un servidor HTTP ligero que exponga el pipeline RECPL y la capa agent-robot como una API REST. Esto permite:

- Integrar el compilador RECPL en **IDEs, web apps, CI/CD pipelines**
- Ofrecer un **endpoint web** para que usuarios prueben instrucciones sin instalar el bot
- Separar la **logica del compilador** (shell) de la **interfaz de acceso** (HTTP)

### Que NO se propone

- **No** es un rewrite del pipeline en otro lenguaje — el nucleo sigue siendo shell
- **No** es un dashboard web con frontend React — solo la API
- **No** es un sustituto del CLI — ambos coexisten

---

## 2. Analisis de la Situacion Actual

### Lo que existe

| Componente | Lenguaje | Estado | Interface |
|-----------|----------|--------|-----------|
| Pipeline RECPL completo | Shell | Implementado | `recpl.sh -c "instruccion"` → JSON stdout |
| Capa agent-robot | Shell | Implementado | `agent.sh "instruccion"` → texto formateado stdout |
| Bridge (normalizacion JSON) | Shell | Implementado | `bridge.sh` → `{exito, origen, tipo_respuesta, mensaje, payload}` |
| Adaptadores LLM (Claude/OpenAI) | Shell | Implementado | `providers/claude.sh`, `providers/openai.sh` |
| Herramientas del sistema | Shell | Implementado | `tool_*.sh` → JSON por herramienta |
| Memoria/estado persistente | Shell (JSON) | Implementado | `$AGENT_MEMORY_DIR/agent_memory.json` |
| C core (`recpl-core`) | C11 | **Stub solamente** | `main.c` — todos los modos retornan "not implemented" |

### Lo que falta para una API HTTP

| Aspecto | Estado actual | Necesario para API |
|---------|---------------|-------------------|
| Servidor HTTP | No existe | Escuchar en puerto TCP, rutear requests |
| Concurrencia | PID-based state dir (`$$`) — no seguro para requests simultaneos | UUID-based isolation por request |
| Autenticacion | No existe | API keys o tokens |
| Rate limiting | No existe | Limitar requests/minuto por cliente |
| Sandboxing | No existe | Restringir paths de file tools a directorio seguro |
| CORS | No existe | Headers para acceso desde browser |
| Logging por request | `memory_log_*` sincronico | Request ID tracking, log rotation |
| Formato de respuesta uniforme | Varios formatos segun herramienta | Envoltorio REST uniforme |

### Entorno disponible

```
$ python3 --version
Python 3.11.5

$ node --version
v22.22.3

$ gcc --version
gcc (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0
```

---

## 3. Enfoques Considerados

### Enfoque A — Python wrapper (stdlib)

**Mecanismo:** `http.server` + `subprocess.run()` llamando a `recpl.sh -c`

```python
import http.server
import json
import subprocess
import uuid

class RECPLHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/prompt':
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length))
            instruction = body.get('instruction', '')

            result = subprocess.run(
                ['./recpl.sh', '-c', instruction],
                capture_output=True, text=True, timeout=30,
                cwd='/path/to/compiler-bot'
            )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'exito': True,
                'data': json.loads(result.stdout)
            }).encode())
```

**Pros:**
- **Cero dependencias externas** — solo Python stdlib
- Implementacion en ~200 lineas
- `subprocess.run()` maneja timeout, stdout/stderr, exit codes
- `uuid` para IDs de sesion y request unicos

**Contras:**
- `http.server` es monohilo — necesita `ThreadingHTTPServer` para concurrencia
- Sin router automatico — `do_GET`/`do_POST` manual
- Sin OpenAPI/Swagger — documentacion manual
- Sin WebSocket nativo (para streaming de respuestas largas)

**Escalabilidad:** ~50 requests/minuto en `ThreadingHTTPServer`

### Enfoque B — Node.js/Express

**Mecanismo:** Servidor Node con Express, `child_process.execFile()` llamando a shell

```javascript
const express = require('express');
const { execFile } = require('child_process');

const app = express();
app.post('/api/prompt', (req, res) => {
    execFile('./recpl.sh', ['-c', req.body.instruction],
        { timeout: 30000, cwd: '/path/to/compiler-bot' },
        (err, stdout) => res.json(JSON.parse(stdout))
    );
});
```

**Pros:**
- Express es maduro para APIs REST
- Middleware ecosystem (auth, rate-limit, CORS, cors, helmet)
- `npm` para gestion de dependencias
- WebSocket via `ws` o `socket.io`

**Contras:**
- **No hay `package.json` en el proyecto** — seria el primer modulo Node.js del repo
- El proyecto explicitamente ignora el stack NestJS/Node planificado
- Dependencia externa (Express, middleware) vs politicas actuales
- `node_modules/` que añadir a `.gitignore`

**Escalabilidad:** ~200 requests/minuto, cluster mode via `pm2`

### Enfoque C — C core daemon (recpl-core --mode=serve)

**Mecanismo:** Implementar el modo `--mode=serve` propuesto en `013_PROP` en `compiler-bot/core/main.c`

**Pros:**
- Sigue la vision original del proyecto (C core)
- Maximo rendimiento (~1000+ requests/minuto)
- Sin dependencias externas (POSIX sockets)
- La infraestructura Makefile ya existe

**Contras:**
- **Stub actual** — todo por implementar desde cero
- C requeriria manejar manualmente: HTTP parsing, JSON serialization, routing, concurrent connections, signal handling
- Complejidad alta (~1000+ lineas de C para un servidor HTTP basico)
- Sin experiencia demostrada en el codebase con C para HTTP (solo stubs)
- Cada cambio requiere compilacion (`make && make install`)
- Depuracion mas dificil que Python/Node

**Escalabilidad:** ~1000+ requests/minuto con worker pool POSIX

### Enfoque D — Shell puro con socat/nc (DESCARTADO)

**Motivo de descarte:** `socat` y `nc` no estan disponibles en el entorno. Un servidor HTTP en shell puro seria extremadamente fragil, sin manejo de concurrencia, y propenso a errores de parsing HTTP.

---

## 4. Enfoque Seleccionado: Python Wrapper

### Justificacion

| Criterio | Python (A) | Node.js (B) | C core (C) |
|----------|-----------|-------------|------------|
| Dependencias externas | **0** (stdlib) | npm + express | **0** (POSIX) |
| Tiempo de implementacion | **~4h** | ~3h | ~20h |
| Lineas de codigo estimadas | **~300** | ~200 + config | ~1500 |
| Concurrencia | Threading (nativo) | Event loop (nativo) | Worker pool (manual) |
| Facilidad de mantenimiento | **Alta** | Alta | Baja |
| Alineacion con el proyecto | **Shell-invocador** | Nueva dependencia | Alineado pero no implementado |
| WebSocket | No nativo | Nativo | Manual |
| **Puntaje** | **4.5/5** | 3.5/5 | 2/5 |

Python ofrece el mejor balance: **cero dependencias nuevas**, implementacion rapida, mantenimiento simple, y su unica limitacion (WebSocket no nativo) no es critica para una API request-response.

### Arquitectura

```
                    ┌─────────────────────────────────┐
                    │     Cliente HTTP (curl, browser,  │
                    │     IDE, CI/CD)                   │
                    └──────────────┬──────────────────┘
                                   │ POST /api/prompt
                                   ▼
┌──────────────────────────────────────────────────────┐
│              recpl-api.py (servidor HTTP)              │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ Router   │  │ Auth     │  │ Rate Limiter       │  │
│  │ (url:    │→│ (API Key)│→│ (token bucket)     │  │
│  │  method) │  │          │  │                    │  │
│  └──────────┘  └──────────┘  └────────────────────┘  │
│                                       │               │
│  ┌────────────────────────────────────▼────────────┐  │
│  │            Request Handler                       │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│  │  │ Recpl    │ │ Agent    │ │ Tools (file,      │ │  │
│  │  │ Bridge   │ │ Bridge   │ │  command, search) │ │  │
│  │  └──────────┘ └──────────┘ └──────────────────┘ │  │
│  └────────────────────┬────────────────────────────┘  │
└───────────────────────┼────────────────────────────────┘
                        │ subprocess.run()
                        ▼
┌──────────────────────────────────────────────────────┐
│           RECPL Pipeline (Shell subprocess)           │
│                                                       │
│  recpl.sh -c "instruccion"                            │
│  agent.sh "instruccion"                               │
│  tool_*.sh ...                                        │
│                                                       │
│  Output: JSON en stdout                               │
└──────────────────────────────────────────────────────┘
```

---

## 5. Especificacion de la API

### 5.1 Endpoints

#### `POST /api/v1/prompt`

Ejecuta una instruccion en el pipeline RECPL.

**Request:**
```json
{
  "instruction": "crea modulo pagos en nestjs",
  "mode": "auto",
  "provider": "",
  "session_id": "abc-123"
}
```

| Campo | Tipo | Default | Descripcion |
|-------|------|---------|-------------|
| `instruction` | string | **requerido** | Instruccion en lenguaje natural |
| `mode` | string | `"auto"` | `auto`, `llm`, `deterministic` |
| `provider` | string | `""` | `claude`, `openai`, `""` (default) |
| `session_id` | string | `""` | UUID de sesion persistente |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "tipo_respuesta": "action",
    "mensaje": "Generando module Payments en nestjs...",
    "payload": {
      "tipo": "module",
      "nombre": "Payments",
      "tech": "nestjs",
      "archivos": ["modules/payments/payments.controller.ts", "..."]
    }
  },
  "meta": {
    "request_id": "req-uuid",
    "session_id": "sess-uuid",
    "tiempo_ms": 45,
    "mode": "deterministic",
    "origen": "recpl"
  }
}
```

**Response (400 — error de validacion):**
```json
{
  "success": false,
  "error": {
    "codigo": "INSTRUCTION_REQUIRED",
    "mensaje": "El campo 'instruction' es requerido"
  },
  "meta": {
    "request_id": "req-uuid",
    "tiempo_ms": 1
  }
}
```

**Response (429 — rate limit):**
```json
{
  "success": false,
  "error": {
    "codigo": "RATE_LIMITED",
    "mensaje": "Demasiadas requests. Limite: 30/min"
  },
  "meta": {
    "request_id": "req-uuid",
    "retry_after": 12
  }
}
```

---

#### `GET /api/v1/health`

Health check del servidor.

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "uptime": 3600,
  "checks": {
    "recpl": true,
    "jq": true,
    "python": "3.11.5"
  }
}
```

---

#### `GET /api/v1/sessions/:id`

Obtiene el historial de una sesion.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "session_id": "abc-123",
    "historial": [
      {"instruccion": "crea modulo X", "respuesta": "...", "timestamp": "..."}
    ],
    "total": 5
  }
}
```

---

#### `DELETE /api/v1/sessions/:id`

Elimina una sesion y su memoria.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "session_id": "abc-123",
    "deleted": true
  }
}
```

---

#### `GET /api/v1/tools`

Lista las herramientas disponibles en el agente.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "tools": [
      {"name": "recpl", "description": "Ejecuta instrucciones RECPL"},
      {"name": "read_file", "description": "Lee contenido de archivo"},
      {"name": "write_file", "description": "Escribe contenido en archivo"},
      {"name": "run_command", "description": "Ejecuta comando shell"},
      {"name": "search_code", "description": "Busca en codigo fuente"}
    ]
  }
}
```

---

### 5.2 Autenticacion

**Metodo:** API Key via header `X-API-Key`

```
POST /api/v1/prompt
X-API-Key: recpl_sk_abc123def456
Content-Type: application/json

{"instruction": "hola"}
```

**Configuracion:** Multiple API keys definidas en variable de entorno:

```sh
export RECPL_API_KEYS="key1:admin,key2:readonly"
```

Cada key tiene un rol asociado que determina permisos.

---

### 5.3 Rate Limiting

| Limite | Ventana | Consecuencia |
|--------|---------|-------------|
| 30 requests | 1 minuto | HTTP 429, retry-after header |
| 100 requests | 1 hora | HTTP 429 + log de advertencia |
| 1000 requests | 24 horas | Bloqueo temporal de API key |

Implementacion: **token bucket** en memoria (Python `collections.deque` + time checks).

---

### 5.4 Sandboxing

Para endpoints que exponen `tool_read_file`, `tool_write_file`, y `tool_run_command`:

- `read_file` / `write_file`: paths restringidos a un directorio base configurable (`RECPL_SANDBOX_DIR`)
- `run_command`: **NO expuesto via API publica** — solo via modo local/autenticado con rol `admin`
- Tiempo maximo de ejecucion: 30 segundos (`subprocess.run(timeout=30)`)

---

## 6. Plan de Implementacion

### Fase 1 — Nucleo del servidor (2-3h)

| Tarea | Descripcion | Archivo |
|-------|-------------|---------|
| 1.1 | Servidor HTTP basico con `ThreadingHTTPServer` | `compiler-bot/recpl-api.py` |
| 1.2 | Endpoint `POST /api/v1/prompt` con `subprocess.run(recpl.sh -c)` | `recpl-api.py` |
| 1.3 | Endpoint `GET /api/v1/health` | `recpl-api.py` |
| 1.4 | Wrapper de respuesta uniforme (success + meta) | `recpl-api.py` |
| 1.5 | Mapeo de errores (exit code → HTTP status) | `recpl-api.py` |
| 1.6 | Script de inicio `recpl-server` | `compiler-bot/recpl-server.sh` |

**Verificacion:**
```sh
./compiler-bot/recpl-api.py --port 9700 &
curl -s http://localhost:9700/api/v1/health | jq .
curl -s -X POST http://localhost:9700/api/v1/prompt \
  -H "Content-Type: application/json" \
  -d '{"instruction":"hola"}' | jq .
```

---

### Fase 2 — Autenticacion y Rate Limiting (1-2h)

| Tarea | Descripcion | Archivo |
|-------|-------------|---------|
| 2.1 | Middleware de API Key (`X-API-Key` header) | `recpl-api.py` |
| 2.2 | Token bucket rate limiter por IP y API key | `recpl-api.py` |
| 2.3 | Roles (`admin`, `readonly`) y permisos por endpoint | `recpl-api.py` |
| 2.4 | Headers CORS para acceso desde browser | `recpl-api.py` |
| 2.5 | Test suite de autenticacion y rate limiting | `compiler-bot/tests/test_api.py` |

---

### Fase 3 — Sesiones y Memoria (1-2h)

| Tarea | Descripcion | Archivo |
|-------|-------------|---------|
| 3.1 | Sesiones via UUID (aislar `AGENT_MEMORY_DIR` por sesion) | `recpl-api.py` |
| 3.2 | Endpoint `GET /api/v1/sessions/:id` | `recpl-api.py` |
| 3.3 | Endpoint `DELETE /api/v1/sessions/:id` | `recpl-api.py` |
| 3.4 | Limpieza periodica de sesiones expiradas (TTL) | `recpl-api.py` |

---

### Fase 4 — Modo agente y Herramientas (2-3h)

| Tarea | Descripcion | Archivo |
|-------|-------------|---------|
| 4.1 | Endpoint `POST /api/v1/agent` — ejecuta via `agent.sh` | `recpl-api.py` |
| 4.2 | Endpoint `POST /api/v1/tools/read` — leer archivo | `recpl-api.py` |
| 4.3 | Endpoint `POST /api/v1/tools/search` — buscar codigo | `recpl-api.py` |
| 4.4 | Endpoint `GET /api/v1/tools` — listar herramientas | `recpl-api.py` |
| 4.5 | Sandboxing de paths para file tools | `recpl-api.py` |
| 4.6 | Documentacion OpenAPI (`/api/v1/openapi.json`) | `recpl-api.py` |
| 4.7 | Integracion con tests existentes | `compiler-bot/tests/test_api.py` |

---

## 7. Seguridad

### 7.1 Autenticacion

```
X-API-Key: recpl_sk_<random_32_chars>
```

- Keys generadas con `os.urandom(32).hex()`
- Almacenadas solo en variable de entorno `RECPL_API_KEYS`
- Rotacion via reinicio del servidor
- Sin almacenamiento en disco

### 7.2 Input validation

- `instruction` limitada a 1000 caracteres
- Campos `mode` y `provider` validados contra whitelist
- `session_id` validado como UUID v4
- JSON malformado → HTTP 400 con mensaje de error

### 7.3 Shell injection prevention

- `subprocess.run()` con **lista de argumentos** (NO shell=True)
- `subprocess.run(['./recpl.sh', '-c', instruction])` — seguro
- La instruccion pasa por `sanitize_instruction()` de agent.sh igualmente
- Endpoint `run_command` solo disponible con rol `admin`

### 7.4 Rate limiting

```python
# Token bucket: 30 tokens, refill 1 token/2s
RATE_LIMIT = {
    'tokens': 30,
    'refill_seconds': 2,
    'window_seconds': 60
}
```

### 7.5 Logging y auditoria

Cada request genera una entrada estructurada:

```
[2026-06-13 12:00:00] req=abc-123 ip=192.168.1.1 key=usr_... 
  method=POST path=/api/v1/prompt status=200 duration=45ms
```

---

## 8. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Concurrencia corrompe `AGENT_MEMORY_DIR` | Media | Alto | Sesiones aisladas por UUID, cada request con su propio dir temporal |
| `subprocess.run()` sin timeout cuelga el servidor | Media | Alto | `timeout=30` en todas las llamadas, signal handler para huerfanos |
| Rate limiting en memoria se pierde al reiniciar | Alta | Bajo | Aceptable para MVP. Version futura: Redis o archivo |
| file tools leen archivos sensibles (`/etc/passwd`) | Media | Alto | Sandboxing: paths deben estar dentro de `RECPL_SANDBOX_DIR` |
| API key leak en logs | Baja | Alto | Filtrar headers antes de loguear. No loguear `X-API-Key` |
| `http.server` monohilo bloquea todos los clients | Alta | Medio | Usar `ThreadingHTTPServer` desde el inicio. Futuro: `asyncio` + `aiohttp` |
| Scripts shell no diseñados para concurrencia | Alta | Alto | Cada request en subproceso independiente con su propio `RECPL_STATE_DIR` basado en UUID |

### Mecanismo de aislamiento por request

```python
import uuid, os, tempfile

def execute_in_isolation(instruction):
    request_id = str(uuid.uuid4())
    state_dir = tempfile.mkdtemp(prefix=f'recpl_{request_id}_')
    env = os.environ.copy()
    env['RECPL_STATE_DIR'] = state_dir
    env['AGENT_MEMORY_DIR'] = f'/tmp/agent_memory_{request_id}'

    result = subprocess.run(
        ['./recpl.sh', '-c', instruction],
        capture_output=True, text=True, timeout=30,
        cwd=BASE_DIR, env=env
    )

    shutil.rmtree(state_dir, ignore_errors=True)
    return result.stdout
```

---

## 9. Referencias

| Documento | Relacion |
|-----------|----------|
| `docs/013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` | Propuesta original de daemon server en C — FASE-C8 (serve mode) |
| `docs/011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` | Propuesta de API NestJS endpoints (FASE-E4) |
| `docs/053_REP_DEV_COMPILER_BOT_FASE4_AGENT_PROMPTS_ROBUSTEZ_1_0_DRAFT.md` | Reporte Fase 4 — seccion "Modo servidor" en proximos pasos |
| `docs/054_PLAN_DEV_COMPILER_BOT_NEXT_STEPS_1_0_DRAFT.md` | Plan de proximos pasos (descarta servidor — ahora revisado) |
| `compiler-bot/recpl.sh` | Entrypoint del pipeline — llamado por el servidor |
| `compiler-bot/agent-robot/bridge.sh` | Bridge que normaliza respuestas JSON |
| `compiler-bot/agent-robot/agent.sh` | Capa agente — modo alternativo de invocacion |
| `compiler-bot/agent-robot/tools/tool_*.sh` | Herramientas del sistema (file, command, search) |
| `compiler-bot/core/main.c` | Stub del C core (modo serve no implementado) |

---

## Apendice A: Esquema del servidor (pseudocodigo)

```python
#!/usr/bin/env python3
"""recpl-api.py — Servidor HTTP para RECPL Compiler Bot"""

import http.server
import json, os, subprocess, uuid, time, re
from collections import defaultdict

BASE_DIR = os.path.join(os.path.dirname(__file__))
PORT = int(os.environ.get('RECPL_API_PORT', 9700))
API_KEYS = os.environ.get('RECPL_API_KEYS', '').split(',')
SANDBOX_DIR = os.environ.get('RECPL_SANDBOX_DIR', '/tmp/recpl_sandbox')

class RateLimiter:
    def __init__(self, max_requests=30, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)

    def check(self, key):
        now = time.time()
        self.requests[key] = [t for t in self.requests[key] if now - t < self.window]
        if len(self.requests[key]) >= self.max_requests:
            return False, int(self.window - (now - self.requests[key][0]))
        self.requests[key].append(now)
        return True, 0

class RECPLHandler(http.server.BaseHTTPRequestHandler):
    rate_limiter = RateLimiter()
    server_version = 'RECPL-API/1.0'

    def _json_response(self, status, body):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _verify_auth(self):
        key = self.headers.get('X-API-Key', '')
        if not API_KEYS:
            return True, 'admin'  # Sin auth configurada = modo abierto
        for entry in API_KEYS:
            if ':' in entry:
                k, role = entry.split(':', 1)
                if k == key:
                    return True, role
        return False, ''

    def _call_recpl(self, instruction, env_extra=None):
        request_id = str(uuid.uuid4())
        state_dir = f'/tmp/recpl_api_{request_id}'
        env = os.environ.copy()
        env['RECPL_STATE_DIR'] = state_dir
        if env_extra:
            env.update(env_extra)
        os.makedirs(state_dir, exist_ok=True)
        try:
            result = subprocess.run(
                [os.path.join(BASE_DIR, 'recpl.sh'), '-c', instruction],
                capture_output=True, text=True, timeout=30,
                cwd=BASE_DIR, env=env
            )
            output = result.stdout.strip()
            parsed = json.loads(output) if output else {'error': 'empty output'}
            return parsed, result.returncode
        except subprocess.TimeoutExpired:
            return {'error': 'timeout', 'mensaje': 'La instruccion excedio 30s'}, 408
        finally:
            import shutil
            shutil.rmtree(state_dir, ignore_errors=True)

    def do_POST(self):
        if self.path == '/api/v1/prompt':
            authed, role = self._verify_auth()
            if not authed:
                return self._json_response(401, {'success': False, 'error': {'codigo': 'UNAUTHORIZED'}})
            allowed, retry = self.rate_limiter.check(self.client_address[0])
            if not allowed:
                return self._json_response(429, {'success': False, 'error': {'codigo': 'RATE_LIMITED'}})
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            instruction = body.get('instruction', '').strip()
            if not instruction:
                return self._json_response(400, {'success': False, 'error': {'codigo': 'INSTRUCTION_REQUIRED'}})
            if len(instruction) > 1000:
                return self._json_response(400, {'success': False, 'error': {'codigo': 'INSTRUCTION_TOO_LONG'}})
            data, exit_code = self._call_recpl(instruction)
            status = 200 if exit_code == 0 else 422
            return self._json_response(status, {
                'success': exit_code == 0,
                'data': data,
                'meta': {'request_id': str(uuid.uuid4()), 'tiempo_ms': 0}
            })
        self._json_response(404, {'success': False, 'error': {'codigo': 'NOT_FOUND'}})

    def do_GET(self):
        if self.path == '/api/v1/health':
            return self._json_response(200, {
                'status': 'ok', 'version': '1.0.0',
                'checks': {'recpl': os.path.exists(os.path.join(BASE_DIR, 'recpl.sh')),
                           'jq': subprocess.run(['which', 'jq'], capture_output=True).returncode == 0}
            })
        self._json_response(404, {'success': False, 'error': {'codigo': 'NOT_FOUND'}})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        self.end_headers()

if __name__ == '__main__':
    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), RECPLHandler)
    print(f'RECPL API server on port {PORT}')
    server.serve_forever()
```
