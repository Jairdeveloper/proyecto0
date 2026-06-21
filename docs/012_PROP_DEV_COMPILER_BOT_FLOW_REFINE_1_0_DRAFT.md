---
id: 012
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
  - flujo-datos
  - integracion
  - web-ui
  - refinamiento
  - multi-stack
  - composicion
summary: "Propuesta de continuacion de 011_PROP_DEV_COMPILER_BOT_EXTENDED. Define el flujo de datos para integracion multi-tech-stack (composicion, dependencias, contratos) y una UI web con ciclo de refinamiento iterativo (editar, regenerar, diff, versionar)."
keywords:
  - propuesta
  - mejora
  - recpl
  - flujo-datos
  - integracion
  - composicion
  - dependencias
  - web-ui
  - refinamiento
  - iteracion
  - diff
  - multi-stack
  - compilador
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion de la propuesta de flujo de datos multi-stack y UI iterativa
---

# Propuesta de Continuacion: Flujo de Datos Multi-Stack y Refinamiento Iterativo

> **Continuacion de:** `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md`
>
> Mientras 011 define **que** stacks y **que** UI, esta propuesta define
> **como se integran** los stacks entre si y **como el usuario refina**
> iterativamente el resultado desde la UI web.

---

## 1. Resumen Ejecutivo

### 1.1 Problemas que Resuelve

| Problema | Solucion en esta propuesta |
|----------|---------------------------|
| Los stacks generan codigo aislado, sin conexion entre si | Flujo de datos multi-stack con contratos automaticos (API, BD, envs) |
| El usuario recibe un proyecto estatico, sin poder iterar | Ciclo de refinamiento: editar → regenerar → diff → versionar |
| No hay trazabilidad entre el prompt y el codigo generado | Grafo de dependencias entre artefactos, cada archivo sabe de donde vino |
| Cambiar un stack requiere regenerar todo desde cero | Regeneracion parcial: solo los modulos afectados por el cambio |

### 1.2 Vision General

```
SESION WEB TIPICA:

[1] USUARIO: "crea un blog con fastapi, react y postgres"
    ↓
[2] SISTEMA: genera proyecto completo + grafo de dependencias entre stacks
    ↓
[3] USUARIO: edita main.py en el Monaco Editor
    ↓
[4] SISTEMA: detecta que el cambio afecta a docker-compose (puerto), regenera solo ese archivo
    ↓
[5] USUARIO: "cambia postgres por mongodb"
    ↓
[6] SISTEMA: regenera modelo de datos, schema, y docker-compose; mantiene frontend intacto
    ↓
[7] USUARIO: descarga ZIP v1, luego prueba otra variante, descarga ZIP v2
```

---

## 2. Flujo de Datos Multi-Stack

### 2.1 Grafo de Dependencias entre Stacks

Cuando un prompt activa multiples stacks, el sistema construye un **grafo de dependencias**
que determina el orden de scaffolding y los contratos entre componentes:

```
         ┌──────────────────────────────────────────────────┐
         │              PROYECTO: "BLOG"                     │
         │                                                    │
         │  ┌──────────┐     ┌──────────┐     ┌──────────┐  │
         │  │ FastAPI  │────→│PostgreSQL│     │  React   │  │
         │  │ Backend  │     │   DB     │     │ Frontend │  │
         │  │ :8000    │     │ :5432    │     │ :3000    │  │
         │  └────┬─────┘     └──────────┘     └────┬─────┘  │
         │       │                                  │       │
         │       │  Contrato API                    │       │
         │       │  - host: backend:8000            │       │
         │       │  - /api/usuarios                 │       │
         │       │  - /api/posts                    │       │
         │       │                                  │       │
         │       └──────────────┬───────────────────┘       │
         │                      │                           │
         │              ┌───────▼───────┐                   │
         │              │   Docker      │                   │
         │              │  Compose      │                   │
         │              │  - network    │                   │
         │              │  - env vars   │                   │
         │              │  - volumes    │                   │
         │              └───────────────┘                   │
         └──────────────────────────────────────────────────┘
```

### 2.2 Contratos entre Stacks

Cada stack declara **contratos** (lo que ofrece) y **dependencias** (lo que necesita).
El sistema resuelve estos contratos para generar codigo de integracion.

```json
{
  "stack": "fastapi",
  "contratos": {
    "api": {
      "type": "rest",
      "base_url": "/api/v1",
      "port": 8000,
      "endpoints": [
        {"method": "GET",  "path": "/{entity}"},
        {"method": "POST", "path": "/{entity}"},
        {"method": "GET",  "path": "/{entity}/{id}"},
        {"method": "PUT",  "path": "/{entity}/{id}"},
        {"method": "DELETE", "path": "/{entity}/{id}"}
      ],
      "schema_format": "pydantic"
    },
    "env_vars": [
      "DATABASE_URL=postgresql://user:pass@db:5432/blog",
      "CORS_ORIGINS=http://localhost:3000"
    ]
  },
  "dependencias": {
    "db": ["postgresql"],
    "infra": ["docker"]
  }
}
```

