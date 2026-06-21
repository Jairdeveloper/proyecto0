---
id: "R02"
area: dev
type: guide
module: agent_patterns
version: "1.0"
status: ACTIVE
tags: ["guide", "reference", "agent-patterns", "design-patterns", "llm", "architecture", "reasoning", "guardrails", "evaluation"]
summary: "Resumen del documento misc/AgentDesignPattern2.md — Capitulos 10-21 + Apendice A: MCP, Goal Setting, Exception Handling, HITL, RAG, A2A, Resource-Aware Optimization, Reasoning Techniques, Guardrails, Evaluation, Prioritization, Exploration & Discovery, Advanced Prompting"
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — resumen de capitulos 10-21 + apendice A"
---

# Resumen: Patrones de Diseno para Agentes LLM (Parte 2)

> **Fuente:** `misc/AgentDesignPattern2.md`
> **Autor:** Marco Fago
> **Alcance:** Capitulos 10-21 + Apendice A, ~7300 lineas, ejemplos en CrewAI, Vertex AI, LangChain, Google ADK

---

## 10. Model Context Protocol (MCP)

**Idea:** Protocolo estandarizado abierto para que los LLM se comuniquen con herramientas externas. Proporciona una interfaz universal entre modelos de lenguaje y fuentes de datos/herramientas.

**Problema que resuelve:** Cada integracion de herramientas requiere adaptadores personalizados. MCP estandariza el contrato.

**Componentes:**
- **MCP Host:** Programa que inicia la conexion (ej. Claude Desktop)
- **MCP Client:** Conexion 1:1 con un servidor especifico
- **MCP Server:** Expone recursos, herramientas y prompts

**Tipos de servidores:**
- **Filesystem:** Acceso seguro a archivos locales
- **Database:** Consultas SQL sobre bases de datos
- **API wrappers:** Interfaces para servicios externos
- **Custom:** Servidores especializados para dominios especificos

**Recursos:** Similares a endpoints GET — datos contextuales (archivos, logs, APIs).

**Herramientas:** Similares a endpoints POST — acciones que el modelo ejecuta (escritura, calculos, envio de datos).

---

## 11. Goal Setting & Monitoring

**Idea:** Mecanismos para que el agente defina, descomponga y monitoree objetivos, asegurando que las acciones se alineen con los resultados deseados.

**Problema que resuelve:** Agentes sin objetivos claros derivan, pierden foco, o ejecutan acciones sin direccion estrategica.

**Componentes clave:**
- **Goal generator:** Descompone objetivos complejos en sub-objetivos ejecutables
- **Progress monitor:** Evalua periodicamente el avance hacia cada objetivo
- **Adaptation engine:** Re-planifica cuando las condiciones cambian o el progreso se estanca

**Metricas de monitoreo:**
- Progreso porcentual hacia objetivo
- Desviacion del plan original
- Tiempo restante estimado
- Calidad de sub-objetivos completados

**Patron:** Goal -> Sub-goals -> Actions -> Monitor -> Adapt/Re-plan

---

## 12. Exception Handling & Recovery

**Idea:** El agente debe anticipar, detectar y recuperarse de fallos en tiempo de ejecucion sin intervencion humana.

**Problema que resuelve:** En sistemas autonomos, los fallos son inevitables (APIs caidas, datos malformados, timeouts). Sin manejo de excepciones, el pipeline completo falla.

**Estrategias de recuperacion:**
- **Retry:** Reintentar con backoff exponencial
- **Fallback:** Usar modelo/herramienta alternativa
- **Graceful degradation:** Reducir funcionalidad pero mantener operacion
- **Checkpoint/Rollback:** Volver a un estado valido conocido
- **Human escalation:** Delegar a un humano cuando la recuperacion automatica falla

**Patron clave:** Try -> Detect error -> Classify severity -> Apply recovery strategy -> Log -> Continue or escalate

---

## 13. Human-in-the-Loop (HITL)

**Idea:** Incorporar supervision humana en puntos criticos del flujo del agente para decisiones de alto riesgo o cuando la confianza del modelo es baja.

**Problema que resuelve:** Agentes completamente autonomos pueden tomar decisiones incorrectas o eticamente problematicas sin rendir cuentas.

**Puntos de intervencion:**
- **Pre-ejecucion:** Humano aprueba/rechaza el plan antes de ejecutar
- **Durante ejecucion:** Humano responde preguntas del agente en puntos de decision
- **Post-ejecucion:** Humano revisa y aprueba el output final

**Niveles de autonomia:**
1. Full automation
2. Automation with human approval on critical actions
3. Human-on-the-loop (monitoreo, no intervencion directa)
4. Human-in-the-loop (intervencion directa requerida)
5. Full human control

---

## 14. Knowledge Retrieval / RAG

