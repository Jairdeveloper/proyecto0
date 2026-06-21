---
id: 013
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - proposal
  - compiler-bot
  - recpl
  - c-core
  - recpl-core
  - rendimiento
  - kernel
  - pipeline
  - nativo
summary: "Propuesta de implementacion de un nucleo en C (recpl-core) para el pipeline del bot RECPL. Reemplaza los scripts shell del frontend/middleend por un binario nativo que ejecuta lexer, parser, semantico e IR en una sola invocacion sin forks. Continuacion de 011 y 012."
keywords:
  - propuesta
  - c
  - recpl-core
  - nativo
  - rendimiento
  - pipeline
  - lexer
  - parser
  - semantico
  - ir
  - grafo
  - contratos
  - api-binaria
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion de la propuesta de implementacion del nucleo C recpl-core
---

# Propuesta de Implementacion: Nucleo C (recpl-core)

> **Continuacion de:** `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` (multi-stack, UI web)
> y `012_PROP_DEV_COMPILER_BOT_FLOW_REFINE_1_0_DRAFT.md` (flujo de datos, refinamiento)
>
> Mientras 011 y 012 definen **que** construimos (stacks, UI, contratos, ciclos),
> esta propuesta define **como ejecutamos** el pipeline: un binario C nativo
> que reemplaza el hot path shell por codigo compilado.

---

## 1. Resumen Ejecutivo

### 1.1 Problema

El pipeline shell actual funciona correctamente para uso interactivo, pero tiene
limitaciones de rendimiento inherentes que se vuelven criticas al escalar:

| Escenario | Shell actual | Problema |
|-----------|-------------|----------|
| UI web con requests concurrentes | ~75ms por request | Tiempo de respuesta visible, bloqueante |
| Pipeline multi-stack (012) | ~150ms con resolucion de contratos | Se acumula por cada version/refinamiento |
| Batch CI con cientos de instrucciones | ~7.5s para 100 prompts | Tiempo de CI innecesariamente alto |
| Regeneracion parcial (012) | ~50ms por deteccion de cambios | Cada edicion en UI requiere recalculo |

Cada llamado a `awk`/`sed`/`grep` implica un `fork+exec` que cuesta ~1-2ms solo
en crear el proceso. El pipeline actual hace **10-20 forks por instruccion**.

### 1.2 Solucion

Un binario C nativo (`recpl-core`) que ejecuta el pipeline completo del frontend
y middleend en **un solo proceso**, comunicandose via stdin/stdout JSON exactamente
igual que los scripts actuales — zero cambios en la interfaz.

```
HOY:                          CON C:
  preprocessor.sh (fork)        recpl-core (1 proceso)
  → lexer.sh (fork)               ├── preprocess
  → parser.sh (fork)              ├── lex (DFA nativo)
  → semantic.sh (fork)            ├── parse (recursive descent)
  → ir_generator.sh (fork)        ├── semantic (hash table)
                                  ├── ir_generate
  = 5 forks + 5 awk procs        └── contract_resolve (grafo)
  ~75ms                            = 1 proceso, ~2ms
```

### 1.3 Beneficios Esperados

| Componente | Shell | C nativo | Mejora |
|------------|-------|----------|--------|
| Lexer (100 tokens) | ~15ms (fork+awk×N) | ~0.5ms | **30x** |
| Parser (AST) | ~10ms (awk+sed×varios) | ~0.3ms | **30x** |
| Semantic (1000 symbols) | ~50ms (grep lineal×N) | ~0.1ms (hash) | **500x** |
| Resolucion contratos (012) | ~100ms (shell arrays) | ~1ms (grafo) | **100x** |
| Pipeline completo | ~75ms | ~2ms | **~35x** |
| Con UI web concurrente (10 req) | ~750ms | ~20ms | **~35x** |
| Batch CI (100 prompts) | ~7.5s | ~200ms | **~35x** |

---

## 2. Arquitectura del Nucleo C

### 2.1 Vision General