```json
{
  "stack": "react",
  "contratos": {
    "api_client": {
      "type": "axios",
      "base_url_env": "VITE_API_URL",
      "endpoints": ["GET /api/v1/{entity}", "POST /api/v1/{entity}", "..."]
    }
  },
  "dependencias": {
    "backend": ["fastapi"],
    "infra": ["docker"]
  }
}
```

### 2.3 Resolucion Automatica de Contratos

El sistema **resuelve automaticamente** los contratos entre stacks:

```
Fase: RESOLVE_CONTRACTS

Entrada:
  stacks = [fastapi, react, postgresql, docker]

Proceso:
  1. fastapi.declara_contratos() → API REST en puerto 8000
  2. react.requiere_backend() → busca stack que ofrezca api.rest
  3. Sistema vincula: react.api_client.base_url ← fastapi.api.base_url
  4. postgresql declara: host=db, port=5432, dbname=blog
  5. Sistema genera DATABASE_URL para fastapi: postgresql://user:pass@db:5432/blog
  6. docker.compose.refleja(): crea servicios backend, frontend, db
  7. Sistema genera network interna + env vars

Salida:
  - .env (compartido entre stacks)
  - docker-compose.yml (servicios interconectados)
  - api-client.ts en React (apunta a backend:8000)
  - main.py en FastAPI (CORS configurado para frontend:3000)
```

### 2.4 Archivos de Integracion Generados

| Archivo | Stacks involucrados | Que contiene |
|---------|-------------------|--------------|
| `docker-compose.yml` | Todos | Servicios, networks, envs, volumes |
| `.env` | Todos | Variables de entorno compartidas |
| `docker/nginx.conf` | Backend + Frontend | Proxy reverso, CORS, rutas |
| `frontend/src/api/client.ts` | Frontend + Backend | Cliente API con URL del backend |
| `backend/app/config.py` | Backend + DB | Configuracion de BD desde env vars |
| `backend/requirements.txt` | Backend + Docker | Dependencias + uvicorn |
| `frontend/package.json` | Frontend + Docker | Dependencias + proxy |
| `Makefile` | Todos | Comandos utiles: `make dev`, `make build` |
| `README.md` | Todos | Instrucciones de ejecucion |

### 2.5 Pipeline de Integracion

```
ENTRADA: prompt + stacks detectados
  │
  ▼
[1] RESOLVE_DEPENDENCIES
    │
    ├──→ fastapi.dependencias = [postgresql, docker]
    ├──→ react.dependencias = [fastapi, docker]
    └──→ docker.dependencias = [fastapi, react, postgresql]
  │
  ▼
[2] RESOLVE_CONTRACTS
    │
    ├──→ fastapi.api_url ← react.api_client.base_url
    ├──→ postgresql.dsn ← fastapi.env.DATABASE_URL
    └──→ docker.network ← [backend, frontend, db]
  │
  ▼
[3] GENERATE_ORDER (topological sort)
    │
    ├──→ 1. postgresql/ (modelos, migrations)
    ├──→ 2. fastapi/ (models, routers, config)
    ├──→ 3. react/ (components, api client)
    └──→ 4. docker/ (compose, nginx, makefile)
  │
  ▼
[4] SCAFFOLD (por cada stack en orden)
    │
    ├──→ scaffold.sh postgresql/ → modules/postgresql/
    ├──→ scaffold.sh fastapi/ → modules/fastapi/
    ├──→ scaffold.sh react/ → modules/react/
    └──→ scaffold.sh docker/ → docker-compose.yml
  │
  ▼
[5] POST_PROCESS
    │
    ├──→ Inyectar DATABASE_URL en fastapi/.env
    ├──→ Inyectar VITE_API_URL en react/.env
    ├──→ Generar docker-compose con 3 servicios
    └──→ Generar README.md con instrucciones
```

### 2.6 Formato de Salida del Pipeline de Integracion

