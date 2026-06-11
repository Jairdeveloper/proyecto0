---
id: 016
area: dev
type: PLAN
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - plan
  - execution
  - c-core
  - recpl-core
  - compiler-bot
  - fases
  - tareas
summary: "Plan de ejecucion detallado para la implementacion del nucleo C (recpl-core) del bot RECPL. Describe el orden de implementacion, dependencias entre modulos, criterios de validacion y referencias cruzadas a la propuesta 013."
keywords:
  - plan
  - ejecucion
  - recpl-core
  - c
  - fases
  - tareas
  - dependencias
  - validacion
  - implementacion
changelog:
  - version: 1.0
    date: 2026-06-08
    author: workflow-agent
    description: Creacion del plan de ejecucion para recpl-core basado en 013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md
---

# Plan de Ejecucion: Nucleo C (recpl-core)

> **Referencia:** `013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md`
> **Guia de estilo:** `015_GUIDE_DEV_C_STYLE_1_0_DRAFT.md`

---

## Resumen

Este plan desglosa las 10 fases de la propuesta 013 en pasos concretos de implementacion.
Cada paso incluye: archivos a crear/modificar, criterio de validacion, y referencia
a los scripts shell existentes que deben coincidir en output.

**Estimacion total:** ~25-30 dias (a tiempo parcial)

---

## FASE-C1: Fundacion C (3-4 dias)

### Objetivo
Tener la infraestructura base compilando: Makefile, tipos fundamentales,
utilidades y dispatch principal. Al final el binario compila aunque no haga nada util.

### Paso 1.1 — Crear Makefile
**Archivo:** `compiler-bot/core/Makefile`
**Referencia:** Secciones 7 y 9 de `015_GUIDE_DEV_C_STYLE_1_0_DRAFT.md`

Acciones:
- Crear Makefile con `CC`, `CFLAGS`, `OPT`, `DEBUG`
- Targets: `all`, `release`, `debug`, `test`, `clean`
- Compilar `.c` a `.o` con regla implicita, linkear binario `recpl-core`
- Verificar que `make` y `make debug` compilan (aunque no haya .c aun)

**Validacion:** `make --dry-run` muestra los comandos correctos

### Paso 1.2 — Crear token.h
**Archivo:** `compiler-bot/core/token.h`
**Referencia:** 013 seccion 3.2, lexer.sh lineas 58-69

Nuevos conceptos en C:
- Enum (`typedef enum { ... } TokenType;`)
- Struct (`typedef struct { ... } Token;`)
- Include guard (`#ifndef TOKEN_H`)
- Funcion inline para `token_type_name()`

Acciones:
- Declarar `TokenType` con todos los valores (TOKEN_UNKNOWN a TOKEN_ERROR)
- Declarar `Token` con campos `type`, `lexeme`, `line`, `col`
- Implementar `token_type_name()` que convierte enum a string

**Validacion:** Compila con `gcc -std=c11 -Wall -Werror -c token.h` (header-only)

### Paso 1.3 — Crear ast.h
**Archivo:** `compiler-bot/core/ast.h`
**Referencia:** 013 seccion 3.2, parser.sh lineas 300-316 (formato AST)

Nuevos conceptos:
- Structs anidados
- Punteros a punteros (`char **entities`)
- Funcion auxiliar `ast_free()`

Acciones:
- Declarar `ModuloEspec` (entities, entity_count)
- Declarar `OpcionalTech` (techs, tech_count)
- Declarar `ASTNode` (accion, obj_tipo, objetivo, techs)
- Implementar `ast_free()` que libera toda la memoria interna

**Validacion:** `gcc -std=c11 -Wall -Werror -c ast.h` compila

### Paso 1.4 — Crear json_builder.h y json_builder.c
**Archivos:** `compiler-bot/core/json_builder.h`, `compiler-bot/core/json_builder.c`
**Referencia:** 013 seccion 3.2, ejemplo en seccion 13 de guia C

Nuevos conceptos:
- `malloc`, `calloc`, `realloc`, `free`
- Manejo de `NULL` y errores de memoria
- `snprintf` para construir strings
- Forward declaration de struct (opaque type)

Acciones:
- Declarar `JSONBuilder` como tipo opaco (struct definido en .c)
- Funciones: `jb_create`, `jb_free`, `jb_reset`, `jb_string`
- Funciones de construccion: `jb_begin_object`, `jb_end_object`, `jb_key`, `jb_string_value`, `jb_int_value`, `jb_bool_value`, `jb_null_value`
- Implementar crecimiento dinamico del buffer (realloc con factor 2)
- Implementar escapado de strings (comillas, backslash, newline, tab)