```
shell (orquestacion)          C nativo (computo intensivo)
────────────────────          ────────────────────────────
recpl.sh (LOOP)               recpl-core (binario unico)
  ├── recpl.sh ──────→          ├── mode=lex
  ├── (orquesta)                ├── mode=parse
  ├── llamadas a ───→           ├── mode=semantic
  ├── recpl-core                ├── mode=ir
  │                            ├── mode=full (pipeline completo)
  │                            ├── mode=contracts (012)
  │                            └── mode=graph (012)
  │
  synthesis.sh  (shell OK, I/O bound)
  scaffold.sh   (shell OK, I/O bound)
  registry.sh   (shell OK, pocas llamadas)
```

### 2.2 Modos de Operacion

El binario opera por modos, seleccionables via flag `--mode`:

```sh
# Modos actuales (reemplazo 1:1 de los scripts shell)
recpl-core --mode=preprocess    < input.txt       # → texto normalizado
recpl-core --mode=lex           < input.txt       # → tokens JSON
recpl-core --mode=parse         < tokens.json     # → AST JSON
recpl-core --mode=semantic      < ast.json        # → AST + symbol table
recpl-core --mode=ir            < validated.json  # → IR.json
recpl-core --mode=full          < input.txt       # → IR.json (pipeline completo)

# Modos nuevos (012: contratos, grafo)
recpl-core --mode=contracts     < ir.json         # → contratos resueltos
recpl-core --mode=graph         < contracts.json  # → grafo de dependencias
recpl-core --mode=stale         < graph.json      # → archivos stale
recpl-core --mode=diff          < v1.json v2.json # → diff estructural

# Modo servidor (para UI web, 011)
recpl-core --mode=serve         # servidor unix socket / TCP
```

### 2.3 API Binaria (stdin/stdout JSON)

Cada modo lee JSON de stdin y escribe JSON a stdout, exactamente igual que
los scripts shell actuales — **intercambio binario compatible**:

```sh
# Uso actual (shell):
lexer.sh "$input" | parser.sh | semantic.sh | ir_generator.sh

# Uso con C:
recpl-core --mode=full "$input"   # ← mismo resultado, mismo formato
```

### 2.4 Modo Servidor (daemon)

Para la UI web (011) y el ciclo de refinamiento (012), el binario puede
ejecutarse como daemon y comunicarse via socket, eliminando el overhead
de fork por cada request:

```sh
# Iniciar daemon
recpl-core --mode=serve --port=9700 --workers=4

# Cliente (shell o Node.js API):
echo '{"text":"crea modulo payments en nestjs"}' | nc localhost 9700
# → {"ast":{...},"symbol_table":{...}}
```

Arquitectura del daemon:

```
                    ┌──────────────────────────────┐
                    │      API Server (NestJS)      │
                    │  (011 - FASE-E4)              │
                    └──────────┬───────────────────┘
                               │ HTTP/WebSocket
                               ▼
                    ┌──────────────────────────────┐
                    │    recpl-core --mode=serve    │
                    │  ┌────────────────────────┐  │
                    │  │  Worker Pool (4 hilos)  │  │
                    │  │  ┌──────┐ ┌──────┐     │  │
                    │  │  │ wkr1 │ │ wkr2 │ ...  │  │
                    │  │  └──┬───┘ └──┬───┘     │  │
                    │  │     │         │         │  │
                    │  │  ┌──▼─────────▼──┐      │  │
                    │  │  │  Pipeline     │      │  │
                    │  │  │  (preprocess  │      │  │
                    │  │  │   → lex       │      │  │
                    │  │  │   → parse     │      │  │
                    │  │  │   → semantic  │      │  │
                    │  │  │   → ir        │      │  │
                    │  │  │   → contracts │      │  │
                    │  │  │   → graph)    │      │  │
                    │  │  └───────────────┘      │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
```

### 2.5 Comparacion de Flujos

```
FLUJO ACTUAL (shell puro):

  [input] → preprocessor.sh → lexer.sh → parser.sh → semantic.sh → ir_generator.sh → [IR]
              fork+awk        fork+awk   fork+sed    fork+awk      fork+awk
              ~10ms           ~15ms      ~10ms       ~15ms         ~5ms = ~55ms + pipe overhead

FLUJO HIBRIDO (shell orquesta, C ejecuta):

  [input] → recpl-core --mode=full → [IR]
             1 proceso, ~2ms

FLUJO DAEMON (C residente, para UI web):

  [input] → API Server (NestJS) → TCP socket → recpl-core worker → [IR]
             0 forks, ~1ms (worker ya en memoria)
```

