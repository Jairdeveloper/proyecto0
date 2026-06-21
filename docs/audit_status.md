---
id: AUDIT-DOC-001
area: dev
type: ANALYSIS
module: DOC_STATUS_AUDIT
version: 1.0
status: IMPLEMENTED
tags: [audit, documentation, status, classification]
summary: Auditoria del campo `status` en toda la documentacion vs. el estado real del proyecto. Define criterios de clasificacion y evalua cada documento frente a su status correcto.
keywords: [status audit, ACTIVE, DRAFT, OBSOLETE, documentation classification]
changelog:
  - date: 2026-06-21
    description: Version inicial del audit de estados de documentacion
---

# Auditoria de Status de Documentacion

## 1. Estado actual del proyecto (AS-IS)

| Metrica | Valor |
|---------|-------|
| Version | **2.8.4** |
| Python agentic_pipeline (prod) | **201 archivos .py, 848 tests** |
| Python pdca_sdlc (prod) | **32 archivos .py, 224 tests** |
| Shell v1.0 (legacy congelado) | **0 modificaciones desde freeze — pendiente de fusion futura** |
| Total tests | **1,072+** |
| Documentos .md en `docs/` | **~231** (185 activos + 46 en archive/) |
| Commits totales | **90** |

## 2. Criterios de clasificacion

| Status | Definicion | Cuando aplica |
|--------|------------|---------------|
| **ACTIVE** | Documento de referencia vivo. Debe mantenerse actualizado con el codigo. | GUIDE/SPEC que describen el sistema actual; runbooks operativos; tutoriales de onboarding; convenciones/estandares vigentes; diagramas del pipeline; stubs de API. |
| **IMPLEMENTED** | Documento historico que describe funcionalidad/codigo implementado al 100%. Congelado — ya no se actualiza. | REP que documenta un componente existente; PLAN que se ejecuto completamente; PROP cuya vision se realizo; sprint reports que documentan entregas completadas; ANALYSIS que describe el estado actual. |
| **DRAFT** | Documento incompleto, describe trabajo futuro pendiente, o describe componentes legacy que seran integrados a futuro. | PROP/PLAN de features sin implementar; documentos marcados con TODO/WIP; REP de trabajo en progreso; Shell v1.0 legacy congelado (pendiente de fusion). |
| **OBSOLETE** | Describe algo superado, que ya no existe, o fue reemplazado por una version mas nueva. | Version antigua de un documento superseded por una version posterior (v1.0 reemplazada por v1.1); documentos sin valor historico ni de referencia. |

### 2.1. Nota sobre Shell v1.0

El pipeline Shell v1.0 esta congelado como legacy pero **no es OBSOLETE** porque:

1. El codigo existe y es funcional (`compiler-bot/frontend/*.sh`, `backend/*.sh`, `middleend/*.sh`, `recpl.sh`, `agent-robot/`)
2. Se espera que sea fusionado al sistema futuro
3. Sirve como referencia de diseno para la implementacion Python

Por tanto, los documentos que describen el Shell v1.0 mantienen **status DRAFT** (no OBSOLETE), salvo que describan un plan/propuesta ya ejecutada que no tenga valor como referencia actual.

## 3. Evaluacion por archivo

### 3.1. Guias y referencias activas

