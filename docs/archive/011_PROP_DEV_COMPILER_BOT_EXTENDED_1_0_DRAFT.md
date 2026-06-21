---
id: 011
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - proposal
  - compiler-bot
  - recpl
  - mejora
  - tech-stack
  - web-ui
  - scaffolding
  - multi-lenguaje
summary: "Propuesta de extension del bot RECPL para soporte multi-tech-stack y UI web. Define arquitectura, componentes, flujos y plan de implementacion para transformar el bot CLI en una plataforma web de scaffolding."
keywords:
  - propuesta
  - mejora
  - recpl
  - web-ui
  - tech-stack
  - scaffolding
  - generador-codigo
  - express
  - fastapi
  - django
  - react
  - docker
  - gestor-proyectos
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion de la propuesta de extension del bot RECPL con multi-tech-stack y UI web
---

# Propuesta de Extension: RECPL Compiler Bot Multi-Tech + Web UI

## 1. Resumen Ejecutivo

El bot RECPL actual es una herramienta CLI que procesa lenguaje natural y genera
scaffolding para **NestJS** y **Prisma**. Esta propuesta extiende el bot para
soportar **multiples tech stacks** y anade una **interfaz web** que permite
generar proyectos completos desde el navegador.

```
ESTADO ACTUAL:
  CLI → lenguaje natural → NestJS | Prisma

ESTADO PROPUESTO:
  CLI + WEB → lenguaje natural → 20+ tech stacks → proyecto completo descargable
```

### Beneficios Esperados

| Beneficio | Impacto |
|-----------|---------|
| Multi-lenguaje | Un solo prompt genera backend, frontend, DB, Docker |
| UI visual | No requiere terminal — accesible a no-desarrolladores |
| Proyecto completo | No solo modulos sueltos, sino proyectos integrales |
| Plantillas colaborativas | Repositorio de templates mantenido por la comunidad |

---

## 2. Soporte Multi-Tech-Stack

### 2.1 Arquitectura de Tech Stacks

Cada tech stack es un **plugin independiente** con su propio directorio de templates,
reglas de scaffolding y configuracion:

```
compiler-bot/
├── stacks/                          # <-- NUEVO: directorio de tech stacks
│   ├── registry.sh                  # Registro y descubrimiento de stacks
│   ├── nestjs/                      # Stack NestJS (existente, migrar)
│   │   ├── stack.json               # Metadatos del stack
│   │   ├── templates/
│   │   │   ├── module/              # Template para modulo NestJS
│   │   │   ├── controller/          # Template para controller
│   │   │   ├── service/             # Template para service
│   │   │   ├── entity/              # Template para entidad
│   │   │   └── full-project/        # Template para proyecto completo
│   │   └── rules.sh                 # Reglas especificas del stack
│   ├── prisma/                      # Stack Prisma
│   │   └── ...
│   ├── express/                     # <-- NUEVO
│   │   ├── stack.json
│   │   ├── templates/
│   │   │   ├── module/
│   │   │   ├── route/
│   │   │   ├── middleware/
│   │   │   ├── model/
│   │   │   └── full-project/
│   │   └── rules.sh
│   ├── fastapi/                     # <-- NUEVO
│   │   ├── stack.json
│   │   ├── templates/
│   │   │   ├── module/
│   │   │   ├── router/
│   │   │   ├── model/
│   │   │   ├── schema/
│   │   │   └── full-project/
│   │   └── rules.sh
│   ├── django/                      # <-- NUEVO
│   │   └── ...
│   ├── react/                       # <-- NUEVO
│   │   └── ...
│   ├── vue/                         # <-- NUEVO
│   │   └── ...
│   ├── docker/                      # <-- NUEVO
│   │   └── ...
│   └── postgres/                    # <-- NUEVO
│       └── ...
└── ...
```

### 2.2 Catalogo de Tech Stacks Propuestos