---

## 3. Diseno del Binario recpl-core

### 3.1 Estructura de Directorios

```
compiler-bot/
├── core/                          # NUEVO: nucleo C
│   ├── Makefile                   # Build system
│   ├── main.c                     # Entry point, dispatch por modo
│   ├── common.h                   # Estructuras compartidas
│   ├── common.c                   # Utilidades (JSON builder, logging)
│   ├── preprocessor.c             # Modo: preprocess
│   ├── preprocessor.h
│   ├── lexer.c                    # Modo: lex (DFA con maximal munch)
│   ├── lexer.h
│   ├── parser.c                   # Modo: parse (recursive descent LL(1))
│   ├── parser.h
│   ├── semantic.c                 # Modo: semantic (hash table + type check)
│   ├── semantic.h
│   ├── ir_generator.c             # Modo: ir (AST → IR.json)
│   ├── ir_generator.h
│   ├── contracts.c                # Modo: contracts (012: resolucion)
│   ├── contracts.h
│   ├── graph.c                    # Modo: graph (012: dependencias)
│   ├── graph.h
│   ├── server.c                   # Modo: serve (daemon TCP)
│   ├── server.h
│   ├── hash_table.c               # Hash table generica
│   ├── hash_table.h
│   ├── json_builder.c             # Constructor JSON en C
│   ├── json_builder.h
│   ├── token.h                    # Tipos de token (enum)
│   ├── ast.h                      # Estructuras del AST
│   └── test/                      # Tests en C
│       ├── test_lexer.c
│       ├── test_parser.c
│       ├── test_semantic.c
│       ├── test_contracts.c
│       └── run_tests.sh
├── core.h                         # NUEVO: cabecera de integracion shell→C
├── frontend/                      # Existente (coexistencia)
├── middleend/                     # Existente (coexistencia)
├── backend/                       # Existente (sin cambios)
├── stacks/                        # 011 (sin cambios)
├── web/                           # 011 (sin cambios)
├── ui/                            # 011 (sin cambios)
└── recpl.sh                       # Modificado: usar recpl-core si existe
```

### 3.2 Estructuras de Datos Principales

#### Token

```c
// token.h
typedef enum {
    TOKEN_UNKNOWN = 0,
    TOKEN_ACTION_CREATE,
    TOKEN_ACTION_DELETE,
    TOKEN_ACTION_UPDATE,
    TOKEN_ACTION_READ,
    TOKEN_MODULE,
    TOKEN_ENTITY,
    TOKEN_TECH_NESTJS,
    TOKEN_TECH_PRISMA,
    TOKEN_TECH_EXPRESS,    // 011
    TOKEN_TECH_FASTAPI,    // 011
    TOKEN_TECH_REACT,      // 011
    TOKEN_TECH_VUE,        // 011
    TOKEN_TECH_POSTGRES,   // 011
    TOKEN_TECH_MONGODB,    // 011
    TOKEN_TECH_DOCKER,     // 011
    TOKEN_TECH_K8S,        // 011
    TOKEN_TECH_GRAPHQL,    // 011
    TOKEN_TECH_NEXT,       // 011
    TOKEN_TECH_DJANGO,     // 011
    TOKEN_TECH_FLASK,      // 011
    TOKEN_TECH_SPRING,     // 011
    TOKEN_TECH_GIN,        // 011
    TOKEN_TECH_SVELTE,     // 011
    TOKEN_PREP_IN,
    TOKEN_SEPARATOR,
    TOKEN_EOF,
    TOKEN_ERROR
} TokenType;

typedef struct {
    TokenType type;
    char     *lexeme;
    int       line;
    int       col;
} Token;
```

#### AST

```c
// ast.h
typedef struct {
    char **entities;
    int    entity_count;
} ModuloEspec;

typedef struct {
    char **techs;
    int    tech_count;
} OpcionalTech;

typedef struct {
    char        *accion;       // "CREATE" | "DELETE" | "UPDATE" | "READ"
    char        *obj_tipo;      // "module" | "entity"
    ModuloEspec  objetivo;
    OpcionalTech techs;
} ASTNode;
```