**Idea:** Aumentar el conocimiento del LLM recuperando informacion relevante de fuentes externas en tiempo de inferencia.

**Problema que resuelve:** Los LLM tienen conocimiento estatico (fecha de corte), alucinan hechos, y no tienen acceso a datos privados o actualizados.

**Pipeline RAG:**
1. **Indexing:** Documentos -> chunking -> embeddings -> vector store
2. **Retrieval:** Query -> embedding -> similarity search -> top-k chunks
3. **Generation:** Query + retrieved chunks -> prompt -> LLM -> response

**Variantes:**
- **Naive RAG:** Retrieve + generate
- **Advanced RAG:** Pre-retrieval (query rewriting, routing) y post-retrieval (reranking, filtering)
- **Modular RAG:** Componentes intercambiables (search, memory, fusion, etc.)

---

## 15. Inter-Agent Communication / A2A

**Idea:** Protocolos y mecanismos para que agentes se comuniquen entre si, compartan informacion y coordinen acciones.

**Problema que resuelve:** En sistemas multi-agente, los agentes necesitan intercambiar datos, delegar tareas y sincronizarse.

**Mecanismos:**
- **Mensajes directos:** Comunicacion punto a punto entre agentes
- **Bus de eventos:** Publicacion/suscripcion de eventos
- **Memoria compartida:** Espacio comun de lectura/escritura
- **Pizarron (Blackboard):** Area compartida donde los agentes depositan y recuperan informacion

**Protocolo A2A (propuesto por Google):** Estandar abierto para que agentes de diferentes frameworks se comuniquen, permitiendo descubrimiento de capacidades, negociacion de formatos, y ejecucion colaborativa.

---

## 16. Resource-Aware Optimization

**Idea:** Gestionar dinamicamente recursos computacionales, temporales y financieros, seleccionando el modelo/herramienta optima segun la complejidad de la tarea.

**Problema que resuelve:** Los LLM son costosos y lentos. Usar el modelo mas grande para todas las tareas es ineficiente.

**Tecnicas:**
- **Dynamic Model Switching:** Router Agent clasifica complejidad -> modelo barato para tareas simples, modelo potente para tareas complejas
- **Adaptive Tool Use & Selection:** Seleccion inteligente de herramientas segun costo/latencia
- **Contextual Pruning & Summarization:** Podar/simplificar el contexto para reducir tokens
- **Proactive Resource Prediction:** Anticipar demanda de recursos
- **Cost-Sensitive Exploration:** Optimizar costos de comunicacion en sistemas multi-agente
- **Graceful Degradation:** Reducir funcionalidad bajo restricciones severas

**Arquitectura:** Router Agent -> critique agent -> feedback loop para mejorar el enrutamiento

---

## 17. Reasoning Techniques

**Idea:** Conjunto de metodologias para que el agente realice inferencias multi-paso, exploracion de caminos, autocorreccion y razonamiento colaborativo.

### Chain-of-Thought (CoT)
El agente genera pasos intermedios de razonamiento antes de responder. "Piensa paso a paso". Mejora accuracy en tareas aritmeticas, logica y sentido comun. Variantes: Zero-shot CoT, Few-shot CoT.

### Tree-of-Thought (ToT)
Extension de CoT que explora **multiples caminos de razonamiento en paralelo** formando un arbol. Permite backtracking y autocorreccion.

### Self-Correction
El agente evalua su propio output, identifica deficiencias, y lo refina iterativamente. Implementado como un agente "critic" que revisa y propone mejoras.

### Program-Aided Language Models (PALM)
El LLM genera y ejecuta codigo (Python) como parte del razonamiento, offloaddeando calculos complejos a un entorno deterministico.

### Reinforcement Learning with Verifiable Rewards (RLVR)
Entrenamiento del modelo con problemas de respuesta conocida (matematicas, codigo) donde aprende a generar razonamientos largos por prueba y error sin supervision humana directa.

### ReAct (Reasoning + Acting)
Ciclo intercalado: **Thought -> Action -> Observation -> Thought...** El agente razona, ejecuta herramientas, observa resultados, y ajusta su plan. Framework fundamental para agentes autonomos.

### Chain of Debates (CoD)
Multiples modelos colaboran y debaten. Presentan ideas iniciales, se critican mutuamente, intercambian contraargumentos. Mejora precision y reduce sesgo.

### Graph of Debates (GoD)
Red no-lineal de argumentos donde cada nodo es una idea y las aristas indican "soporta" o "refuta". La conclusion emerge del cluster mejor soportado del grafo.

### Multi-Agent System Search (MASS)
Framework para **optimizar automaticamente** sistemas multi-agente. Tres etapas:
1. Block-Level Prompt Optimization (optimizar prompts individuales)
2. Workflow Topology Optimization (seleccionar topologia optima)
3. Workflow-Level Prompt Optimization (optimizar prompts del sistema completo)