**Validacion:** Escribir un test temporal en main que construya `{"nombre":"test"}` y verifique el string

### Paso 1.5 — Crear hash_table.h y hash_table.c
**Archivos:** `compiler-bot/core/hash_table.h`, `compiler-bot/core/hash_table.c`
**Referencia:** 013 seccion 3.2 (tabla de simbolos)

Nuevos conceptos:
- Arreglo de structs
- Hash function (djb2)
- Linear probing para colisiones
- Puntero generico `void *`

Acciones:
- Declarar `HTEntry` (key, value, active)
- Declarar `HashTable` (entries, capacity, count)
- Funciones: `ht_create`, `ht_free`, `ht_insert`, `ht_lookup`, `ht_contains`, `ht_delete`, `ht_values`
- Implementar hash djb2
- Implementar insercion con linear probing
- Implementar busqueda

**Validacion:** Test rapido: insertar 3 pares, buscar, verificar

### Paso 1.6 — Crear common.h y common.c
**Archivos:** `compiler-bot/core/common.h`, `compiler-bot/core/common.c`
**Referencia:** main.c de 013 seccion 3.3

Nuevos conceptos:
- `fgets`, `stdin`, `stdout`, `stderr`
- `getopt`/parse manual de flags
- Macros de logging

Acciones:
- `read_stdin(char *buf, size_t size)` — leer stdin completo
- `parse_flag(char **argv, const char *flag)` — extraer valor de flag `--flag=valor`
- `parse_int_flag(char **argv, const char *flag, int default_val)` — igual pero entero
- `log_info`, `log_error`, `log_warn` — logging estandar

**Validacion:** Escribir test que pase flags y verifique parseo

### Paso 1.7 — Crear main.c (dispatch basico)
**Archivo:** `compiler-bot/core/main.c`
**Referencia:** 013 seccion 3.3

Nuevos conceptos:
- `main(int argc, char **argv)`
- `strcmp` para comparar strings
- Codigos de salida (`return 0` = exito, `return 1` = error)

Acciones:
- Parsear `--mode` de argv
- Dispatch con if/else if/else
- Por ahora los modos solo imprimen "mode X: not implemented yet"
- Si no hay `--mode`, imprimir uso y return 1

**Validacion:** `./recpl-core --mode=lex` imprime "mode lex: not implemented yet". `./recpl-core` imprime uso.

### Checkpoint FASE-C1
- [ ] `make release` compila sin warnings
- [ ] `make debug` compila con -g
- [ ] `./recpl-core --help` o sin args muestra uso
- [ ] `./recpl-core --mode=lex` responde (aunque sea stub)
- [ ] Todos los `.h` tienen include guards
- [ ] Todas las funciones publicas tienen documentacion

---

## FASE-C2: Lexer en C (3-4 dias)

### Objetivo
Implementar el analizador lexico en C que produzca exactamente los mismos tokens
que `lexer.sh` para cualquier entrada.

### Paso 2.1 — Leer y entender lexer.sh
**Archivo de referencia:** `compiler-bot/frontend/lexer.sh`

Estudiar:
- Como matchea keywords con `awk_match_prefix` (lineas 40-48)
- Como implementa maximal munch (lineas 51-108, loop que queda con el match mas largo)
- Como salta whitespace (lineas 121-127)
- Como maneja errores (lineas 145-149)
- Formato de salida JSON de tokens (linea 140)

Diferencia clave en C: en vez de llamar `awk` por cada token (fork+exec),
todo ocurre en el mismo proceso con un bucle sobre el buffer de caracteres.

### Paso 2.2 — Crear lexer.h
**Archivo:** `compiler-bot/core/lexer.h`

Funciones:
```c
int lex(const char *input, Token *tokens, int max_tokens);
```

Acciones:
- Declarar funcion `lex()` que toma string de entrada, arreglo de tokens y maximo
- Retorna cantidad de tokens encontrados, o -1 en error

### Paso 2.3 — Implementar lexer.c (nucleo)
**Archivo:** `compiler-bot/core/lexer.c`

Nuevos conceptos:
- Arreglos estaticos de strings para keywords
- `strncmp` para comparar prefijos
- Bucles anidados para maximal munch
- Puntero de avance sobre el buffer de entrada

Acciones:

**a) Tabla de keywords**
Crear un arreglo de structs que mapee patron → TokenType:
```c
typedef struct {
    const char *pattern;
    TokenType   type;
} KeywordEntry;
```

Lista completa de patrones (desde lexer.sh + 18 techs de 011):
- ACTION: "creando", "crear", "crea", "generar", "make", "new", "eliminar", "borrar", "delete", "remove", "actualizar", "modificar", "update", "edit", "mostrar", "listar", "get", "show", "read"
- MODULE: "modulo", "module"
- TECH: "nestjs", "prisma", "express", "fastapi", "react", "vue", "postgres", "mongodb", "docker", "k8s", "graphql", "next", "django", "flask", "spring", "gin", "svelte"
- PREP: "en", "para", "de", "in", "for", "of"

**b) Funcion de matching**
```c
int match_keyword(const char *input, TokenType *type, int *length) {
    // Recorrer todas las keywords
    // Para cada una, verificar si input empieza con ese patron (strncmp)
    // Si matchea y es mas largo que el mejor match anterior, guardarlo
    // Al final, si hay match, retornar 1 con type y length
    // Si no, retornar 0
}
```

**c) Funcion principal lex()**
```c
int lex(const char *input, Token *tokens, int max_tokens) {
    int pos = 0, col = 1, count = 0;

    while (input[pos] != '\0' && count < max_tokens) {
        // Saltar whitespace
        if (input[pos] == ' ' || input[pos] == '\t') {
            pos++; col++; continue;
        }

        TokenType type;
        int length;

        if (match_keyword(input + pos, &type, &length)) {
            // Matcheo keyword
            tokens[count].type = type;
            tokens[count].lexeme = strndup(input + pos, length);
            tokens[count].line = 1;
            tokens[count].col = col;
            count++;
            pos += length;
            col += length;
        } else if (input[pos] >= 'a' && input[pos] <= 'z') {
            // ENTITY: palabra generica
            // Avanzar mientras sea letra minuscula
        } else if (strchr(",.;!?", input[pos])) {
            // SEPARATOR
        } else {
            // Error: token no reconocido
            fprintf(stderr, "Error lexico: token no reconocido en col %d: '%c'\n", col, input[pos]);
            pos++; col++;
        }
    }

    return count;
}
```

**d) Funcion match_keyword() detallada**

```c
int match_keyword(const char *input, TokenType *type, int *length) {
    *type = TOKEN_UNKNOWN;
    *length = 0;

    for (int i = 0; i < keyword_count; i++) {
        int plen = strlen(keywords[i].pattern);
        if (strncmp(input, keywords[i].pattern, plen) == 0) {
            // Verificar que no sea prefijo de palabra mas larga
            // (opcional con maximal munch)
            if (plen > *length) {
                *length = plen;
                *type = keywords[i].type;
            }
        }
    }

    return *length > 0 ? 1 : 0;
}
```

### Paso 2.4 — Implementar modo lex
**Modificar:** `main.c`

Acciones:
- Implementar `mode_lex()`:
  1. `read_stdin(input, sizeof(input))`
  2. `lex(input, tokens, MAX_TOKENS)`
  3. Recorrer tokens, imprimir cada uno como JSON: `{"type":"...","lexeme":"...","position":{"line":1,"col":...}}`
  4. Retornar 0

**Validacion:**
```sh
echo "crea modulo pagos en nestjs" | ./recpl-core --mode=lex
# Debe producir mismo output que:
echo "crea modulo pagos en nestjs" | compiler-bot/frontend/lexer.sh
```

### Paso 2.5 — Probar contra tests existentes
Ejecutar los tests de lexer del proyecto:
```sh
compiler-bot/tests/run_tests.sh
# Verificar que las pruebas del lexer (Test 3) pasan
```

Comparar output manualmente:
```sh
echo "crea modulo pagos en nestjs" > /tmp/test_input.txt
./recpl-core --mode=lex < /tmp/test_input.txt > /tmp/c_output.txt
compiler-bot/frontend/lexer.sh "$(cat /tmp/test_input.txt)" > /tmp/sh_output.txt
diff /tmp/c_output.txt /tmp/sh_output.txt
# Debe ser identico
```

### Checkpoint FASE-C2
- [ ] `lex()` produce tokens correctos para "crea modulo pagos en nestjs"
- [ ] `lex()` maneja maximal munch: "crear" > "crea"
- [ ] `lex()` salta whitespace correctamente
- [ ] `lex()` reporta errores para caracteres no reconocidos
- [ ] Salida JSON compatible con parser.sh
- [ ] `make debug` compila sin warnings