| Stack | Categoria | Templates incluidos | Prioridad |
|-------|-----------|-------------------|-----------|
| **NestJS** | Backend (TypeScript) | module, controller, service, entity, full-project | Existente |
| **Prisma** | ORM/DB | model, schema, migration | Existente |
| **Express** | Backend (Node.js) | route, middleware, model, controller, full-project | Alta |
| **FastAPI** | Backend (Python) | router, model, schema, crud, full-project | Alta |
| **Django** | Backend (Python) | app, model, view, serializer, url, full-project | Alta |
| **Flask** | Backend (Python) | blueprint, model, route, full-project | Media |
| **Spring Boot** | Backend (Java) | controller, service, repository, entity, full-project | Media |
| **Go Gin** | Backend (Go) | handler, service, model, route, full-project | Media |
| **React** | Frontend (TS) | component, hook, service, page, full-project | Alta |
| **Vue** | Frontend (TS) | component, composable, store, view, full-project | Alta |
| **Angular** | Frontend (TS) | component, service, module, directive, full-project | Media |
| **Svelte** | Frontend (TS) | component, store, page, full-project | Baja |
| **PostgreSQL** | Base de datos | schema, migration, seed, function | Alta |
| **MongoDB** | Base de datos | schema, model, aggregation, seed | Alta |
| **Docker** | Infraestructura | Dockerfile, docker-compose, .dockerignore | Alta |
| **Kubernetes** | Infraestructura | deployment, service, configmap, ingress | Media |
| **GraphQL** | API | schema, resolver, type, query, mutation | Media |
| **Next.js** | Full-stack | page, api-route, component, layout, full-project | Alta |

### 2.3 Formato stack.json

Cada stack tiene un archivo de metadatos:

```json
{
  "id": "fastapi",
  "name": "FastAPI",
  "version": "0.104.0",
  "category": "backend",
  "language": "python",
  "description": "Framework moderno para APIs en Python",
  "dependencies": ["pydantic", "uvicorn", "sqlalchemy"],
  "templates": {
    "module": "Modulo CRUD completo",
    "router": "Router con endpoints",
    "model": "Modelo SQLAlchemy",
    "schema": "Esquema Pydantic",
    "full-project": "Proyecto FastAPI completo"
  },
  "prompts_keywords": ["fastapi", "python api", "api rest python"]
}
```

### 2.4 Deteccion de Stack desde Lenguaje Natural

El lexer debe reconocer nuevos tokens TECH_* para cada stack:

| Token | Patron | Stack |
|-------|--------|-------|
| `TECH_NESTJS` | `nestjs\|nest js` | NestJS |
| `TECH_PRISMA` | `prisma` | Prisma |
| `TECH_EXPRESS` | `express\|expressjs` | Express |
| `TECH_FASTAPI` | `fastapi\|fast api` | FastAPI |
| `TECH_DJANGO` | `django` | Django |
| `TECH_FLASK` | `flask` | Flask |
| `TECH_REACT` | `react\|reactjs` | React |
| `TECH_VUE` | `vue\|vuejs\|vue.js` | Vue |
| `TECH_ANGULAR` | `angular\|ng` | Angular |
| `TECH_NEXT` | `nextjs\|next.js\|next` | Next.js |
| `TECH_POSTGRES` | `postgresql\|postgres\|pg` | PostgreSQL |
| `TECH_MONGODB` | `mongodb\|mongo` | MongoDB |
| `TECH_DOCKER` | `docker` | Docker |
| `TECH_K8S` | `kubernetes\|k8s` | Kubernetes |
| `TECH_GRAPHQL` | `graphql\|gql` | GraphQL |
| `TECH_SPRING` | `spring\|spring boot` | Spring Boot |
| `TECH_GIN` | `gin\|go gin` | Go Gin |
| `TECH_SVELTE` | `svelte` | Svelte |

### 2.5 Comandos Multi-Stack

El parser debe soportar multiples tech stacks en una instruccion:

```
> crea un proyecto con backend fastapi frontend react y docker
> anade modulo users a express con base de datos postgres
> genera full-stack: nestjs backend + vue frontend + postgres db + docker
```

**Gramatica extendida:**

```
comando         → accion modulo_espec opcional_techs
opcional_techs  → SEPARATOR? PREP TECH (SEPARATOR TECH)*
                 | PREP TECH (SEPARATOR? PREP TECH)*
                 | ε
```

### 2.6 Sistema de Scaffolding Multi-Stack

El scaffold.sh actual copia templates de un solo stack. El nuevo sistema debe:

1. Aceptar **multiples stacks** en una sola invocacion
2. Resolver **dependencias entre stacks** (e.g., FastAPI necesita uvicorn)
3. Generar **archivos de integracion** (e.g., docker-compose que conecta backend + db)
4. **Nombrar archivos** segun las convenciones de cada lenguaje