### Scaling Inference Law
La ley que establece que un modelo **mas pequeno con mas tiempo de computo en inferencia** puede superar a un modelo mas grande con menos computo. Permite decisiones economicas sobre tamano de modelo vs. "thinking budget".

### Deep Research
Agentes que realizan investigaciones autonomas multi-paso: busqueda inicial -> lectura y sintesis -> identificar gaps -> busquedas de seguimiento -> sintesis final con citas.

---

## 18. Guardrails / Safety Patterns

**Idea:** Mecanismos de seguridad multi-capa que aseguran que el agente opere de forma etica, segura y predecible.

**Capas de defensa:**
1. **Input Validation/Sanitization:** Filtrar contenido malicioso antes del procesamiento
2. **Behavioral Constraints (Prompt-level):** Instrucciones directas en el prompt del sistema
3. **Tool Use Restrictions:** Limitar que herramientas puede usar el agente
4. **Output Filtering/Post-processing:** Analizar respuestas generadas por toxicidad/sesgo
5. **External Moderation APIs:** APIs especializadas en moderacion de contenido
6. **Human Oversight (HITL):** Supervision humana para decisiones criticas

**Implementacion con CrewAI:** Agente "policy enforcer" dedicado + Pydantic guardrail + callback de validacion. Prompt de seguridad define politicas: subversion de instrucciones, contenido prohibido, fuera de dominio, informacion competitiva.

**Implementacion con Vertex AI:** Callbacks `before_tool_callback` que validan parametros antes de ejecutar herramientas (ej. verificar identidad del usuario).

---

## 19. Evaluation & Monitoring

**Idea:** Medicion continua de la efectividad, eficiencia y cumplimiento del agente en entornos de produccion.

**Metricas basicas:**
- **Response accuracy:** Coincidencia exacta vs. ground truth
- **Latency monitoring:** Tiempo de respuesta
- **Token usage:** Costo operacional

**Metricas avanzadas:**
- **LLM-as-a-Judge:** Usar un LLM para evaluar cualitativamente la salida de otro LLM (ej. utilidad, claridad, neutralidad)
- **Trajectory evaluation:** Evaluar la secuencia de pasos que el agente tomo (tool selection, estrategia, eficiencia)
- **Drift detection:** Detectar degradacion del rendimiento por cambios en datos de entrada

**Evaluacion de trayectorias:**
- **Exact match:** Secuencia perfecta
- **In-order match:** Acciones correctas en orden, permitiendo pasos extra
- **Any-order match:** Acciones correctas en cualquier orden
- **Precision/Recall:** Relevancia de las acciones predichas

**Archivos de test y evalset:**
- **Test files:** JSON con sesiones individuales, unit testing
- **Evalset files:** Multiples sesiones, integration testing

**Del agente al "contractor":** Propuesta de evolucion hacia contratos formales donde el agente-negocia, descompone en subcontratos, auto-valida y ejecuta con calidad verificable.

---

## 20. Prioritization

**Idea:** El agente evalua y ordena tareas basandose en urgencia, importancia, dependencias y recursos disponibles.

**Problema que resuelve:** Sin priorizacion, el agente se vuelve ineficiente ante multiples objetivos conflictivos y recursos limitados.

**Elementos fundamentales:**
1. **Criteria definition:** Urgencia, importancia, dependencias, recursos, costo/beneficio
2. **Task evaluation:** Evaluar cada tarea contra los criterios
3. **Scheduling/selection logic:** Algoritmo que selecciona la siguiente accion optima
4. **Dynamic re-prioritization:** Reajustar prioridades cuando cambian las condiciones

**Ejemplo:** Project Manager Agent con LangChain que crea tareas, asigna prioridades (P0/P1/P2) y asigna trabajadores segun urgencia.

---

## 21. Exploration & Discovery

**Idea:** Agentes que proactivamente buscan informacion novedosa, disenan experimentos, y generan nuevo conocimiento.

**Problema que resuelve:** Agentes con conocimiento estatico no pueden innovar ni adaptarse a dominios en evolucion rapida.

**Google Co-Scientist:** Sistema multi-agente para investigacion cientifica:
- **Generation agent:** Produce hipotesis iniciales
- **Reflection agent:** Evalua correccion y novedad
- **Ranking agent:** Torneo Elo para priorizar hipotesis
- **Evolution agent:** Refina las mejores hipotesis
- **Proximity agent:** Agrupa ideas similares
- **Meta-review agent:** Sintetiza patrones comunes

**Agent Laboratory:** Framework autonomo de investigacion con roles academicos (Professor, Postdoc, Reviewers, ML Engineer, SW Engineer). Pipeline: Literature Review -> Experimentation -> Report Writing -> Knowledge Sharing (AgentRxiv).

