---
id: 066
area: dev
type: prop
module: compiler_bot
version: 1.0.0
status: IMPLEMENTED
tags:
  - proposal
  - scaling
  - architecture
  - design-patterns
  - agent-framework
  - pipeline
summary: Propuesta de escalamiento del pipeline RECPL para soportar dominios complejos (SaaS web completo)
keywords: [pipeline, lexer, parser, IR, planner, synthesis, scaffold, langchain, langgraph, crew-ai, google-adk]
changelog:
  - 2026-06-13: Documento creado
---

# Propuesta de Escalamiento — RECPL Compiler Bot v2.0

## Resumen Ejecutivo

El pipeline RECPL actual resuelve un dominio mínimo: generar scaffolding
NestJS/Prisma desde instrucciones estructuradas (~6 verbos, ~3
sustantivos). Para escalar a dominios complejos como la generación de un
SaaS completo (acortador de enlaces con auth, analytics, QR, panel de
control), se requiere una rearquitectura profunda del pipeline.

Esta propuesta describe:
- La evolución de cada etapa del pipeline
- Patrones de diseño aplicables (Alexander Shvets)
- Un loop de 5 pasos para cada etapa
- La evaluación de frameworks multi-agente (LangChain, LangGraph, Crew
  AI, Google ADK)
- Una hoja de ruta de 6-12 meses

---

## 1. El Nuevo Dominio Mínimo Viable

El siguiente prompt define el nuevo dominio objetivo:

> "Diseña una página web moderna, profesional y totalmente responsive
> para un servicio de acortamiento de enlaces. La página debe tener una
> interfaz limpia con un formulario principal donde el usuario pueda
> introducir una URL larga y obtener un enlace corto. Incluye una
> sección de estadísticas que muestre clics, fecha de creación, país y
> dispositivo de acceso. Agrega autenticación de usuarios, panel de
> control, historial de enlaces, códigos QR para cada enlace y opciones
> de enlaces personalizados. Utiliza una paleta de colores moderna,
> tipografía clara y animaciones sutiles. Prioriza velocidad,
> accesibilidad, experiencia de usuario y diseño SaaS profesional."

**Complejidad estimada:**
| Dimensión | Actual | Objetivo |
|-----------|--------|----------|
| Tokens en lexer | ~10 | ~120 |
| Tipos de nodos AST | ~5 | ~40 |
| Targets de generación | 2 (NestJS, Prisma) | 6 (React, Next.js, Tailwind, Prisma, Docker, API) |
| Pasos de planificación | 1-3 | 30-50 |
| Archivos generados | 3-5 | 40-80 |
| Dependencias entre módulos | Lineales | Grafo acíclico |

---

## 2. Principios Arquitectónicos Generales

### 2.1 Loop de 5 Pasos (Todas las Etapas)

Cada etapa del pipeline implementa el mismo ciclo reflexivo, inspirado
en el patrón **Chain of Responsibility** combinado con **State**:

```
  ┌─────────────────────────────────────────────────┐
  │  1. Recibir la misión                           │
  │     (input del stage anterior o del usuario)    │
  └──────────────────┬──────────────────────────────┘
                     ↓
  ┌──────────────────▼──────────────────────────────┐
  │  2. Analizar la situación                       │
  │     (evaluar input, contexto, restricciones)    │
  └──────────────────┬──────────────────────────────┘
                     ↓
  ┌──────────────────▼──────────────────────────────┐
  │  3. Reflexionar y planificar                    │
  │     (seleccionar estrategia, patrones, tools)    │
  └──────────────────┬──────────────────────────────┘
                     ↓
  ┌──────────────────▼──────────────────────────────┐
  │  4. Actuar                                      │
  │     (ejecutar transformación, generar output)   │
  └──────────────────┬──────────────────────────────┘
                     ↓
  ┌──────────────────▼──────────────────────────────┐
  │  5. Aprender y mejorar                          │
  │     (feedback, ajuste de pesos, log)            │
  └─────────────────────────────────────────────────┘
```

Cada stage recibe un "contexto de misión" (JSON con objetivo,
restricciones, estado actual) y produce un output estructurado que
alimenta al siguiente. El paso 5 retroalimenta al paso 1 de la
siguiente iteración, permitiendo ciclos de refinamiento.

### 2.2 Patrón Mediator entre Etapas