#### Symbol Table

```c
// hash_table.h
typedef struct {
    char *name;
    char *tipo;
    char *tech;
    char *estado;
    char *scope;
    char **dependencias;
    int    dep_count;
} SymbolEntry;

typedef struct {
    SymbolEntry *entries;
    int          capacity;
    int          count;
} HashTable;

HashTable *ht_create(int capacity);
void       ht_insert(HashTable *ht, const char *key, SymbolEntry *entry);
SymbolEntry *ht_lookup(HashTable *ht, const char *key);
void       ht_free(HashTable *ht);
```

#### Contract Resolver (012)

```c
// contracts.h
typedef struct {
    char *stack_id;
    char *category;     // "backend" | "frontend" | "db" | "infra"
    char *language;

    // Contratos que ofrece
    char *api_base_url;
    int    api_port;
    char *db_dsn;
    char **env_vars;
    int    env_count;

    // Dependencias
    char **depends_on;
    int    dep_count;
} StackContract;

typedef struct {
    StackContract *stacks;
    int            stack_count;
    int          **adjacency;    // matriz de adyacencia (grafo)
    int           *order;        // orden topologico
} ContractGraph;

ContractGraph *cg_build(StackContract *stacks, int count);
int           *cg_topological_sort(ContractGraph *cg);
void           cg_free(ContractGraph *cg);
```

### 3.3 Main Dispatch

```c
// main.c
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: recpl-core --mode=<mode> [args]\n");
        return 1;
    }

    const char *mode = parse_flag(argv, "--mode");

    if (strcmp(mode, "preprocess") == 0)  return mode_preprocess();
    if (strcmp(mode, "lex") == 0)          return mode_lex();
    if (strcmp(mode, "parse") == 0)        return mode_parse();
    if (strcmp(mode, "semantic") == 0)     return mode_semantic();
    if (strcmp(mode, "ir") == 0)           return mode_ir();
    if (strcmp(mode, "full") == 0)         return mode_full();
    if (strcmp(mode, "contracts") == 0)    return mode_contracts();
    if (strcmp(mode, "graph") == 0)        return mode_graph();
    if (strcmp(mode, "stale") == 0)        return mode_stale();
    if (strcmp(mode, "diff") == 0)         return mode_diff(argc, argv);
    if (strcmp(mode, "serve") == 0)        return mode_serve(argc, argv);

    fprintf(stderr, "Modo desconocido: %s\n", mode);
    return 1;
}
```

### 3.4 Modo Full (Pipeline Completo)

```c
// Pipeline completo: un solo paso, zero forks
int mode_full() {
    char  input[65536];
    int   len = read_stdin(input, sizeof(input));

    // 1. Preprocess
    char *normalized = preprocess(input);

    // 2. Lex
    Token  tokens[256];
    int    n_tokens = lex(normalized, tokens, 256);

    // 3. Parse
    ASTNode ast;
    parse(tokens, n_tokens, &ast);

    // 4. Semantic
    HashTable *symbols = ht_create(64);
    semantic(&ast, symbols);

    // 5. IR
    char *ir_json = generate_ir(&ast, symbols);

    // 6. Output
    printf("%s\n", ir_json);

    // Cleanup
    free(normalized);
    ht_free(symbols);
    free(ir_json);
    return 0;
}
```

---

## 4. Integracion con Propuestas Anteriores

### 4.1 Integracion con 011 (Multi-Stack)

El lexer en C incorpora los 18 tokens TECH_* desde el inicio, eliminando la
necesidad de extender el lexer shell (FASE-E3 de 011 se simplifica):

```
011-FASE-E3 (Parser Multi-Stack):
  Antes:  extender lexer.sh con 15 patrones nuevos (tarea EST-024)
          extender parser.sh con gramatica multi-tech (EST-025)
  Ahora:  los tokens ya estan en recpl-core desde el diseño
          solo queda configurar stack.json → registry.sh
```

### 4.2 Integracion con 012 (Contratos y Grafo)

Los modos `contracts`, `graph` y `stale` son implementaciones C directas de los
algoritmos descritos en 012:

| Concepto 012 | Implementacion C | Estructura |
|-------------|-----------------|------------|
| Resolucion de contratos | `contracts.c` | `ContractGraph` con DFS |
| Grafo de dependencias | `graph.c` | Adjacency list + topological sort |
| Stale detection | `graph.c → graph_affected()` | BFS desde nodo modificado |
| Diff entre versiones | `diff.c` | Tree-walker recursivo |

### 4.3 Compatibilidad hacia atras

Los scripts shell existentes **no se eliminan**. El sistema detecta si
`recpl-core` existe y lo usa; si no, cae al pipeline shell:

```sh
# recpl.sh (modificado)
if command -v recpl-core >/dev/null 2>&1; then
    recpl-core --mode=full "$input"
else
    # fallback shell existente
    input=$(preprocessor.sh "$input")
    tokens=$(lexer.sh "$input")
    ast=$(echo "$tokens" | parser.sh)
    validated=$(echo "$ast" | semantic.sh)
    ir=$(echo "$validated" | ir_generator.sh)
fi
```

---

## 5. Plan de Implementacion

### 5.1 Fases

| Fase | Nombre | Descripcion | Duracion est. |
|------|--------|-------------|---------------|
| **FASE-C1** | Fundacion C | Makefile, estructuras base, JSON builder, hash table | 3-4 dias |
| **FASE-C2** | Lexer en C | DFA con maximal munch, todos los tokens (18 tech) | 3-4 dias |
| **FASE-C3** | Parser en C | Recursive descent LL(1), AST builder | 3-4 dias |
| **FASE-C4** | Semantico en C | Hash table, type checking, validacion techs | 2-3 dias |
| **FASE-C5** | IR Generator en C | AST → IR.json, template mapping | 2-3 dias |
| **FASE-C6** | Modo Full + Integracion | Pipeline completo en un paso, integracion con recpl.sh | 2-3 dias |
| **FASE-C7** | Contratos y Grafo (012) | Contract resolver, dependency graph, stale detection | 4-5 dias |
| **FASE-C8** | Daemon Server | Modo serve, worker pool, socket TCP, integracion API | 3-4 dias |
| **FASE-C9** | Tests y Hardening | Tests unitarios C, regression contra tests shell, valgrind | 3-4 dias |
| **FASE-C10** | Documentacion | README, runbook actualizado, metricas de rendimiento | 1-2 dias |

### 5.2 Tareas Detalladas

#### FASE-C1: Fundacion C

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-001 | Crear Makefile con targets debug/release/test | — | S |
| CORE-002 | Implementar `json_builder.h/c` — API para construir JSON en C | — | M |
| CORE-003 | Implementar `hash_table.h/c` — tabla hash generica (string→void*) | — | M |
| CORE-004 | Implementar `token.h` — enum TokenType + struct Token | — | S |
| CORE-005 | Implementar `ast.h` — structs ASTNode, ModuloEspec, OpcionalTech | — | S |
| CORE-006 | Implementar `common.h/c` — utilidades: read_stdin, parse_flag, log | — | M |
| CORE-007 | Implementar `main.c` — dispatch por modo | CORE-006 | M |
| CORE-008 | Verificar compilacion con `make` y `make test` | CORE-001..007 | S |

#### FASE-C2: Lexer en C

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-009 | Implementar DFA estatico con matriz de transicion | CORE-004 | L |
| CORE-010 | Implementar maximal munch: scan forward, backtrack al ultimo accept | CORE-009 | L |
| CORE-011 | Patrones de tokens: ACTION_CREATE/DELETE/UPDATE/READ | CORE-009 | M |
| CORE-012 | Patrones de tokens: MODULE, ENTITY, PREP_IN, SEPARATOR | CORE-009 | M |
| CORE-013 | Patrones de tokens: 18 TECH_* (todos los de 011) | CORE-009 | M |
| CORE-014 | Manejo de errores lexicos: token no reconocido con posicion | CORE-009 | M |
| CORE-015 | Modo `--mode=lex`: leer stdin, emitir tokens JSON a stdout | CORE-010..014 | M |
| CORE-016 | Benchmark: lexer C vs lexer.sh (1000 iteraciones) | CORE-015 | S |