```json
{
  "session_id": "sess_abc123",
  "prompt": "crea un blog con fastapi, react y postgres",
  "stacks": ["fastapi", "react", "postgresql", "docker"],
  "dependencies": {
    "fastapi": ["postgresql", "docker"],
    "react": ["fastapi", "docker"],
    "postgresql": ["docker"],
    "docker": ["fastapi", "react", "postgresql"]
  },
  "contracts": {
    "fastapi.api.base_url": "http://backend:8000/api/v1",
    "react.api_client.base_url": "http://localhost:8000/api/v1",
    "postgresql.dsn": "postgresql://user:pass@db:5432/blog",
    "docker.services": ["backend", "frontend", "db"]
  },
  "order": ["postgresql", "fastapi", "react", "docker"],
  "files": {
    "total": 24,
    "generated": [
      {"path": "modules/postgresql/models/", "count": 3},
      {"path": "modules/fastapi/", "count": 8},
      {"path": "modules/react/", "count": 10},
      {"path": "docker-compose.yml", "count": 1},
      {"path": ".env", "count": 1},
      {"path": "README.md", "count": 1}
    ]
  },
  "integration_files": [
    "docker-compose.yml",
    ".env",
    "frontend/src/api/client.ts",
    "backend/app/config.py"
  ]
}
```

---

## 3. UI Web con Ciclo de Refinamiento

### 3.1 Arquitectura de la Sesion Iterativa

A diferencia de la propuesta 011 (una sola ejecucion → descarga), esta UI
soporta un **ciclo de refinamiento** dentro de la misma sesion:

```
                    ┌──────────────────────────────────────┐
                    │         SESION DE TRABAJO             │
                    │                                      │
  INICIO            │  ┌──────────┐    ┌──────────┐       │
    │               │  │ Prompt   │───→│ Version  │       │
    ▼               │  │ v1       │    │  1       │       │
┌────────┐          │  └──────────┘    └────┬─────┘       │
│Prompt  │          │         │             │             │
│Input   │          │         ▼             ▼             │
└────────┘          │  ┌──────────┐    ┌──────────┐       │
    │               │  │ Prompt   │───→│ Version  │       │
    │ (refinar)     │  │ v2       │    │  2       │       │
    ▼               │  └──────────┘    └────┬─────┘       │
┌────────┐          │         │             │             │
│Prompt  │          │         ▼             ▼             │
│Input   │          │  ┌──────────┐    ┌──────────┐       │
│v2      │          │  │ Prompt   │───→│ Version  │       │
└────────┘          │  │ v3       │    │  3       │       │
    │               │  └──────────┘    └──────────┘       │
    ▼               │         │             │             │
  ...               │         ▼             ▼             │
                    │    (siguiente)    (siguiente)        │
                    └──────────────────────────────────────┘
                                        │
                                   ┌────▼────┐
                                   │Exportar │
                                   │ZIP v3   │
                                   └─────────┘
```

### 3.2 Componentes de la UI (Mejorados)

#### 3.2.1 Panel de Conversacion

```
┌──────────────────────────────────────────────────────────┐
│  💬 Sesion: blog-fastapi-react              [+ Nuevo]    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Tú — 14:30                                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │ crea un blog con fastapi, react y postgres         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Bot — 14:30 (2.4s)                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ ✅ Proyecto generado: 24 archivos                   │  │
│  │ 📦 stacks: fastapi • react • postgresql • docker   │  │
│  │                                                    │  │
│  │ [Ver Archivos]  [Ver Diff]  [⬇ ZIP v1]            │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Tú — 14:32                                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │ cambia la base de postgres a mongodb y anade un    │  │
│  │ modulo de autenticacion con JWT                    │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  Bot — 14:32 (3.1s)                                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 🔄 Cambios detectados:                             │  │
│  │   ├── postgresql → mongodb: 5 archivos modificados│  │
│  │   ├── fastapi/auth/: 4 archivos nuevos             │  │
│  │   ├── docker-compose.yml: actualizado              │  │
│  │   └── react: sin cambios (no afectado)             │  │
│  │                                                    │  │
│  │ [Ver Diff v1→v2]  [⬇ ZIP v2]                     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ > _                                                 │  │
│  │ [▶ Generar]  [💾 Sugerir mejora]                    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

#### 3.2.2 Editor de Archivos con Monaco

```
┌───────────────────────────────────────────────────────────┐
│  📁 proyecto-blog/                     [💾] [↻] [⬇ ZIP]  │
├───────────────────────────────────────────────────────────┤
│ 📂 proyecto-blog/                                         │
│  ├📁 backend/                       ▲                     │
│  │ ├📄 main.py                  ◄───┘ (activo)            │
│  │ ├📄 config.py                                           │
│  │ ├📁 routers/                                            │
│  │ │ ├📄 users.py                                          │
│  │ │ ├📄 posts.py                ┌─────────────────────┐   │
│  │ │ └📄 auth.py                 │ 1 from fastapi ...  │   │
│  │ ├📁 models/                   │ 2                    │   │
│  │ │ ├📄 user.py                 │ 3 app = FastAPI()    │   │
│  │ │ └📄 post.py                 │ 4                    │   │
│  │ ├📁 schemas/                  │ 5 app.include(...)   │   │
│  │ └📄 requirements.txt          └─────────────────────┘   │
│  ├📁 frontend/                   ┌─────────────────────┐   │
│  │ ├📁 src/                      │ Python  • 12 lines  │   │
│  │ │ ├📁 components/             │                      │   │
│  │ │ ├📁 pages/                  │ [Editor en vivo —    │   │
│  │ │ ├📁 services/               │  los cambios se ven  │   │
│  │ │ └📄 App.tsx                 │  al instante]        │   │
│  │ └📄 package.json              └─────────────────────┘   │
│  ├📄 docker-compose.yml          ┌─────────────────────┐   │
│  ├📄 .env                        │ ⚠ docker-compose    │   │
│  └📄 README.md                   │   se regenerara con  │   │
│                                  │   el nuevo puerto    │   │
│                                  └─────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

