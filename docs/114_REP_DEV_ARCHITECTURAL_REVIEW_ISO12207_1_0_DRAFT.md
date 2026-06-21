---
id: "114"
area: dev
type: rep
module: architectural_review_iso12207
version: "1.0"
status: IMPLEMENTED
tags:
  - "architectural-review"
  - "iso-12207"
  - "sdlc"
  - "multi-agent"
  - "chain-of-responsibility"
summary: "Revision arquitectonica de Proyecto0 como orquestador SDLC basado en ISO 12207 + agentes especializados + Chain of Responsibility"
keywords:
  - "architectural review"
  - "ISO 12207"
  - "SDLC orchestrator"
  - "chain of responsibility"
  - "RECPL"
  - "agent contracts"
changelog:
  - "2026-06-17: Revision arquitectonica inicial"
---

# 114-REP-DEV-ARCHITECTURAL-REVIEW-ISO12207-1-0-DRAFT

## Resumen

**Proyecto0** se redefine de "compilador de lenguaje natural a codigo NestJS/Prisma" a "compilador de lenguaje natural a codigo IR"
a **orquestador SDLC completo basado en ISO/IEC/IEEE 12207**. El sistema recibe
una idea de producto SaaS en lenguaje natural y la transforma en codigo
funcional mediante una cadena de agentes especializados, cada uno con
contratos de interfaz formales, un schema JSON de tareas versionado, y
workspaces aislados por tarea.

La arquitectura se compone de 3 capas:

1. **RECPL Runtime** — orquestador de ciclo de vida que maneja issues,
   workspaces, handoffs y estado del sistema
2. **Agentes especializados** — CEO, CTO, Coder, QA, SecurityEngineer,
   UXDesigner — cada uno con bounded context y contratos formales
3. **Chain of Responsibility** — patron de diseño que encadena los agentes
   como microprocesos, donde cada solicitud atraviesa la cadena hasta que
   un handler la procesa

El pipeline RECPL actual (preprocess → lexer → parser → semantic → IR →
synthesis) se transforma en microprocesos bajo el patrón Chain of
Responsibility, donde cada etapa es un handler que decide si procesa o
delega al siguiente.

---

## Fortalezas

### 1. Alineación con estandar ISO 12207

La decision de alinear el sistema con ISO/IEC/IEEE 12207 es tecnicamente
solida. Este estandar cubre el ciclo de vida completo del software
(adquisicion, suministro, desarrollo, operacion, mantenimiento). Proporciona:

- **Vocabulario comun** entre stakeholders tecnicos y de negocio
- **Procesos definidos** que mapean directamente a agentes (Requirements
  Engineering → CTO/RequirementEngineer, Development → Coder, Testing → QA)
- **Auditabilidad** por diseno, no por accidente

### 2. Bounded contexts por agente

La separacion en 6 tipos de agente con capability boundaries estrictos
es una decision de arquitectura correcta. Cada agente:

- Es dueno de una capacidad de negocio completa (no una capa tecnica)
- Tiene input/output contracts formales
- No puede cruzar boundaries de seguridad (Coder no aprueba security)

Esto sigue el principio de **segregacion de responsabilidades** (SoC) y
limita el blast radius ante fallos.

### 3. Task JSON Schema versionado

El schema de tareas en `TJS.md` con `"additionalProperties": true` y
version semantica es pragmatico. Permite:

- Validacion programatica en cada handoff
- Evolucion controlada del schema
- Extension por agente sin romper contratos existentes

### 4. Workspace-per-task aislado

La decision de workspaces efimeros por tarea (ephemeral) con artefactos
durables en issue documents es correcta para un sistema multi-agente:

- Elimina contaminacion de estado entre tareas
- Hace cada tarea reproducible desde cero
- Simplifica el modelo de concurrencia

### 5. Chain of Responsibility como patron de orquestacion

El uso de Chain of Responsibility para los microprocesos del pipeline
es acertado porque:

- Desacopla emisor de receptor — cada etapa solo conoce a su sucesor
- Permite configuracion dinamica de la cadena (handlers se agregan/remueven
  sin cambiar clientes)
- Composición recursiva permite profundidad ilimitada
- "Red de seguridad" (ultimo eslabon que no delega en nulo) cubre el
  caso de solicitudes no manejadas
- Se alinea con el pipeline RECPL actual (cada etapa del pipeline clasico
  puede convertirse en un handler de la cadena)

---

## Riesgos y Debilidades

### 🔴 Riesgo 1: La latencia de RECPL como bus de orquestacion

**Problema:** ADR-001 Decision 1 establece que NO hay RPC entre agentes.
Todo handoff va por RECPL issues (checkout → work → update → comment →
done). Esto introduce latencia O(minutos) por handoff.

En un pipeline tipico (Idea → CTO → SystemDesign → RequirementEng →
TaskBreakdown → Coder → QA → Delivery), hay **7 handoffs secuenciales**.
Cada uno requiere que RECPL "despierte" al agente, este lea el issue,
procese, comente, y marque done. Con latencia de ~30s-2min por handoff,
el tiempo total de ciclo minimo es ~3.5-14 minutos para tareas triviales.

**Impacto:** Para tareas simples ("agregar endpoint GET /health"), el
overhead de orquestacion puede superar el tiempo de ejecucion real.

**Mitigacion propuesta:** Introducir un modo "fast-track" para tareas
de bajo riesgo donde el CTO Agent pueda delegar directamente al Coder
sin pasar por SystemDesign + RequirementEngineer + TaskBreakdown.

### 🔴 Riesgo 2: Chain of Responsibility + RECPL = conflicto de granularidad

**Problema:** El patron Chain of Responsibility tipicamente opera
**in-process** (misma memoria, mismo proceso). Cada handler recibe la
solicitud, decide si procesa, y opcionalmente pasa al siguiente. Esto es
de grano fino y baja latencia.

Pero RECPL opera **cross-process** (issues, workspaces, wake/sleep). Cada
handoff implica serializacion/deserializacion del estado, E/S de disco, y
latencia de red. La sobrecarga de RECPL por "eslabon" de la cadena puede
hacer que el patron pierda su principal ventaja: la eficiencia del
encadenamiento recursivo.

**Impacto:** 7 eslabones de CoR × overhead RECPL por eslabon = latencia
acumulativa que puede hacer el sistema impractico para desarrollo iterativo
rapido.

**Mitigacion propuesta:** Considerar una jerarquia de 2 niveles:
- **CoR in-process** para microprocesos del pipeline (preprocess→lexer→parser
  →semantic→IR→synthesis) — baja latencia, mismo proceso
- **RECPL out-of-process** para handoffs entre agentes (CTO→Coder,
  Coder→QA) — alta latencia, pero necesaria para aislamiento

### 🟡 Riesgo 3: Sin modelo de concurrencia definido

**Problema:** El ADR menciona "usar child issues para trabajo paralelo"
pero no define:
- Que pasa cuando 2 agentes escriben al mismo workspace simultaneamente
- Como se resuelven conflictos de merge en el codigo
- Si hay un mecanismo de lock por tarea/recurso
- Que pasa si un agente se cuelga (heartbeat timeout, crash)

**Impacto:** Condiciones de carrera (race conditions) en generacion de
codigo, conflictos de merge irresolubles, tareas huerfanas.

**Mitigacion propuesta:** Definir un modelo de concurrencia explicito:
- Workspace lock por tarea (exclusivo)
- Heartbeat obligatorio cada N segundos con timeout + escalation
- Git como unica fuente de verdad para resolucion de conflictos

### 🟡 Riesgo 4: ISO 12207 no cubre agentes de IA

**Problema:** ISO/IEC/IEEE 12207 asume que los procesos son ejecutados por
humanos. No define:
- Criterios de calidad para output de un LLM
- Limites de autonomia para sistemas generativos
- Protocolos de verificacion para codigo generado por IA
- Sesgo, alucinacion, o degradacion de modelo

