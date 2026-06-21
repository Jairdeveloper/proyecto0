---
id: alg_p_003
area: algorithms
type: algp
module: documentation
version: 1.0
status: ACTIVE
author: system
created: 2026-05-30
last_updated: 2026-05-30
tags:
  - convention
  - documentation
  - knowledge-base
  - proposal
  - naming
summary: "Propuesta de convención formal para la documentación del proyecto @compilador-compilador, orientada a convertir la base de conocimiento en un sistema RAG para agentes IA."
keywords:
  - convencion
  - documentacion
  - knowledge-base
  - RAG
  - naming
  - frontmatter
  - tags
changelog:
  - version: 1.0
    date: 2026-05-30
    author: system
    changes:
      - "Migración a formato ALGP con ID alg_p_003 y vocabulario controlado de tags"
---

# Propuesta de Convención de Documentación — @tienda/api

## Objetivo

Formalizar una convención única para toda la documentación del proyecto (`docs/`, `.opencode/agents/`, `algoritmos/`, y cualquier futura documentación) que:

1. **Unifique criterios** de nombres, estructura y contenido entre todos los archivos documentales.
2. **Optimice para RAG** — que el contenido sea fácilmente chunkable, embeddeable y recuperable por agentes IA (soporte, build, code review).
3. **Sea automatizable** — un agente IA debe poder crear, actualizar y mantener documentos siguiendo la convención sin intervención humana.
4. **Escalable** — soporte para múltiples áreas (backend, frontend, IA, DevOps, productos) sin colapsar.

---

## 1. Convención de Nombres de Archivo

### 1.1 IDs

Cada documento tiene un **ID único e inmutable**. El ID se asigna en el momento de creación y nunca cambia.

#### Formato

```
[AREA][TIPO][NNN]
```

| Componente | Descripción | Valores |
|-----------|-------------|---------|
| `AREA` | Prefijo de 2-3 letras mayúsculas | `ARCH`, `API`, `DB`, `FLOW`, `ADR`, `PRM`, `AI`, `ALG`, `AGENT`, `SEC`, `UX`, `DEV`, `OPS` |
| `TIPO` | Tipo de documento (1 letra) | `S` (spec), `R` (record), `G` (guide), `P` (proposal), `T` (template) |
| `NNN` | Número secuencial de 3 dígitos | `001`, `002`, ..., `999` |

**Ejemplos:**

| ID actual | Propuesto | Razón |
|-----------|-----------|-------|
| `001` | `ARCHS001` | Architecture spec |
| `015` | `ADRR001` | ADR record |
| `018` | `PRMP001` | Prompt proposal / template |
| — | `AGENTS001` | Agent spec |
| — | `ALGP001` | Algorithm proposal |

#### Reglas de ID

- **Inmutables**: una vez creado un ID, no se reasigna aunque se elimine el documento.
- **No secuenciales globalmente**: cada área+tipo tiene su propio contador. `ARCHS001` y `APIS001` pueden coexistir.
- **El ID en frontmatter** (`id:` field) usa el formato con guiones bajo para legibilidad: `arch_s_001`.
- **El ID en nombre de archivo** usa el formato sin separadores para brevedad: `ARCHS001`.
- **Registro de IDs**: se mantiene un archivo `docs/REGISTRO_IDS.md` con todos los IDs asignados para evitar colisiones.

### 1.2 Nombres Semánticos

Formato completo del nombre de archivo:

```
[ID]_[NOMBRE_SEMANTICO]_v[VERSION]_[ESTADO].md
```

| Componente | Reglas |
|-----------|--------|
| `ID` | `ARCHS001` — sin guiones ni separadores |
| `NOMBRE_SEMANTICO` | `UPPER_SNAKE_CASE`, máximo 5 palabras, describe el contenido |
| `VERSION` | `1_0`, `1_1`, `2_0` — semántica (major_minor) |
| `ESTADO` | `DRAFT`, `REVIEW`, `ACTIVE`, `STALE`, `DEPRECATED` |

**Estado propuesto** (reemplaza CURRENT por ACTIVE para evitar ambigüedad con "current" como directorio de trabajo):

| Estado | Significado |
|--------|------------|
| `DRAFT` | Borrador inicial, contenido incompleto |
| `REVIEW` | Contenido completo, pendiente de revisión |
| `ACTIVE` | Verificado contra código, vigente |
| `STALE` | Desactualizado, necesita revisión |
| `DEPRECATED` | Reemplazado por otro documento, se conserva como referencia histórica |