---

## FASE-C3: Parser en C (3-4 dias)

### Objetivo
Implementar parser LL(1) recursivo descendente que produzca exactamente el mismo
AST JSON que `parser.sh`.

### Paso 3.1 — Leer parser.sh y entender la gramatica
**Archivo de referencia:** `compiler-bot/frontend/parser.sh`

Gramatica BNF (de parser.sh linea 12-17):
```
comando       → accion modulo_espec opcional_tech
accion        → ACTION_CREATE | ACTION_DELETE | ACTION_UPDATE | ACTION_READ
modulo_espec  → MODULE ARTICLE? ENTITY (PREP ENTITY)*
              | ENTITY
opcional_tech → PREP TECH (SEPARATOR TECH)*
              | ε
```

Funciones del parser.sh a replicar:
- `parse_accion()` → establece `g_accion`
- `parse_modulo_espec()` → establece `g_obj_tipo`, `g_obj_ents`
- `parse_entity_list()` → entidades con PREP opcional
- `parse_opcional_tech()` → establece `g_tech`
- `format_ast()` → produce JSON

### Paso 3.2 — Crear parser.h
**Archivo:** `compiler-bot/core/parser.h`

```c
int parse(const Token *tokens, int token_count, ASTNode *ast);
```

### Paso 3.3 — Implementar parser.c
**Archivo:** `compiler-bot/core/parser.c`

Nuevos conceptos:
- Parser recursivo descendente
- Lookahead de un token
- Manejo de cursor (indice en arreglo de tokens)
- funciones auxiliares: `current_token()`, `advance()`, `expect()`, `match()`

Estructura:
```c
typedef struct {
    const Token *tokens;
    int          count;
    int          cursor;
    ASTNode     *ast;
} Parser;

static Token current(Parser *p) {
    if (p->cursor >= p->count) {
        return (Token){TOKEN_EOF, NULL, 0, 0};
    }
    return p->tokens[p->cursor];
}

static void advance(Parser *p) {
    p->cursor++;
}

static int expect(Parser *p, TokenType type) {
    Token t = current(p);
    if (t.type != type) {
        fprintf(stderr, "Error sintactico: se esperaba %s, se encontro %s\n",
                token_type_name(type), token_type_name(t.type));
        return 0;
    }
    advance(p);
    return 1;
}
```

Funciones de parseo (cada una retorna 0 = exito, -1 = error):
```c
static int parse_accion(Parser *p) {
    Token t = current(p);
    switch (t.type) {
    case TOKEN_ACTION_CREATE:
        p->ast->accion = strdup("CREATE"); advance(p); return 0;
    case TOKEN_ACTION_DELETE:
        p->ast->accion = strdup("DELETE"); advance(p); return 0;
    // ... etc
    default:
        fprintf(stderr, "Error: se esperaba accion\n");
        return -1;
    }
}

static int parse_entity_list(Parser *p) {
    // PREP opcional
    // ENTITY principal
    // (PREP ENTITY)*
}

static int parse_modulo_espec(Parser *p) {
    // MODULE? → determinar si es module o entity
    // parse_entity_list()
}

static int parse_opcional_tech(Parser *p) {
    // PREP TECH (SEPARATOR TECH)*
    // o ε
}

int parse(const Token *tokens, int token_count, ASTNode *ast) {
    Parser p = {tokens, token_count, 0, ast};
    memset(ast, 0, sizeof(*ast));

    if (parse_accion(&p) != 0) return -1;
    if (parse_modulo_espec(&p) != 0) return -1;
    if (parse_opcional_tech(&p) != 0) return -1;

    if (current(&p).type != TOKEN_EOF) {
        fprintf(stderr, "Error: tokens sobrantes\n");
        return -1;
    }

    return 0;
}
```

### Paso 3.4 — Implementar modo parse
**Modificar:** `main.c`

- `mode_parse()`: leer stdin (tokens JSON), parsear, imprimir AST como JSON
- Usar `json_builder` para construir el AST JSON

**Validacion:**
```sh
echo 'crea modulo pagos en nestjs' | ./recpl-core --mode=lex | ./recpl-core --mode=parse
# Debe producir mismo AST que:
echo 'crea modulo pagos en nestjs' | compiler-bot/frontend/lexer.sh | compiler-bot/frontend/parser.sh
```