**Impacto:** El estandar proporciona el "que" (procesos del ciclo de vida)
pero no el "como" (ejecucion por IA). El equipo termina implementando
ISO 12207 en la nomenclatura pero sin la disciplina de proceso que el
estandar exige.

**Mitigacion:** Complementar ISO 12207 con ISO/IEC 5338 (ciclo de vida
para sistemas de IA) y ISO/IEC 38507 (gobernanza de IA). No es opcional
si el sistema sera auditado.

### 🟡 Riesgo 5: Costo operativo de multi-modelo

**Problema:** La arquitectura asume que cada agente usa un modelo LLM
(DeepSeek V4 Flash Free + fallback GPT/Claude). Con 6+ agentes, cada
tarea puede consumir:

- CTO Agent: 1-3 llamadas (descomposicion, diseño)
- Coder Agent: 3-10+ llamadas (generacion, debug, tests)
- QA Agent: 2-5 llamadas (ejecucion, analisis)
- SecurityEngineer: 1-3 llamadas
- UXDesigner: 1-3 llamadas

**Total estimado: 8-24+ llamadas LLM por tarea.** En un SaaS con
100 tareas/dia, esto puede alcanzar 800-2400 llamadas/dia. Incluso con
DeepSeek V4 Flash Free (gratuito/barato), el fallback a GPT-4 o Claude
multiplica el costo por 10x-30x.

**Impacto:** El costo operativo por tarea puede superar el valor del
output generado para tareas simples.

**Mitigacion propuesta:** Cache de LLM (ya implementado como LLMCache en
F5), modelo routing inteligente (tareas simples → modelo barato, tareas
complejas → GPT/Claude), y presupuesto por tarea con corte automatico.

### 🟡 Riesgo 6: El pipeline actual (RECPL v2.0) no se integra naturalmente con la vision ISO 12207

**Problema:** El pipeline RECPL actual es un compilador de lenguaje natural a codigo IR
a scaffolding NestJS/Prisma (preprocess → lexer → parser → semantic → IR →
synthesis). La vision ISO 12207 es un orquestador SDLC completo con
agentes especializados. Son 2 cosas diferentes.

El pipeline actual produce codigo. El nuevo sistema produce decisiones,
arquitectura, tareas, y codigo. Son 2 niveles de abstraccion distintos.

**Impacto:** Riesgo de mezclar 2 arquitecturas incompatibles y terminar
con un sistema que no es ni buen compilador ni buen orquestador SDLC.

**Recomendacion:** Separar claramente:
- **RECPL Compiler** (el pipeline actual) → modulo de generacion de codigo
  dentro del Coder Agent
- **Code Serve Orchestrator** (la vision ISO 12207) → sistema de orquestacion
  que usa RECPL Compiler como uno de sus componentes

---

## Evaluacion Tecnica

### Mantenibilidad: ⚠️ Media

| Aspecto | Evaluacion |
|---------|-----------|
| **Modularidad** | ✅ Alta — bounded contexts por agente, contratos formales |
| **Acoplamiento** | ⚠️ Medio — RECPL como bus unico crea dependencia fuerte en su API |
| **Cohesion** | ✅ Alta — cada agente tiene una responsabilidad clara |
| **Deuda tecnica** | ⚠️ Media — schema v1.0.0 con `additionalProperties: true` es flexible pero permite incoherencias |
| **Testing** | ⚠️ Bajo — no se menciona estrategia de testing para agentes (LLM output no determinista) |
| **Documentacion** | ✅ Alta — ADR, AIC, TJS, WDS documentos completos y consistentes |

**Observacion:** La mantenibilidad a largo plazo dependera de la
estabilidad de la API de RECPL. Si RECPL cambia su modelo de issues,
workspaces, o handoffs, todos los agentes se ven afectados.

### Escalabilidad: ⚠️ Media