| Archivo | Claimed | Codigo descrito | Existe? | Recomendado | Justificacion |
|---------|---------|-----------------|---------|-------------|---------------|
| `docs/005_SPEC_DOC_COMPILADORTHEORY_1.0_ACTIVE.md` | ACTIVE | Teoria de compiladores (referencia) | N/A | **ACTIVE** | Spec teorica, sin dependencia de codigo. Correcto. |
| `docs/008_PRM_BUILD_AGENT_1_0_DRAFT.md` | DRAFT | Convenciones de prompts para subagentes | N/A | **ACTIVE** | Las convenciones descritas son las que se usan actualmente. |
| `docs/029_PROP_DOC_DOCS_ORGANIZATION_1_0_DRAFT.md` | DRAFT | Convencion de organizacion de docs | implementada | **ACTIVE** | La propuesta fue adoptada como convencion estandar del proyecto. |
| `docs/ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md` | DRAFT | Convencion de nombrado y frontmatter | N/A | **ACTIVE** | Es la convencion activa. Debe subir a ACTIVE. |
| `docs/offline_mode.md` | *(sin frontmatter)* | Modo offline del pipeline | si | **ACTIVE** | Describe funcionalidad actual. Agregar frontmatter. |
| `docs/index.md` | *(sin frontmatter)* | Pagina de inicio mkdocs | si | **ACTIVE** | Pagina activa del sitio de documentacion. |
| `docs/onboarding/README.md` | DRAFT | Indice de tutoriales de onboarding | si | **ACTIVE** | Tutoriales que describen el sistema actual. |
| `docs/onboarding/01_pipeline.md` | DRAFT | Tutorial: arquitectura del pipeline | si | **ACTIVE** | Contenido actualizado del pipeline v2.0. |
| `docs/onboarding/02_new_stage.md` | DRAFT | Tutorial: crear nuevo stage | si | **ACTIVE** | Metodologia valida para el sistema actual. |
| `docs/onboarding/03_testing.md` | DRAFT | Tutorial: tests | si | **ACTIVE** | Guia actual de testing. |
| `docs/onboarding/04_debugging.md` | DRAFT | Tutorial: debugging | si | **ACTIVE** | Guia actual de debugging. |
| `docs/architecture/001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md` | DRAFT | Reporte de arquitectura | si | **ACTIVE** | Describe la arquitectura actual del sistema. |
| `docs/diagrams/001_CLASS_DIAGRAM_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de clases | si | **ACTIVE** | Diagrama actual del pipeline. |
| `docs/diagrams/001_CLASS_DIAGRAM_ASCII_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de clases ASCII | si | **ACTIVE** | Diagrama actual. |
| `docs/diagrams/002_USECASE_DIAGRAM_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de casos de uso | si | **ACTIVE** | Diagrama actual. |
| `docs/diagrams/003_SEQUENCE_DIAGRAM_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de secuencia | si | **ACTIVE** | Diagrama actual. |
| `docs/diagrams/004_ACTIVITY_DIAGRAM_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de actividades | si | **ACTIVE** | Diagrama actual. |
| `docs/diagrams/005_STATEMACHINE_DIAGRAM_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de maquina de estados | si | **ACTIVE** | Diagrama actual. |
| `docs/diagrams/006_COMPONENT_DIAGRAM_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de componentes | si | **ACTIVE** | Diagrama actual. |
| `docs/diagrams/007_DEPLOYMENT_DIAGRAM_RECPL_1_0_DRAFT.md` | DRAFT | Diagrama de despliegue | si | **ACTIVE** | Diagrama actual. |
| `docs/diagrams/008_CLASS_DIAGRAM_RECPL_Chatgpt_1_0_DRAFT_.md` | *(sin frontmatter)* | Diagrama generado por ChatGPT | si | **ACTIVE** | Agregar frontmatter. |
| `docs/152_GUIDE_DEV_AGENT_DESIGN_PATTERNS_SUMMARY_1_0_DRAFT.md` | DRAFT | Resumen de patrones GoF (cap 1-9) | N/A | **ACTIVE** | Resumen de referencia util. |
| `docs/153_GUIDE_DEV_AGENT_DESIGN_PATTERNS2_SUMMARY_1_0_DRAFT.md` | DRAFT | Resumen de patrones GoF (cap 10-21) | N/A | **ACTIVE** | Resumen de referencia util. |
| `docs/API/*` | *(sin frontmatter)* | Stubs mkdocstrings | si | **ACTIVE** | Stubs generados para la documentacion API. |

### 3.2. Shell v1.0 — Legacy congelado (status DRAFT correcto)

| Archivo | Claimed | Descripcion | Recomendado | Justificacion |
|---------|---------|-------------|-------------|---------------|
| `docs/007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md` | DRAFT | Plan de implementacion del bot shell | **DRAFT** | Shell existe, pendiente de fusion futura |
| `docs/009_GUIDE_DEV_COMPILER_BOT_IMPL_REPORT_1_0_DRAFT.md` | DRAFT | Reporte de implementacion shell | **DRAFT** | Shell existe, pendiente de fusion |
| `docs/010_GUIDE_DEV_COMPILER_BOT_RUNBOOK_1_0_DRAFT.md` | DRAFT | Runbook shell (superado por 136) | **DRAFT** | Superado parcialmente, pero shell existe |
| `docs/014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md` | DRAFT | Propuesta NLP para shell | **DRAFT** | NLP existe en Python, no en shell; pendiente fusion |
| `docs/030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md` | DRAFT | Reporte integracion LLM shell | **DRAFT** | Shell existe |
| `docs/031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan LLM shell | **DRAFT** | Plan ejecutado, pero shell existe |
| `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` | DRAFT | Propuesta TUI shell | **DRAFT** | TUI existe en agent-robot |
| `docs/041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md` | **ACTIVE** | Reporte debugger shell | **DRAFT** | Debugger shell existe pero es legacy; bajarlo a DRAFT |
| `docs/042_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_RUNBOOK_1_0_DRAFT.md` | DRAFT | Runbook debugger shell | **DRAFT** | Shell existe |
| `docs/043_REP_DEV_COMPILER_BOT_PIPELINE_RE_1_0_DRAFT.md` | DRAFT | RE del pipeline shell | **DRAFT** | Shell existe |
| `docs/048_PLAN_DEV_COMPILER_BOT_AGENT_IMPL_1_0_DRAFT.md` | DRAFT | Plan agent-robot | **DRAFT** | agent-robot existe |
| `docs/049_PLAN_DEV_COMPILER_BOT_AGENT_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan ejecucion agent-robot | **DRAFT** | agent-robot existe |
| `docs/054_PLAN_DEV_COMPILER_BOT_NEXT_STEPS_1_0_DRAFT.md` | DRAFT | Siguientes pasos shell | **DRAFT** | Shell existe |
| `docs/056_REP_DEV_COMPILER_BOT_LLM_AGENT_1_0_DRAFT.md` | DRAFT | Reporte LLM agente F1 | **DRAFT** | Shell existe |
| `docs/057_REP_DEV_COMPILER_BOT_PLANNER_LLM_1_0_DRAFT.md` | DRAFT | Reporte planner LLM | **DRAFT** | Shell existe |
| `docs/058_REP_DEV_COMPILER_BOT_TUI_1_0_DRAFT.md` | DRAFT | Reporte TUI | **DRAFT** | Shell existe |
| `docs/060_REP_DEV_COMPILER_BOT_INCONSISTENCIAS_1_0_DRAFT.md` | DRAFT | Reporte inconsistencias shell | **DRAFT** | Shell existe |
| `docs/061_GUIDE_DEV_COMPILER_BOT_TUI_BEHAVIOR_1_0_DRAFT.md` | DRAFT | Spec comportamiento TUI | **DRAFT** | Shell existe |
| `docs/062_PROP_DEV_COMPILER_BOT_TUI_IMPLEMENTACION_1_0_DRAFT.md` | DRAFT | Propuesta implementacion TUI | **DRAFT** | Shell existe |
| `docs/063_REP_DEV_COMPILER_BOT_TUI_CLEANUP_1_0_DRAFT.md` | DRAFT | Reporte cleanup TUI | **DRAFT** | Shell existe |
| `docs/064_REP_DEV_COMPILER_BOT_TUI_ALTA_1_0_DRAFT.md` | DRAFT | Reporte TUI alta prioridad | **DRAFT** | Shell existe |
| `docs/065_REP_DEV_COMPILER_BOT_APIFREELLM_DEFAULT_1_0_DRAFT.md` | DRAFT | Reporte apifreellm | **DRAFT** | Shell existe |

### 3.3. Plans ejecutados — deben ser IMPLEMENTED

| Archivo | Claimed | Descripcion | Recomendado | Justificacion |
|---------|---------|-------------|-------------|---------------|
| `docs/067_PLAN_DEV_COMPILER_BOT_SCALE_IMPL_1_0_DRAFT.md` | DRAFT | Plan de escalado a Python v2.0 (13 sprints) | **IMPLEMENTED** | Plan ejecutado. Python v2.0 existe |
| `docs/093_PLAN_DEV_SPRINT16_1_0_DRAFT.md` | DRAFT | Plan Sprint 16 | **IMPLEMENTED** | Sprint ejecutado |
| `docs/100_PLAN_DEV_AGENT_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan ejecucion agente N0-N3 | **IMPLEMENTED** | Plan ejecutado |
| `docs/106_PLAN_DEV_PROMPT_CHAIN_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan prompt chain | **IMPLEMENTED** | Plan ejecutado |
| `docs/116_PLAN_DEV_BEHAVIORAL_PATTERNS_REFACTOR_1_0_DRAFT.md` | DRAFT | Plan refactor patrones | **IMPLEMENTED** | Plan ejecutado |
| `docs/122_PLAN_DEV_PATTERNS_REFACTOR_1_0_DRAFT.md` | DRAFT | Plan patrones GoF formales | **IMPLEMENTED** | Plan ejecutado como 123 |
| `docs/123_PLAN_DEV_PATTERNS_ACTION_1_0_DRAFT.md` | DRAFT | Plan accion patrones (Tracks A-C) | **IMPLEMENTED** | Plan ejecutado |
| `docs/126_PLAN_DEV_PIPELINE_FIXES_1_0_DRAFT.md` | DRAFT | Plan fixes pipeline | **IMPLEMENTED** | Fixes aplicados |
| `docs/138_PLAN_DEV_METRICS_DASHBOARD_VERSION_ALIGNMENT_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan dashboard + version alignment | **IMPLEMENTED** | Plan ejecutado |
| `docs/149_PLAN_DEV_REMAINING_ARCHITECTURAL_ITEMS_1_0_DRAFT.md` | DRAFT | Plan items arquitectonicos restantes (P4, P5) | **IMPLEMENTED** | Plan ejecutado |
| `docs/157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md` | DRAFT | Plan implementacion PDCA-sdlc | **IMPLEMENTED** | Plan ejecutado (F1 en adelante) |
| `docs/158_PLAN_DEV_PDCA_SDLC_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan ejecucion PDCA-sdlc F1 | **IMPLEMENTED** | Plan ejecutado |
| `docs/169_PLAN_DEV_PDCA_SDLC_DASHBOARD_1_0_DRAFT.md` | DRAFT | Plan dashboard PDCA-sdlc | **IMPLEMENTED** | Plan ejecutado |
| `docs/172_PLAN_DEV_PDCA_SDLC_EVENTBUS_API_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan EventBus API | **IMPLEMENTED** | Plan ejecutado |

### 3.4. Proposals implementadas — deben ser IMPLEMENTED

| Archivo | Claimed | Descripcion | Recomendado | Justificacion |
|---------|---------|-------------|-------------|---------------|
| `docs/066_PROP_DEV_COMPILER_BOT_SCALE_VISION_1_0_DRAFT.md` | DRAFT | Vision de escalado a Python | **IMPLEMENTED** | Vision implementada como agentic_pipeline |
| `docs/085_PROP_DEV_PIPELINE_DEBUG_REFINE_1_0_DRAFT.md` | DRAFT | Propuesta refine debugger | **IMPLEMENTED** | Implementada |
| `docs/087_PROP_DEV_NLP_INTENT_PIPELINE_1_0_DRAFT.md` | DRAFT | Propuesta NLP + Intent pipeline | **IMPLEMENTED** | Implementada como nlp/ |
| `docs/092_PROP_DEV_MULTI_PERSPECTIVE_IMPLEMENTATION_1_0_DRAFT.md` | DRAFT | Propuesta implementacion multi-perspectiva | **IMPLEMENTED** | Implementada como Tracks A-F |
| `docs/099_PROP_DEV_AGENT_VISION_1_0_DRAFT.md` | DRAFT | Vision agentes N0-N3 | **IMPLEMENTED** | Implementada como agents/ |
| `docs/105_PROP_DEV_PROMPT_CHAIN_REFACTOR_1_0_DRAFT.md` | DRAFT | Propuesta refactor prompt chain | **IMPLEMENTED** | Implementada como prompt_chain/ |
| `docs/120_PROP_DEV_DASHBOARD_MVP_1_0_DRAFT.md` | DRAFT | Propuesta dashboard MVP | **IMPLEMENTED** | Implementada como dashboard/ |
| `docs/121_PLAN_DEV_ARCHITECTURAL_REFACTOR_1_0_DRAFT.md` | DRAFT | Plan refactor arquitectonico (25 problemas) | **IMPLEMENTED** | Ejecutado parcialmente, decisiones ya tomadas |
| `docs/137_PROP_DEV_METRICS_DASHBOARD_AND_VERSION_ALIGNMENT_1_0_DRAFT.md` | DRAFT | Propuesta metrics dashboard | **IMPLEMENTED** | Implementada |

### 3.5. Reports y analysis de features existentes — deben ser IMPLEMENTED

*Nota: `104_GUIDE`, `136_GUIDE` y `176_GUIDE` son guias de referencia viva y permanecen como **ACTIVE** (ver seccion 3.1). Las PROP de ISO 12207 (154-156) se consideran implementadas como PDCA-sdlc.*

| Archivo | Claimed | Descripcion | Recomendado |
|---------|---------|-------------|-------------|
| `docs/086_REP_DEV_DEBUGGER_RUNBOOK_1_0_DRAFT.md` | DRAFT | Runbook debugger Python | **IMPLEMENTED** |
| `docs/089_REP_DEV_SPRINT15_FASE1_2_1_0_DRAFT.md` | DRAFT | Sprint 15 NLP F1+2 | **IMPLEMENTED** |
| `docs/090_REP_DEV_SPRINT15_FASE3_1_0_DRAFT.md` | DRAFT | Sprint 15 NLP F3 | **IMPLEMENTED** |
| `docs/091_REP_MGT_MULTI_PERSPECTIVE_ANALYSIS_1_0_DRAFT.md` | DRAFT | Analisis multi-perspectiva | **IMPLEMENTED** |
| `docs/094_REP_DEV_TRACK_ABC_1_0_DRAFT.md` | DRAFT | Track ABC (v1.1) | **IMPLEMENTED** |
| `docs/096_REP_DEV_TRACK_D_1_0_DRAFT.md` | DRAFT | Track D | **IMPLEMENTED** |
| `docs/097_REP_DEV_TRACK_E_1_0_DRAFT.md` | DRAFT | Track E | **IMPLEMENTED** |
| `docs/098_REP_DEV_TRACK_F_1_0_DRAFT.md` | DRAFT | Track F | **IMPLEMENTED** |
| `docs/101_REP_DEV_AGENT_N1_1_0_DRAFT.md` | DRAFT | Agente N1 | **IMPLEMENTED** |
| `docs/102_REP_DEV_AGENT_N2_1_0_DRAFT.md` | DRAFT | Agente N2 | **IMPLEMENTED** |
| `docs/103_REP_DEV_AGENT_N3_1_0_DRAFT.md` | DRAFT | Agente N3 | **IMPLEMENTED** |
| `docs/104_GUIDE_DEV_AGENT_RUNBOOK_1_0_DRAFT.md` | DRAFT | Runbook agente | **ACTIVE** |
| `docs/107_REP_DEV_PROMPT_CHAIN_F1_1_0_DRAFT.md` | DRAFT | Prompt chain F1 | **IMPLEMENTED** |
| `docs/108_REP_DEV_PROMPT_CHAIN_F2_1_0_DRAFT.md` | DRAFT | Prompt chain F2 | **IMPLEMENTED** |
| `docs/109_REP_DEV_PROMPT_CHAIN_F3_1_0_DRAFT.md` | DRAFT | Prompt chain F3 | **IMPLEMENTED** |
| `docs/110_REP_DEV_PROMPT_CHAIN_F4_1_0_DRAFT.md` | DRAFT | Prompt chain F4 | **IMPLEMENTED** |
| `docs/111_REP_DEV_PROMPT_CHAIN_F5_1_0_DRAFT.md` | DRAFT | Prompt chain F5 | **IMPLEMENTED** |
| `docs/112_REP_DEV_BUGS_FIXES_1_0_DRAFT.md` | DRAFT | Reporte bugs y fixes | **IMPLEMENTED** |
| `docs/113_REP_DEV_STATE_VS_LESSONS_1_0_DRAFT.md` | DRAFT | Estado vs lecciones | **IMPLEMENTED** |
| `docs/114_REP_DEV_ARCHITECTURAL_REVIEW_ISO12207_1_0_DRAFT.md` | DRAFT | Revision arquitectonica ISO 12207 | **IMPLEMENTED** |
| `docs/117_REP_DEV_FASE1_COR_REFACTOR_1_0_DRAFT.md` | DRAFT | F1 Chain of Responsibility | **IMPLEMENTED** |
| `docs/118_REP_DEV_FASE2_COMMAND_REFACTOR_1_0_DRAFT.md` | DRAFT | F2 Command Pattern | **IMPLEMENTED** |
| `docs/119_REP_DEV_FASE3_OBSERVER_REFACTOR_1_0_DRAFT.md` | DRAFT | F3 Observer Pattern | **IMPLEMENTED** |
| `docs/124_REP_DEV_PATTERNS_ACTION_TRACK-A_1_0_DRAFT.md` | DRAFT | Track A Visitor Pattern | **IMPLEMENTED** |
| `docs/125_REP_DEV_PATTERNS_ACTION_TRACK-B_1_0_DRAFT.md` | DRAFT | Track B Mediator+Adapter | **IMPLEMENTED** |
| `docs/128_REP_DEV_PIPELINE_FIXES_VERIFICATION_1_0_DRAFT.md` | DRAFT | Verificacion fixes pipeline | **IMPLEMENTED** |
| `docs/131_REP_DEV_M0_EXECUTION_REPORT_1_0_DRAFT.md` | DRAFT | M0 ejecucion | **IMPLEMENTED** |
| `docs/132_REP_DEV_M1_EXECUTION_REPORT_1_0_DRAFT.md` | DRAFT | M1 ejecucion | **IMPLEMENTED** |
| `docs/133_REP_DEV_M2_EXECUTION_REPORT_1_0_DRAFT.md` | DRAFT | M2 ejecucion | **IMPLEMENTED** |
| `docs/134_REP_DEV_M3_EXECUTION_REPORT_1_0_DRAFT.md` | DRAFT | M3 ejecucion | **IMPLEMENTED** |
| `docs/135_REP_DEV_M4_EXECUTION_REPORT_1_0_DRAFT.md` | DRAFT | M4 ejecucion | **IMPLEMENTED** |
| `docs/136_GUIDE_DEV_PROJECT0_RUNBOOK_1_0_ACTIVE.md` | **ACTIVE** | Runbook activo del proyecto | **ACTIVE** | Correcto |
| `docs/139_REP_DEV_FASE1_VERSION_ALIGNMENT_1_0_DRAFT.md` | DRAFT | F1 Version alignment | **IMPLEMENTED** |
| `docs/139_REP_DEV_PHASE0_PREPARATION_METRICS_DASHBOARD_1_0_DRAFT.md` | DRAFT | F0 Preparacion dashboard | **IMPLEMENTED** | Duplicado ID 139 |
| `docs/140_REP_DEV_FASE2_VERSION_CHECK_SCRIPT_1_0_DRAFT.md` | DRAFT | F2 Version check script | **IMPLEMENTED** |
| `docs/141_REP_DEV_FASE3_CI_INTEGRATION_1_0_DRAFT.md` | DRAFT | F3 CI integration | **IMPLEMENTED** |
| `docs/142_REP_DEV_FASE4_DASHBOARD_SERVICE_1_0_DRAFT.md` | DRAFT | F4 Dashboard service | **IMPLEMENTED** |
| `docs/143_REP_DEV_FASE5_HTTP_SERVER_1_0_DRAFT.md` | DRAFT | F5 HTTP server | **IMPLEMENTED** |
| `docs/144_REP_DEV_FASE6_CLI_DASHBOARD_1_0_DRAFT.md` | DRAFT | F6 CLI dashboard | **IMPLEMENTED** |
| `docs/145_REP_DEV_FASE7_STATIC_UI_1_0_DRAFT.md` | DRAFT | F7 Static UI | **IMPLEMENTED** |
| `docs/146_REP_DEV_FASE8_OPERATIONAL_DOCS_1_0_DRAFT.md` | DRAFT | F8 Operational docs | **IMPLEMENTED** |
| `docs/147_REP_DEV_FASE9_DAILY_GATE_1_0_DRAFT.md` | DRAFT | F9 Daily gate | **IMPLEMENTED** |
| `docs/148_REP_DEV_FASE10_RELEASE_GATE_1_0_DRAFT.md` | DRAFT | F10 Release gate | **IMPLEMENTED** |
| `docs/150_REP_DEV_P4_THREAD_SAFE_STAGESUBJECT_1_0_DRAFT.md` | DRAFT | P4 Thread-safe StageSubject | **IMPLEMENTED** |
| `docs/151_REP_DEV_P5_EVENTBUS_UNIFICATION_1_0_DRAFT.md` | DRAFT | P5 EventBus unification | **IMPLEMENTED** |
| `docs/154_PROP_DEV_ISO12207_AGENT_SYSTEM_ANALYSIS_1_0_DRAFT.md` | DRAFT | Analisis ISO 12207 a sistema agente | **IMPLEMENTED** | Analisis usado para disenar PDCA-sdlc |
| `docs/155_PROP_DEV_ISO12207_AGENT_SYSTEM_REACTIVE_VISION_1_0_DRAFT.md` | DRAFT | Vision reactiva ISO 12207 | **IMPLEMENTED** | Implementada en PDCA-sdlc |
| `docs/156_PROP_DEV_ISO12207_AGENT_SYSTEM_ARCHITECT_IMPL_1_0_DRAFT.md` | DRAFT | Skeleton ISO 12207 | **IMPLEMENTED** | Implementado como PDCA-sdlc |
| `docs/159_REP_DEV_PDCA_SDLC_F1_EXECUTION_1_0_DRAFT.md` | DRAFT | PDCA-sdlc F1 cierre | **IMPLEMENTED** |
| `docs/161_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dias 1-2 | **IMPLEMENTED** |
| `docs/162_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dia 3 | **IMPLEMENTED** |
| `docs/163_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dia 4 | **IMPLEMENTED** |
| `docs/164_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dia 5 | **IMPLEMENTED** |
| `docs/165_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dia 6 | **IMPLEMENTED** |
| `docs/166_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dia 7 | **IMPLEMENTED** |
| `docs/167_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dias 8-9 | **IMPLEMENTED** |
| `docs/168_REP_DEV_PDCA_SDLC_DAILY_1_0_DRAFT.md` | DRAFT | PDCA-sdlc Dia 10 | **IMPLEMENTED** |
| `docs/170_REP_DEV_PDCA_SDLC_DASHBOARD_1_0_DRAFT.md` | DRAFT | Dashboard PDCA-sdlc | **IMPLEMENTED** |
| `docs/171_ANALYSIS_DEV_PDCA_SDLC_EVENTBUS_API_1_0_DRAFT.md` | DRAFT | Analisis EventBus API | **IMPLEMENTED** |
| `docs/173_REP_DEV_PDCA_SDLC_EVENTBUS_FASE_A_1_0_DRAFT.md` | DRAFT | EventBus Fase A | **IMPLEMENTED** |
| `docs/174_REP_DEV_PDCA_SDLC_EVENTBUS_FASE_B_1_0_DRAFT.md` | DRAFT | EventBus Fase B | **IMPLEMENTED** |
| `docs/175_REP_DEV_PDCA_SDLC_EVENTBUS_FASE_C_1_0_DRAFT.md` | DRAFT | EventBus Fase C | **IMPLEMENTED** |
| `docs/176_GUIDE_OPS_PDCA_SDLC_EVENTBUS_DASHBOARD_1_0_DRAFT.md` | DRAFT | Runbook operativo EventBus dashboard | **ACTIVE** |
| `docs/177_REP_DEV_PDCA_SDLC_DASHBOARD_FIXES_1_0_DRAFT.md` | DRAFT | Fixes dashboard PDCA-sdlc | **IMPLEMENTED** |
| `docs/178_ANALYSIS_DEV_COMPREHENSIVE_TECHNICAL_REPORT_1_0_DRAFT.md` | DRAFT | Reporte tecnico comprensivo | **IMPLEMENTED** |

### 3.6. Archive — Sprint reports de Python v2.0 (deben ser IMPLEMENTED)

*Nota: `070_GUIDE_DEV_PYTHON_STYLE` es una guia de referencia viva y permanece como **ACTIVE**.*

| Archivo | Claimed | Descripcion | Recomendado | Justificacion |
|---------|---------|-------------|-------------|---------------|
| `docs/archive/069_REP_DEV_SPRINT1_FOUNDATION_1_0_DRAFT.md` | DRAFT | Sprint 1: Fundacion Python | **IMPLEMENTED** | Documenta componentes actuales (completado) |
| `docs/archive/070_GUIDE_DEV_PYTHON_STYLE_1_0_DRAFT.md` | DRAFT | Guia de estilo Python | **ACTIVE** | Convencion activa (guia de referencia) |
| `docs/archive/071_REP_DEV_SPRINT2_REQUIREMENT_DECOMPOSER_1_0_DRAFT.md` | DRAFT | Sprint 2: RequirementDecomposer | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/072_REP_DEV_SPRINT3_PREPROCESSOR_1_0_DRAFT.md` | DRAFT | Sprint 3: Preprocessor | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/073_REP_DEV_SPRINT4_LEXER_1_0_DRAFT.md` | DRAFT | Sprint 4: Lexer | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/074_REP_DEV_SPRINT5_PARSER_GLR_1_0_DRAFT.md` | DRAFT | Sprint 5: Parser | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/075_REP_DEV_SPRINT6_SEMANTIC_ANALYZER_1_0_DRAFT.md` | DRAFT | Sprint 6: Semantic Analyzer | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/076_REP_DEV_SPRINT7_IR_GENERATOR_1_0_DRAFT.md` | DRAFT | Sprint 7: IR Generator | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/077_REP_DEV_SPRINT8_PLANNER_HIBRIDO_1_0_DRAFT.md` | DRAFT | Sprint 8: Hybrid Planner | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/078_REP_DEV_SPRINT9_SYNTHESIS_1_0_DRAFT.md` | DRAFT | Sprint 9: Synthesis | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/079_REP_DEV_SPRINT10_VALIDATOR_1_0_DRAFT.md` | DRAFT | Sprint 10: Validator | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/080_REP_DEV_SPRINT11_UI_GENERATOR_1_0_DRAFT.md` | DRAFT | Sprint 11: UI Generator | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/081_REP_DEV_SPRINT12_FEEDBACK_1_0_DRAFT.md` | DRAFT | Sprint 12: Feedback Loop | **IMPLEMENTED** | Documenta componente actual (completado) |
| `docs/archive/082_REP_DEV_SPRINT13_BETA_1_0_DRAFT.md` | DRAFT | Sprint 13: Integration + Beta | **IMPLEMENTED** | Documenta estado actual (completado) |

### 3.7. DRAFT correcto — sin implementar o en progreso

| Archivo | Claimed | Descripcion | Recomendado | Justificacion |
|---------|---------|-------------|-------------|---------------|
| `docs/012_PROP_DEV_COMPILER_BOT_FLOW_REFINE_1_0_DRAFT.md` | DRAFT | Refinamiento de flujo multi-stack | **DRAFT** | No implementado |
| `docs/013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` | DRAFT | Core en C | **DRAFT** | No implementado |
| `docs/018_PROP_DEV_COMPILER_BOT_TUTORIAL_EXEC_1_0_DRAFT.md` | DRAFT | Tutorial executor | **DRAFT** | No implementado |
| `docs/022_GUIDE_DEV_LIFECYCLE_FRAMEWORK_1_0_DRAFT.md` | DRAFT | Framework SDLC generico | **DRAFT** | Metodologico, sin implementacion directa |
| `docs/055_PROP_DEV_COMPILER_BOT_HTTP_API_SERVER_1_0_DRAFT.md` | DRAFT | HTTP API server | **DRAFT** | No implementado |
| `docs/115_PLAN_DEV_POST_F5_IMPLEMENTATION_1_0_DRAFT.md` | DRAFT | Post-F5 implementation | **DRAFT** | Parcialmente implementado |
| `docs/127_PROP_DEV_PIPELINE_HTTP_WRAPPER_1_0_DRAFT.md` | DRAFT | HTTP wrapper pipeline | **DRAFT** | No implementado |
| `docs/129_PROP_DEV_ARCHITECTURAL_MIGRATION_1_0_DRAFT.md` | DRAFT | Migracion arquitectonica | **DRAFT** | Parcialmente implementado |
| `docs/130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan ejecucion migracion | **DRAFT** | Parcialmente implementado |
| `docs/159_PLAN_DEV_PDCA_SDLC_F2_EXECUTION_1_0_DRAFT.md` | DRAFT | PDCA-sdlc F2 plan | **DRAFT** | No implementado aun |
| `docs/160_PLAN_DEV_PDCA_SDLC_F3_EXECUTION_1_0_DRAFT.md` | DRAFT | PDCA-sdlc F3 plan | **DRAFT** | No implementado aun |
| `docs/179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md` | DRAFT | Code assistant platform | **DRAFT** | No implementado |
| `docs/180_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md` | DRAFT | Extension cognitiva | **DRAFT** | No implementado |
| `docs/181_PLAN_DEV_CODE_ASSISTANT_F4_EXECUTION_1_0_DRAFT.md` | DRAFT | Plan ejecucion F4 | **DRAFT** | No implementado |

### 3.8. Problemas de integridad

| Problema | Archivos | Accion recomendada |
|----------|----------|--------------------|
| Sin frontmatter | `082_REP_DEV_PROJECT0_COMPREHENSIVE_ANALYSIS`, `127_PROP_DEV_PIPELINE_HTTP_WRAPPER`, `128_REP_DEV_PIPELINE_FIXES_VERIFICATION`, `129_PROP_DEV_ARCHITECTURAL_MIGRATION`, `130_PLAN_DEV_MIGRATION_EXECUTION`, `offline_mode.md`, `docs/index.md`, `docs/diagrams/008_CLASS_DIAGRAM_RECPL_Chatgpt_1_0_DRAFT_.md` | Agregar frontmatter completo + status ACTIVE |
| Duplicado ID 139 | `139_REP_DEV_PHASE0_PREPARATION_METRICS_DASHBOARD` (Phase0) y `139_REP_DEV_FASE1_VERSION_ALIGNMENT` (Fase1) | Mantener ambos con ACTIVE. Renombrar Phase0 a ID unico |
| Duplicado ID 094 | `094_REP_DEV_TRACK_AB_1_0_DRAFT.md` (v1.0, 94 lines) y `094_REP_DEV_TRACK_ABC_1_0_DRAFT.md` (v1.1, 12146 bytes) | v1.0 -> OBSOLETE (superseded por v1.1) |
| Frontmatter casing inconsistente | Varios: `area:DEV` vs `area:dev`, `module:COMPILER_BOT` vs `module:compiler-bot`, `type:GUIDE` vs `type:GUIDE` (ok) | Normalizar: `area: dev`, `module: kebab-case` |
| `docs/archive/027_PROP_DEV_COMPILER_BOT_CLI_FLAGS_1_0_DRAFT.md` | Claimed: IMPLEMENTED (antes no estandar) | **Mantener IMPLEMENTED** — ahora es estandar valido |
| `docs/archive/028_PROP_DEV_COMPILER_BOT_COMPOSITE_1_0_DRAFT.md` | Claimed: IMPLEMENTED (antes no estandar) | **Mantener IMPLEMENTED** — ahora es estandar valido |
| `docs/archive/040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md` | Claimed: IMPLEMENTED (antes no estandar) | **Mantener IMPLEMENTED** — ahora es estandar valido |

## 4. Resumen de cambios recomendados

| Cambio | Cantidad |
|--------|----------|
| DRAFT -> IMPLEMENTED (reports, analysis, props implementadas, plans ejecutados) | ~75 |
| DRAFT -> ACTIVE (guias, specs, convenciones, diagramas) | ~16 |
| ACTIVE -> DRAFT (041 debugger shell) | 1 |
| DRAFT -> OBSOLETE (094 v1.0 superseded por v1.1) | 1 |
| Sin frontmatter -> ACTIVE o IMPLEMENTED | ~8 |
| DRAFT correcto (sin implementar) | ~14 |
| DRAFT correcto (shell legacy, fusion futura) | ~22 |
| Status IMPLEMENTED preexistente validado | 3 (archive) |
| Normalizar casing frontmatter | Muchos |

## 5. Resumen por status recomendado

| Status recomendado | Cantidad de docs | Antes |
|-------------------|-----------------|-------|
| **ACTIVE** | ~22 | ~7 |
| **IMPLEMENTED** | ~75 | 0 (+3 en archive no estandar) |
| **DRAFT** | ~37 | ~95 |
| **OBSOLETE** | ~1 | 0 |
| **Sin frontmatter** | ~8 | ~8 |
| **Total evaluados** | **~143** | |

## 6. Notas finales

- **Ningun documento se elimina o mueve**. Solo cambia el campo `status` en el frontmatter YAML.
- **Jerarquia de criterios**:
  1. `ACTIVE` — documento de referencia viva que debe mantenerse actualizado (guias, runbooks, tutoriales, specs, diagramas, convenciones).
  2. `IMPLEMENTED` — documento historico que describe funcionalidad/codigo implementado al 100%. Ya no se actualiza pero sirve como trazabilidad.
  3. `DRAFT` — documento incompleto, trabajo futuro no realizado, o (caso Shell v1.0) componente legacy congelado pendiente de fusion.
  4. `OBSOLETE` — documento superado por una version mas nueva (ej: v1.0 reemplazada por v1.1).
- **IMPLEMENTED no es lo mismo que OBSOLETE**: IMPLEMENTATED indica que el trabajo descrito fue completado exitosamente; OBSOLETE indica que el documento fue reemplazado y ya no debe consultarse.
- **Transiciones de status esperadas**:
  - Cuando Shell v1.0 se fusione formalmente al sistema: `DRAFT → IMPLEMENTED` (todo el grupo 3.2)
  - Cuando features en DRAFT se implementen: `DRAFT → IMPLEMENTED`
  - Cuando un ACTIVE ya no se mantenga: `ACTIVE → IMPLEMENTED`
  - Solamente cuando un documento tenga una version mas nueva: `IMPLEMENTED → OBSOLETE`
- Los cambios pueden aplicarse por lotes con un script de sed/awk sobre los archivos identificados, seguido de verificacion manual.
- Este audit debe actualizarse cuando cambie el estado del proyecto (ej: si Shell v1.0 se fusiona formalmente, sus docs pasarian de DRAFT a IMPLEMENTED).
