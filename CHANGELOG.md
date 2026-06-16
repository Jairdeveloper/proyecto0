# Changelog

Todas las cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] — 2026-06-16

### Added
- Fase 4 (Sistema Multi-Agente Prompt-Driven): 5 agentes modificados para usar prompts del chain como primera opcion con fallback rule-based
- SupervisorAgent: usa `ChainOrchestrator` cuando hay `llm`, mantiene delegacion clasica como fallback
- PerceptionAgent: usa `intent_handler` (prompt INTENT) cuando hay `llm`, mantiene spaCy+SentenceTransformers como fallback
- ReasoningAgent: usa `plan_handler` (prompt PLAN) cuando hay `llm`, mantiene GoalTreePlanner como fallback
- ExecutionAgent: usa `generate_handler` (prompt GENERATE) para acciones de generacion cuando hay `llm`, mantiene ToolRegistry como fallback
- ValidatorAgent: usa `verify_handler` (prompt VERIFY) cuando hay `llm`, mantiene WorldModel.query como fallback
- `docs/110_REP_DEV_PROMPT_CHAIN_F4_1_0_DRAFT.md` — reporte de implementacion Fase 4

### Changed
- todos los agentes: `__init__` acepta `llm: LLMBackend | None` (default None, 100% backward compat)
- Suite de tests: 86 totales (71 prompt chain + 15 multiagente), todos PASS, ruff 0 errores

## [2.4.0] — 2026-06-16

### Added
- Fase 3 (Chain Orchestrator): ChainOrchestrator con LangGraph StateGraph, 6 nodos (preprocess→intent→plan→generate→verify→format), routing condicional verify→retry/format, CLI `--chain` flag en `compiler-bot/agentic`
- `prompt_chain/cli.py` — `add_chain_args()` + `run_chain()` para integracion CLI
- `prompt_chain/orchestrator.py` — `ChainOrchestrator` class, `ChainState` TypedDict, `_ensure_prompts_registered()`, 6 nodos async, `_router_verify()` condicional
- `tests/test_chain_orchestrator.py` — 8 tests (full flow, retry, max retries, fallback, debug callback, invalid input, CLI chain flag, CLI no-chain)
- `docs/109_REP_DEV_PROMPT_CHAIN_F3_1_0_DRAFT.md` — reporte de implementacion Fase 3

### Fixed
- `_router_verify`: abort rutea a format en vez de END, asegurando que la cadena siempre produzca `final_output`
- Imports no utilizados removidos de `orchestrator.py` (END, PromptRegistry, Any)

### Changed
- `compiler-bot/agentic`: importa `add_chain_args`/`run_chain`, anade `--chain` flag, routing condicional `if args.chain: ... elif args.debug: ... else: ...`
- Suite de tests: 71 prompt chain tests (8 nuevos F3 + 63 F1+F2), todos PASS

## [2.3.0] — 2026-06-16

### Added
- Nivel 3 completo (Sistema Multiagente Colaborativo): Agent base class con Task/TaskResult/SharedContext/AsyncSharedContext
- 4 agentes especializados: PerceptionAgent (spaCy + SentenceTransformers + WordNet), ReasoningAgent (GoalTreePlanner), ExecutionAgent (ToolRegistry), ValidatorAgent (WorldModel query)
- SupervisorAgent con flujo percibir→razonar→ejecutar→validar y replanificacion en fallo
- 15 tests multiagente (base, perception, reasoning, execution, validator, supervisor)
- `docs/103_REP_DEV_AGENT_N3_1_0_DRAFT.md` — reporte de implementacion Nivel 3

### Changed
- Suite de tests: 556 → 572+ (15 nuevos N3, resto sin cambios)

## [2.2.0] — 2026-06-16

### Added
- Nivel 2.1 completo (Percepcion Enriquecida): SpacyProcessor con POS/lemma/dep/NER, SentenceTransformerClassifier con 5 intenciones por embeddings, WordNet disambiguacion con algoritmo de Lesk
- Nivel 2.2 completo (Planificacion Estrategica): WorldModel con escaneo/query/apply_action, GoalTreePlanner con descomposicion/verificacion/replan (4 templates), Context Engineering con ContextWindow por stage
- 6 nuevos archivos de test: test_spacy_processor, test_sentence_classifier, test_wordnet_disambiguation, test_world_model, test_goal_tree_planner, test_context_engineering
- Dependencias: spacy>=3.7, sentence-transformers>=3.0, nltk>=3.8
- `docs/102_REP_DEV_AGENT_N2_1_0_DRAFT.md` — reporte de implementacion Nivel 2