---

## Appendix A: Advanced Prompting Techniques

### Principios basicos
- **Clarity & Specificity:** Instrucciones sin ambiguedad
- **Conciseness:** Directo, sin verborrea
- **Verbos de accion:** Summarize, Extract, Classify, Generate, etc.
- **Instructions over Constraints:** Preferir "haz X" sobre "no hagas Y"
- **Experimentation & Iteration:** Refinamiento progresivo

### Tecnicas basicas
- **Zero-shot:** Sin ejemplos
- **One-shot:** Un ejemplo
- **Few-shot:** 3-5 ejemplos (o many-shot con cientos de ejemplos en modelos con contexto largo)

### Estructuracion
- **System prompting:** Contexto global y comportamiento
- **Role prompting:** Asignar una personalidad al modelo
- **Delimiters:** Separar instrucciones, contexto, ejemplos e input (```, XML tags)
- **Context Engineering:** Contexto dinamico (historial, documentos recuperados, tool outputs, datos implicitos del usuario)
- **Structured Output:** JSON, XML, CSV, Pydantic validation (model_validate_json)

### Razonamiento
- **Chain-of-Thought (CoT):** "Piensa paso a paso"
- **Self-Consistency:** Multiples caminos de razonamiento -> mayoria de votos
- **Step-Back Prompting:** Preguntar principio general antes del problema especifico
- **Tree-of-Thought (ToT):** Exploracion de multiples ramas

### Accion e interaccion
- **Tool Use / Function Calling:** El LLM genera JSON con tool + argumentos; el sistema ejecuta
- **ReAct:** Thought -> Action -> Observation -> loop

### Avanzadas
- **Automatic Prompt Engineering (APE):** LLMs que generan y evaluan prompts
- **DSPy-style optimization:** Goldset + objective function -> optimizer (Bayesian) refina few-shot examples e instrucciones
- **Iterative Prompting / Refinement:** Ciclo humano de prueba-error-refinamiento
- **Negative Examples:** Mostrar que NO hacer (uso cuidadoso)
- **Analogies:** Framing con analogias familiares
- **Factored Cognition / Decomposition:** Dividir tarea compleja en sub-tareas independientes
- **RAG:** Recuperacion de documentos externos como contexto
- **Persona Pattern (User Persona):** Describir la audiencia destino
- **Google Gems:** Instancias especializadas de Gemini con instrucciones persistentes
- **Meta-Prompting:** Usar LLM para refinar prompts

### Prompting para codigo
Generacion, explicacion, traduccion y debugging de codigo. Requiere especificar lenguaje, version y contexto suficiente.

### Multimodal
Combinacion de texto + imagenes/audio/video como input. Prompting para descripcion de imagenes, explicacion de diagramas, etc.

---

## Tabla Comparativa

| Patron | Control | Procesamiento | Costo | Complejidad |
|--------|---------|---------------|-------|-------------|
| MCP | Protocolo | Estandarizado | Bajo | Media |
| Goal Setting | Directivo | Proactivo | Medio | Alta |
| Exception Handling | Reactivo | Recuperativo | Medio | Alta |
| HITL | Supervisado | Interactivo | Alto | Media |
| RAG | Aumentativo | Recuperativo | Medio | Alta |
| A2A | Distribuido | Cooperativo | Alto | Muy alta |
| Resource Optimization | Adaptativo | Selectivo | Variable | Muy alta |
| Reasoning | Cognitivo | Multi-paso | Alto | Alta |
| Guardrails | Preventivo | Multi-capa | Medio | Media-Alta |
| Evaluation | Medible | Continuo | Medio | Alta |
| Prioritization | Estrategico | Ordenado | Bajo-Medio | Media |
| Exploration & Discovery | Proactivo | Generativo | Muy alto | Muy alta |

---

## Frameworks mencionados

| Framework | Enfoque | Patrones soportados |
|-----------|---------|---------------------|
| **CrewAI** | Role-based + guardrails | Multi-Agent, Tool Use, Guardrails (Pydantic validation), Planning |
| **Vertex AI** | Google Cloud | Guardrails (callbacks), Safety filters, Prompt optimization |
| **LangChain** | LCEL + herramientas | Tool Use (function calling), Planning, Memory, RAG |
| **LangGraph** | StateGraph | Reasoning, Planning, Multi-Agent, Reflection |  
| **Google ADK** | Agent-based | Multi-Agent, A2A, Tool Use, Evaluation |
| **OpenRouter** | Model routing | Resource-Aware Optimization (model fallback, auto-selection) |
| **DSPy** | Programmatic prompts | Automatic Prompt Engineering (APE) |

---

*Resumen generado del documento `misc/AgentDesignPattern2.md` — capitulos 10-21 + Apendice A. Fecha: 2026-06-19.*