**Ejemplos:**

```
ARCHS001_SYSTEM_OVERVIEW_v1_0_DRAFT.md
APIS003_AUTH_JWT_RBAC_v1_0_DRAFT.md
ADRR015_DATABASE_POSTGRESQL_v1_0_DRAFT.md
PRMP018_BUILD_AGENT_v1_0_DRAFT.md
AGENTS001_PRISMA_REVIEWER_v1_0_ACTIVE.md
ALGP001_PRODUCCION_ALGORITMO_v1_0_DRAFT.md
```

#### Áreas y Tipos Válidos (extensibles)

| Área | Prefijo | Tipos válidos | Descripción |
|------|---------|---------------|-------------|
| Architecture | `ARCH` | `S` (spec), `R` (record) | Diseño del sistema |
| API | `API` | `S` (spec) | Especificación de endpoints |
| Database | `DB` | `S` (spec) | Schema, modelos, migraciones |
| Flows | `FLOW` | `S` (spec) | Diagramas de flujo de negocio |
| Decisions | `ADR` | `R` (record) | Architecture Decision Records |
| Prompts | `PRM` | `P` (proposal), `T` (template) | Prompts para agentes |
| AI/KB | `AI` | `G` (guide) | Documentación de knowledge base |
| Algorithms | `ALG` | `P` (proposal) | Planes y algoritmos |
| Agent | `AGENT` | `S` (spec) | Especificaciones de subagentes |
| Security | `SEC` | `S` (spec), `R` (record) | Políticas de seguridad |
| DevOps | `OPS` | `S` (spec), `G` (guide) | CI/CD, infraestructura |
| Frontend | `UX` | `S` (spec), `G` (guide) | UI/UX specifications |
| Dev | `DEV` | `G` (guide) | Guías de desarrollo |

---

## 2. Convención de Contenido

### 2.1 Frontmatter (YAML)

Todo archivo .md documental **debe** comenzar con frontmatter YAML. Esquema formal:

```yaml
---
id: arch_s_001
area: architecture
type: ARCHS
module: system
version: 1.0
status: DRAFT
author: system
created: 2026-05-23
last_updated: 2026-05-23
dependencies:
  - db_s_002
tags:
  - architecture
  - overview
  - system-design
summary: "Descripción de una línea del contenido del documento."
keywords:
  - sistema
  - arquitectura
  - nestjs
  - prisma
  - postgresql
changelog:
  - version: 1.0
    date: 2026-05-23
    author: system
    changes:
      - "Creación inicial del documento"
---
```

#### Campos Obligatorios

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | string | ID único en formato `area_tipo_nnn` (snake_case) |
| `area` | string | Área del documento (ver tabla arriba) |
| `type` | string | Tipo completo: `AREA + TIPO + NNN` ej: `ARCHS` |
| `module` | string | Módulo del sistema que documenta |
| `version` | string | Versión del documento (semver: `1.0`, `1.1`, `2.0`) |
| `status` | enum | `DRAFT`, `REVIEW`, `ACTIVE`, `STALE`, `DEPRECATED` |
| `last_updated` | date | Fecha ISO de última modificación |
| `tags` | array | Array de strings para categorización |
| `summary` | string | Resumen de 1 línea (max 200 chars) — usado como excerpt en RAG |

#### Campos Opcionales

| Campo | Tipo | Cuándo usarlo |
|-------|------|---------------|
| `author` | string | Cuando el autor se distingue del sistema |
| `created` | date | Fecha ISO de creación |
| `dependencies` | array | IDs de otros documentos de los que depende |
| `keywords` | array | Palabras clave para búsqueda (incluir sinónimos) |
| `changelog` | array | Historial de versiones del documento |
| `supersedes` | string | ID del documento al que reemplaza |
| `superseded_by` | string | ID del documento que lo reemplaza |
| `lang` | string | `es` o `en` (default: `es`) |

#### Reglas de Frontmatter

