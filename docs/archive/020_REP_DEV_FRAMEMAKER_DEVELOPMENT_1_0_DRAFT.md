---
id: 020
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - development
  - framemaker
  - analysis
  - reverse-engineering
  - compiler
  - language-theory
  - mif
  - edd
  - architecture
  - pipeline
summary: "Reporte tecnico de desarrollo sobre Adobe FrameMaker desde compiladores y teoria de lenguajes. Traduce MIF, EDD, structured/unstructured, single-source a componentes concretos del pipeline RECPL."
keywords:
  - reporte
  - desarrollo
  - framemaker
  - compiladores
  - teoria-lenguajes
  - mif
  - edd
  - arquitectura
  - pipeline
  - tokenizacion
  - parsing
  - ir
  - gramatica
  - ast
  - single-source
changelog:
  - version: 1.0
    date: 2026-06-08
    author: workflow-agent
    description: Reporte tecnico de desarrollo sobre analisis de FrameMaker
---

# Reporte de Desarrollo: Arquitectura de FrameMaker — Ingenieria Inversa

> **Audiencia:** Equipo de desarrollo
> **Fuente:** `misc/FrameMaker.md`
> **Enfoque:** Compiladores, teoria de lenguajes, traduccion a componentes RECPL

---

## 1. FrameMaker como Compilador de Documentos

FrameMaker no es "un editor de texto". Es un **compilador de documentos** con arquitectura que mapea directamente a las fases de un compilador clasico (Aho, Dragon Book):

```
FRAMEMAKER INTERNO                EQUIVALENTE EN COMPILADORES
────────────────────────────      ──────────────────────────────
[Documento fuente]                [Codigo fuente]

1. EDD (Element Definition Doc)   1. Gramatica (BNF/EBNF)
   - Elementos validos               - Tokens y producciones
   - Relaciones jerarquicas          - AST
   - Formato contextual              - Atributos semanticos

2. Parsing estructural             2. Lexer + Parser
   - Valida contra EDD               - Tokeniza input
   - Arbol de elementos              - Construye AST
   - Atributos por contexto          - Analisis semantico

3. MIF (Maker Interchange Format)  3. IR (Intermediate Representation)
   - ASCII completo                  - IR.json canonico
   - Version-agnostic               - Pipeline-agnostic
   - Crash recovery                 - Estado serializable

4. Single-source publishing        4. Code Generation
   - PDF / HTML / Help               - Synthesis / Scaffolding
```

### 1.1 Mapeo 1:1 con nuestro Pipeline

| Fase compilador | FrameMaker | RECPL + Doc Processor | Estado |
|----------------|------------|----------------------|--------|
| Preprocesamiento | Input normalization | `preprocessor.sh` | COMPLETADO |
| Lexer | DTD/EDD define tokens | `lexer.sh` — ACTION, MODULE, ENTITY, TECH | COMPLETADO |
| Parser | Valida contra EDD, arbol elementos | `parser.sh` — LL(1) recursive descent → ASTNode | COMPLETADO |
| Semantico | Atributos por contexto, herencia | `semantic.sh` — symbol table, type checking | COMPLETADO |
| IR | **MIF** — ASCII completo | `ir_generator.sh` — **IR.json** | COMPLETADO |
| Synthesis | PDF / HTML / Help | `synthesis.sh` + `scaffold.sh` | COMPLETADO |
| Optimizacion | Conditional filtering | (futuro: 012 contract resolution) | PLANEADO |

**Observacion clave:** FrameMaker implementa el pipeline en orden inverso al nuestro. Nosotros: texto → tokens → AST → IR → output. FrameMaker: UI actions → AST → IR → output. Ambos convergen en: **IR como intermediario universal**.

---

## 2. Analisis desde Teoria de Lenguajes

### 2.1 MIF — El Lenguaje Intermedio

MIF es un lenguaje de marcado ASCII que funciona como **Intermediate Representation** de FrameMaker. Sus propiedades:

| Propiedad | Descripcion | Importancia |
|-----------|-------------|-------------|
| Serializacion completa | Todo documento FrameMaker se representa en MIF | Completeza de Turing para dominio documental |
| Idempotencia | MIF → FrameMaker → MIF produce el mismo MIF | Estabilidad del pipeline |
| Versionado semantico | MIF de cualquier version es legible por cualquier version | Compatibilidad hacia atras |
| Extensibilidad | MIF tiene features que la UI no expone | Superconjunto funcional |
| Legibilidad humana | ASCII, no binario | Depuracion, integracion |

**Estructura inferida de MIF:**

```
<MIFVersion version="9.0">
  <Doc docType="TechnicalDocument">
    <Section name="Introduction">
      <Para tag="Heading1">`Introduction`</Para>
      <Para tag="BodyText">`This document describes...`</Para>
      <Table columns="3">
        <Row><Cell>ID</Cell><Cell>Name</Cell></Row>
      </Table>
    </Section>
  </Doc>
</MIFVersion>
```

**Mapa MIF → RECPL:**

| MIF | RECPL | Explicacion |
|-----|-------|-------------|
| `<MIFVersion>` | Schema version en IR.json | Version del formato |
| `<Doc>` | Objeto raiz del AST | Documento completo |
| `<Section>` | Seccion (frontmatter area) | Unidad organizativa |
| `<Para tag="Heading1">` | Token MODULE o ENTITY | Elemento con tipo |
| `<Table>` | JSON object/array | Estructura de datos |
| Atributos (`style=`, `pageBreak=`) | Propiedades del AST | Metadata del nodo |
| Texto `` `...` `` | Lexeme de token | Contenido textual |

### 2.2 EDD — La Gramatica

EDD es una **gramatica de documentos** de FrameMaker. Es una DTD propietaria que define:

```
EDD (Gramatica inferida):
  Element: Section
    Content: (Title, Para+, Section*, Table*)
    Attributes: name=CDATA, pageBreak=(Before|After) "Before"

  Element: Para
    Content: (#PCDATA | CrossRef | Image)*
    Attributes: tag=CDATA, style=CDATA, indent=NUMBER "0"

  Element: Table
    Content: (Title?, Row+)
    Attributes: columns=NUMBER, header=(Yes|No) "No"
```

**Mapa EDD → RECPL:**

| EDD | RECPL |
|-----|-------|
| Definicion de elementos | BNF grammar (parser.sh:12-17) |
| Content model (secuencia, repeticion) | Reglas LL(1) |
| Atributos con defaults | Frontmatter YAML |
| Validacion de contexto | Semantic analyzer + type checking |
| Elementos anidados | ASTNode (ModuloEspec, OpcionalTech) |

**Diferencia critica:** EDD define **documentos**, nuestro BNF define **comandos**. Pero la estructura formal es identica: una gramatica define combinaciones validas, y un parser valida contra ella.

### 2.3 Structured vs Unstructured — Dos Modos de Procesamiento

```
STRUCTURED (Modo compilado):
  INPUT → [EDD Grammar] → Parser valida → AST → MIF → Output
  Beneficio: Consistencia, validacion automatica
  Costo: Curado inicial, aprendizaje de gramatica

UNSTRUCTURED (Modo interpretado):
  INPUT → Tag matching → Estructura libre → MIF → Output
  Beneficio: Flexibilidad, velocidad
  Costo: Sin validacion, inconsistencia potencial
```

**Traduccion a RECPL:**

| FrameMaker | RECPL |
|------------|-------|
| Structured mode | Pipeline completo (preprocess → lexer → parser → semantic → IR) |
| Unstructured mode | Preprocessor + NLP intent classification (014) |
| EDD | BNF grammar + frontmatter schema |
| EDD validation errors | Semantic analysis errors |

Nuestro pipeline ya soporta ambos modos implicitamente:
- **Estructurado:** `crea modulo pagos en nestjs` → pipeline completo
- **No estructurado:** `necesito un sistema de pagos` → NLP layer (014) lo clasifica