#### FASE-C3: Parser en C

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-017 | Implementar parser LL(1): `parse_comando()`, `parse_accion()` | CORE-005 | L |
| CORE-018 | Implementar `parse_modulo_espec()` con articulos y PREP opcional | CORE-017 | L |
| CORE-019 | Implementar `parse_opcional_techs()` multi-tech (012) | CORE-017 | M |
| CORE-020 | Construir ASTNode desde tokens consumidos | CORE-017 | M |
| CORE-021 | Manejo de errores sintacticos con mensajes descriptivos | CORE-017 | M |
| CORE-022 | Modo `--mode=parse`: leer tokens JSON, emitir AST JSON | CORE-017..021 | M |
| CORE-023 | Validar contra 47 tests existentes (misma salida que parser.sh) | CORE-022 | M |

#### FASE-C4: Semantico en C

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-024 | Implementar `symbol_table_init/lookup/insert/delete` con HashTable | CORE-003 | M |
| CORE-025 | Implementar scope stack (push/pop/current) | CORE-024 | M |
| CORE-026 | Implementar validacion de tech contra lista blanca | CORE-024 | M |
| CORE-027 | Implementar `semantic_analyze()`: visitar AST, validar + poblar tabla | CORE-025, CORE-026 | L |
| CORE-028 | Modo `--mode=semantic`: emitir AST + symbol table JSON | CORE-027 | M |
| CORE-029 | Soportar `RECPL_STATE_DIR` para persistencia entre invocaciones | CORE-027 | M |

#### FASE-C5: IR Generator en C

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-030 | Implementar `generate_ir()`: mapear accion, tipo, template | CORE-002 | M |
| CORE-031 | Generar trace_id unico | CORE-030 | S |
| CORE-032 | Extraer symbol table snapshot desde HashTable a JSON | CORE-030 | M |
| CORE-033 | Modo `--mode=ir`: emitir IR.json canonico | CORE-030..032 | S |

#### FASE-C6: Modo Full + Integracion

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-034 | Implementar `mode_full()`: preprocess → lex → parse → semantic → ir | CORE-015, CORE-022, CORE-028, CORE-033 | L |
| CORE-035 | Modificar `recpl.sh` para detectar `recpl-core` y delegar | CORE-034 | M |
| CORE-036 | Verificar que `recpl.sh` con `recpl-core` pasa los 47 tests | CORE-035 | M |
| CORE-037 | Benchmark comparativo: shell vs C (publicar resultados) | CORE-036 | S |

#### FASE-C7: Contratos y Grafo (012)

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-038 | Implementar `contracts.h/c` — estructuras StackContract, ContractGraph | CORE-002 | L |
| CORE-039 | Implementar `cg_build()` — construir grafo desde contratos | CORE-038 | L |
| CORE-040 | Implementar `cg_topological_sort()` — orden de scaffolding | CORE-039 | M |
| CORE-041 | Modo `--mode=contracts`: leer IR, resolver contratos, emitir JSON | CORE-039 | M |
| CORE-042 | Implementar `graph_affected()` — BFS desde nodo modificado | CORE-038 | L |
| CORE-043 | Modo `--mode=stale`: leer grafo, detectar archivos stale | CORE-042 | M |
| CORE-044 | Tests de resolucion de contratos (5 escenarios de 012) | CORE-041 | L |

#### FASE-C8: Daemon Server

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-045 | Implementar socket TCP (IPv4 + Unix domain) | — | M |
| CORE-046 | Implementar worker pool con hilos (pthread) | — | L |
| CORE-047 | Modo `--mode=serve`: aceptar conexiones, delegar a workers | CORE-045, CORE-046 | L |
| CORE-048 | Protocolo: leer JSON length-prefixed, responder JSON | CORE-047 | M |
| CORE-049 | Integrar con API Server (NestJS) via socket | CORE-048, FASE-E4 | M |
| CORE-050 | Benchmark: daemon vs fork por request (1000 req simultaneos) | CORE-049 | S |