### Checkpoint FASE-C3
- [ ] `parse()` produce AST correcto para "crea modulo pagos en nestjs"
- [ ] `parse()` maneja entity directa ("listar usuarios")
- [ ] `parse()` maneja PREP opcional
- [ ] `parse()` reporta errores sintacticos
- [ ] Output JSON compatible con semantic.sh

---

## FASE-C4: Semantico en C (2-3 dias)

### Objetivo
Analizador semantico con tabla de simbolos, type checking de techs,
y soporte de scope. Output compatible con `semantic.sh`.

### Paso 4.1 — Leer semantic.sh
**Archivo de referencia:** `compiler-bot/frontend/semantic.sh`

Funciones a replicar:
- `symbol_init`, `symbol_insert`, `symbol_lookup`, `symbol_exists`, `symbol_delete`
- `scope_init`, `scope_push`, `scope_pop`, `scope_current`
- `validate_tech()` — lista blanca de techs
- `semantic_analyzer()` — orquestador

### Paso 4.2 — Crear semantic.h y semantic.c
**Archivos:** `compiler-bot/core/semantic.h`, `compiler-bot/core/semantic.c`

Nuevos conceptos:
- Reutilizar `HashTable` (de CORE-003) para la tabla de simbolos
- `SymbolEntry` como struct con metadatos
- Validacion contra lista blanca

```c
typedef struct {
    char *name;
    char *tipo;
    char *tech;
    char *estado;
    char *scope;
    char **dependencias;
    int    dep_count;
} SymbolEntry;

int semantic_analyze(ASTNode *ast, HashTable *symbols, const char *state_dir);
```

### Paso 4.3 — Implementar modo semantic
**Modificar:** `main.c`

- `mode_semantic()`: leer AST JSON de stdin, parsear tokens, ejecutar semantica
- Emitir JSON con AST + symbol table

### Checkpoint FASE-C4
- [ ] `semantic_analyze()` detecta tech invalido
- [ ] `semantic_analyze()` detecta undefined en READ/DELETE
- [ ] `semantic_analyze()` inserta simbolos en CREATE/UPDATE
- [ ] Output JSON compatible con ir_generator.sh

---

## FASE-C5: IR Generator en C (2-3 dias)

### Objetivo
Generar IR.json canonico a partir del AST validado + symbol table.

### Paso 5.1 — Leer ir_generator.sh
**Archivo de referencia:** `compiler-bot/middleend/ir_generator.sh`

Funciones a replicar:
- `map_action()` → CREATE→scaffold, DELETE→delete, etc.
- `map_template()` → tipo+tech → nombre de template
- `generate_trace_id()` → timestamp+pid
- `generate_ir()` → ensamblar JSON final

### Paso 5.2 — Crear ir_generator.h y ir_generator.c
**Archivos:** `compiler-bot/core/ir_generator.h`, `compiler-bot/core/ir_generator.c`

```c
char *generate_ir(const ASTNode *ast, const HashTable *symbols);
```

### Paso 5.3 — Implementar modo ir
**Modificar:** `main.c`

### Checkpoint FASE-C5
- [ ] IR.json contiene accion, tipo, nombre, tech, template
- [ ] IR.json contiene symbol_table
- [ ] trace_id es unico por invocacion

---

## FASE-C6: Modo Full + Integracion (2-3 dias)

### Objetivo
Pipeline completo en un solo paso: preprocess → lex → parse → semantic → IR.
Integrar con `recpl.sh` para que use `recpl-core` si existe.

### Paso 6.1 — Implementar preprocess en C
**Archivo:** `compiler-bot/core/preprocessor.c`

Nuevos conceptos:
- `ctype.h` (`tolower`, `isspace`)
- `trim()`, `to_lowercase()`, `collapse_punct()`, `split_sentences()`

### Paso 6.2 — Implementar mode_full()
**Modificar:** `main.c`

```c
int mode_full(void) {
    char input[65536];
    int len = read_stdin(input, sizeof(input));
    if (len <= 0) return 1;

    // 1. Preprocess
    char *normalized = preprocess(input);

    // 2. Lex
    Token tokens[256];
    int nt = lex(normalized, tokens, 256);
    free(normalized);

    // 3. Parse
    ASTNode ast;
    if (parse(tokens, nt, &ast) != 0) return 3;

    // 4. Semantic
    HashTable *symbols = ht_create(64);
    if (semantic_analyze(&ast, symbols, NULL) != 0) {
        ht_free(symbols);
        ast_free(&ast);
        return 4;
    }

    // 5. IR
    char *ir_json = generate_ir(&ast, symbols);
    printf("%s\n", ir_json);

    // Cleanup
    free(ir_json);
    ht_free(symbols);
    ast_free(&ast);
    return 0;
}
```