### Changed
- Suite de tests: 556 → 593
- `preprocessor.py`: SpacyProcessor integrado en act() como etapa opcional
- `perception_unit.py`: SentenceTransformerClassifier como enrichment semantico
- `parser.py`: _select_grammar() usa WordNet para desambiguar terminos ambiguos
- `reasoning_engine.py`: GoalTreePlanner integrado en act() con goal_tree en output
- `orchestrator.py`: build_context() para contexto optimo por stage
- `state_models.py`: ContextWindow dataclass

## [2.1.0] — 2026-06-16

### Added
- Nivel 1 completo (Solucionador de Problemas Conectado) del plan 100
- Renombrado de componentes al frame agente: IntentStage→PerceptionUnit, HybridPlanner→ReasoningEngine, SynthesisOrchestrator→ActionExecutor, PipelineOrchestrator→AgentOrchestrator
- ToolRegistry con 7 herramientas portadas del shell: read_file, write_file, run_command, search_code, generate_code, ask_user, explain
- ConversationalMemory con persistencia JSON, sesiones multiples, export
- AgentLoop con run(), run_interactive(), y registro automatico de herramientas
- Backward compatibilidad: archivos legacy conservados como re-exportadores
- 32 tests nuevos (tool_registry: 12, memory: 10, agent_loop: 7)
- `docs/101_REP_DEV_AGENT_N1_1_0_DRAFT.md` — reporte de implementacion Nivel 1

### Changed
- Suite de tests: 524 → 556
- `state_models.py`: nuevos valores PERCEPTION, REASONING, EXECUTION en Stage enum
- `contracts.py`: nuevas entradas perception, reasoning, execution en STAGE_CONTRACTS

## [2.0.0] — 2026-06-14

### Added
- Python v2.0 declarado stack primario de producción (9,886 líneas, 463+ tests)
- StateGraph completo con 10 PipelineStages conectados secuencialmente
- CLI entrypoint `compiler-bot/agentic` con `--prompt`, `--file`, `--output`, `--stream`
- 6 generadores de código: React, NextJS, Tailwind, Prisma, NestJS, Docker
- UI Generator con Builder pattern (5 pasos), DesignTokens, ResponsiveEngine
- Validator Pipeline con Chain of Responsibility (Syntax, Type, Security)
- Feedback Loop: MetricsStore (SQLite/JSON), GlobalFeedbackLoop, ASTCache
- 6 generadores multi-target (synthesis stage)
- `VERSION` file en raíz del proyecto (2.0.0)
- `ci.sh` con validación: syntax check → ruff → pytest → VERSION
- Tests de integración end-to-end (6 escenarios)
- Arquitectura `providers/` esquelete para LLM

### Changed
- Shell v1.0 congelado como referencia/legacy — no se añaden nuevas features
- C Core archivado en `contrib/c-core-archive/`
- Reportes de sprint individuales movidos a `docs/archive/`
- `AGENTS.md` actualizado con tabla completa de componentes Python

### Fixed
- Path traversal en synthesis stage: `_sanitize_path()` bloquea `../`
- MetricsStore: límite de 1000 entradas por stage (SQLite y JSON)
- RequirementDecomposer: ASTCache LLM evita recomputación en inputs repetidos
- FeedbackLoop legacy restaurado (clase faltante)
- `base_stage.execute()` ahora captura métricas automáticamente

## [1.8.0] — 2026-06-13