#### FASE-C9: Tests y Hardening

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-051 | Tests unitarios: json_builder, hash_table | CORE-002, CORE-003 | M |
| CORE-052 | Tests unitarios: lexer (20 casos, incluyendo errores) | CORE-015 | M |
| CORE-053 | Tests unitarios: parser (15 casos) | CORE-022 | M |
| CORE-054 | Tests unitarios: semantic (10 casos) | CORE-028 | M |
| CORE-055 | Tests unitarios: contracts (5 casos de 012) | CORE-041 | M |
| CORE-056 | Regression: mismo output que shell en todos los 47 tests existentes | CORE-034 | L |
| CORE-057 | Valgrind: memory leaks, uso no inicializado, buffer overflows | CORE-051..056 | M |
| CORE-058 | Fuzzing: entradas aleatorias al lexer/parser, detectar crashes | CORE-052, CORE-053 | L |

#### FASE-C10: Documentacion

| ID | Tarea | Depende de | Esfuerzo |
|----|-------|------------|----------|
| CORE-059 | Documentar API del binario (modos, flags, formato JSON) | CORE-034 | M |
| CORE-060 | Actualizar runbook (010) con seccion de C core | CORE-059 | M |
| CORE-061 | Publicar resultados de benchmark (shell vs C) en docs | CORE-037, CORE-050 | S |
| CORE-062 | Diagrama de arquitectura hibrida shell+C | CORE-059 | S |

### 5.3 Grafo de Dependencias entre Fases

```
FASE-C1 (Fundacion)
  │
  ├──→ FASE-C2 (Lexer) ──→ FASE-C3 (Parser) ──→ FASE-C4 (Semantico) ──→ FASE-C5 (IR)
  │                                                                              │
  └──────────────────────────────────────────────────────────────────────────────┤
                                                                                 ▼
                                                                            FASE-C6 (Full + Integracion)
                                                                                 │
                                      ┌──────────────────────────────────────────┤
                                      │                                          │
                                 FASE-C7 (Contratos + Grafo)              FASE-C9 (Tests)
                                      │                                          │
                                 FASE-C8 (Daemon)                                │
                                      │                                          │
                                      └──────────────────────────────────────────┤
                                                                                 ▼
                                                                            FASE-C10 (Documentacion)
```

### 5.4 Relacion con Fases de 011 y 012

```
011-FASE-E3 (Parser Multi-Stack) ──→ se simplifica: CORE-013, CORE-019
012-FASE-F1 (Contratos)           ──→ CORE-038..041 (implementacion C directa)
012-FASE-F3 (Grafo Dependencias)  ──→ CORE-042..043 (implementacion C directa)
012-FASE-F4 (API Refinamiento)    ──→ CORE-045..049 (daemon reemplaza fork por request)
011-FASE-E4 (API Server)          ──→ CORE-049 (integra con daemon via socket)
```

---

## 6. API del Binario (Referencia)

### 6.1 Modos

```
Uso: recpl-core [flags]

Flags generales:
  --mode=MODO       Modo de operacion (requerido)
  --input=FILE      Leer de archivo (defecto: stdin)
  --output=FILE     Escribir a archivo (defecto: stdout)
  --log=FILE        Archivo de log (defecto: stderr)
  --state-dir=DIR   Directorio de estado persistente (para --mode=semantic)

Modos:
  --mode=preprocess    Normalizar texto de entrada
  --mode=lex           Tokenizar texto → tokens JSON
  --mode=parse         Tokens JSON → AST JSON
  --mode=semantic      AST JSON → AST + symbol table JSON
  --mode=ir            AST + symbol table → IR.json
  --mode=full          preprocess + lex + parse + semantic + ir (pipeline completo)
  --mode=contracts     IR.json → contratos resueltos + orden topologico
  --mode=graph         contracts.json → grafo de dependencias
  --mode=stale         grafo.json + archivo editado → archivos stale
  --mode=diff          v1.json v2.json → diff estructural
  --mode=serve         Iniciar daemon (requiere --port)

Flags de daemon:
  --port=PUERTO       Puerto TCP (defecto: 9700)
  --workers=N         Numero de workers (defecto: 4)
  --unix-socket=PATH  Usar Unix socket en vez de TCP
```

### 6.2 Codigos de Salida

| Codigo | Significado |
|--------|-------------|
| 0 | Exito |
| 1 | Error generico |
| 2 | Error lexico (token no reconocido) |
| 3 | Error sintactico (AST mal formado) |
| 4 | Error semantico (undefined, duplicado, tech invalido) |
| 5 | Error de entrada (stdin vacio, JSON mal formado) |
| 6 | Error de argumentos (modo invalido, flags faltantes) |