```
> crea proyecto blog con fastapi postgres docker y react
Output:
  backend/
    app/
      main.py
      routers/
      models/
      schemas/
    requirements.txt
    Dockerfile
  frontend/
    src/
      components/
      pages/
      services/
    package.json
    Dockerfile
  docker-compose.yml
  .env.example
  README.md
```

---

## 3. UI Web

### 3.1 Arquitectura General

```
┌──────────────────────────────────────────────────────────┐
│                   NAVEGADOR WEB                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │  RECPL Web UI (SPA)                                │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │  │
│  │  │ Prompt   │  │ Preview  │  │ File Explorer    │ │  │
│  │  │ Input    │→ │ (IR/AST) │  │ + Download       │ │  │
│  │  └──────────┘  └──────────┘  └──────────────────┘ │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP / WebSocket
                         ▼
┌──────────────────────────────────────────────────────────┐
│              RECPL API SERVER (Node.js/NestJS)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ POST     │  │ Pipeline │  │ Stack    │  │ File     │ │
│  │ /prompt  │→│ Runner   │→│ Registry │→│ Server   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└────────────────────────┬─────────────────────────────────┘
                         │ exec() / pipe
                         ▼
┌──────────────────────────────────────────────────────────┐
│              RECPL SHELL PIPELINE                         │
│  preprocess → lexer → parser → semantic → IR → synthesis │
│  → scaffold (genera archivos en /tmp/output/)             │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Componentes de la UI Web

#### 3.2.1 Prompt Input (Chat-like)

```
┌──────────────────────────────────────────────┐
│  RECPL Compiler Bot  ○ ○ ○                   │
├──────────────────────────────────────────────┤
│                                              │
│  > crea un modulo de usuarios en FastAPI     │
│  ──────────────────────────────────────      │
│  ✅ Generando module Usuarios en FastAPI...  │
│                                              │
│  Archivos generados:                         │
│  📁 modules/usuarios/                        │
│    ├── 📄 usuarios.router.py                 │
│    ├── 📄 usuarios.model.py                  │
│    └── 📄 usuarios.schema.py                 │
│                                              │
│  [▶ Ejecutar]  [↻ Reiniciar]  [💾 Descargar] │
├──────────────────────────────────────────────┤
│  > _                                         │
│                                              │
└──────────────────────────────────────────────┘
```

**Funcionalidades:**
- Input tipo chat con historial
- Autocompletado de verbos, tech stacks y entidades
- Multi-linea (Shift+Enter)
- Ejemplos rapidos (botones de "prueba estos")

#### 3.2.2 AST/IR Preview

Panel lateral que muestra el arbol de procesamiento:

```
┌──────────────────────────┐
│ 🔍 Pipeline Explorer     │
├──────────────────────────┤
│ ✅ PREPROCESSOR          │
│   "crea un modulo de     │
│    usuarios en fastapi"  │
│                          │
│ ✅ LEXER (7 tokens)      │
│   ACTION_CREATE  "crea"  │
│   ENTITY         "un"    │
│   MODULE         "modulo" │
│   PREP           "de"    │
│   ENTITY         "users"  │
│   PREP           "en"    │
│   TECH_FASTAPI "fastapi" │
│                          │
│ ✅ PARSER → AST          │
│   accion: CREATE         │
│   objetivo: module       │
│   entidad: usuarios      │
│   tech: fastapi          │
│                          │
│ ✅ SEMANTIC              │
│   tech validado: FastAPI │
│                          │
│ ✅ IR GENERATOR          │
│   template: module-fastapi│
│   trace_id: trc_...      │
│                          │
│ ✅ SYNTHESIS + SCAFFOLD  │
│   3 archivos generados   │
└──────────────────────────┘
```

#### 3.2.3 File Explorer

Visor de archivos generados con editor y descarga:

```
┌──────────────────────────────────────────────┐
│ 📂 modules/usuarios/          [⬇ ZIP] [📋] │
├──────────────────────────────────────────────┤
│ 📁 modules/                                  │
│  └📁 usuarios/                               │
│    ├📄 usuarios.router.py  ← selected        │
│    ├📄 usuarios.model.py                     │
│    └📄 usuarios.schema.py                    │
├──────────────────────────────────────────────┤
│ 1 from fastapi import APIRouter              │
│ 2 from .usuarios.model import Usuario        │
│ 3 from .usuarios.schema import UsuarioSchema │
│ 4                                            │
│ 5 router = APIRouter(prefix="/usuarios")     │
│ 6                                            │
│ 7 @router.get("/")                           │
│ 8 async def list_usuarios():                 │
│ 9     return []                              │
├──────────────────────────────────────────────┤
│ Python  │ 9 lineas  │  UTF-8  │  LF         │
└──────────────────────────────────────────────┘
```

#### 3.2.4 Stack Selector Visual

Selector de tech stacks con dependencias automaticas:

```
┌──────────────────────────────────────────────┐
│ 🛠 Selecciona tu stack tecnologico            │
├──────────────────────────────────────────────┤
│ Backend                                       │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│ │ NestJS │ │Express │ │FastAPI │ │ Django │ │
│ │  ✓     │ │        │ │        │ │        │ │
│ └────────┘ └────────┘ └────────┘ └────────┘ │
│ Frontend                                      │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │
│ │ React  │ │  Vue   │ │Angular │ │ Svelte │ │
│ │  ✓     │ │        │ │        │ │        │ │
│ └────────┘ └────────┘ └────────┘ └────────┘ │
│ DB                                            │
│ ┌──────────┐ ┌────────┐ ┌──────────────────┐ │
│ │PostgreSQL│ │ MongoDB│ │ ┌──────────────┐ │ │
│ │   ✓      │ │        │ │ │   Docker     │ │ │
│ └──────────┘ └────────┘ │ │    ✓ auto    │ │ │
│                         │ └──────────────┘ │ │
│                         └──────────────────┘-│
└──────────────────────────────────────────────┘
```

### 3.3 API Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `POST` | `/api/prompt` | Envia instruccion NL, ejecuta pipeline completo |
| `GET` | `/api/prompt/:id` | Obtiene resultado de una ejecucion |
| `GET` | `/api/stacks` | Lista tech stacks disponibles |
| `GET` | `/api/stacks/:id/templates` | Lista templates de un stack |
| `GET` | `/api/files/:session/*` | Descarga archivos generados |
| `GET` | `/api/files/:session/zip` | Descarga todo como ZIP |
| `GET` | `/api/history` | Historial de ejecuciones |
| `DELETE` | `/api/history` | Limpia historial |

### 3.4 Stack Tecnologico de la UI

| Componente | Tecnologia | Justificacion |
|------------|------------|---------------|
| Frontend | React + TypeScript | Ecosistema maduro, tipado fuerte |
| Build tool | Vite | Rapido, soporte TS nativo |
| UI Framework | Tailwind CSS | Prototipado rapido, diseno consistente |
| Editor de codigo | Monaco Editor (VS Code core) | Experiencia de edicion profesional |
| Arbol de archivos | custom React component | Visualizacion de estructura de directorios |
| API Server | NestJS (mismo stack del proyecto) | Consistencia con el ecosistema @tienda/api |
| WebSocket | Socket.io | Streaming de pipeline en tiempo real |
| Empaquetado | Docker multi-stage | Frontend compilado + API estatico |

### 3.5 Flujo de Ejecucion Web

```
USUARIO: escribe "crea proyecto blog con fastapi postgres y react"
  │
  ▼
[1] UI: envia POST /api/prompt con { text: "..." }
  │
  ▼
[2] API Server:
    ├── Crea directorio temporal /tmp/recpl_web_<session>/
    ├── Ejecuta pipeline shell (preprocess → lexer → parser → semantic → IR → synthesis)
    ├── scaffold.sh escribe archivos en /tmp/recpl_web_<session>/output/
    ├── Genera tree.json con estructura de directorios
    └── Responde con resultado + session_id
  │
  ▼
[3] UI: recibe respuesta
    ├── Muestra mensaje del bot
    ├── Carga arbol de archivos via GET /api/files/<session>/
    └── Habilita descarga ZIP
  │
  ▼
[4] USUARIO: explora archivos, edita, descarga
```

### 3.6 Streaming en Tiempo Real

Para instrucciones largas, el pipeline se ejecuta con WebSocket:

```
[WS] /api/prompt/stream

CLIENT → { text: "crea proyecto completo ecommerce..." }
SERVER →
  {"stage": "preprocessor", "status": "ok", "data": "..."}
  {"stage": "lexer", "status": "ok", "tokens": 12}
  {"stage": "parser", "status": "ok", "ast": {...}}
  {"stage": "semantic", "status": "ok"}
  {"stage": "ir", "status": "ok", "template": "full-project"}
  {"stage": "scaffold", "status": "progress", "file": "backend/app/main.py"}
  {"stage": "scaffold", "status": "progress", "file": "backend/requirements.txt"}
  {"stage": "scaffold", "status": "progress", "file": "frontend/src/App.tsx"}
  {"stage": "done", "status": "ok", "files": 24, "session": "abc123"}
```

### 3.7 Interfaz Multi-Sesion

El sistema web soporta multiples sesiones simultaneas, cada una con su
propio directorio temporal y estado:

```
/tmp/recpl_web_abc123/
├── input.txt
├── pipeline.log
├── output/
│   ├── backend/
│   ├── frontend/
│   └── docker-compose.yml
└── tree.json

/tmp/recpl_web_def456/
├── input.txt
├── pipeline.log
├── output/
└── tree.json
```

---

## 4. Plan de Implementacion

### 4.1 Fases

| Fase | Nombre | Descripcion | Duracion est. |
|------|--------|-------------|---------------|
| **FASE-E1** | Registry de Stacks | Crear `stacks/registry.sh`, migrar templates existentes, definir formato stack.json | 3-4 dias |
| **FASE-E2** | Nuevos Tech Stacks | Implementar templates para Express, FastAPI, Django, React, Vue, Docker, PostgreSQL | 5-7 dias |
| **FASE-E3** | Multi-Stack Parser | Extender lexer/parser para tokens TECH_* adicionales y gramatica multi-tech | 2-3 dias |
| **FASE-E4** | API Server (NestJS) | Crear servidor REST + WebSocket que envuelve el pipeline shell | 4-5 dias |
| **FASE-E5** | UI Web (React) | Interfaz de usuario con prompt, preview, file explorer y descarga | 5-7 dias |
| **FASE-E6** | Integracion y Tests | Pipeline end-to-end via UI, tests de regresion, hardening | 3-4 dias |
| **FASE-E7** | Despliegue | Dockerizacion, documentacion, CI/CD | 2-3 dias |

### 4.2 Tareas Detalladas

#### FASE-E1: Registry de Stacks

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| EST-001 | Disenar formato stack.json (metadatos por stack) | — | S |
| EST-002 | Crear `stacks/registry.sh` — descubrimiento y carga de stacks | EST-001 | M |
| EST-003 | Migrar templates NestJS existentes a `stacks/nestjs/` | — | M |
| EST-004 | Migrar templates Prisma existentes a `stacks/prisma/` | — | M |
| EST-005 | Crear `stacks/registry.sh list` — listar stacks disponibles | EST-002 | S |
| EST-006 | Crear `stacks/registry.sh detect <texto>` — detectar stacks desde NL | EST-002, FASE-E3 | M |
| EST-007 | Validar con `bash -n` y tests unitarios | EST-002 | S |

#### FASE-E2: Nuevos Tech Stacks

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| EST-008 | Implementar stack Express (route, middleware, model, controller) | EST-001 | L |
| EST-009 | Implementar stack FastAPI (router, model, schema, crud) | EST-001 | L |
| EST-010 | Implementar stack Django (app, model, view, serializer, url) | EST-001 | L |
| EST-011 | Implementar stack Flask (blueprint, model, route) | EST-001 | M |
| EST-012 | Implementar stack Spring Boot (controller, service, repository) | EST-001 | L |
| EST-013 | Implementar stack Go Gin (handler, service, model) | EST-001 | L |
| EST-014 | Implementar stack React (component, hook, service, page) | EST-001 | L |
| EST-015 | Implementar stack Vue (component, composable, store, view) | EST-001 | L |
| EST-016 | Implementar stack Angular (component, service, module) | EST-001 | L |
| EST-017 | Implementar stack Next.js (page, api-route, component, layout) | EST-001 | L |
| EST-018 | Implementar stack PostgreSQL (schema, migration, seed) | EST-001 | M |
| EST-019 | Implementar stack MongoDB (schema, model, aggregation) | EST-001 | M |
| EST-020 | Implementar stack Docker (Dockerfile, compose, .dockerignore) | EST-001 | M |
| EST-021 | Implementar stack Kubernetes (deployment, service, configmap) | EST-001 | L |
| EST-022 | Implementar stack GraphQL (schema, resolver, type) | EST-001 | M |
| EST-023 | Templates "full-project" para stacks principales | EST-008..022 | XL |

#### FASE-E3: Multi-Stack Parser

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| EST-024 | Extender lexer con nuevos tokens TECH_* (express, fastapi, react, etc.) | — | M |
| EST-025 | Extender parser para gramatica multi-tech (varios PREP TECH) | — | M |
| EST-026 | Extender semantic.sh para validar multiples tech stacks | EST-025 | M |
| EST-027 | Extender ir_generator.sh para lista de templates multi-stack | EST-026 | M |
| EST-028 | Extender synthesis.sh para scaffolding multi-stack | EST-027 | L |
| EST-029 | Tests de regresion para parser multi-tech | EST-024, EST-025 | M |

#### FASE-E4: API Server

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| EST-030 | Crear proyecto NestJS para API server (`web/`) | — | S |
| EST-031 | Implementar `POST /api/prompt` — ejecuta pipeline shell via `child_process` | EST-030 | L |
| EST-032 | Implementar `GET /api/sessions/:id` — consultar resultado | EST-031 | M |
| EST-033 | Implementar `GET /api/stacks` — lista stacks del registry | EST-030, EST-002 | M |
| EST-034 | Implementar `GET /api/files/:session/*` — servir archivos generados | EST-031 | M |
| EST-035 | Implementar `GET /api/files/:session/zip` — descarga ZIP | EST-034 | M |
| EST-036 | Implementar WebSocket `/api/prompt/stream` — streaming en tiempo real | EST-031 | L |
| EST-037 | Gestion de sesiones (crear, limpiar TTL, directorios temporales) | EST-031 | M |
| EST-038 | Tests de integracion API + pipeline shell | EST-031 | M |

#### FASE-E5: UI Web

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| EST-039 | Crear proyecto React + Vite + Tailwind (`ui/`) | — | S |
| EST-040 | Componente PromptInput (chat, autocompletado, multi-linea) | EST-039 | L |
| EST-041 | Componente PipelineExplorer (AST/IR preview por etapas) | EST-039 | L |
| EST-042 | Componente FileExplorer (arbol de directorios + Monaco editor) | EST-039 | XL |
| EST-043 | Componente StackSelector (visual, con dependencias) | EST-039, EST-033 | L |
| EST-044 | Componente ResponseView (mensaje del bot, archivos, acciones) | EST-039 | M |
| EST-045 | Integracion con API REST (fetch + WebSocket) | EST-040..044, FASE-E4 | L |
| EST-046 | Historial de sesiones (localStorage + API) | EST-045 | M |
| EST-047 | Descarga ZIP de archivos generados | EST-042, EST-035 | M |
| EST-048 | Modo oscuro / claro | EST-039 | S |
| EST-049 | Tests E2E con Cypress | EST-045 | L |

#### FASE-E6: Integracion

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| EST-050 | Pipeline end-to-end: UI → API → shell → archivos → descarga | FASE-E4, FASE-E5 | L |
| EST-051 | Tests de regresion (47 tests existentes + nuevos) | — | L |
| EST-052 | Manejo de errores en todos los componentes web | EST-050 | M |
| EST-053 | Seguridad: sanitizar input, limitar tamano de proyectos | EST-050 | M |
| EST-054 | Performance: lazy loading, paginacion de historial | EST-050 | M |

#### FASE-E7: Despliegue

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| EST-055 | Docker multi-stage: frontend compilado + API + shell | — | M |
| EST-056 | docker-compose para desarrollo local | EST-055 | S |
| EST-057 | Documentacion de la UI web (README, runbook) | EST-050 | M |
| EST-058 | CI/CD: build + test + deploy | EST-055 | M |

### 4.3 Diagrama de Dependencias

```
FASE-E1 (Registry)
  │
  ├──→ FASE-E2 (Nuevos Stacks)
  │
  └──→ FASE-E3 (Parser Multi-Stack) ──→ FASE-E4 (API Server) ──→ FASE-E6 (Integracion)
                                              │                        │
                                              └──→ FASE-E5 (UI Web) ──┘
                                                                        │
                                                                   FASE-E7 (Despliegue)
```

---

## 5. Stack Tecnologico de la UI Web

| Tecnologia | Uso | Version |
|------------|-----|---------|
| React 18 | UI framework | 18.x |
| TypeScript 5 | Lenguaje frontend | 5.x |
| Vite | Build tool | 5.x |
| Tailwind CSS | Estilos | 3.x |
| Monaco Editor | Editor de codigo | última |
| React Router | Routing SPA | 6.x |
| Socket.io Client | WebSocket | 4.x |
| NestJS 11 | API server | 11.x |
| Socket.io | WebSocket server | 4.x |
| archiver (npm) | Generacion ZIP | última |
| Docker | Contenedores | 24+ |
| docker-compose | Orquestacion local | 2.x |

---

## 6. Arquitectura de Directorios (Estado Final)

```
compiler-bot/
├── frontend/                    # CLI pipeline (existente)
├── middleend/                   # CLI pipeline (existente)
├── backend/                     # CLI pipeline (existente)
├── stacks/                      # NUEVO: tech stacks
│   ├── registry.sh
│   ├── nestjs/
│   ├── prisma/
│   ├── express/
│   ├── fastapi/
│   ├── django/
│   ├── flask/
│   ├── spring/
│   ├── gin/
│   ├── react/
│   ├── vue/
│   ├── angular/
│   ├── svelte/
│   ├── nextjs/
│   ├── postgres/
│   ├── mongodb/
│   ├── docker/
│   ├── kubernetes/
│   └── graphql/
├── web/                         # NUEVO: API server NestJS
│   ├── src/
│   │   ├── prompt/
│   │   ├── pipeline/
│   │   ├── stacks/
│   │   ├── files/
│   │   └── sessions/
│   ├── test/
│   └── package.json
├── ui/                          # NUEVO: frontend React
│   ├── src/
│   │   ├── components/
│   │   │   ├── PromptInput/
│   │   │   ├── PipelineExplorer/
│   │   │   ├── FileExplorer/
│   │   │   ├── StackSelector/
│   │   │   └── ResponseView/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── public/
│   └── package.json
├── recpl.sh                     # LOOP CLI (existente)
├── tests/                       # Tests (existente)
└── docker-compose.yml           # NUEVO: orquestacion
```

---

## 7. Metricas de Exito

| KPI | Target | Como se mide |
|-----|--------|-------------|
| Tech stacks implementados | 18 stacks | Conteo en `stacks/registry.sh list` |
| Templates por stack | ≥ 3 por stack | `ls stacks/*/templates/` |
| Tests de pipeline multi-tech | ≥ 80 tests | `tests/run_tests.sh` |
| UI: tiempo hasta primer prompt | < 3s | Lighthouse / medida manual |
| UI: proyectos generados por sesion | Ilimitados | Conteo en historial |
| Cobertura de deteccion NL | > 90% | Test con variaciones de lenguaje natural |
| Satisfaccion de usuario | > 4/5 | Encuesta interna |

---

## 8. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| Templates de baja calidad para nuevos stacks | Medio | Alta | Revision por pares, tests de compilacion |
| UI web demasiado compleja para el problema | Alto | Media | MVP con solo prompt + file explorer, iterar |
| Dependencia de Node.js en el servidor | Medio | Baja | Docker encapsula todo |
| Seguridad: ejecucion de shell desde web | Alto | Baja | Sanitizar input, container temporal por sesion |
| Mantenimiento de 18+ stacks | Medio | Alta | CI que verifica templates, detector de roturas |
| Permisos de archivos en Docker | Bajo | Media | Usuario no-root en container, volumenes mapeados |

---

## 9. Conclusion

La extension del bot RECPL con multi-tech-stack y UI web lo transforma de una
herramienta CLI especializada en NestJS/Prisma a una **plataforma general de
scaffolding multi-lenguaje** accesible desde el navegador.

**Impacto esperado:**
- Reduccion de tiempo de setup de nuevos proyectos de horas a segundos
- Curva de aprendizaje plana: lenguaje natural en vez de comandos complejos
- Consistencia: todos los proyectos generados siguen las mismas convenciones
- Colaboracion: templates compartibles y versionables

**Proximo paso recomendado:** FASE-E1 (Registry de Stacks) + FASE-E3 (Parser
Multi-Stack) para habilitar los nuevos tech stacks en el CLI existente antes
de construir la UI web.