### Added
- `compiler-bot/agent-robot/planner.sh` — planificador multi-paso que descompone instrucciones complejas ("crea X y Y") en pasos individuales. Funciones: `planificar()`, `_plan_multi_create()`, `_plan_full_project()`, `ejecutar_plan()`.
- `compiler-bot/agent-robot/tools/tool_search_code.sh` — herramienta de busqueda en codigo fuente via `grep -rn` con respuesta JSON estructurada.
- `memory.sh`: 3 funciones nuevas — `memory_list_sessions()` (listar sesiones), `memory_set_session()` (cambiar sesion), `memory_export()` (exportar memoria a JSON).
- Tests de Fase 3 en `test_agent.sh`: 3 tests nuevos (planner multi-create, memory persistente, tool_search_code). Suite total: 13 tests funcionales.
- `docs/051_REP_DEV_COMPILER_BOT_FASE1_AGENT_FOUNDATION_1_0_DRAFT.md` — reporte de implementacion de Fase 1 (anadido retroactivamente al INDEX).
- `docs/052_REP_DEV_COMPILER_BOT_FASE3_AGENT_PLANNER_MEMORY_1_0_DRAFT.md` — reporte de implementacion de Fase 3.
- INDEX.md actualizado a 54 documentos (REP dev: 12 → 14, doc total: 52 → 54)

### Changed
- `agent.sh`: `classify_intent()` extendido con deteccion de multi-instruccion ("crea X y Y" → plan) y proyecto completo. `execute_intent()`: nuevo caso `plan` que carga planner.sh y ejecuta plan. `format_response()`: soporte para tipo `plan_completed`, y fallback a `.tipo` si no hay `.tipo_respuesta`.
- `planner.sh`: `ejecutar_plan()` envia texto legible a stderr y solo JSON a stdout, para compatibilidad con el pipeline de format_response.
- AGENTS.md: tabla de componentes actualizada con `tool_search_code.sh`, `planner.sh`; tabla de tareas actualizada (14→18 tasks, 13 tests).

### Fixed
- `planner.sh`: parsing de modulos en `_plan_multi_create()` — `tr 'y' ' '` reemplazaba el caracter 'y' dentro de palabras (ej. "payments" → "pa ments"). Reemplazado por `sed` con delimitadores de palabra. `sed 's/en.*$//'` cortaba palabras que contienen "en" (ej. "payments" → "paym"). Reemplazado por `sed 's/ en .*$//'` con espacio delimitador.
- `agent.sh`: patron de deteccion de multi-instruccion corregido de `(y |,).*(crea|...)` a `(crea|...).*(y |,)` para instrucciones donde la accion precede a la conjuncion.

## [1.7.0] — 2026-06-13

### Added
- `compiler-bot/agent-robot/tools/tool_read_file.sh` — herramienta de lectura de archivos con validaciones (ruta, existencia, permisos). Responde JSON con path, lineas, bytes, y contenido.
- `compiler-bot/agent-robot/tools/tool_write_file.sh` — herramienta de escritura de archivos con creacion automatica de directorios y verificacion de permisos.
- `compiler-bot/agent-robot/tools/tool_run_command.sh` — herramienta de ejecucion de comandos del sistema via `sh -c` con medicion de tiempo.
- Tests de Fase 2 en `test_agent.sh`: 3 tests nuevos (read_file, write_file, run_command). Suite total: 10 tests funcionales.
- `docs/050_REP_DEV_COMPILER_BOT_FASE2_AGENT_TOOLS_1_0_DRAFT.md` — reporte de implementacion de Fase 2.
- INDEX.md actualizado a 52 documentos (REP dev: 11 → 12, doc total: 51 → 52)

### Changed
- `agent.sh`: `classify_intent()` y `execute_intent()` extendidos con deteccion y ejecucion de read_file, write_file, run_command. Las detecciones de Fase 2 se ubican antes que RECPL para priorizar patrones especificos ("crea archivo" antes que "crea").
- `agent.sh`: `format_response()` ampliado con manejo de tipos `file_content`, `command_output`, `file_written`. Uso de `printf` en vez de `echo` para compatibilidad con dash.
- `agent.sh`: `main()` usa archivo temporal en vez de `$()` para capturar respuesta de execute_intent, evitando bug de dash + echo + jq.
- `tool_respond.sh`: reescrito a `jq -n --arg` en lugar de heredoc, eliminando riesgo de expansion de shell.

### Fixed
- Compatibilidad con **dash** (`/bin/sh` en Debian/Ubuntu): `echo` en dash interpreta secuencias de escape (`\n`), rompiendo JSON con contenido multilinea. Reemplazado por `printf '%s'` en todas las funciones que procesan JSON.