El pipeline completo usa **Mediator** (un orquestador central) en lugar
de acoplar las etapas directamente. Cada etapa se registra en el
mediator y recibe/enruta mensajes tipados. Esto permite:
- Añadir/remover etapas sin cambiar el resto
- Logging y trazabilidad centralizada
- Reintentos y fallback entre etapas

### 2.3 Patrón Composite para IR/AST

El IR actual es un JSON plano. El nuevo IR usa **Composite**: cada nodo
puede ser atómico (token, declaración) o compuesto (módulo, página,
componente), compartiendo una interfaz común `IRNode` con métodos
`toCode()`, `validate()`, `dependencies()`.

---

## 3. Etapa 1: Preprocessor

### Estado Actual

- Normalización mínima: trim, lowercase, colapso de puntuación
- Sin análisis de dominio ni contexto

### Target

- Detección automática del dominio del prompt (web, API, CLI, DB)
- Extracción de requerimientos implícitos (auth → necesita User model,
  JWT, session)
- Segmentación del prompt en intenciones múltiples
- Enriquecimiento semántico vía embeddings

### Patrones de Diseño

| Patrón | Uso |
|--------|-----|
| **Chain of Responsibility** | Múltiples filtros en cadena: normalización → detección de dominio → extracción de requerimientos → enriquecimiento |
| **Strategy** | Diferentes estrategias de preprocesamiento según el dominio detectado (web vs CLI vs mobile) |

### Loop de 5 Pasos

1. **Recibir la misión**: Texto crudo del usuario + contexto de sesión
2. **Analizar la situación**: Detectar dominio, idioma, intención
   principal, nivel de detalle
3. **Reflexionar y planificar**: Seleccionar estrategia de
   normalización y enriquecimiento según dominio
4. **Actuar**: Normalizar, extraer entidades, clasificar, generar
   estructura inicial de tareas
5. **Aprender y mejorar**: Registrar frecuencia de términos,
   correcciones de clasificación errónea, feedback del usuario

---

## 4. Etapa 2: Lexer

### Estado Actual

- DFA con maximal munch
- ~10 tokens fijos: ACTION_CREATE, DELETE, UPDATE, READ, MODULE,
  ENTITY, TECH_NESTJS, TECH_PRISMA, PREP_IN, SEPARATOR
- Case-sensitive, espera input en minúsculas

### Target

- Léxico expandido a ~120+ tokens organizados por categorías:
  - **Domain tokens**: WEB_APP, SAAS, API, DATABASE, FRONTEND, AUTH,
    ANALYTICS, QR, LINK, SHORTENER, USER, CLICK, STATS
  - **Action tokens**: CREATE, DELETE, UPDATE, READ, DESIGN,
    CONFIGURE, DEPLOY, INTEGRATE, OPTIMIZE
  - **Tech tokens**: REACT, NEXT_JS, TAILWIND, PRISMA, DOCKER,
    POSTGRES, REDIS, JWT, OAUTH
  - **UI tokens**: LANDING_PAGE, FORM, TABLE, CHART, MODAL,
    NAVBAR, FOOTER, SIDEBAR, DASHBOARD
  - **Quality tokens**: RESPONSIVE, ACCESSIBLE, FAST, SECURE,
    MODERN, PROFESSIONAL, ANIMATED
