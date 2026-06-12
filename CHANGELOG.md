# Changelog

Todas las cambios notables de este proyecto se documentan en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] — 2026-06-12

### Added
- `pipeline_debugger.sh` — debugger instrumentado del pipeline RECPL con 5 modos (trace, step, timing, inspect, xtrace) y flag --output
- `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` — propuesta de capa TUI con whiptail
- `docs/040_PROP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_DRAFT.md` — propuesta del debugger de pipeline
- `docs/041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md` — reporte de implementacion del debugger
- `docs/042_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_RUNBOOK_1_0_DRAFT.md` — runbook de uso del debugger
- Seccion 8 "Estado de Implementacion" en `028_PROP`
- Secciones 8 "Observaciones" y 9 "Estado de Implementacion" en `027_PROP`
- Subseccion "CHANGELOG.md" en AGENTS.md con convenciones de anotacion

### Changed
- `docs/027_PROP` status: DRAFT → IMPLEMENTED, version 1.1.0 → 1.2.0, test count 47 → 72
- `docs/040_PROP` status: DRAFT → IMPLEMENTED, tabla de riesgos mejorada con mitigaciones reales del sistema
- INDEX.md actualizado a 44 documentos (GUIDE dev: 9 → 10, REP dev: 9 → 10, PROP dev: 10)

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