#### 3.2.3 Visor de Diff Entre Versiones

```
┌───────────────────────────────────────────────────────────┐
│  🔄 Diff: v1 → v2                      [← Anterior] [→]  │
├───────────────────────────────────────────────────────────┤
│  Archivos modificados (5):                                │
│  ┌────────────────────────────────────────────────────┐   │
│  │ backend/app/config.py                               │   │
│  │ - DATABASE_URL=postgresql://user:pass@db:5432/blog │   │
│  │ + DATABASE_URL=mongodb://user:pass@mongo:27017/blog│   │
│  ├────────────────────────────────────────────────────┤   │
│  │ docker-compose.yml                                  │   │
│  │ -  image: postgres:15                               │   │
│  │ -  POSTGRES_DB: blog                                │   │
│  │ +  image: mongo:7                                   │   │
│  │ +  MONGO_INITDB_DATABASE: blog                      │   │
│  ├────────────────────────────────────────────────────┤   │
│  │ backend/app/models/user.py  (NUEVO)                  │   │
│  │ backend/app/models/post.py  (NUEVO)                  │   │
│  │ backend/app/routers/auth.py  (NUEVO)                 │   │
│  └────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

#### 3.2.4 Grafo de Dependencias Visual

```
┌───────────────────────────────────────────────┐
│  🔗 Grafo del Proyecto       [v1] [v2] [v3]  │
├───────────────────────────────────────────────┤
│                                               │
│     ┌──────────┐        ┌──────────┐          │
│     │  React   │◄───────│ FastAPI  │          │
│     │  :3000   │  HTTP  │  :8000   │          │
│     └──────────┘        └────┬─────┘          │
│                              │                 │
│                              │ SQLAlchemy      │
│                              ▼                 │
│                       ┌──────────┐             │
│                       │ MongoDB  │             │
│                       │  :27017  │             │
│                       └──────────┘             │
│                                               │
│     ┌────────────────────────────────────┐    │
│     │         Docker Compose             │    │
│     │   [backend] [frontend] [mongo]     │    │
│     └────────────────────────────────────┘    │
│                                               │
│  📦 4 stacks  │  🔗 5 conexiones              │
└───────────────────────────────────────────────┘
```

### 3.3 Ciclo de Refinamiento

#### Fase 1: Edicion Directa

El usuario edita cualquier archivo directamente en el Monaco Editor.
Los cambios se detectan en vivo y se marcan con un indicador visual:

```
📄 main.py  ● (modificado localmente)
```

Si el archivo editado es un **contrato** (cambia una ruta de API, un puerto,
una variable de entorno), el sistema sugiere regenerar los archivos dependientes.

#### Fase 2: Regeneracion Parcial

Cuando el usuario modifica el prompt o un archivo, el sistema determina
el **alcance del cambio** usando el grafo de dependencias:

```
Cambio: usuario editó backend/app/routers/users.py (agregó un endpoint)

Analisis:
  - users.py → contrato afectado: API añade GET /users/stats
  - Dependientes: api-client.ts en React necesita nuevo endpoint
  - NO afectados: modelos, schemas, docker-compose

Accion:
  - Regenerar: frontend/src/services/api-client.ts (solo 1 archivo)
  - No regenerar: docker-compose.yml, modelos, etc.
```

#### Fase 3: Prompt Refinement

El usuario escribe un nuevo prompt que refina el anterior.
El sistema hace un **merge inteligente**:

```
Prompt v1: "crea un blog con fastapi, react y postgres"
Prompt v2: "cambia postgres a mongodb y agrega auth con jwt"