- Soporte para tokenización de frases multi-palabra ("panel de
  control" → DASHBOARD)
- Salida con metadata: posición, confianza, contexto

### Patrones de Diseño

| Patrón | Uso |
|--------|-----|
| **State** | La DFA se vuelve dinámica: cada estado conoce qué tokens pueden seguir, permitiendo sub-máquinas por categoría |
| **Flyweight** | Los tokens se comparten entre instancias del lexer para ahorrar memoria |

### Loop de 5 Pasos

1. **Recibir la misión**: Texto preprocesado + mapa de dominio
2. **Analizar la situación**: Identificar qué categorías de tokens son
   relevantes según el dominio detectado
3. **Reflexionar y planificar**: Seleccionar sub-DFA(s) a activar;
   definir umbral de confianza para maximal munch
4. **Actuar**: Tokenizar, asignar metadata, resolver ambigüedades
5. **Aprender y mejorar**: Registrar nuevas palabras como candidatos
   para expansión del léxico; ajustar pesos de desambiguación

---

## 5. Etapa 3: Parser

### Estado Actual

- LL(1) recursive descent
- Gramática minimalista: `comando → accion modulo_espec opcional_tech`
- Sin manejo de ambigüedad ni recuperación de errores

### Target

- Parser **GLR** (Generalized LR) o **PEG** (Parsing Expression
  Grammar) para manejar gramáticas ambiguas del lenguaje natural
- Gramática multi-dominio con reglas para:
  - **Estructura de proyecto**: `proyecto → (pagina | modulo | API | DB)+`
  - **Componentes UI**: `pagina → seccion+` donde `seccion → formulario | tabla | grafico | navbar`
  - **Relaciones**: `entidad → atributo+ (relacion entidad)*`
  - **Calidad**: `restriccion → RESPONSIVE | ACCESIBLE | RAPIDO`
- AST tipado con nodos genéricos y nodos específicos de dominio
- Recuperación de errores con "panic mode" + reparación guiada por LLM

### Patrones de Diseño

| Patrón | Uso |
|--------|-----|
| **Interpreter** | Cada nodo del AST sabe interpretarse a sí mismo, permitiendo walking semántico sin switch statements |
| **Visitor** | Separar la lógica de recorrido del AST de las operaciones (type-checking, generación de código, validación) |
| **Composite** | AST como árbol de nodos donde cada nodo implementa `evaluate()`, `validate()`, `toIR()` |

### Loop de 5 Pasos

1. **Recibir la misión**: Secuencia de tokens + reglas gramaticales
   activas
2. **Analizar la situación**: Identificar secciones del prompt,
   detectar patrones gramaticales conocidos
3. **Reflexionar y planificar**: Seleccionar estrategia de parsing
   (determinista vs LLM-assisted); decidir manejo de ambigüedades
4. **Actuar**: Construir AST con nodos tipados; registrar errores y
   warning
5. **Aprender y mejorar**: Registrar patrones gramaticales nuevos;
   refinar reglas de producción basado en errores frecuentes

---

## 6. Etapa 4: Semantic Analyzer

### Estado Actual

- Symbol table en disco (archivos JSON)
- Type checking mínimo: verifica que el módulo existe
- Persistencia via `RECPL_STATE_DIR`

### Target

- **Symbol table en memoria con persistencia opcional** — Usar patrón
  **Memento** para snapshots del estado semántico
- **Type system multi-dominio**:
  - Tipos de UI: `Component`, `Page`, `Layout`, `Widget`
  - Tipos de datos: `Entity`, `Attribute`, `Relation`, `Constraint`
  - Tipos de infra: `Service`, `Middleware`, `Route`, `Migration`
- **Type checking**:
  - Verificar que las relaciones entre entidades sean válidas
  - Verificar que los componentes UI tengan los props requeridos
  - Verificar consistencia entre frontend y backend (API routes vs
    components)
- **Scope analysis**: Cada módulo/página tiene su propio scope con
  herencia del scope global del proyecto

### Patrones de Diseño

| Patrón | Uso |
|--------|-----|
| **Visitor** | Recorrer el AST aplicando reglas de tipo según el tipo de nodo |
| **Memento** | Snapshots del estado semántico para rollback y experimentación |
| **Prototype** | Clonar contextos semánticos para análisis paralelos de ramas |

### Loop de 5 Pasos

1. **Recibir la misión**: AST del parser + tabla de símbolos actual
2. **Analizar la situación**: Identificar tipos de nodos, detectar
   dependencias circulares, evaluar cobertura semántica
3. **Reflexionar y planificar**: Seleccionar reglas de validación a
   aplicar; decidir orden de resolución de tipos
4. **Actuar**: Resolver tipos, validar restricciones, construir grafo
   de dependencias semánticas
5. **Aprender y mejorar**: Registrar errores semánticos frecuentes;
   ajustar reglas de inferencia de tipos

---

## 7. Etapa 5: IR (Intermediate Representation)

### Estado Actual

- JSON plano con accion, modulo, tecnologia
- Mapeo directo a templates

### Target

- **IR basado en Composite** con tres capas:

```
IRProject
 ├── IRConfig (framework, DB, deploy, testing)
 ├── IRDomainModel (entidades, relaciones, value objects)
 │    ├── IREntity (User, Link, Click)
 │    │    └── IRAttribute (id, url, clicks, createdAt)
 │    └── IRLlation (User 1→N Link, Link 1→N Click)
 ├── IRUIModel (páginas, componentes, layout)
 │    ├── IRPage (Landing, Dashboard, Login)
 │    │    └── IRComponent (Form, Table, Chart, QRCode)
 │    └── IRRoute (path, method, component, guard)
 ├── IRAPIModel (endpoints, middleware, auth)
 │    ├── IREndpoint (POST /links, GET /stats)
 │    └── IRMiddleware (auth, rate-limit, caching)
 └── IRInfraModel (Docker, CI/CD, env vars)
      ├── IRDockerService (web, db, redis)
      └── IRPipelineStep (build, test, deploy)
```

- **Grafo de dependencias**: Cada nodo IR tiene un método
  `dependencies() → IRNode[]` que permite al planificador ordenar la
  generación
- **Formato canónico**: JSON schema versionado con validación JSON
  Schema

### Patrones de Diseño

| Patrón | Uso |
|--------|-----|
| **Composite** | IR como árbol homogéneo de nodos con operaciones polimórficas |
| **Builder** | Construcción step-by-step del IR con validación intermedia |
| **Bridge** | Separar la abstracción del IR de su representación (JSON, YAML, Graphviz) |

### Loop de 5 Pasos

1. **Recibir la misión**: AST validado semánticamente + tabla de
   símbolos
2. **Analizar la situación**: Evaluar complejidad del grafo, detectar
   componentes compartidos, identificar patrones reutilizables
3. **Reflexionar y planificar**: Decidir estructura del IR (cuántas
   capas, qué nodos), planificar resolución de dependencias
4. **Actuar**: Construir el grafo IR, validar consistencia, serializar
5. **Aprender y mejorar**: Registrar patrones de IR frecuentes para
   acelerar futuras construcciones

---

## 8. Etapa 6: Planner

### Estado Actual

- ~20 líneas de heurística shell
- Detecta "crea X y Y" → multi_create
- Sin validación de plan ni rollback

### Target

- **Planner híbrido**: Heurística para casos simples + LLM para
  planificación compleja
- **Grafo de tareas** con dependencias, estimaciones y estados:
  ```
  Tarea: "Generar modelo User"
    Dependencias: []
    Estado: pending
    Generador: prisma_generator
    Output: prisma/schema.prisma

  Tarea: "Generar API auth"
    Dependencias: ["Generar modelo User"]
    Estado: blocked
    Generador: nestjs_generator
    Output: src/auth/

  Tarea: "Generar Login page"
    Dependencias: ["Generar API auth"]
    Estado: blocked
    Generador: react_generator
    Output: pages/login.tsx
  ```
- **Plan executor**: Ejecuta tareas en orden topológico, con reintentos
  y rollback parcial
- **Validation gate**: Cada tarea ejecutada se valida antes de marcar
  como completa

### Patrones de Diseño

| Patrón | Uso |
|--------|-----|
| **Command** | Cada tarea del plan es un Command ejecutable con undo() |
| **Template Method** | Esqueleto de ejecución de plan con hooks para validación, logging, rollback |
| **Observer** | Notificar cambios de estado del plan a otros componentes (UI, logs) |

### Loop de 5 Pasos

1. **Recibir la misión**: IR completo + restricciones del usuario
2. **Analizar la situación**: Descomponer el IR en tareas atómicas;
   calcular dependencias entre tareas
3. **Reflexionar y planificar**: Ordenar tareas topológicamente;
   estimar esfuerzo; identificar riesgos (dependencias circulares,
   componentes faltantes)
4. **Actuar**: Ejecutar plan (delegar cada tarea al synthesis
   correspondiente); monitorear progreso; manejar fallos
5. **Aprender y mejorar**: Registrar desviaciones entre estimación y
   realidad; refinar heurísticas de descomposición

---

## 9. Etapa 7: Synthesis (Generación Multi-Target)

### Estado Actual

- Synthesis.sh genera un JSON de respuesta simple
- Scaffold.sh copia templates y reemplaza `__NAME__`

### Target

- **Generadores especializados** registrados en un **Factory**:
  - `ReactGenerator` → components, hooks, pages, styles
  - `NextJSGenerator` → pages router, API routes, middleware
  - `TailwindGenerator` → config, theme, utilities
  - `PrismaGenerator` → schema, migrations, seeds
  - `DockerGenerator` → Dockerfile, docker-compose, .dockerignore
  - `APIGenerator` → NestJS controllers, services, guards, DTOs
- **AST-based code generation**: En lugar de templates de texto, cada
  generador construye un AST del lenguaje target y lo serializa
- **Cross-target consistency**: Un cambio en una entidad del IR se
  refleja en Prisma schema, API endpoints, y frontend forms
- **Code formatting automático**: Prettier/eslint post-processing

### Patrones de Diseño

| Patrón | Uso |
|--------|-----|
| **Factory Method** | Cada generador se crea según el target (React, Prisma, Docker) |
| **Visitor** | Recorrer el IR y generar código visitando cada nodo |
| **Abstract Factory** | Familias de generadores relacionados (frontend: React+Tailwind; backend: NestJS+Prisma) |
| **Decorator** | Añadir behavior transversal a los generadores (logging, validación, cache) |

### Loop de 5 Pasos

1. **Recibir la misión**: Sub-grafo del IR (una tarea del plan) +
   target de generación
2. **Analizar la situación**: Evaluar qué generador(es) aplicar; 
   detectar dependencias con otros targets
3. **Reflexionar y planificar**: Seleccionar estrategia de generación
   (template vs AST); planificar integración con otros targets
4. **Actuar**: Construir AST del target, serializar a código, formatear
5. **Aprender y mejorar**: Registrar patrones de generación exitosos;
   cachear ASTs reutilizables

---

## 10. Etapa 8: Scaffold (¿Eliminar o Evolucionar?)

### Diagnóstico

El scaffold actual copia archivos de `templates/` y reemplaza
placeholders. Este modelo es:
- **Rígido**: cada nuevo template requiere crear archivos a mano
- **No composable**: no puedes combinar fragmentos de templates
- **Sin contexto**: el template no sabe qué otros módulos existen

### Opción A: Eliminar (Recomendada para v2.0)

Reemplazar scaffold por los generadores AST-based de Synthesis. Cada
generador Produce archivos directamente sin pasar por templates. El
directorio `templates/` se depreca.

**Ventajas:**
- Cero mantenimiento de templates
- Los generadores son testeables unitariamente
- Composición natural de fragmentos de código
- Tipado fuerte (el AST garantiza código sintácticamente válido)

**Desventajas:**
- Mayor esfuerzo inicial de implementación
- Pérdida de la flexibilidad "edita el template y ya"

### Opción B: Evolucionar

Si se mantiene scaffold, evolucionarlo con:
- **Template Engine** (Jinja2-like con herencia, bloques, macros)
- **Template Registry** con detección automática de templates según
  dominio
- **Template Composer** que combina múltiples templates en un archivo

### Patrones de Diseño para Scaffold (si se mantiene)

| Patrón | Uso |
|--------|-----|
| **Template Method** | Esqueleto de scaffold con hooks para pre/post procesamiento |
| **Strategy** | Diferentes motores de template (shell sed, Jinja2, AST) |
| **Decorator** | Añadir validación, logging, backup al scaffold |

### Veredicto

Se recomienda **eliminar scaffold** en v2.0 y delegar toda la
generación a synthesis con generadores AST-based. El patrón **Abstract
Factory** en synthesis permite añadir nuevos targets sin cambiar la
infraestructura existente.

---

## 11. Nuevo Componente: Descomponedor de Requerimientos

### Propósito

Traduce un prompt de alto nivel ("Diseña una página web...") en una
estructura de requerimientos formal que alimenta al pipeline.

### Funcionamiento

1. **Clasificación de dominio** (web, mobile, CLI, API)
2. **Extracción de entidades** (User, Link, Click, Stats)
3. **Identificación de features** (auth, QR, analytics, dashboard)
4. **Detección de constraints** (responsive, accessible, fast)
5. **Generación de user stories** en formato estructurado
6. **Priorización** (MVP vs nice-to-have)

### Patrón: **Facade**

El descomponedor actúa como Facade sobre el LLM, ocultando la
complejidad de prompts, temperature, y parsing de respuestas.

---

## 12. Nuevo Componente: Generador de UI

### Propósito

Traduce especificaciones de UI del IR (páginas, componentes, layout) en
código frontend real.

### Funcionamiento

1. Recibe `IRPage` o `IRComponent` del IR
2. Aplica reglas de diseño responsive (CSS Grid, Flexbox, media
   queries)
3. Genera componentes con Tailwind CSS utility classes
4. Aplica principios de accesibilidad (ARIA labels, roles, focus
   management)
5. Agrega animaciones sutiles (CSS transitions, Framer Motion)

### Patrón: **Builder**

El UI Generator construye componentes paso a paso: estructura →
estilos → comportamiento → accesibilidad → animaciones.

---

## 13. Nuevo Componente: Validador de Output

### Propósito

Verificar que el código generado es correcto y consistente antes de
entregarlo al usuario.

### Funcionamiento

1. **Syntax validation**: linter específico del lenguaje
2. **Type checking**: TypeScript strict mode
3. **Integration test**: verificar que componentes importan
   correctamente
4. **Visual diff**: comparar con screenshots de referencia (opcional)
5. **Security scan**: detectar secretos hardcodeados, SQL injection, XSS

### Patrón: **Chain of Responsibility**

Múltiples validadores en cadena, cada uno puede detener la entrega si
encuentra un error crítico.

---

## 14. Selección de Framework Multi-Agente

### Candidatos

| Framework | Tipo | Fortaleza | Debilidad |
|-----------|------|-----------|-----------|
| **LangChain** + **LangGraph** | Orquestación de LLM + grafos de estado | Ecosistema maduro, herramientas integradas, streaming | Curva de aprendizaje, dependencia pesada |
| **Crew AI** | Multi-agente colaborativo | Roles definidos, delegación automática, fácil de empezar | Menos control sobre el grafo de ejecución |
| **Google ADK** | Agent Developer Kit | Integración nativa con Gemini, tool use robusto | Muy nuevo, ecosistema pequeño |

### Recomendación: LangChain + LangGraph

**Razones:**

1. **Graph-based state machine**: LangGraph modela naturalmente el
   pipeline como un grafo de estados donde cada etapa es un nodo. El
   loop de 5 pasos se traduce directamente a nodos LangGraph con
   `StateGraph`.

2. **Tool integration**: Cada generador (React, Prisma, Docker) se
   registra como una tool que el agente orquestador puede invocar.

3. **Persistence**: LangGraph soporta persistencia de estado entre
   ejecuciones, ideal para el ciclo "aprender y mejorar".

4. **Streaming**: Soporte nativo para streaming de tokens, útil para
   feedback en tiempo real al usuario.

5. **Ecosistema**: LangChain tiene conectores para ~100+ modelos,
   vectordbs, y herramientas.

### Arquitectura Propuesta con LangGraph

```
                          ┌──────────────┐
                          │  User Input  │
                          └──────┬───────┘
                                 ↓
                    ┌────────────────────────┐
                    │   RequerimentDecomposer │  (LLM node)
                    └──────────┬─────────────┘
                               ↓
           ┌───────────────────────────────────┐
           │         Pipeline Orquestator       │  (StateGraph)
           │  ┌─────┐  ┌─────┐  ┌─────┐  ┌───┐│
           │  │Pre  │→│Lexer│→│Parser│→│Sem ││
           │  └─────┘  └─────┘  └─────┘  └───┘│
           │  ┌─────┐  ┌─────┐  ┌─────┐  ┌───┐│
           │  │IR   │→│Plan │→│Synth│→│Val ││
           │  └─────┘  └─────┘  └─────┘  └───┘│
           └───────────────────────────────────┘
                               ↓
                    ┌────────────────────────┐
                    │      Output Formatter   │
                    └────────────────────────┘
```

Cada nodo del grafo implementa el loop de 5 pasos como sub-grafo
interno, permitiendo refinamiento iterativo dentro de cada etapa.

---

## 15. Design Patterns — Mapa Completo

| Patrón | Etapa | Propósito |
|--------|-------|-----------|
| **Chain of Responsibility** | Preprocessor, Validador | Múltiples filtros/validadores en cadena |
| **State** | Lexer | DFA dinámico por categorías |
| **Flyweight** | Lexer | Compartir tokens entre instancias |
| **Interpreter** | Parser | AST con nodos auto-evaluables |
| **Composite** | Parser, IR | Árbol homogéneo de nodos |
| **Visitor** | Parser, Semantic, Synthesis | Separar walking de operaciones |
| **Memento** | Semantic | Snapshots de estado semántico |
| **Prototype** | Semantic | Clonar contextos para análisis paralelo |
| **Builder** | IR, UI Generator | Construcción step-by-step |
| **Bridge** | IR | Separar abstracción de representación |
| **Command** | Planner | Tareas ejecutables con undo |
| **Template Method** | Planner, Synthesis | Esqueleto con hooks |
| **Observer** | Planner | Notificar cambios de estado |
| **Factory Method** | Synthesis | Crear generadores por target |
| **Abstract Factory** | Synthesis | Familias de generadores |
| **Decorator** | Synthesis | Añadir behavior transversal |
| **Mediator** | Pipeline completo | Coordinación entre etapas |
| **Facade** | RequirementDecomposer | Simplificar interfaz del LLM |

---

## 16. Hoja de Ruta

### Fase 1 (Meses 1-3): Fundación

1. Configurar proyecto LangChain + LangGraph
2. Implementar RequirementDecomposer (Facade sobre LLM)
3. Expandir lexer a ~50 tokens (dominio web)
4. Rediseñar IR con patrón Composite
5. Implementar loop de 5 pasos en preprocessor y lexer
6. Tests: 20 nuevos tests de integración

### Fase 2 (Meses 4-6): Pipeline Central

1. Migrar parser a GLR con gramática web
2. Implementar semantic analyzer con type-checking multi-dominio
3. Rediseñar planner con Command pattern y grafo de tareas
4. Implementar plan executor con validación
5. Implementar loop de 5 pasos en parser, semantic, IR
6. Tests: 40 nuevos tests

### Fase 3 (Meses 7-9): Generación Multi-Target

1. Implementar Abstract Factory de generadores
2. Crear ReactGenerator (AST-based)
3. Crear NextJSGenerator
4. Crear TailwindGenerator
5. Crear PrismaGenerator
6. Crear DockerGenerator
7. Implementar validador de output (Chain of Responsibility)
8. Implementar loop de 5 pasos en planner, synthesis, scaffold
9. Tests: 60 nuevos tests

### Fase 4 (Meses 10-12): UI y Refinamiento

1. Implementar UI Generator con Builder pattern
2. Sistema de feedback y aprendizaje (loop 5→1 entre sesiones)
3. Optimización de velocidad (caching de ASTs, parallel generation)
4. Documentación y ejemplos
5. Beta testing con el prompt del acortador de enlaces
6. Tests: 100+ tests total

---

## 17. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Dependencia excesiva del LLM para pasos deterministas | Alta | Medio | Mantener rama determinista como fallback; umbrales de confianza |
| Costo de API LLM en planificación compleja | Media | Alto | Cachear planes; usar modelos pequeños para tareas simples |
| Complejidad del grafo LangGraph difícil de debuggear | Media | Alto | Logging estructurado; visualización del grafo; tests por nodo |
| Generación de código con errores sintácticos | Alta | Medio | Validador de output obligatorio; formateo automático |
| Scope creep (querer abarcar demasiados dominios) | Alta | Alto | Mantener el foco en dominio web SaaS los primeros 12 meses |

---

## 18. Conclusión

El pipeline actual de Proyecto0 es sólido en concepto pero limitado en
alcance. Esta propuesta describe una evolución que:

1. **Preserva la arquitectura de pipeline compilador** (preprocess →
   lexer → parser → semantic → IR → synthesis), que es correcta y
   escalable.

2. **Agrega profundidad a cada etapa** mediante patrones de diseño,
   loops reflexivos de 5 pasos, y un sistema de tipos multi-dominio.

3. **Introduce LangGraph como orquestador** para manejar la
   complejidad del grafo de ejecución y el estado entre etapas.

4. **Reemplaza templates por generadores AST-based**, eliminando la
   rigidez del scaffold actual.

5. **Agrega tres componentes nuevos** (descomponedor de
   requerimientos, generador de UI, validador de output) que cierran
   el ciclo de generación autónoma.

El resultado es un sistema capaz de tomar un prompt como "Diseña una
página web moderna para acortar enlaces..." y producir código
funcional, testeable y desplegable en múltiples tecnologías, con un
nivel de calidad SaaS profesional.

**Estimación: 6-12 meses de desarrollo enfocado con un equipo de 1-2
personas.**
