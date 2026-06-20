---
id: "R01"
area: "DEV"
type: "GUIDE"
module: "AGENT_PATTERNS"
version: "1.0"
status: "DRAFT"
tags: ["guide", "reference", "agent-patterns", "design-patterns", "llm", "architecture"]
summary: "Resumen del documento misc/agentDesignPattern.md — 9 patrones de diseno para sistemas agente con LLM: Prompt Chaining, Routing, Parallelization, Reflection, Tool Use, Planning, Multi-Agent, Memory Management, Learning & Adaptation"
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — resumen de patrones de diseno agente"
---

# Resumen: Patrones de Diseno para Agentes LLM

> **Fuente:** `misc/agentDesignPattern.md`  
> **Autor:** Marco Fago  
> **Alcance:** 9 patrones, ~2000 lineas, ejemplos en LangChain/LangGraph + Google ADK

---

## 1. Prompt Chaining (Pipeline Pattern)

**Idea:** Descomponer una tarea compleja en una secuencia de sub-tareas, cada una con su propio prompt. La salida de un paso es la entrada del siguiente.

**Problema que resuelve:** Un solo prompt para tareas multifaceticas causa instruction neglect, contextual drift, error propagation, y alucinaciones.

**Ejemplo:** Analisis de reporte → resumen → identificar tendencias → redactar email.

**Tecnica clave:** Usar structured output (JSON/XML) entre pasos para garantizar integridad de datos.

**Frameworks:** LangChain LCEL (`|`), LangGraph (StateGraph), Google ADK (SequentialAgent).

---

## 2. Routing

**Idea:** El agente evalua dinamicamente el input para seleccionar entre multiples caminos de ejecucion posibles.

**Problema que resuelve:** Flujos lineales no pueden adaptarse a diferentes tipos de entrada o contexto.

**Mecanismos de enrutamiento:**
- **LLM-based:** El modelo clasifica el intent y devuelve un identificador de ruta
- **Embedding-based:** Similaridad semantica con embeddings
- **Rule-based:** Reglas deterministicas (if/else, keywords)
- **ML Model-based:** Clasificador fine-tuneado especificamente para la tarea

**Frameworks:** LangChain (RunnableBranch), LangGraph (conditional edges), Google ADK (sub_agents con Auto-Flow).

---

## 3. Parallelization

**Idea:** Ejecutar multiples componentes independientes concurrentemente para reducir latencia.

**Problema que resuelve:** Flujos secuenciales son ineficientes cuando hay tareas independientes (especialmente I/O como APIs).

**Casos de uso:** Investigacion multi-fuente, analisis multi-dimensional, procesamiento multi-modal, generacion de variantes A/B.

**Frameworks:** LangChain (RunnableParallel), Google ADK (ParallelAgent con sub_agents), asyncio.

---

## 4. Reflection

**Idea:** El agente evalua su propio output y lo refina iterativamente mediante un bucle de retroalimentacion.

**Problema que resuelve:** El output inicial rara vez es optimo, preciso o completo sin un mecanismo de autocorreccion.

**Arquitectura clave:** **Generator-Critic / Producer-Reviewer** — un agente produce, otro evalua. Separar roles mejora la objetividad.

**Trade-offs:** Mayor calidad a cambio de mayor latencia y costo. Riesgo de exceder la ventana de contexto.

**Frameworks:** LangChain (prompts separados para generator/critic con message history), Google ADK (SequentialAgent generador→revisor).

---

## 5. Tool Use (Function Calling)

**Idea:** El LLM decide cuando y como llamar funciones externas (APIs, bases de datos, ejecucion de codigo) basado en el input del usuario.

**Proceso:** Definicion de herramientas → LLM decide si llamar → genera JSON con nombre y argumentos → ejecucion → resultado devuelto al LLM → respuesta final.

**Problema que resuelve:** Los LLM por si solos no pueden interactuar con el mundo exterior ni ejecutar computaciones precisas.

---

## 6. Planning

**Idea:** El agente descompone un objetivo en una secuencia de pasos ejecutables antes de actuar.

**Tipos:**
- **Single-shot:** Plan completo generado de una vez
- **Re-planning:** Plan inicial que se revisa dinamicamente
- **Hierarchical:** Plan en niveles de abstraccion
- **Tree-of-Thought:** Exploracion de multiples caminos en paralelo

---

## 7. Multi-Agent

**Idea:** Multiples agentes especializados colaboran para resolver tareas, delegando entre si segun su expertise.

**Topologias:** Centralizada (coordinador unico), descentralizada (agentes peer-to-peer), jerarquica.

**Coordinacion:** Comunicacion directa, bus de eventos, espacio de memoria compartido.

---

## 8. Memory Management

**Idea:** El agente preserva y recupera informacion a traves de interacciones usando multiples niveles de memoria.

**Niveles:**
- **Working memory:** Contexto inmediato de la conversacion (ventana del LLM)
- **Episodic memory:** Historial de interacciones pasadas
- **Semantic memory:** Conocimiento factual acumulado
- **Procedural memory:** Habilidades y patrones aprendidos

---

## 9. Learning and Adaptation

**Idea:** El agente mejora su rendimiento con el tiempo basado en retroalimentacion y experiencia.

**Mecanismos:** Fine-tuning, in-context learning (ejemplos en el prompt), RLHF, feedback loops con almacenamiento de outcomes exitosos/fallidos.

---

## Tabla Comparativa

| Patron | Control | Procesamiento | Costo | Calidad output |
|--------|---------|---------------|-------|----------------|
| Chaining | Secuencial | Lineal | Bajo | Media |
| Routing | Condicional | Selectivo | Bajo | Media-Alta |
| Parallelization | Concurrente | Independiente | Medio | Media |
| Reflection | Iterativo | Feedback loop | Alto | Alta |
| Tool Use | Integrativo | Externo | Medio | Alta |
| Planning | Proactivo | Anticipatorio | Alto | Alta |
| Multi-Agent | Distribuido | Colaborativo | Muy alto | Muy alta |
| Memory | Contextual | Persistente | Medio | Alta |
| Learning | Evolutivo | Acumulativo | Variable | Creciente |

---

## Frameworks mencionados

| Framework | Enfoque | Patrones soportados |
|-----------|---------|---------------------|
| **LangChain** | LCEL (pipes) | Chaining, Routing (RunnableBranch), Parallelization (RunnableParallel) |
| **LangGraph** | StateGraph (nodos/edges) | Chaining, Routing (condicional), Reflection (ciclos), Planning |
| **Google ADK** | Agent-based (sub_agents) | Chaining (SequentialAgent), Routing (Auto-Flow), Parallelization (ParallelAgent), Reflection |
| **Crew AI** | Role-based | Multi-Agent, Planning, Tool Use |

---

*Resumen generado del documento `misc/agentDesignPattern.md`. Fecha: 2026-06-19.*