## [1.6.0] — 2026-06-13

### Added
- `docs/049_PLAN_DEV_COMPILER_BOT_AGENT_EXECUTION_1_0_DRAFT.md` — plan de ejecucion detallado de la capa agent-robot. 4 fases con 25 tareas, pseudocodigo completo de cada archivo (config.sh, bridge.sh, agent.sh, memory.sh, planner.sh, 7 tools, system prompts), comandos de verificacion por tarea, dependencias entre fases, y criterios de exito.
- INDEX.md actualizado a 51 documentos (PLAN dev: 3 → 4)

### Fixed
- `tool_registry.sh`: sintaxis incorrecta `}` → `fi` en bloque `if` de `run_tool()` (linea 72) que causaba error de syntax check
- Dependencia `jq` instalada via binario estatico (jq 1.7.1 linux-amd64) — necesaria para parsing JSON en tool_respond, memory, y tool_registry
- Suite de tests agent-robot: FAIL=0 (0 fallos de 7 tests funcionales)

## [1.5.0] — 2026-06-13

### Added
- `docs/047_PROP_DEV_COMPILER_BOT_AGENT_CONCEPT_1_0_DRAFT.md` — propuesta de nuevo concepto para Proyecto0 como agente de IA open-source multi-proposito. Analisis de viabilidad, arquitectura de agentes, gap analysis, plan de migracion.
- `docs/048_PLAN_DEV_COMPILER_BOT_AGENT_IMPL_1_0_DRAFT.md` — plan de implementacion de la capa agent-robot. Arquitectura, bridge, herramientas del agente, 4 fases con 25 tareas, reglas de diseno (no tocar codigo existente, modo deterministico como capa inferior, solo terminal).
- INDEX.md actualizado a 50 documentos (PLAN dev: 2 → 3, total docs: 49 → 50)

## [1.4.0] — 2026-06-12

### Added
- `pipeline_debugger.sh` — debugger instrumentado del pipeline RECPL con 5 modos (trace, step, timing, inspect, xtrace) y flag --output
- `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` — propuesta de capa TUI con whiptail
- `docs/040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md` — propuesta del debugger de pipeline
- `docs/041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md` — reporte de implementacion del debugger
- `docs/042_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_RUNBOOK_1_0_DRAFT.md` — runbook de uso del debugger
- `docs/043_REP_DEV_COMPILER_BOT_PIPELINE_RE_1_0_DRAFT.md` — reporte de ingenieria inversa del pipeline RECPL
- `docs/044_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_CHEATSHEET_1_0_DRAFT.md` — cheatsheet de comandos del debugger
- `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` — propuesta de provider apifreellm.com
- `docs/046_PROP_DEV_COMPILER_BOT_TIER_ARCHITECTURE_1_0_DRAFT.md` — propuesta de arquitectura free/paid para providers LLM
- Seccion 8 "Estado de Implementacion" en `028_PROP`
- Secciones 8 "Observaciones" y 9 "Estado de Implementacion" en `027_PROP`
- Subseccion "CHANGELOG.md" en AGENTS.md con convenciones de anotacion

### Changed
- `docs/027_PROP` status: DRAFT → IMPLEMENTED, version 1.1.0 → 1.2.0, test count 47 → 72
- `docs/040_PROP` status: DRAFT → IMPLEMENTED, tabla de riesgos mejorada con mitigaciones reales del sistema
- INDEX.md actualizado a 45 documentos (GUIDE dev: 9 → 10, REP dev: 9 → 11, PROP dev: 10)

## [1.3.0] — 2026-06-12

### Added
- `composite_exec()` y `composite_file()` como funciones de estado compartido
- Comandos `source <archivo>` y `exec <instruccion>` en `interactive_mode()` y `batch_mode()`
- Banner y `show_help()` actualizados con source/exec
- Test 12 en `run_tests.sh` (6 aserciones): source archivo valido/inexistente, exec valido/sin-argumento, estado compartido CREATE+READ
- Reportes `037_REP` (Fase 2), `038_REP` (Fase 3)
- checklist de `028_PROP` finalizado como IMPLEMENTED