---

## 3. Patrones de Diseno Extraidos

### 3.1 MIF como Write-Ahead Log (Crash Recovery)

FrameMaker escribia MIF **antes** de un crash. Patron de write-ahead logging (WAL):

```
FrameMaker:
  [Editar] → [Escribir MIF temporal] → [Procesar cambio]
                ↓
           Si crash → Recuperar de MIF

Nuestra aplicacion:
  [Ejecutar paso] → [Guardar estado ANTES] → [Ejecutar accion]
                ↓
           Si fallo → Reanudar desde ultimo estado
```

**Implementacion:** `state_manager.sh` (018 TUT-013) debe guardar estado ANTES de ejecutar cada paso, no despues.

### 3.2 MIF como API de Integracion

MIF permitia que sistemas externos generaran documentos sin FrameMaker (API-first):

```
FrameMaker: [Sistema externo] → MIF → FrameMaker → Documento
Nosotros:   [NLP 014] → enriched_input.json → Pipeline → Output
            [Tutorial 018] → step.json → step_runner → Accion
```

**Leccion:** Nuestros formatos JSON deben ser contratos de API, no detalles internos. Documentar schema, versionar, mantener retrocompatibilidad.

### 3.3 Single-Source Publishing con Filtros Condicionales

```
FrameMaker: [Documento con tags condicionales]
  ├── if cliente=A → output A
  └── if cliente=B → output B

Nosotros: [Plantilla con variables]
  ├── if tech=NestJS → scaffold NestJS
  ├── if tech=Prisma → scaffold Prisma
  └── if include_auth=true → modulo auth
```

**Implementacion:** Sistema de templates (scaffold.sh + templates/) ya implementa esto parcialmente. Extension: filtros condicionales en IR (013 FASE-C7).

---

## 4. Reconstruccion del Pipeline FrameMaker

### 4.1 Diagrama de Flujo de Datos Inferido

```
User Input ──→ Event Loop ──→ Command Parser ──→ Mode Selector
                                                    │
                              ┌─────────────────────┼──────────┐
                              ▼                     ▼          │
                    EDD Validator           Tag Applicator     │
                    (contra gramatica)      (estilo libre)     │
                              │                     │          │
                              └─────────┬───────────┘          │
                                        ▼                      │
                                  AST Builder                  │
                                        │                      │
                                        ▼                      │
                                  MIF Generator                │
                                        │                      │
                              ┌─────────┼──────────┐           │
                              ▼         ▼          ▼           │
                         PDF       HTML        XML             │
                        Renderer  Renderer    Exporter         │
                              └─────────────────────────────────┘
                                        Output
```

### 4.2 Mapa de Componentes FrameMaker → RECPL

| FrameMaker | RECPL | Estado |
|-----------|-------|--------|
| Event Loop UI | `nlp/classify_intent.sh` (014) + `recpl.sh` | Planeado |
| Command Parser | `frontend/parser.sh` | COMPLETADO |
| Mode Selector | `--mode=full` vs `--mode=preprocess` | COMPLETADO |
| EDD Validator | `frontend/semantic.sh` | COMPLETADO |
| Tag Applicator | `frontend/preprocessor.sh` | COMPLETADO |
| AST Builder | parser.sh → ASTNode | COMPLETADO |
| MIF Generator | `ir_generator.sh` + `json_builder` | COMPLETADO |
| PDF Renderer | `synthesis.sh` + `scaffold.sh` | COMPLETADO |
| HTML Renderer | (futuro, 011 UI web) | Planeado |
| XML Exporter | (futuro) | No planeado |
| Filtro Condicional | Tags + estado en frontmatter | Parcial (003) |
| Crash Recovery | `tutorial/state_manager.sh` (018) | Planeado |

---

## 5. Implicaciones Arquitectonicas para RECPL

### 5.1 IR.json debe evolucionar a un "MIF-lite"