| Aspecto | Evaluacion |
|---------|-----------|
| **Horizontal** | ⚠️ Limitada — workspaces aislados permiten paralelismo, pero RECPL como cuello de botella central |
| **Vertical** | ✅ Alta — cada agente puede usar modelos mas grandes/potentes |
| **Concurrencia** | ⚠️ No definida — falta modelo de concurrencia explicito |
| **Carga** | ⚠️ No definida — sin benchmarks ni limites de throughput |

**Observacion:** El modelo workspace-per-task escala bien para decenas
de tareas concurrentes. Para cientos, RECPL necesitara particionamiento.

### Rendimiento: 🔴 Bajo

| Aspecto | Evaluacion |
|---------|-----------|
| **Latencia por tarea** | 🔴 Alta — 7 handoffs × overhead RECPL por handoff |
| **Throughput** | ⚠️ No definido — sin metricas objetivo |
| **Tiempo de respuesta** | 🔴 Alto — minutos por tarea, no segundos |
| **LLM latency** | 🔴 Alta — 8-24+ llamadas por tarea, cada una 1-10s |

**Observacion:** El rendimiento no es un problema si el caso de uso es
"deploy y revisa en una hora". Pero si se espera interaccion en tiempo
real (tipo Copilot), la latencia actual es inaceptable.

### Seguridad: 🟡 En definicion

| Aspecto | Evaluacion |
|---------|-----------|
| **Boundaries** | ✅ Bien definidos — agentes no cruzan capability boundaries |
| **Secretos** | ✅ RECPL injecta secretos via env, no en repo |
| **Auth** | ⚠️ No definido — como autentican agentes entre si y con RECPL? |
| **Audit trail** | ✅ Issues + comments + documents = trazabilidad completa |
| **Code supply chain** | ⚠️ No definido — como se verifica que el codigo generado no tiene vulnerabilidades? |

**Observacion:** El modelo de "defense in depth" mencionado en ADR-001
necesita detalle: que controles hay en cada boundary? Como se previene
que un Coder malicioso (o prompt injected) genere codigo peligroso?

### Complejidad: 🔴 Alta

| Aspecto | Evaluacion |
|---------|-----------|
| **Arquitectura** | 🔴 Alta — 6 agentes + RECPL + Chain of Responsibility + workspaces + schemas |
| **Configuracion** | ⚠️ Media — AGENTS.md por agente + por proyecto |
| **Debugging** | 🔴 Alto — output no determinista de LLMs, fallos dificiles de reproducir |
| **Operacion** | ⚠️ Media — RECPL maneja orquestacion, pero monitoreo de agentes es nuevo |

### Coste de implementacion: 🟡 Medio-Alto

| Componente | Coste estimado |
|------------|---------------|
| RECPL runtime | Existente (reutilizar) |
| Pipeline RECPL actual | Existente (adaptar a modulo de Coder Agent) |
| 6 agentes (prompts + contracts) | 2-4 semanas de ingenieria de prompts |
| Chain of Responsibility infra | 1-2 semanas de implementacion |
| Testing + hardening | 2-4 semanas |
| Infraestructura (Docker, CI/CD) | 1 semana |
| **Total estimado** | **6-11 semanas hombre** |

### Experiencia del desarrollador (DX): ⚠️ Media

| Aspecto | Evaluacion |
|---------|-----------|
| **Onboarding** | ⚠️ Medio — requiere entender RECPL, ISO 12207, CoR, y 6 contratos de agente |
| **Iteracion** | 🔴 Lenta — handoff RECPL por cada cambio, latencia de minutos |
| **Feedback** | ⚠️ Medio — output no deterministico, errores dificiles de clasificar |
| **Herramientas** | ⚠️ No definido — CLI? UI? Solo RECPL issues? |

---

## Supuestos implicitos

1. **RECPL escala verticalmente** — se asume que RECPL puede manejar
   N agentes concurrentes sin degradacion. No hay evidencia de esto.
2. **Los LLMs producen output consistente** — se asume que el mismo prompt
   produce resultados deterministicos. Los LLMs son probabilisticos por
   naturaleza.