### Changed
- `file_mode()` refactorizado para delegar en `composite_file()` (DRY)
- `batch_mode()` extendido con soporte para source/exec
- INDEX.md actualizado a 40 documentos
- Suite de tests: 66 → 72

## [1.2.0] — 2026-06-11

### Added
- Integracion con LLMs (Claude y OpenAI) via `--llm` y `--provider`
- `frontend/router.sh`: router inteligente con 3 modos (auto/llm/deterministic)
- `frontend/llm_classifier.sh`: fachada LLM con system prompt y 6 tool schemas
- `middleend/llm_ir_mapper.sh`: mapper de tool calls a IR.json
- `providers/provider_common.sh`, `providers/claude.sh`, `providers/openai.sh`: adapters de proveedor
- `recpl.sh` flags `--llm` y `--provider` combinables con `-c`/`-f`
- `tests/test_router.sh`: 4 tests del router
- Runbook actualizado con seccion "Modo LLM"
- Reportes 030, 032, 033, 034, 035
- `.gitignore` para `.env`

### Changed
- `recpl.sh` v1.1.0 → v1.2.0
- `process_instruction()` ahora usa router en vez de pipeline deterministico fijo
- `show_help()` incluye vars de entorno `RECPL_LLM_*`
- Syntax check cubre 15 scripts (nuevos: router, llm_classifier, llm_ir_mapper, provider_common, claude, openai)
- Suite de tests: 47 → 66

### Fixed
- `mkdir -p` en `run_deterministic` para `RECPL_STATE_DIR`
- Keyword `mostrar` anadido a heuristica del router

## [1.1.0] — 2026-06-11

### Added
- `docs/INDEX.md`: indice maestro por area tematica
- `docs/<area>/INDEX.md`: vistas parciales con backlinks
- `scripts/generate_docs_index.sh`: generador automatico de indices
- Frontmatter YAML a documentos legacy (001, 002, 005)

### Changed
- Archivos renombrados a convencion `NNN_TIPO_AREA_MODULO_VERSION_ESTADO.md`
- `AGENTS.md` y `README.md` actualizados con nuevos nombres de archivo
- 47 tests pasan sin modificaciones

## [1.0.0] — 2026-06-11

### Added
- Banderas `-c`/`--command` y `-f`/`--file` para `recpl.sh`
- 4 modos de operacion: interactivo, batch, comando, archivo
- Documento `027_PROP` con especificacion de CLI flags
- Propuesta de patron composite (`028_PROP`)
- Pipeline teorico (`025_GUIDE`)
- Arquitectura del bucle (`026_GUIDE`)
- Diagnosticos de proyecto (`024_REP`)
- Nucleo C experimental (`recpl-core/`) con stubs: common.c, hash_table.c, json_builder.c, main.c
- Guia de estilo C (`015_GUIDE`), plan de ejecucion C core (`016_PLAN`), guia de aprendizaje C core (`017_GUIDE`)
- Marco de ciclo de vida (`022_GUIDE`)
- Reportes de ingenieria inversa FrameMaker (`019_REP`, `020_REP`), analisis de mercado (`021_REP`)
- 14 nuevos archivos de documentacion (015-028)

### Changed
- `recpl.sh` v1.0.0 → v1.1.0
- `.gitignore` ignora `*.o` y artefactos de recpl-core
- `AGENTS.md` actualizado con objetivo real del proyecto
- Suite de tests se mantiene en 47

## [0.1.0] — 2026-06-07

### Added
- Implementacion inicial del RECPL Compiler Bot
- Pipeline compilador completo: preprocessor, lexer (DFA), parser (LL(1)), semantic, IR generator, synthesis
- Scaffolding NestJS/Prisma via templates
- `recpl.sh` con modo interactivo y batch
- 47 tests cubriendo todas las etapas del pipeline
- Fundacion C core: Makefile, token.h, ast.h, json_builder, hash_table, main dispatch
- 15 documentos de documentacion: guia de estilo shell, propuestas (011/012/013), specs, guias, runbook, AGENTS.md
- Propuesta NLP/Intent (014): intent classifier, NER, slot filler, dialog manager
- Herramientas legacy: masterindex.sh, spellcheck.sh
- Configuracion de agente OpenCode y prompts de build
- `CHANGELOG.md` inicial