Interpretacion:
  - postgresql → mongodb: reemplazar stack, regenerar modelos y config
  - agregar auth: anadir stack auth-jwt, generar routers/auth.py
  - react: mantener intacto (no afectado)
  - docker-compose: actualizar (postgres → mongo, anadir auth no requiere cambio)
```

#### Fase 4: Versionado de la Sesion

Cada ejecucion genera una **version** dentro de la sesion.
El usuario puede navegar entre versiones, comparar y exportar cualquiera:

```
Sesion: blog-fastapi-react
├── v1: prompt original (24 archivos)
├── v2: postgres → mongodb + auth (28 archivos, 5 modificados)
├── v3: agrega dashboard en react (32 archivos, 4 nuevos)
└── v4: cambia fastapi por express (28 archivos, 12 modificados)

[⬇ Exportar v3]  [⬇ Exportar v4]  [⬇ Exportar todas]
```

### 3.4 API Endpoints del Ciclo de Refinamiento

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| `POST` | `/api/session` | Crear nueva sesion |
| `GET` | `/api/session/:id` | Obtener estado de la sesion |
| `POST` | `/api/session/:id/refine` | Enviar prompt de refinamiento |
| `GET` | `/api/session/:id/versions` | Listar versiones de la sesion |
| `GET` | `/api/session/:id/versions/:v` | Obtener una version especifica |
| `GET` | `/api/session/:id/versions/:v/diff/:prev` | Diff entre dos versiones |
| `GET` | `/api/session/:id/graph` | Obtener grafo de dependencias |
| `PUT` | `/api/files/:session/*` | Guardar archivo editado |
| `POST` | `/api/files/:session/regenerate` | Regenerar archivos afectados por cambios |
| `GET` | `/api/versions/:v/export` | Descargar ZIP de una version |

### 3.5 Estados de la UI

Cada archivo en el arbol tiene un **estado** visual:

| Estado | Indicador | Descripcion |
|--------|-----------|-------------|
| `generated` | Gris | Generado por el sistema, sin cambios |
| `edited` | Azul ● | Modificado por el usuario localmente |
| `stale` | Naranja ⚠ | Desactualizado (dependencia cambio, necesita regenerar) |
| `regenerated` | Verde ✓ | Regenerado tras un cambio |
| `new` | Verde + | Nuevo archivo en esta version |
| `deleted` | Rojo ✗ | Eliminado respecto a la version anterior |
| `locked` | Candado 🔒 | Archivo de contrato que no debe editarse manualmente |

---

## 4. Algoritmo de Deteccion de Cambios

### 4.1 Arbol de Dependencias entre Archivos

Cada archivo generado sabe **por que fue generado** y **que otros archivos
dependen de el**:

```json
{
  "path": "docker-compose.yml",
  "generated_by": ["fastapi", "react", "postgresql"],
  "template": "docker-compose",
  "contracts_used": [
    "fastapi.api.port",
    "react.app.port",
    "postgresql.db.port",
    "postgresql.db.name"
  ],
  "depends_on": [
    "backend/app/main.py",
    "frontend/package.json",
    "backend/requirements.txt"
  ],
  "regenerate_if_changed": [
    "backend/app/config.py",
    ".env"
  ]
}
```

### 4.2 Propagacion de Cambios

Cuando un archivo cambia, el sistema **propaga** el cambio a traves del grafo:

```
Evento: usuario edita backend/app/main.py
  │
  ├──→ main.py cambia (modificado localmente)
  │
  ├──→ Se analiza si cambios afectan contratos:
  │     ├── ¿Cambio puerto? → NO
  │     ├── ¿Cambio rutas API? → SI (anadi /users/stats)
  │     └── ¿Cambio variables de entorno? → NO
  │
  ├──→ Archivos dependientes marcados como stale:
  │     ├── frontend/src/services/api-client.ts (⚠ stale)
  │     └── README.md (⚠ stale)
  │
  └──→ UI muestra boton "Regenerar dependencias (2 archivos)"
```

### 4.3 Regeneracion Selectiva

El usuario puede regenerar solo un archivo, un grupo, o todo:

```
┌────────────────────────────────────────────────┐
│  🔄 Regeneracion selectiva                      │
│                                                 │
│  🖊 Editado: backend/app/routers/users.py       │
│                                                 │
│  Archivos stale (dependientes):                 │
│  ┌────────────────────────────────────────┐    │
│  │ ☑ frontend/src/services/api-client.ts  │    │
│  │ ☐ README.md (cambio menor)             │    │
│  └────────────────────────────────────────┘    │
│                                                 │
│  [Regenerar seleccionados]  [Regenerar todo]    │
└────────────────────────────────────────────────┘
```

---

## 5. Flujo de Datos Detallado por Escenario

### 5.1 Escenario: Proyecto Full-Stack con 4 Stacks

```
PROMPT: "crea un e-commerce con nestjs backend, react frontend,
         postgresql database, y docker"

1. LEXER → tokens:
   ACTION_CREATE, ENTITY("e-commerce"), PREP, TECH_NESTJS,
   ENTITY("backend"), SEPARATOR, TECH_REACT, ENTITY("frontend"),
   SEPARATOR, TECH_POSTGRES, ENTITY("database"), SEPARATOR,
   PREP, TECH_DOCKER

2. PARSER → AST extendido:
   accion: CREATE
   objetivo: entity → "e-commerce"
   techs: [nestjs, react, postgresql, docker]

3. RESOLVE_DEPENDENCIES (NUEVO):
   nestjs → [postgresql, docker]
   react → [nestjs, docker]
   postgresql → [docker]
   docker → [nestjs, react, postgresql]

4. RESOLVE_CONTRACTS (NUEVO):
   nestjs.api_port ← 3000
   react.api_url ← http://localhost:3000/api
   postgresql.dsn ← postgresql://user:pass@db:5432/ecommerce
   docker.compose ← [api, frontend, db]
   docker.env ← [DATABASE_URL, API_URL]

5. GENERATE_ORDER (topological sort):
   postgresql → nestjs → react → docker

6. SCAFFOLD en orden:
   postgresql/: schema.sql, seed.sql
   nestjs/: module, controller, service, entity, config
   react/: component, page, service, app
   docker/: docker-compose.yml, .env, nginx.conf, makefile

7. POST_PROCESS:
   - Inyectar DATABASE_URL en nestjs/.env
   - Inyectar API_URL en react/.env
   - Configurar CORS en nestjs para react
   - Generar docker-compose con 3 servicios
   - Generar README.md

8. SALIDA: 28 archivos, 4 stacks, proyecto funcional
```

### 5.2 Escenario: Refinamiento Cambio de DB

```
PROMPT v1: "crea un e-commerce con nestjs, react, postgresql, docker"
  → Proyecto generado (v1, 28 archivos)

USUARIO: edita prompt → "cambia postgresql a mongodb"

1. DETECTAR CAMBIO:
   - postgresql removido de techs
   - mongodb anadido a techs

2. ANALIZAR IMPACTO:
   - Modelos: postgresql/ → mongodb/ (regenerar todo)
   - nestjs/config.py: DATABASE_URL cambia (regenerar)
   - docker-compose: postgres → mongo (regenerar)
   - react: NO afectado (mantener)

3. REGENERAR:
   - modules/mongodb/ (5 archivos nuevos)
   - backend/app/config.py (modificado)
   - docker-compose.yml (modificado)
   - backend/app/models/ (regenerado con schema MongoDB)

4. SALIDA v2: 32 archivos, 4 nuevos, 3 modificados, 5 eliminados (postgresql)
```

### 5.3 Escenario: Edicion Manual + Regeneracion Parcial

```
USUARIO: abre frontend/src/pages/Home.tsx en Monaco Editor
  → Anade un nuevo componente <FeaturedProducts />

1. SISTEMA detecta cambio local
2. Analiza si el cambio afecta contratos:
   - ¿Cambio rutas de API? NO
   - ¿Cambio props de componente? SI (FeaturedProducts necesita data)
3. Sugiere regenerar:
   - backend/app/routers/products.ts (anadir endpoint GET /products/featured)
   - frontend/src/services/api.ts (anadir llamado a nuevo endpoint)
4. Usuario acepta → regeneracion parcial (2 archivos)
5. Version v3 creada con cambios locales + regenerados
```

---

## 6. Plan de Implementacion

### 6.1 Fases

| Fase | Nombre | Descripcion | Duracion est. |
|------|--------|-------------|---------------|
| **FASE-F1** | Contratos y Dependencias | Sistema de declaracion de contratos por stack, resolucion automatica | 4-5 dias |
| **FASE-F2** | Pipeline de Integracion | Generate order, resolve, scaffold multi-stack con post-process | 3-4 dias |
| **FASE-F3** | Grafo de Dependencias | Tracking de que archivo depende de que, metadatos por artefacto | 3-4 dias |
| **FASE-F4** | API de Refinamiento | Endpoints para refine, diff, versions, regenerate | 4-5 dias |
| **FASE-F5** | UI de Ciclo Iterativo | Conversacion, Monaco Editor, diff view, grafo visual | 5-7 dias |
| **FASE-F6** | Regeneracion Selectiva | Algoritmo de propagacion de cambios, stale detection | 3-4 dias |
| **FASE-F7** | Tests y Hardening | Tests de integracion multi-stack, diff, regeneracion | 3-4 dias |

### 6.2 Dependencias con 011

```
FASE-E3 (Multi-Stack Parser) ──→ FASE-F1 (Contratos)
                                       │
FASE-E2 (Nuevos Stacks) ──────────────┤
                                       │
FASE-E1 (Registry) ───────────────────┤
                                       │
                                       ▼
                                 FASE-F2 (Pipeline Integracion)
                                       │
                                       ▼
                                 FASE-F3 (Grafo Dependencias)
                                       │
                          ┌────────────┤
                          │            │
                    FASE-E4 (API) ──→ FASE-F4 (API Refinamiento)
                          │            │
                    FASE-E5 (UI) ────→ FASE-F5 (UI Ciclo Iterativo)
                          │            │
                          └────────────┤
                                       │
                                  FASE-F6 (Regen Selectiva)
                                       │
                                  FASE-F7 (Tests)
```

### 6.3 Tareas Detalladas

#### FASE-F1: Contratos y Dependencias

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| FLU-001 | Disenar schema de contratos por stack (api, db, env, infra) | EST-001 | L |
| FLU-002 | Implementar `stacks/registry.sh contracts <stack>` — declara contratos | FLU-001 | M |
| FLU-003 | Implementar `stacks/registry.sh resolve <stacks>` — resuelve contratos entre stacks | FLU-002 | L |
| FLU-004 | Crear formato `contracts.json` con resolucion automatica de dependencias | FLU-001 | M |
| FLU-005 | Tests unitarios de resolucion de contratos (3 escenarios) | FLU-003 | M |

#### FASE-F2: Pipeline de Integracion

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| FLU-006 | Implementar `generate_order()` — topological sort sobre grafo de stacks | FLU-003 | M |
| FLU-007 | Extender scaffold.sh para multi-stack con orden de generacion | FLU-006 | L |
| FLU-008 | Implementar `post_process.sh` — inyectar env vars, configs, CORS | FLU-003 | L |
| FLU-009 | Generar docker-compose.yml con todos los servicios del grafo | FLU-008 | M |
| FLU-010 | Generar .env compartido entre stacks | FLU-008 | S |
| FLU-011 | Generar README.md con instrucciones de ejecucion (make dev) | FLU-008 | S |
| FLU-012 | Template "full-project" que compone stacks existentes | FLU-007 | XL |
| FLU-013 | Tests de integracion multi-stack (3 combinaciones) | FLU-007 | L |

#### FASE-F3: Grafo de Dependencias

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| FLU-014 | Disenar metadata por archivo generado (que stack, que template, que contratos) | FLU-001 | M |
| FLU-015 | Extender scaffold.sh para emitir `file-manifest.json` con dependencias | FLU-014 | L |
| FLU-016 | Implementar `graph.sh` — construye grafo desde manifest | FLU-015 | M |
| FLU-017 | Implementar `graph.sh affected <file>` — lista archivos dependientes | FLU-016 | M |
| FLU-018 | API endpoint `GET /api/session/:id/graph` — expone grafo como JSON | FLU-016, FASE-E4 | M |

#### FASE-F4: API de Refinamiento

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| FLU-019 | Implementar `POST /api/session/:id/refine` — prompt de refinamiento | FASE-E4 | L |
| FLU-020 | Implementar `GET /api/session/:id/versions` — lista de versiones | FASE-E4 | M |
| FLU-021 | Implementar `GET /api/session/:id/versions/:v/diff/:prev` — diff entre versiones | FLU-020 | L |
| FLU-022 | Implementar `POST /api/files/:session/regenerate` — regenerar archivos stale | FLU-017 | L |
| FLU-023 | Implementar `PUT /api/files/:session/*` — guardar edicion local | FASE-E4 | M |
| FLU-024 | Implementar `GET /api/versions/:v/export` — descarga ZIP version especifica | FLU-020 | M |
| FLU-025 | Gestion de versiones en disco (snapshot por version, diff por cambio) | FLU-020 | L |

#### FASE-F5: UI de Ciclo Iterativo

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| FLU-026 | Componente ConversationPanel (historial de prompts + respuestas) | FASE-E5 | L |
| FLU-027 | Componente MonacoEditor (editor de codigo con resaltado de sintaxis) | FASE-E5 | L |
| FLU-028 | Componente DiffViewer (visualizacion de diferencias entre versiones) | FLU-021 | XL |
| FLU-029 | Componente DependencyGraph (grafo visual interactivo) | FLU-018 | L |
| FLU-030 | Componente FileStatusBadge (generated/edited/stale/regenerated) | FASE-E5 | M |
| FLU-031 | Componente VersionTimeline (linea de tiempo de versiones) | FLU-020 | M |
| FLU-032 | Componente SelectiveRegenerate (selector de archivos a regenerar) | FLU-022 | L |
| FLU-033 | Hook `useSession` — estado global de la sesion (version actual, archivos) | FLU-026 | M |
| FLU-034 | Hook `useFileEditor` — edicion en vivo con auto-save | FLU-027 | M |
| FLU-035 | Integracion con API de refinamiento (fetch + WebSocket) | FLU-019..025 | L |

#### FASE-F6: Regeneracion Selectiva

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| FLU-036 | Algoritmo de stale detection (marcar archivos afectados por cambio) | FLU-017 | L |
| FLU-037 | Implementar `regenerate.sh <files>` — regenera solo archivos especificos | FLU-015 | L |
| FLU-038 | Lock de archivos de contrato (no edicion manual, solo regeneracion) | FLU-036 | M |
| FLU-039 | UI de confirmacion de regeneracion (que archivos, preview de cambios) | FLU-032 | M |

#### FASE-F7: Tests

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| FLU-040 | Tests de resolucion de contratos (5 combinaciones) | FASE-F1 | M |
| FLU-041 | Tests de pipeline multi-stack (3 escenarios completos) | FASE-F2 | L |
| FLU-042 | Tests de regeneracion parcial (cambiar 1 stack, verificar solo ese se regenera) | FASE-F6 | L |
| FLU-043 | Tests de diff entre versiones (json estructural, no texto plano) | FASE-F4 | M |
| FLU-044 | Tests E2E de UI: editar archivo → regenerar dependiente → verificar diff | FASE-F5 | XL |

---

## 7. Stack Tecnologico Adicional

| Tecnologia | Uso | Version |
|------------|-----|---------|
| `json-diff` (npm) | Diff estructural entre JSONs de metadatos | ultima |
| `diff` (unix) | Diff de texto plano para archivos generados | sistema |
| `graphviz` | Generacion de grafos de dependencias (dot → svg) | ultima |
| `react-flow` | Grafo interactivo en React | 11.x |
| `react-diff-viewer` | Visualizacion de diff en React | 3.x |
| `immer` | Manejo de estado inmutable para versiones | 10.x |
| `zod` | Validacion de schemas de contratos | 3.x |

---

## 8. Metricas de Exito

| KPI | Target | Como se mide |
|-----|--------|-------------|
| Resolucion de contratos correcta | 100% | Tests automatizados |
| Regeneracion parcial sin efectos colaterales | 100% | Tests de integracion |
| Tiempo de regeneracion parcial | < 1s | Benchmark |
| Versiones por sesion (promedio) | ≥ 3 | Analitica de uso |
| Archivos editados manualmente por sesion | ≥ 2 | Conteo en UI |
| Precisión de stale detection | > 95% | Tests de mutacion |
| Satisfaccion con ciclo de refinamiento | > 4/5 | Encuesta |

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| Grafo de dependencias muy complejo para proyectos grandes | Alto | Media | Limitar a max 10 stacks por proyecto, lazy loading en UI |
| Regeneracion parcial corrupta si no se actualizan todas las dependencias | Alto | Media | Lock de contratos, verificacion post-regeneracion |
| Diff entre versiones dificil de leer si cambian muchos archivos | Medio | Alta | Agrupar por stack, filtros por tipo de cambio |
| Edicion manual + regeneracion causa conflictos | Alto | Media | Marcar archivos como "conflict", UI de resolucion | 
| Sesiones muy largas consumen mucho espacio en disco | Bajo | Alta | TTL de 24h, limpieza automatica, compresion de versiones viejas |

---

## 10. Conclusion

Esta propuesta extiende la vision de 011 al anadir dos capacidades fundamentales:

1. **Flujo de datos multi-stack**: Los tech stacks no son islas — el sistema
   resuelve automaticamente contratos entre ellos, genera codigo de integracion
   y produce proyectos funcionales desde el primer momento.

2. **Ciclo de refinamiento iterativo**: El usuario no recibe un proyecto estatico.
   Puede editar, cambiar de opinion, comparar versiones, regenerar selectivamente
   y exportar la variante que mas le guste — todo desde la UI web.

**Impacto esperado:**
- Proyectos multi-stack funcionales sin configuracion manual
- Exploracion de alternativas tecnologicas sin riesgo (cambiar stack y ver diff)
- Curva de aprendizaje minima: el usuario conversa con el bot hasta obtener lo que necesita
- Trazabilidad completa: cada archivo sabe de donde vino y a quien afecta

**Proximo paso recomendado:** FASE-F1 (Contratos y Dependencias) en paralelo con
FASE-E3 (Multi-Stack Parser), ya que ambas son independientes y necesarias para
el pipeline de integracion.
