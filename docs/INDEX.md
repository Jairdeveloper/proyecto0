---
id: INDEX
area: doc
type: GUIDE
module: documentation-index
version: 1.0
status: ACTIVE
tags:
  - index
  - documentation
  - navigation
summary: "Indice maestro de documentacion de @Proyecto0. Organizado por AREA_SEMANTICA del frontmatter. La secuencia de creacion se preserva mediante el prefijo NNN."
keywords:
  - index
  - documentation
  - navigation
  - area
  - knowledge-base
---

# Indice de Documentacion

> 54 documentos organizados por area tematica.
> Secuencia de creacion: NNN ascendente.

## Area: dev

Desarrollo. 44 documentos (GUIDE 11, PLAN 4, PROP 13, REP 14, SPEC 2).

| NNN | Tipo | Modulo | Resumen |
|-----|------|--------|---------|
| 000 | GUIDE | shell-style | Guia de estilo para scripts Shell en @Proyecto0. Define convenciones de nomencla... |
| 004 | SPEC | doc-processor | Especificacion completa del Sistema Compilador-Compilador de Documentacion para ... |
| 005 | SPEC | compiler-theory | Especificacion de teoria de compiladores: Godel, Turing, automatas, lambda calcu... |
| 006 | PROP | compiler-bot | Propuesta de implementacion de un bot RECPL (READ-EVAL-PRINT-LOOP) basado en teo... |
| 007 | GUIDE | compiler-bot | Plan de accion detallado para implementar cada seccion de la propuesta 006_PROP_... |
| 009 | GUIDE | compiler-bot | Reporte detallado de implementacion del bot RECPL. Describe todas las acciones r... |
| 010 | GUIDE | compiler-bot | Runbook de uso operativo del bot RECPL. Describe modos de ejecucion, instruccion... |
| 011 | PROP | compiler-bot | Propuesta de extension del bot RECPL para soporte multi-tech-stack y UI web. Def... |
| 012 | PROP | compiler-bot | Propuesta de continuacion de 011_PROP_DEV_COMPILER_BOT_EXTENDED. Define el flujo... |
| 013 | PROP | compiler-bot | Propuesta de implementacion de un nucleo en C (recpl-core) para el pipeline del ... |
| 014 | PROP | compiler-bot | Propuesta de sistema NLP y clasificador de intenciones (Intent) para el bot RECP... |
| 015 | GUIDE | c-style | Guia de estilo para programacion en C en @Proyecto0. Define convenciones de nome... |
| 016 | PLAN | compiler-bot | Plan de ejecucion detallado para la implementacion del nucleo C (recpl-core) del... |
| 017 | GUIDE | compiler-bot | Guia detallada de aprendizaje para implementar el nucleo C (recpl-core) del bot ... |
| 018 | PROP | compiler-bot | Propuesta de sistema Ejecutor de Tutoriales para el bot RECPL. Extiende la capa ... |
| 020 | REP | compiler-bot | Reporte tecnico de desarrollo sobre Adobe FrameMaker desde compiladores y teoria... |
| 022 | GUIDE | lifecycle-framework | Marco generico de ciclo de vida para proyectos de desarrollo de software. Define... |
| 024 | REP | project-diagnostic | Diagnostico integral del proyecto @Proyecto0 basado exclusivamente en los archiv... |
| 025 | GUIDE | compiler-bot | Descripcion teorica del pipeline RECPL (READ-EVAL-PRINT Compiler Loop). Explica ... |
| 026 | GUIDE | compiler-bot | Descripcion del bucle principal RECPL (recpl.sh) que envuelve e itera sobre el p... |
| 027 | PROP | compiler-bot | Propuesta de mejora para agregar las banderas -c/--command y -f/--file al bucle ... |
| 028 | PROP | compiler-bot | Propuesta de diseno para implementar un patron composite que permita al modo int... |
| 031 | PLAN | compiler-bot | Plan de ejecucion detallado para integrar LLMs (Claude, OpenAI) en el RECPL Compiler Bot. Describe ... |
| 048 | PLAN | compiler-bot | Plan de implementacion detallado para la capa agent-robot sobre RECPL. Arquitectura, bridge, herramientas del agente, fases con tareas, reglas de diseno... |
| 049 | PLAN | compiler-bot | Plan de ejecucion detallado de la capa agent-robot. 4 fases, 25 tareas concretas con pseudocodigo de cada archivo, comandos de verificacion, dependencias entre tareas, y criterios de exito por fase... |
| 050 | REP | compiler-bot | Reporte de implementacion de la Fase 2 del plan 049: herramientas del sistema para la capa agent-robot (tool_read_file, tool_write_file, tool_run_command), integracion en agent.sh, tests, y fix de compatibilidad con dash... |
| 051 | REP | compiler-bot | Reporte de implementacion de la Fase 1 del plan 049: fundacion de la capa agent-robot (config.sh, bridge.sh, agent.sh, memory.sh, tool_registry.sh, tool_recpl.sh, tool_respond.sh), tests, y compatibilidad con dash... |
| 052 | REP | compiler-bot | Reporte de implementacion de la Fase 3 del plan 049: planificador multi-paso (planner.sh), memoria multi-sesion y exportacion, busqueda en codigo (tool_search_code.sh), integracion en agent.sh, 13 tests funcionales... |
| 032 | REP | compiler-bot | Reporte de implementacion de la FASE-L1 del plan 031: adapters de proveedor LLM... |
| 033 | REP | compiler-bot | Reporte de implementacion de la FASE-L2 del plan 031: fachada LLM y mapper IR... |
| 034 | REP | compiler-bot | Reporte de implementacion de la FASE-L3 del plan 031: router inteligente e integ... |
| 035 | REP | compiler-bot | Reporte de implementacion de la FASE-L4 del plan 031: tests, documentacion y hard... |
| 036 | REP | compiler-bot | Reporte de implementacion de la Fase 1 del patron composite: funciones composite_... |
| 037 | REP | compiler-bot | Reporte de implementacion de la Fase 2 del patron composite: comandos source y exec en modo interactivo y batch... |
| 038 | REP | compiler-bot | Reporte de implementacion de la Fase 3 del patron composite: pruebas de source, exec y estado compartido... |
| 039 | PROP | compiler-bot | Propuesta de capa TUI (Terminal UI) para RECPL. Analiza si el proyecto esta maduro, recomienda wrapper liviano whiptail... |
| 040 | PROP | compiler-bot | Propuesta de debugger de pipeline RECPL con 5 modos: trace, step, timing, inspect, xtrace... |
| 041 | REP | compiler-bot | Reporte de implementacion del debugger de pipeline RECPL. pipeline_debugger.sh con 5 modos, 784 lineas, probado en 10 escenarios... |
| 042 | GUIDE | compiler-bot | Runbook de uso del pipeline_debugger.sh: 5 modos, ejemplos, troubleshooting, buenas practicas... |
| 043 | REP | compiler-bot | Reporte de ingenieria inversa del pipeline RECPL. 10 escenarios, 6 etapas, 3 bugs detectados. Basado en pipeline_debugger.sh... |
| 044 | GUIDE | compiler-bot | Cheatsheet de comandos de pipeline_debugger.sh. Todos los modos, flags y ejemplos con salida real... |
| 045 | PROP | compiler-bot | Propuesta de provider apifreellm.com para RECPL. Analisis de API, diseno de adapter free/premium, integracion con llm_classifier.sh... |
| 046 | PROP | compiler-bot | Propuesta de arquitectura free/paid para providers LLM. Dispatcher multi-provider, registry de proveedores, fallback chain, 0 cambios en adapters existentes... |
| 047 | PROP | compiler-bot | Analisis y propuesta de nuevo concepto para Proyecto0: de compilador NL a agente de IA open-source multi-proposito. Arquitectura de agentes, analisis de brechas, plan de migracion... |
 