1. **`id`** debe coincidir con el prefijo del nombre de archivo (en snake_case). Ej: archivo `ARCHS001_...` → frontmatter `id: arch_s_001`.
2. **`dependencies`** referencia IDs de otros documentos, NO nombres de archivo. El RAG resolverá las referencias.
3. **`tags`** usa solo minúsculas y guiones. Normalizar a un vocabulario controlado (ver sección 3).
4. **`summary`** es crítico para RAG — debe ser un extracto que un embedding pueda indexar efectivamente.
5. **`changelog`** se actualiza manualmente (o por agente) en cada cambio significativo.

### 2.2 Estructura de Contenido por Tipo de Documento

Cada tipo de documento sigue una plantilla específica:

#### ARCHS (Architecture Spec)

```markdown
# Título Descriptivo

## Tech Stack

## Arquitectura por Capas
(diagrama en ASCII)

## Módulos Globales

## Diseño de API (visión general)

## Seguridad

## Infraestructura
```

#### APIS (API Spec)

```markdown
# [Módulo] API — [Subtítulo]

## Base Path

## Endpoints

### `METHOD /path`
- **Auth:** [@Public | JWT | @Roles()]
- **Rate limit:** [n/min]
- **Body:** `{ type, fields }`
- **Response:** `{ type, fields }`
- **Logic:** [descripción]

## Guards Aplicados

## Roles y Permisos (tabla)

## Formatos Especiales
```

#### ADRR (Architecture Decision Record)

```markdown
# ADR: [Título de la Decisión]

## Status
[Accepted | Proposed | Deprecated]

## Context
[Problema, restricciones, fuerzas]

## Decision
[Decisión tomada]

### Rationale
[Razones detalladas]

### Alternativas Consideradas
(tabla)

## Consequences
### Positivas
### Negativas

## Related
[Referencias a otros documentos]
```

#### FLOWS (Flow Spec)

```markdown
# [Nombre] Flow

## Secuencia Principal
(diagrama de secuencia en ASCII)

## Secuencias Alternativas
(diagramas cuando aplique)

## Validaciones y Errores
(tabla de condiciones)

## Estados
(máquina de estados si aplica)
```

#### PRMP (Prompt Proposal)

```markdown
# [Nombre] — Prompt Convention

## Identity Statement

## Tech Stack

## Architecture Rules

## Commands

## Key Patterns

## Template
```

#### AGENTS (Agent Spec)

```markdown
# [Nombre del Subagente]

## Propósito
[Una línea sobre qué hace]

## Cuándo se invoca
[Trigger conditions]

## Dependencias
[IDs de documentos que debe leer]

## Instrucciones
[Prompt completo]

## Formato de Salida
[Qué debe devolver al agente principal]
```

#### ALGP (Algorithm Proposal)

```markdown
# Algoritmo: [Nombre]

## Definición Formal
- INPUT:
- OUTPUT:
- PRECONDICIÓN:
- POSTCONDICIÓN:

## Pasos
### Paso 1: [Nombre]
- Acción:
- Verificación:
- Error:

## Diagrama de Flujo
(ASCII)

## Runbook
```

### 2.3 Reglas Generales de Contenido

1. **Idioma**: los documentos pueden estar en español o inglés. Usar `lang` field en frontmatter para indicarlo.
2. **Diagramas**: usar exclusivamente diagramas ASCII (art de texto). No imágenes, no Mermaid (no es RAG-friendly).
3. **Tablas**: usar formato GFM (GitHub Flavored Markdown) para tablas.
4. **Código**: bloques de código con lenguaje especificado. ` ```typescript `, ` ```bash `, ` ```yaml `, ` ```json `, ` ```sql `, ` ```prisma `.
5. **Títulos**: `#` solo para el título principal. `##` para secciones. `###` para subsecciones. Máximo 3 niveles.
6. **Links internos**: usar referencias a `id:` fields, no a rutas de archivo. Formato: `[ARCHS001](./docs/architecture/ARCHS001_SYSTEM_OVERVIEW_v1_0_DRAFT.md)`.
7. **Sin contenido duplicado**: si un concepto se documenta en otro lugar, usar referencia cruzada en vez de copiar.
8. **Extensión máxima**: idealmente 200-300 líneas. Si un documento excede 500 líneas, dividir en múltiples documentos.
9. **Chunking-friendly**: cada sección `##` debe ser auto-contenida (puede entenderse sin leer el documento completo). Primera oración de cada sección debe ser un resumen.
10. **Sin placeholders**: no dejar `[TODO]`, `[PENDIENTE]`, `[...]`. Usar `PENDING: descripción de lo que falta`.

