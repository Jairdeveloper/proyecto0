# AGENTS.md

Repo `@tienda/api` — planned NestJS 11 API backend (no source code yet). Currently in shell-script tooling phase.

## Existing shell scripts

- **`masterindex.sh`** — legacy index generator (1990s troff-style). Reads structured entries, pipes through modular filters (`input.idx → sort → pagenums.idx → combine.idx → format.idx`). Adapter needed for `.md` frontmatter.
- **`spellscheck.sh`** — legacy awk interactive spell checker. Runs `spell`, loops over misspellings, offers C/G/A/H/Q. Patterns to preserve: temp files, confirm-before-save, `.orig` backups, recursive `make_change()`.

Both are **reference code** — adapt (don't rewrite) their patterns.

## Docs directory (`docs/`)

| File | Content |
|---|---|
| `001_DOC_GUIDE_MASTERINDEX_1.0_DRAFT.md` | Original masterindex docs (Dale Dougherty) |
| `002_DOC_GUIDE_SPELLCHECK_1.0_DRAFT.md` | Original spellcheck.awk docs (O'Reilly) |
| `003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md` | Implementation proposal for doc-processor tools |
| `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md` | Proposed doc naming convention |

## Doc naming convention

Format: `[NNN]_[TIPOSEMANTICO]_[AREASEMANTICA]_[MODULO]_[VERSION]_[ESTADO].md`
Example: `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` (was `000_DEV_GUIDE_SHELL_STYLE_1_0_DRAFT.md`).

TIPO (GUIDE, PROP, etc.) precedes AREA (DEV, DOC, etc.).
Existing files still use the old order (`[AREA]_[TIPO]`) — rename when editing.

All `.md` files must have YAML frontmatter: `id, area, type, module, version, status, tags, summary, keywords, changelog`.

## Planned stack (from `prompts/build.txt`)

NestJS 11, TypeScript 5.9 strict, Prisma 5, PostgreSQL 16, Redis 7, Passport JWT, Jest 29.

## Shell script rules

Strict conventions in `000_DEV_GUIDE_SHELL_STYLE_1_0_DRAFT.md`:
- **No `set -e`** — handle errors explicitly at each call site
- **No `eval`** — never
- Always double-quote variables
- 4-space indent, no tabs, max 100 chars/line
- Functions: `snake_case` with `()`, not `function` keyword
- Constants: `SCREAMING_SNAKE_CASE`
- Validate: `bash -n script.sh && shellcheck script.sh`

## State machine pattern (shell workflows)

File-based state via `get_state()` / `set_state()`. Cycle: `analyze → propose → approve → plan → approve → execute → verify`.

## Git

Initialized on `master`, no commits yet. All files untracked.

## RECPL Compiler Bot (`compiler-bot/`)

Shell-based bot that processes natural language as a compiler pipeline (Aho Dragon Book).

### Pipeline stages

```
INPUT → preprocess → lexer → parser → semantic → IR → synthesis → OUTPUT
                        (READ)     (EVAL)              (PRINT)
```

All stages pass data as JSON via stdin/stdout pipes. Persistent symbol table via `RECPL_STATE_DIR`.

### Component map

| File | Function |
|------|----------|
| `frontend/preprocessor.sh` | Normalize input: trim, lowercase, collapse punct, split sentences |
| `frontend/lexer.sh` | DFA tokenizer with maximal munch. Tokens: ACTION_CREATE/DELETE/UPDATE/READ, MODULE, ENTITY, TECH_NESTJS/PRISMA, PREP_IN, SEPARATOR |
| `frontend/parser.sh` | LL(1) recursive descent. Grammar: `comando → accion modulo_espec opcional_tech` |
| `frontend/semantic.sh` | Symbol table (hash) + type checking. Persistente via RECPL_STATE_DIR env var |
| `middleend/ir_generator.sh` | Validated AST → canonical IR.json with action mapping and template resolution |
| `backend/synthesis.sh` | IR.json → bot response JSON (tipo_respuesta, mensaje, payload) |
| `backend/scaffold.sh` | Template rendering: copies template files, replaces `__NAME__`/`__LOWERNAME__` |
| `recpl.sh` | Main LOOP: interactive/batch mode, error recovery, persistent state |
| `tests/run_tests.sh` | Test suite: 47 tests covering all components and integration |

### Template dirs (`templates/`)

- `module-nestjs/` — NestJS module scaffold (controller, service, module)
- `entity-nestjs/` — NestJS entity scaffold
- `module-prisma/` — Prisma model scaffold

### Key design decisions

- **Preprocessor handles case folding** — lexer is case-sensitive, expects lowercase input
- **No `ARTICLE` token type** — article words ("un", "el") are ENTITY tokens recognized contextually in parser
- **Persistent state via env var** — `RECPL_STATE_DIR` points to a directory; semantic.sh reads/writes state files there
- **Symbol table stored on disk** — pipe-safe, processes one AST per invocation
- **Scaffolding writes to `modules/<name>/`** — added to `.gitignore`

### State of tasks

| ID | Component | Status |
|----|-----------|--------|
| TASK-001 | Alphabet/tokens | COMPLETED (in lexer.sh) |
| TASK-002 | DFA lexer | COMPLETED (lexer.sh) |
| TASK-003 | Preprocessor | COMPLETED (preprocessor.sh) |
| TASK-004 | BNF grammar | COMPLETED (in parser.sh) |
| TASK-005 | Recursive descent parser | COMPLETED (parser.sh) |
| TASK-006 | Symbol table | COMPLETED (in semantic.sh) |
| TASK-007 | Semantic analyzer | COMPLETED (semantic.sh) |
| TASK-008 | IR generator | COMPLETED (ir_generator.sh) |
| TASK-009 | Tracer (three-address code) | PENDING |
| TASK-010 | Synthesis/PRINT | COMPLETED (synthesis.sh) |
| TASK-011 | LOOP principal | COMPLETED (recpl.sh) |
| TASK-012 | Scorer (pattern matching) | PENDING |
| TASK-013 | Template scaffolding | COMPLETED (scaffold.sh + templates/) |
| TASK-014 | Tests | COMPLETED (tests/run_tests.sh, 47 tests) |

## Active conventions

- `.opencode/agents/` — agent instruction files (follow ALGP003 AGENTS format)
- `prompts/` — build specs and user prompts for the project