### Paso 6.3 — Modificar recpl.sh
**Archivo:** `compiler-bot/recpl.sh`

Agregar deteccion de `recpl-core`:
```sh
if command -v recpl-core >/dev/null 2>&1; then
    RECPL_CORE="recpl-core"
else
    RECPL_CORE=""
fi

process_instruction() {
    if [ -n "$RECPL_CORE" ]; then
        $RECPL_CORE --mode=full "$1"
    else
        # fallback shell existente
        ...
    fi
}
```

### Paso 6.4 — Validar contra los 47 tests
```sh
compiler-bot/tests/run_tests.sh
```
Todos los tests deben pasar igual que con el pipeline shell.

### Checkpoint FASE-C6
- [ ] `mode_full()` pipeline completo funciona end-to-end
- [ ] `recpl.sh --mode=batch` usa recpl-core si existe
- [ ] Los 47 tests existentes pasan con recpl-core
- [ ] Fallback a shell funciona si recpl-core no existe

---

## FASE-C7: Contratos y Grafo (012) (4-5 dias)

### Objetivo
Implementar resolucion de contratos y grafo de dependencias entre stacks
(propuesta 012). Solo si el proyecto necesita multi-stack aun.

### Referencia
`012_PROP_DEV_COMPILER_BOT_FLOW_REFINE_1_0_DRAFT.md`

### Archivos a crear
- `contracts.h/c` — estructuras StackContract, ContractGraph
- `graph.h/c` — BFS/DFS para dependencias

### Checkpoint
- Resolucion de contratos con orden topologico
- Deteccion de archivos stale
- Tests con 5 escenarios

---

## FASE-C8: Daemon Server (3-4 dias)

### Objetivo
Modo servidor con socket TCP y pool de workers.

### Archivos a crear
- `server.h/c` — socket TCP, accept loop
- Thread pool con pthread

### Checkpoint
- `--mode=serve --port=9700` acepta conexiones
- Workers procesan pipelines en paralelo
- Protocolo JSON length-prefixed

---

## FASE-C9: Tests y Hardening (3-4 dias)

### Objetivo
Tests unitarios en C, regression tests contra shell, valgrind, fuzzing.

### Archivos a crear en `core/test/`
- `test_lexer.c` — 20 casos
- `test_parser.c` — 15 casos
- `test_semantic.c` — 10 casos
- `test_json_builder.c`
- `test_hash_table.c`
- `run_tests.sh` — orquestador

### Validaciones
```sh
valgrind --leak-check=full ./recpl-core --mode=full < input.txt
# 0 leaks, 0 errors

# Regression contra shell
diff <(echo "crea modulo pagos en nestjs" | pipeline_shell) \
     <(echo "crea modulo pagos en nestjs" | ./recpl-core --mode=full)
# Sin diferencias
```

---

## FASE-C10: Documentacion (1-2 dias)

### Archivos a crear/modificar
- `README.md` — actualizar con instrucciones de compilacion
- `docs/010_GUIDE_DEV_COMPILER_BOT_RUNBOOK_1_0_DRAFT.md` — agregar seccion C core
- Documentar API del binario (modos, flags, exit codes)
- Publicar resultados de benchmark shell vs C

---

## Resumen de dependencias

```
FASE-C1 (siempre primero)
  │
  ├──→ C2 (Lexer)
  │      │
  │      └──→ C3 (Parser)
  │             │
  │             └──→ C4 (Semantico)
  │                    │
  │                    └──→ C5 (IR)
  │                           │
  │    ┌──────────────────────┘
  │    ▼
  ├──→ C6 (Full + Integracion)
  │    │
  │    ├──→ C7 (Contratos)  ──→ C8 (Daemon)
  │    │
  │    └──→ C9 (Tests)
  │           │
  │           └──→ C10 (Docs)
  │
  └──→ Las fases C2..C5 pueden implementarse secuencialmente
       (cada una depende de la anterior)
```

**Orden recomendado para empezar:**
1. C1 (Fundacion) — imprescindible
2. C2 (Lexer) — primer modulo funcional, validacion visible
3. C3 (Parser) — segundo modulo
4. C4 (Semantico) — tercer modulo
5. C5 (IR) — cuarto modulo
6. C6 (Full) — integracion final
7. C9 (Tests) — hardening inmediato
8. C7, C8, C10 — opcional segun necesidad