### 6.3 Ejemplos

```sh
# Pipeline completo (reemplaza 5 scripts)
echo "crea modulo payments en nestjs" | recpl-core --mode=full

# Solo lexer (compatible con parser.sh)
echo "crea modulo payments en nestjs" | recpl-core --mode=lex

# Solo parser (lee tokens de pipe)
lexer.sh "crea modulo payments" | recpl-core --mode=parse

# Resolver contratos multi-stack (012)
recpl-core --mode=contracts < ir.json

# Daemon para UI web
recpl-core --mode=serve --port=9700 --workers=4

# Cliente del daemon
echo '{"text":"crea modulo payments en nestjs"}' | nc localhost 9700
```

---

## 7. Stack Tecnologico

| Tecnologia | Uso | Version |
|------------|-----|---------|
| C11 (ISO/IEC 9899:2011) | Lenguaje del nucleo | C11 |
| POSIX | API de sistema (socket, threads, mmap) | POSIX.1-2008 |
| Make | Build system | — |
| GCC / Clang | Compilador | 11+ / 14+ |
| pthread | Thread pool para daemon | POSIX threads |
| valgrind | Deteccion de memory leaks | 3.20+ |
| gprof / perf | Profiling y benchmark | — |
|规制 | Formato de intercambio | ninguno (JSON manual en C) |

---

## 8. Metricas de Exito

| KPI | Target | Como se mide |
|-----|--------|-------------|
| Tiempo de pipeline completo | < 3ms | `hyperfine 'recpl-core --mode=full < input.txt'` |
| Throughput daemon | > 1000 req/s | `wrk -t4 -c100 http://localhost:9700` |
| Matching con shell | 100% en 47 tests | `diff <(shell_pipeline) <(recpl-core --mode=full)` |
| Memory leaks | 0 | `valgrind --leak-check=full recpl-core ...` |
| Cobertura de tests C | > 85% lineas | `gcov` |
| Tiempo de respuesta UI web | < 50ms (incluyendo red) | Lighthouse / medida manual |

---

## 9. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| JSON manual en C propenso a bugs | Alto | Media | Usar json_builder con API type-safe, tests de fuzzing |
| Buffer overflows en input de usuario | Alto | Baja | Usar `snprintf`, limites estrictos, valgrind en CI |
| Portabilidad: dependencias POSIX no en todos los entornos | Medio | Baja | Encapsular en #ifdef, fallback a shell si no compila |
| Dificultad de mantenimiento vs shell | Medio | Alta | Codigo modular (< 200 lineas por .c), tests exhaustivos |
| Duplicacion de logica (shell + C) | Medio | Alta | Los scripts shell son el fallback, no se mantienen activamente |
| pthread no disponible en algunos entornos | Bajo | Baja | Daemon opcional, modo standalone siempre funciona |

---

## 10. Conclusion

El nucleo C (`recpl-core`) transforma el pipeline de 5 forks y ~75ms en un solo
binario de ~2ms, manteniendo compatibilidad total con la interfaz JSON existente.

**Impacto esperado:**

| Aspecto | Sin C core | Con C core |
|---------|-----------|------------|
| Tiempo de pipeline | ~75ms | ~2ms |
| Forks por instruccion | 5-10 | 0 |
| Procesos concurrentes (UI web) | 5×N (fork por etapa) | N threads (pool) |
| Complejidad del pipeline shell | 5 scripts, ~800 lineas total | 1 binario |
| Mantenibilidad de tokens/gramatica | Editar regex en awk | Editar enum + tabla en C |
| Portabilidad | Cualquier Unix con sh+awk | Cualquier Unix con C11+POSIX |
| Dependencia de compilacion | No necesita compilacion | Necesita `make` para optimo |

**Proximo paso recomendado:** FASE-C1 (Fundacion C) + FASE-C2 (Lexer en C) como
primer entregable: un binario que solo haga `--mode=lex` y pase los mismos tests
que `lexer.sh`. Esto valida la arquitectura antes de invertir en el pipeline completo.