**Estado actual (IR.json):**
```json
{
  "accion": "create",
  "tipo": "module",
  "nombre": "pagos",
  "tech": "nestjs",
  "template": "module-nestjs",
  "trace_id": "trc_12345_6789"
}
```

**Estado deseado (IR.json v2, inspirado en MIF):**
```json
{
  "mif_version": "2.0",
  "created_at": "2026-06-08T10:00:00Z",
  "pipeline_version": "1.0",
  "document": {
    "type": "command",
    "body": {
      "accion": "create",
      "objetivo": {
        "tipo": "module",
        "nombre": "pagos",
        "entities": ["pagos"]
      },
      "techs": [
        {"nombre": "nestjs", "rol": "framework"},
        {"nombre": "prisma", "rol": "orm"}
      ],
      "requisitos": [
        {"tipo": "autenticacion", "valor": "jwt"}
      ]
    }
  },
  "context": {
    "session_id": "sess_abc123",
    "turno": 1,
    "defaults": {"tech": "nestjs"}
  },
  "metadata": {
    "trace_id": "trc_12345_6789",
    "duracion_ms": 42,
    "modo": "structured"
  }
}
```

**Mejoras clave:**
- Version del schema (compatible con MIF versioning)
- Metadata de pipeline (trazabilidad)
- Contexto de sesion (multi-turno, 014)
- Requisitos extendidos (NER, 014)
- Techs como objetos (multi-tech, 011)

### 5.2 Modo Structured/Unstructured Explicito

FrameMaker tenia Structured/Unstructured como decision consciente. Nosotros debemos hacer lo mismo:

```
recpl-core --mode=structured "crea modulo pagos en nestjs"
  → Pipeline completo con validacion semantica
  → Falla si falta tech, entidad no existe, etc.

recpl-core --mode=unstructured "necesito un sistema de pagos"
  → NLP layer (014) clasifica intencion
  → Si confianza > 0.8: sugiere pasar a structured
  → Si confianza < 0.8: pregunta que quiere hacer exactamente
```

### 5.3 EDD → BNF: Lecciones para el Parser

| Caracteristica EDD | Beneficio | Implementacion en RECPL |
|-------------------|-----------|------------------------|
| Content models con ocurrencia | Section: (Title, Para+, Section*) | Extension BNF con +, *, ? |
| Atributos con defaults | pageBreak = (Before|After) "Before" | Valores por defecto en frontmatter |
| Validacion de contexto | Para solo dentro de Section | Scope en semantic analyzer |
| Elementos opcionales | Table: (Title?, Row+) | if/else en parser |
| Cross-references | CrossRef → Section | Dependencias entre modulos (012) |

### 5.4 Filtros Condicionales

FrameMaker permitia markup condicional. Traduccion a nuestro sistema:

```
Template: module-nestjs/controller.ts
────────────────────────────────────
{% if tech.auth == "jwt" %}
import { JwtAuthGuard } from './auth.guard';
{% endif %}

{% if db.type == "prisma" %}
import { PrismaService } from './prisma.service';
{% endif %}
```

Requiere un **template engine condicional** en synthesis layer. Actualmente los templates son estaticos (scaffold.sh copia y reemplaza `__NAME__`). Extension condicional: 013 FASE-C7 (contratos y grafo).

---

## 6. Lecciones del Fracaso de FrameMaker (Perspectiva Tecnica)

### 6.1 Monolito vs Pipeline Modular

FrameMaker era un monolito. Dificultaba: extension, testing, integracion.

**Nuestra ventaja:** Pipeline modular desde el diseno. Cada fase es un script independiente via stdin/stdout JSON. Reemplazable, extensible, testeable individualmente.

### 6.2 Formato Cerrado vs Abierto

MIF era cerrado. Solo FrameMaker generaba MIF valido.

**Nuestra ventaja:** JSON abierto, documentado, con herramientas en todos los lenguajes.

### 6.3 Dependencia de Plataforma vs Portabilidad

FrameMaker: SunOS → Mac → Windows (cada transicion perdio usuarios).