## Area: mgt

Gestion. 4 documentos (REP 4).

| NNN | Tipo | Modulo | Resumen |
|-----|------|--------|---------|
| 019 | REP | framemaker | Reporte de gerencia: analisis de ingenieria inversa sobre Adobe FrameMaker desde... |
| 021 | REP | framemaker | Reporte de analisis de mercado: estimacion de interes en el producto RECPL Compi... |
| 023 | REP | project-analysis | Analisis integral del proyecto @Proyecto0. Cubre objetivos alcanzados, debilidad... |
| 030 | REP | compiler-bot | Reporte de ingenieria inversa de Claude/OpenAI y propuesta de integracion con RECPL... |

## Area: doc

Documentacion. 2 documentos (PROP 2).

| NNN | Tipo | Modulo | Resumen |
|-----|------|--------|---------|
| 003 | PROP | doc-processor | Propuesta de implementacion para un procesador-compilador de documentos que comp... |
| 029 | PROP | documentation | Propuesta de organizacion de la base de conocimiento en docs/ por AREA_SEMANTICA... |

## Area: prompts

Prompts. 1 documentos (PRM 1).

| NNN | Tipo | Modulo | Resumen |
|-----|------|--------|---------|
| 008 | PRM | build-agent | Convenciones para la creación de prompts de subagentes opencode: estructura, con... |