---

## 3. Vocabulario Controlado de Tags

Para facilitar búsqueda y filtrado RAG, los tags deben normalizarse:

### Tags de Área
| Tag | Descripción |
|-----|-------------|
| `architecture` | Documentos de arquitectura |
| `api-spec` | Especificaciones de API |
| `database` | Schema y modelos |
| `flow` | Diagramas de flujo |
| `adr` | Decisiones arquitectónicas |
| `prompt` | Prompts de agente |
| `knowledge-base` | Documentación de KB |
| `algorithm` | Algoritmos y planes |
| `agent-spec` | Especificaciones de subagentes |
| `security` | Seguridad |
| `devops` | CI/CD, infraestructura |

### Tags de Módulo
`auth`, `users`, `catalog`, `cart`, `checkout`, `orders`, `payments`, `inventory`, `admin`, `system`

### Tags de Estado
`proposal`, `active`, `deprecated`, `reference`

### Tags Técnicos
`nestjs`, `prisma`, `postgresql`, `redis`, `jwt`, `rbac`, `docker`, `typescript`, `testing`, `e2e`, `unit-test`

---

## 4. Directorios y Organización

### Árbol Propuesto

```
docs/
├── REGISTRO_IDS.md           # <-- NUEVO: registro central de IDs
├── MASTER_INDEX.md            # Mapa del sistema (actualizado)
├── architecture/              # ARCHS*
├── api/                       # APIS*
├── database/                  # DBS*
├── flows/                     # FLOWS*
├── decisions/                 # ADRR*
├── prompts/                   # PRMP*, PRMT*
├── ai/                        # AIG*
├── security/                  # SECS*, SECR*  <-- NUEVO
├── devops/                    # OPSS*, OPSG*  <-- NUEVO
└── archive/                   # Documentos DEPRECATED movidos aquí

algoritmos/                    # ALGP*
  └── (planes y algoritmos)

.opencode/agents/              # AGENTS*
  └── (especificaciones de subagentes)
```

### REGISTRO_IDS.md

Archivo central que mantiene el registro de todos los IDs asignados:

```yaml
# Registro de IDs — @tienda/api

## ARCHS (Architecture Spec)
| ID | Archivo | Estado | Creado |
|----|---------|--------|--------|
| ARCHS001 | SYSTEM_OVERVIEW | ACTIVE | 2026-05-23 |

## APIS (API Spec)
| ID | Archivo | Estado | Creado |
|----|---------|--------|--------|
| APIS003 | AUTH_JWT_RBAC | ACTIVE | 2026-05-23 |
| ... | ... | ... | ... |

## ADRR (ADR Record)
| ID | Archivo | Estado | Creado |
|----|---------|--------|--------|
| ADRR015 | DATABASE_POSTGRESQL | ACTIVE | 2026-05-23 |
| ... | ... | ... | ... |
```

---

## 5. Integración con RAG / Knowledge Base

### 5.1 Chunking Strategy

Cada documento se divide en chunks a nivel de sección `##`:

```
Documento
├── Frontmatter → chunk 0 (metadatos, usado para filtrado)
├── ## Sección 1 → chunk 1
├── ## Sección 2 → chunk 2
└── ## Sección 3 → chunk 3
```

Cada chunk incluye en su metadato:
- `doc_id`: ID del documento origen
- `section`: nombre de la sección
- `summary`: del frontmatter
- `tags`: del frontmatter
- `module`: del frontmatter
- `status`: del frontmatter
- `version`: del frontmatter

### 5.2 Estrategia de Embedding

- **Documentos ACTIVE**: se embeddean y se incluyen en la base vectorial.
- **Documentos DRAFT/REVIEW**: se embeddean con flag `is_draft: true` para exclusión en producción.
- **Documentos STALE**: se embeddean pero con prioridad baja, marcados para re-indexación.
- **Documentos DEPRECATED**: se excluyen de la base vectorial (se conservan en archive/ para referencia).

### 5.3 Consultas RAG

El bot de soporte debe poder responder consultas como:

- "¿Cómo funciona el flujo de checkout?"
- "¿Qué permisos tiene el rol admin?"
- "¿Qué endpoints de autenticación existen?"
- "¿Cuál es la estructura de la tabla Order?"
- "¿Qué decisiones arquitectónicas se tomaron para pagos?"