3. **Los agentes no necesitan estado compartido** — workspace-per-task
   elimina estado entre tareas, pero el CTO necesita contexto historico
   para decisiones arquitectonicas.
4. **Chain of Responsibility es el patron correcto** — CoR asume que
   cada solicitud tiene UN handler que la procesa. Pero en un SDLC,
   MULTIPLES agentes pueden necesitar procesar la misma solicitud
   (Coder + SecurityEngineer + QA). CoR puro no soporta esto.
5. **Los agentes son cooperativos** — no hay mencion de agentes
   adversariales, prompt injection, o comportamiento inesperado.
6. **ISO 12207 es suficiente** — el estandar cubre procesos pero no
   cubre calidad de datos, metricas de rendimiento de IA, ni gobierno
   de agentes autonomos.

---

## Alternativas y mejoras propuestas

### Mejora 1: Composite Chain of Responsibility + Observer

En vez de Chain of Responsibility puro (cadena lineal), usar una
composicion de CoR + Observer donde:

- La cadena principal (CoR) maneja el flujo principal: CTO → Coder → QA
- Los agentes transversales (SecurityEngineer, UXDesigner) se registran
  como Observers que reciben notificaciones cuando la cadena pasa por
  ciertos puntos (ej: PR created → SecurityEngineer revisa)

Esto resuelve el problema de "multiples handlers para una solicitud".

### Mejora 2: Fast-track para tareas simples

Introducir un clasificador de complejidad al inicio de la cadena:
- **Simple** (1-2 archivos, sin dependencias externas) → CTO delega
  directamente a Coder, bypassing SystemDesign + RequirementEngineer
- **Compleja** (multi-modulo, cambios arquitectonicos) → cadena completa

Esto reduce la latencia promedio significativamente.

### Mejora 3: ISO 12207 + ISO 5338 + ISO 38507

Complementar ISO 12207 con:
- **ISO/IEC 5338** — ciclo de vida para sistemas de IA (cubre calidad
  de datos, entrenamiento, validacion, monitoreo)
- **ISO/IEC 38507** — gobernanza de IA (cubre rendicion de cuentas,
  transparencia, etica)

### Mejora 4: Event-driven en vez de issue-polling

RECPL issues como bus es simple pero ineficiente. Considerar:
- **Event bus interno** (Redis Pub/Sub o NATS) para notificaciones
  entre agentes en el mismo runtime
- RECPL issues solo para persistencia y audit trail
- Los agentes reaccionan a eventos en vez de pollear issues

### Mejora 5: Cache predictivo de tareas

Implementar un cache que reconozca patrones de tareas repetitivas:
- "Agregar endpoint CRUD para X" → template conocido
- "Agregar tests para X" → template conocido
- Si el hash de la tarea coincide con una tarea previa, reusar output
  (ya hay LLMCache en F5, extenderlo a nivel de tarea completa)

---

## Impacto en sistemas existentes