## Area: algorithms

Algoritmos. 1 documentos (ALGP 1).

| NNN | Tipo | Modulo | Resumen |
|-----|------|--------|---------|
| ALGP003 | ALGP | documentation | Propuesta de convención formal para la documentación del proyecto @compilador-co... |

## Area: legacy

Legacy. 2 documentos (GUIDE 2).

| NNN | Tipo | Modulo | Resumen |
|-----|------|--------|---------|
| 001 | GUIDE | masterindex | Documentacion original del programa masterindex por Dale Dougherty. Programa de ... |
| 002 | GUIDE | spellcheck | Documentacion original del programa spellcheck.awk por O'Reilly. Corrector ortog... |

---

## Secuencia completa por NNN

| NNN | Archivo | Area | Tipo |
|-----|---------|------|------|
| 000 | `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` | dev | GUIDE |
| 001 | `001_GUIDE_DOC_MASTERINDEX_1.0_DRAFT.md` | legacy | GUIDE |
| 002 | `002_GUIDE_DOC_SPELLCHECK_1.0_DRAFT.md` | legacy | GUIDE |
| 003 | `003_PROP_DOC_DOC_PROCESSOR_1.0_DRAFT.md` | doc | PROP |
| 004 | `004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md` | dev | SPEC |
| 005 | `005_SPEC_DOC_COMPILADORTHEORY_1.0_ACTIVE.md` | dev | SPEC |
| 006 | `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` | dev | PROP |
| 007 | `007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` | dev | GUIDE |
| 008 | `008_PRM_BUILD_AGENT_1_0_DRAFT.md` | prompts | PRM |
| 009 | `009_GUIDE_DEV_COMPILER_BOT_IMPL_REPORT_1_0_DRAFT.md` | dev | GUIDE |
| 010 | `010_GUIDE_DEV_COMPILER_BOT_RUNBOOK_1_0_DRAFT.md` | dev | GUIDE |
| 011 | `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` | dev | PROP |
| 012 | `012_PROP_DEV_COMPILER_BOT_FLOW_REFINE_1_0_DRAFT.md` | dev | PROP |
| 013 | `013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` | dev | PROP |
| 014 | `014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md` | dev | PROP |
| 015 | `015_GUIDE_DEV_C_STYLE_1_0_DRAFT.md` | dev | GUIDE |
| 016 | `016_PLAN_DEV_C_CORE_EXECUTION_1_0_DRAFT.md` | dev | PLAN |
| 017 | `017_GUIDE_DEV_C_CORE_LEARNING_1_0_DRAFT.md` | dev | GUIDE |
| 018 | `018_PROP_DEV_COMPILER_BOT_TUTORIAL_EXEC_1_0_DRAFT.md` | dev | PROP |
| 019 | `019_REP_MGT_FRAMEMAKER_1_0_DRAFT.md` | mgt | REP |
| 020 | `020_REP_DEV_FRAMEMAKER_DEVELOPMENT_1_0_DRAFT.md` | dev | REP |
| 021 | `021_REP_MGT_FRAMEMAKER_MARKET_1_0_DRAFT.md` | mgt | REP |
| 022 | `022_GUIDE_DEV_LIFECYCLE_FRAMEWORK_1_0_DRAFT.md` | dev | GUIDE |
| 023 | `023_REP_MGT_PROJECT_ANALYSIS_1_0_DRAFT.md` | mgt | REP |
| 024 | `024_REP_DEV_PROJECT_DIAGNOSTIC_1_0_DRAFT.md` | dev | REP |
| 025 | `025_GUIDE_DEV_COMPILER_BOT_PIPELINE_1_0_DRAFT.md` | dev | GUIDE |
| 026 | `026_GUIDE_DEV_COMPILER_BOT_LOOP_1_0_DRAFT.md` | dev | GUIDE |
| 027 | `027_PROP_DEV_COMPILER_BOT_CLI_FLAGS_1_0_DRAFT.md` | dev | PROP |
| 028 | `028_PROP_DEV_COMPILER_BOT_COMPOSITE_1_0_DRAFT.md` | dev | PROP |
| 029 | `029_PROP_DOC_DOCS_ORGANIZATION_1_0_DRAFT.md` | doc | PROP |
| 030 | `030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md` | mgt | REP |
| 031 | `031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` | dev | PLAN |
| 032 | `032_REP_DEV_COMPILER_BOT_LLM_FASE_L1_1_0_DRAFT.md` | dev | REP |
| 033 | `033_REP_DEV_COMPILER_BOT_LLM_FASE_L2_1_0_DRAFT.md` | dev | REP |
| 034 | `034_REP_DEV_COMPILER_BOT_LLM_FASE_L3_1_0_DRAFT.md` | dev | REP |
| 035 | `035_REP_DEV_COMPILER_BOT_LLM_FASE_L4_1_0_DRAFT.md` | dev | REP |
| 036 | `036_REP_DEV_COMPILER_BOT_COMPOSITE_FASE1_1_0_DRAFT.md` | dev | REP |
| 037 | `037_REP_DEV_COMPILER_BOT_COMPOSITE_FASE2_1_0_DRAFT.md` | dev | REP |
| 038 | `038_REP_DEV_COMPILER_BOT_COMPOSITE_FASE3_1_0_DRAFT.md` | dev | REP |
| 039 | `039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` | dev | PROP |
| 040 | `040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md` | dev | PROP |
| 041 | `041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md` | dev | REP |
| 042 | `042_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_RUNBOOK_1_0_DRAFT.md` | dev | GUIDE |
| 043 | `043_REP_DEV_COMPILER_BOT_PIPELINE_RE_1_0_DRAFT.md` | dev | REP |
| 044 | `044_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_CHEATSHEET_1_0_DRAFT.md` | dev | GUIDE |
| 045 | `045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` | dev | PROP |
| 046 | `046_PROP_DEV_COMPILER_BOT_TIER_ARCHITECTURE_1_0_DRAFT.md` | dev | PROP |
| 047 | `047_PROP_DEV_COMPILER_BOT_AGENT_CONCEPT_1_0_DRAFT.md` | dev | PROP |
| 048 | `048_PLAN_DEV_COMPILER_BOT_AGENT_IMPL_1_0_DRAFT.md` | dev | PLAN |
| 049 | `049_PLAN_DEV_COMPILER_BOT_AGENT_EXECUTION_1_0_DRAFT.md` | dev | PLAN |
| 050 | `050_REP_DEV_COMPILER_BOT_FASE2_AGENT_TOOLS_1_0_DRAFT.md` | dev | REP |
| 051 | `051_REP_DEV_COMPILER_BOT_FASE1_AGENT_FOUNDATION_1_0_DRAFT.md` | dev | REP |
| 052 | `052_REP_DEV_COMPILER_BOT_FASE3_AGENT_PLANNER_MEMORY_1_0_DRAFT.md` | dev | REP |
| ALGP003 | `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md` | algorithms | ALGP |