**Nuestra ventaja:** Shell POSIX + C11 (POSIX.1-2008). Cualquier Unix/Linux.

---

## 7. Recomendaciones Tecnicas

### 7.1 Acciones Inmediatas

| Tarea | Archivo/s | Prioridad |
|-------|-----------|-----------|
| Anadir `mif_version` al IR.json | `ir_generator.sh`, C core | Alta |
| Documentar schema de IR.json como contrato | `docs/` | Alta |
| Implementar modo `--mode=structured/unstructured` | `main.c` | Media |
| Agregar tutorial como test de integracion | `tutorial/tests/fixtures/` (018) | Media |

### 7.2 Refinamiento del Pipeline

```
Estado actual:
  INPUT → [preprocess → lexer → parser → semantic → IR → synthesis]

Estado futuro (inspirado en FrameMaker):
  INPUT → [Mode Selector]
           → [Structured Pipeline] → [MIF-like IR] → [Renderers]
           → [Unstructured Pipeline] /
                           ↓
               [Enriched IR con contexto]
                           ↓
               [Conditional Filters]
                           ↓
               [Output: scaffold | report | index]
```

### 7.3 Integracion con Tutorial Executor (018)

FrameMaker (via MIF) leia documentos de otros sistemas. Nuestro Tutorial Executor debe:

1. Leer tutorial .md → extraer pasos
2. Traducir cada paso a IR.json → como comando RECPL
3. Ejecutar IR.json → mediante pipeline existente
4. Trackear progreso → via state_manager.sh

Esto convierte tutoriales .md en **programas ejecutables por RECPL**, exactamente como MIF convertia documentos en datos procesables por FrameMaker.

### 7.4 Propuesta: Schema de Validacion .md (EDD-lite)

```yaml
# docs/.schema.yaml (futuro)
elements:
  document:
    required_fields: [id, area, type, module, version, status]
    optional_fields: [tags, summary, keywords, changelog]
    allowed_areas: [dev, doc, ops, misc]
    allowed_types: [GUIDE, PROP, SPEC, PLAN, REP]
    allowed_status: [DRAFT, ACTIVE, DEPRECATED]

  section:
    parents: [document]
    pattern: "^## "
    required: title

  step:
    parents: [section]
    pattern: "^## Paso \\\\d+:"
    children: [code_block, instruction, verification]
```

---

## 8. Glosario FrameMaker vs RECPL

| FrameMaker | RECPL | Explicacion |
|------------|-------|-------------|
| MIF | IR.json / enriched_input.json | Lenguaje intermedio ASCII/JSON |
| EDD | BNF grammar + frontmatter schema | Gramatica de estructura valida |
| DTD | parser.sh BNF + semantic.sh types | Definicion formal de tipos |
| Structured mode | Pipeline completo | Procesamiento con validacion |
| Unstructured mode | NLP layer (014) + preprocessor | Procesamiento libre |
| Single-source publishing | Templates + IR + conditional filters | Un fuente → multiples outputs |
| Element | ASTNode | Unidad semantica del arbol |
| Attribute | Propiedad del nodo | Metadato asociado |
| Conditional text | Tags + filtros | Texto condicional |
| Cross-reference | Dependencias entre modulos (012) | Referencia a otro elemento |
| WYSIWYG | UI web (011, futuro) | Vista en tiempo real |
| Crash recovery | state_manager.sh (018) | Persistencia antes de cambios |

---

## 9. Referencias

- `misc/FrameMaker.md` — Documento fuente
- `003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md` — Procesador de documentos
- `004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md` — Especificacion del procesador
- `014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md` — Capa NLP
- `018_PROP_DEV_COMPILER_BOT_TUTORIAL_EXEC_1_0_DRAFT.md` — Ejecutor de tutoriales
- `013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` — Nucleo C nativo
- `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` — Multi-tech-stack
- Aho, Sethi, Ullman — "Compilers: Principles, Techniques, and Tools" (Dragon Book)