| Sistema | Impacto |
|---------|---------|
| **RECPL Compiler Bot (pipeline actual)** | Debe convertirse en modulo interno del Coder Agent. El CLI `compiler-bot/agentic --chain` se adapta como un subcomando del nuevo orquestador. |
| **agent-robot layer** | Las herramientas (tool_recpl, tool_respond, tool_read_file, etc.) se convierten en handlers de la cadena CoR. |
| **templates/ (NestJS, Prisma)** | Siguen siendo el output del Coder Agent para scaffolding. Sin cambios mayores. |
| **docs/** | Los reportes existentes (107-113) son compatibles pero operan a nivel de componente, no de sistema. |
| **CHANGELOG.md** | La version 2.x.x actual cubre el pipeline RECPL. La version 3.0.0 iniciaria el orquestador SDLC. |
| **tests/** | Los 105 tests actuales cubren el pipeline. Se necesitarian tests nuevos para: handoffs entre agentes, validacion de contratos, comportamiento de la cadena CoR. |

---

## Informacion adicional necesaria

Para una evaluacion mas precisa, se necesita:

1. **Benchmarks de RECPL** — latencia promedio de handoff, throughput
   maximo, tiempo de wake/sleep por agente
2. **Metricas de costo LLM** — costo promedio por llamada, por agente,
   por tarea, con los modelos propuestos
3. **Definicion de "tarea tipica"** — distribucion esperada de tipos de
   tarea (feature:bugfix:refactor), complejidad, frecuencia
4. **Modelo de concurrencia** — maximo de tareas concurrentes esperadas,
   politica de retry, timeout, dead letter queue
5. **Estrategia de testing para LLMs** — como se validan outputs no
   deterministicos? Metricas de calidad? Regression testing?
6. **Plan de migracion** — desde el pipeline actual al orquestador SDLC.
   Fases? Hitos? Backward compatibility?
7. **Requisitos no funcionales** — latencia P95 maximo, disponibilidad
   objetivo, throughput minimo, ventana de mantenimiento
8. **Modelo de datos completo** — ademas del task schema, que entidades
   persiste el sistema? Proyectos, agentes, ejecuciones, metricas?

---

## Veredicto Final

### No recomiendo adoptar la propuesta en su forma actual.

**Justificacion:**

La vision de un orquestador SDLC basado en ISO 12207 con agentes
especializados tiene merito arquitectonico y potencial estrategico. Los
documentos ADR-001, AIC, TJS y WDS estan bien estructurados y muestran
pensamiento sistemico.

Sin embargo, la propuesta actual tiene **3 problemas fundamentales** que
impiden recomendarla sin modificaciones sustanciales:

1. **Chain of Responsibility y RECPL operan en granularidades
   incompatibles.** CoR es un patron in-process (microsegundos por
   handoff). RECPL es un orquestador out-of-process (segundos a minutos
   por handoff). Forzar 7 eslabones de CoR sobre RECPL multiplica la
   latencia hasta hacer el sistema impractico para desarrollo iterativo.

2. **Chain of Responsibility puro no modela correctamente un SDLC.**
   En un SDLC real, multiples procesos operan sobre el mismo artefacto
   concurrentemente (Coder genera, SecurityEngineer revisa, QA verifica).
   CoR asume un solo handler por solicitud. Sin Composite + Observer,
   el modelo es incompleto.

3. **No hay plan de migracion desde el pipeline actual.** El pipeline
   RECPL v2.0 (105 tests, ~65 archivos, 9,886 lineas) es un compilador
   de lenguaje natural. El orquestador SDLC es un sistema de ingenieria
   de software completo. Son dominios diferentes. Mezclarlos sin una
   separacion clara crea un sistema que no es optimo para ninguna de
   las 2 funciones.

### Recomendacion: Adoptar con modificaciones

1. **Separar RECPL Compiler de Code Serve Orchestrator** como 2 modulos
   independientes pero integrables. El compilador es el motor de
   generacion de codigo del Coder Agent.

2. **Usar Composite Chain of Responsibility + Observer** en vez de CoR
   puro. La cadena principal es lineal (CTO → Coder → QA), pero los
   agentes transversales (Security, UX) se registran como observers.

3. **Implementar fast-track** para tareas simples donde el overhead de
   orquestacion superaria el tiempo de ejecucion.

4. **Complementar ISO 12207 con ISO 5338 + ISO 38507** para cubrir
   calidad, gobierno y etica de IA.

5. **Definir modelo de concurrencia explicito** antes de escalar a
   multiples agentes simultaneos.

6. **Establecer metricas de costo por tarea** con presupuesto automatico
   y corte si se excede.

### Proxima accion recomendada

Escribir un ADR-002 que aborde los 3 problemas fundamentales identificados
aqui antes de continuar con la implementacion. Este ADR-002 debe:

1. Definir la separacion RECPL Compiler vs Code Serve Orchestrator
2. Especificar el patron de orquestacion (CoR + Observer compuesto)
3. Definir el modelo de concurrencia (locks, heartbeats, timeouts)
4. Estimar costos operativos por tarea con los modelos propuestos