Cada documento debe escribirse asumiendo que será recuperado por similitud semántica, no por navegación.

---

## 6. Ciclo de Vida del Documento

```
[Creación] → DRAFT → REVIEW → ACTIVE → STALE → (ACTIVE otra vez) → DEPRECATED → ARCHIVE
                 ↑         |         |
                 └─────────┘         |
                         (correcciones) │
                                        └──→ Si no se actualiza, va a DEPRECATED
```

### Reglas de Transición

| Transición | Disparador | Acción |
|-----------|------------|--------|
| → DRAFT | Nuevo documento creado | Asignar ID, registrar en REGISTRO_IDS.md |
| DRAFT → REVIEW | Contenido completo | Notificar para revisión |
| REVIEW → ACTIVE | Revisión aprobada | Actualizar estado en frontmatter y filename |
| ACTIVE → STALE | Código cambia, doc no se actualiza | Marcar como STALE, alertar |
| STALE → ACTIVE | Documento actualizado | Actualizar versión, fecha, estado |
| ACTIVE → DEPRECATED | Nuevo documento lo reemplaza | Añadir `superseded_by` en frontmatter |
| DEPRECATED → ARCHIVE | Documento trasladado | Mover a docs/archive/ |

---

## 7. Implementación Inmediata

### 7.1 Acciones para Migrar la Base Existente

1. Crear `docs/REGISTRO_IDS.md` con todos los IDs actuales (001-019) mapeados al nuevo formato.
2. Actualizar `docs/MASTER_INDEX.md` para reflejar el nuevo esquema de IDs.
3. Migrar frontmatter de los 19 documentos existentes al nuevo esquema.
4. Migrar nombres de archivo de los 19 documentos existentes (añadir prefijo de tipo).
5. Crear directorios `docs/security/` y `docs/devops/` (vacíos por ahora).
6. Crear directorio `docs/archive/`.

### 7.2 Acciones para Subagentes (.opencode/agents/)

Los archivos en `.opencode/agents/` siguen una convención separada pero compatible:
- Nombres: `[rol].md` (kebab-case, sin ID ni versión)
- Frontmatter: mismo esquema pero más simple (sin dependencies, sin changelog)
- Contenido: sigue el formato AGENTS (ver sección 2.2)

Estos archivos **no** forman parte del RAG principal (son instrucciones para subagentes de build/code review, no para el bot de soporte).

### 7.3 Acciones para algoritmos/

Los archivos en `algoritmos/` siguen el formato ALGP (Algorithm Proposal):
- Nombres: `ALGP[NNN]_[NOMBRE]_v[VERSION]_[ESTADO].md`
- Frontmatter: mismo esquema con `area: algorithms`
- Contenido: sigue el formato ALGP (ver sección 2.2)

---

## 8. Glosario

| Término | Definición |
|---------|------------|
| RAG | Retrieval-Augmented Generation — técnica que combina recuperación de información con generación de texto |
| Chunk | Fragmento de texto de un documento, usado como unidad de embedding |
| Embedding | Vector numérico que representa semánticamente un fragmento de texto |
| Frontmatter | Bloque YAML al inicio de un archivo .md con metadatos |
| ADR | Architecture Decision Record — documento que registra una decisión arquitectónica y su contexto |
| ID | Identificador único e inmutable de un documento |
| Status | Estado del documento dentro de su ciclo de vida |

---

## 9. Pendientes para Discusión

- [ ] ¿Usar contadores por área+tipo (ARCHS001, APIS001) o contador global único?
- [ ] ¿Mantener el formato actual `[NNN]_[AREA]_[TIPO]_[MODULO]_[VERSION]_[ESTADO].md` como está y solo añadir el prefijo de tipo? Ej: `001_ARCH_SYSTEM_OVERVIEW_v1_0_DRAFT.md` vs `ARCHS001_SYSTEM_OVERVIEW_v1_0_DRAFT.md`
- [ ] ¿Los documentos en `docs/prompts/` deberían migrar a `.opencode/` o mantenerse en docs/ para el RAG?
- [ ] ¿Establecer un tag obligatorio `lang: es` para todos los documentos existentes?
- [ ] ¿Crear un script de validación (CI) que verifique frontmatter, IDs y referencias?
