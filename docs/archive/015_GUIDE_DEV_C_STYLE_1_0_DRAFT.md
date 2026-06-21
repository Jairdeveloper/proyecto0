---
id: 015
area: dev
type: guide
module: c-style
version: 1.0
status: DRAFT
tags:
  - c
  - style
  - convention
  - c11
  - posix
  - recpl-core
  - embedded
summary: "Guia de estilo para programacion en C en @Proyecto0. Define convenciones de nomenclatura, estructura de archivos, manejo de memoria, errores y patrones de diseno para el nucleo recpl-core y cualquier otro codigo C del proyecto."
keywords:
  - c
  - c11
  - estilo
  - convencion
  - nomenclatura
  - memoria
  - punteros
  - recpl-core
  - embedded
  - posix
changelog:
  - version: 1.0
    date: 2026-06-08
    author: workflow-agent
    description: Creacion inicial de la guia de estilo C
---

# Guia de Estilo C — @tienda/api

## 0. Filosofia

El codigo C en este proyecto sigue cuatro principios fundamentales:

1. **Explicit memory ownership** — Cada asignacion de memoria tiene un dueno claro. Quien reserva (`malloc`/`calloc`) es responsable de liberar (`free`). Ninguna funcion transfiere propiedad sin documentarlo explicitamente.

2. **Fail early, fail loudly** — Las precondiciones se validan al inicio de cada funcion. Los errores se detectan en el origen, no se propagan silenciosamente. `assert` en debug, `if` en release.

3. **Flat over nested** — Maximo 3 niveles de indentacion por funcion. Si necesitas mas, extrae una funcion auxiliar. Las funciones no superan 50 lineas (salvo el dispatch principal).

4. **Self-documenting types** — Los nombres de tipos, estructuras y funciones deben expresar la intencion sin necesidad de comentarios. Los comentarios explican *por que*, no *que*.

---

## 1. Estandar y compilador

| Aspecto | Estándar | Notas |
|---------|----------|-------|
| Lenguaje | C11 (ISO/IEC 9899:2011) | Usar `-std=c11` |
| Compilador | GCC 11+ o Clang 14+ | Ambos soportados |
| Flags minimos | `-Wall -Wextra -Wpedantic -Werror` | Obligatorio en release |
| Optimizacion | `-O2` release, `-g -DDEBUG` debug | Modos separados en Makefile |
| Extensiones | Solo POSIX.1-2008 | No extensiones de compilador especifico |

Flags de compilacion recomendados en el Makefile:

```makefile
CC      ?= gcc
CFLAGS  ?= -std=c11 -Wall -Wextra -Wpedantic -Werror -Wconversion -Wshadow
OPT     ?= -O2
DEBUG   ?= -g -DDEBUG -fsanitize=address -fsanitize=undefined
LIBS    := -lm
```

---

## 2. Estructura del archivo

### 2.1 Orden de secciones en `.c`

```
1. #include "header.h"          (header propio primero)
2. #include <stdio.h>           (headers de sistema en orden alfabetico)
3. #include <stdlib.h>
4. #include "project_header.h"  (headers del proyecto)
5.
6. #define INTERNAL_CONSTANT  42 (constantes internas)
7.
8. typedef struct {             (tipos privados)
9.     int field;
10. } InternalType;
11.
12. /* --- Funcion auxiliar --- */
13. static void helper_function(void);
14.
15. /* --- Funcion publica --- */
16. void public_function(void);
```

### 2.2 Orden de secciones en `.h`

```
1. #ifndef HEADER_H            (include guard)
2. #define HEADER_H
3.
4. #include <stddef.h>          (dependencias)
5.
6. #ifdef __cplusplus
7. extern "C" {
8. #endif
9.
10. /* --- Constantes publicas --- */
11. #define PUBLIC_CONSTANT 42
12.
13. /* --- Tipos publicos --- */
14. typedef struct {
15.     int field;
16. } PublicType;
17.
18. /* --- Funciones publicas --- */
19. void public_function(int arg);
20.
21. #ifdef __cplusplus
22. }
23. #endif
24. #endif
```

### 2.3 Separadores visuales

```
/* ============================================================================
 * SECTION HEADER
 * ============================================================================ */
```

```
/* --- Sub-section --- */
```

### 2.4 Include guards

Usar `NOMBRE_H` en mayusculas con guion bajo, basado en el nombre del archivo:

```c
// archivo: json_builder.h
#ifndef JSON_BUILDER_H
#define JSON_BUILDER_H
...
#endif
```

---

## 3. Convenciones de nomenclatura

### 3.1 Archivos

```
snake_case.c
snake_case.h
```

**Regla:** Un `.c` y un `.h` por modulo. El `.h` define la API publica, el `.c`
implementa los detalles privados. Funciones y tipos internos llevan `static`.

### 3.2 Constantes y macros

```
SCREAMING_SNAKE_CASE — macros del preprocesador y constantes numericas.
```

```c
#define MAX_TOKEN_COUNT 256
#define GROWTH_FACTOR   2
#define JSON_BUF_INIT   256
```

### 3.3 Tipos (typedef, struct, enum)

```
snake_case_t — sufijo _t para tipos definidos con typedef.
```

```c
typedef int          token_type_t;
typedef struct {     Token;
    token_type_t type;
    char         *lexeme;
    int           line;
    int           col;
} Token;

typedef enum {
    TOKEN_UNKNOWN = 0,
    TOKEN_ACTION_CREATE,
    TOKEN_EOF
} TokenType;
```

**Reglas:**
- `struct` anonimo dentro de `typedef` — no repetir el nombre
- Enumeraciones en `SCREAMING_SNAKE_CASE` con prefijo del tipo
- Sufijo `_t` solo para `typedef`, no para `struct`/`enum` tags

### 3.4 Funciones

```
snake_case — verbo al inicio, sustantivo despues.
```

```c
// Correcto
int  tokenize_input(const char *text, Token *tokens, int max_tokens);
void ht_insert(HashTable *ht, const char *key, void *value);
int  read_stdin(char *buf, size_t size);
void json_builder_reset(JSONBuilder *jb);

// Incorrecto
int tokenizefunc(const char *text, Token *tokens, int max);
void HT_INSERT(HashTable *ht, const char *key, void *value);
```

**Prefijos por modulo:**
```c
// json_builder.h
JSONBuilder *jb_create(size_t initial_cap);
void         jb_free(JSONBuilder *jb);

// hash_table.h
HashTable *ht_create(int capacity);
void       ht_free(HashTable *ht);
```

### 3.5 Variables

```
snake_case — descriptiva, sin abreviaturas.
```

```c
// Correcto
int    token_count;
char  *normalized_text;
FILE  *log_file;
size_t buffer_size;

// Incorrecto
int    tc;
char  *nt;
FILE  *f;
size_t bs;
```

### 3.6 Nombres prohibidos

- No `x`, `y`, `z`, `tmp`, `buf`, `ptr`, `data` como unico nombre
- No nombres de una sola letra (salvo `i`, `j` en bucles cortos)
- No usar `reservado` o `val` como nombre generico
- No prefijo `_` (reservado por el estandar)
- No nombres en hungarian notation (`pchBuffer`, `dwFlags`)

---

## 4. Formato y espaciado

### 4.1 Indentacion

- Usar **4 espacios** por nivel (NO tabs)
- Maximo **100 caracteres** por linea
- Llaves en la misma linea (K&R style):

```c
// Correcto
void function(int arg) {
    if (arg > 0) {
        process(arg);
    } else {
        handle_error("negative");
    }
}

// Incorrecto
void function(int arg)
{
    if (arg > 0)
    {
        process(arg);
    }
}
```

### 4.2 Estructuras de control

```c
// if-else
if (condition) {
    do_something();
} else {
    do_other();
}

// for
for (int i = 0; i < count; i++) {
    process(items[i]);
}

// while
while (remaining > 0) {
    remaining = consume(buffer, remaining);
}

// switch
switch (type) {
case TOKEN_ACTION_CREATE:
    handle_create();
    break;
case TOKEN_EOF:
    return 0;
default:
    return -1;
}
```

### 4.3 Punteros

El `*` pegado al nombre de la variable (no al tipo):

```c
// Correcto
int  *pointer;
char *string;
void (*callback)(int);

// Incorrecto
int* pointer;
char * string;
```

### 4.4 Funciones con muchos parametros

Si una funcion tiene mas de 4 parametros, alinear verticalmente:

```c
int parse_tokens(const Token  *tokens,
                 int           token_count,
                 ASTNode      *ast,
                 HashTable    *symbols,
                 int           flags);
```

---

## 5. Manejo de memoria

### 5.1 Reglas generales

- Toda asignacion con `malloc`/`calloc`/`realloc` debe tener su `free` correspondiente
- Inicializar punteros a `NULL` despues de `free`
- Preferir `calloc` sobre `malloc` para estructuras (zero-initialized)
- Usar `sizeof(*ptr)` en vez de `sizeof(StructType)`:

```c
// Correcto (type-safe si el tipo de ptr cambia)
Token *tokens = calloc(count, sizeof(*tokens));

// Incorrecto (fragil si el tipo cambia)
Token *tokens = calloc(count, sizeof(Token));
```

### 5.2 Ownership explicito

Documentar quien libera la memoria:

```c
// La funcion crea y retorna un string. El llamador es responsable de free().
char *token_type_name(TokenType t) {
    char *name = malloc(32);
    if (!name) return NULL;
    snprintf(name, 32, "%d", t);
    return name;  // caller frees
}

// La funcion recibe ownership. jb_free() libera el buffer interno y el struct.
JSONBuilder *jb_create(size_t initial_cap) {
    JSONBuilder *jb = calloc(1, sizeof(*jb));
    if (!jb) return NULL;
    jb->buf = malloc(initial_cap);
    ...
    return jb;
}
void jb_free(JSONBuilder *jb) {
    if (jb) {
        free(jb->buf);
        free(jb);
    }
}
```

### 5.3 Patron de error con cleanup

Para funciones que reservan multiples recursos:

```c
int process_data(const char *input) {
    int   ret = -1;
    char *buf = NULL;
    FILE *fp  = NULL;

    buf = malloc(1024);
    if (!buf) goto cleanup;

    fp = fopen(input, "r");
    if (!fp) goto cleanup;

    if (fread(buf, 1, 1024, fp) < 0) goto cleanup;

    ret = 0;  // exito

cleanup:
    free(buf);
    if (fp) fclose(fp);
    return ret;
}
```

**Alternativa** (sin goto, para casos simples):

```c
int process_data_simple(const char *input) {
    char *buf = malloc(1024);
    if (!buf) return -1;

    int result = do_work(buf);
    free(buf);
    return result;
}
```

### 5.4 Buffer overflow prevention

- Usar `snprintf` en vez de `sprintf`
- Usar `strncpy`/`strncat` en vez de `strcpy`/`strcat`
- Pasar siempre el tamaño del buffer como parametro:

```c
int read_stdin(char *buf, size_t size) {
    if (!buf || size == 0) return -1;

    size_t i = 0;
    int c;
    while ((c = getchar()) != EOF && i < size - 1) {
        buf[i++] = (char)c;
    }
    buf[i] = '\0';
    return (int)i;
}
```

---

## 6. Manejo de errores

### 6.1 Codigos de retorno

| Tipo de funcion | Convencion |
|-----------------|------------|
| Funcion que retorna exito/fallo | `0` = exito, `-1` = error (o codigo negativo especifico) |
| Funcion que retorna cantidad | `>= 0` = valor valido, `-1` = error |
| Funcion que retorna puntero | `NULL` = error; `errno` debe estar seteado |
| Funcion booleana | `int`: `0` = falso, `1` = verdadero |

```c
int  do_something(void);         // 0 ok, -1 error
int  read_tokens(const char *s); // cantidad de tokens, -1 error
void *allocate(size_t n);        // puntero o NULL
int  is_valid(TokenType t);      // 0 no, 1 si
```

### 6.2 Validacion de precondiciones

Toda funcion publica valida sus argumentos al inicio:

```c
int ht_insert(HashTable *ht, const char *key, void *value) {
    if (!ht || !key) return -1;

    // ...
}
```

### 6.3 Assertions (debug only)

```c
#include <assert.h>

void json_builder_begin_object(JSONBuilder *jb) {
    assert(jb != NULL);  // solo en debug
    assert(jb->buf != NULL);
    // ...
}
```

En release, `assert` se elimina con `-DNDEBUG`. Las validaciones que deben
permanecer en release usan `if` explicito.

---

## 7. Archivos de cabecera

### 7.1 Encapsulamiento

- En el `.h` solo va la API publica: typedefs, structs completos si son parte
  de la API, prototipos de funciones publicas, constantes publicas.
- Structs internos se declaran como forward declaration en el `.h` y se
  definen completamente en el `.c`:

```c
// json_builder.h
typedef struct JSONBuilder JSONBuilder;

JSONBuilder *jb_create(size_t initial_cap);
void         jb_free(JSONBuilder *jb);

// json_builder.c
struct JSONBuilder {
    char *buf;
    size_t cap;
    size_t len;
    int    depth;
    int    need_comma;
};
```

### 7.2 Includes minimos

- Incluir solo lo que el archivo necesita directamente
- NO incluir por transitividad — cada `.h` debe ser autocontenido
- Usar forward declarations para reducir dependencias:

```c
// parser.h
#include "token.h"     // Token, TokenType (necesario para prototipos)

typedef struct ASTNode ASTNode;  // forward decl, no necesita ast.h

int parse_tokens(const Token *tokens, int count, ASTNode *ast);
```

---

## 8. Comentarios y documentacion

### 8.1 Comentarios de funcion (Doxygen-style)

```c
/**
 * Create a new JSON builder.
 *
 * Allocates and initializes a JSONBuilder with at least `initial_cap` bytes.
 * The caller is responsible for calling jb_free().
 *
 * @param initial_cap  Initial buffer capacity (0 = use default).
 * @return             Pointer to new JSONBuilder, or NULL on allocation failure.
 */
JSONBuilder *jb_create(size_t initial_cap);
```

### 8.2 Comentarios en linea

Explicar *por que*, no *que*:

```c
// Correcto: explica la razon
tokens[pos] = '\0';  /* null-terminate: strtok requires it */

// Incorrecto: explica lo obvio
i = i + 1;  /* incrementar i */
```

### 8.3 Comentarios de seccion

```c
/* ============================================================================
 * DFA State Machine
 * ============================================================================ */

/* --- Transition table --- */
```

---

## 9. Makefile conventions

### 9.1 Estructura base

```makefile
CC      ?= gcc
CFLAGS  ?= -std=c11 -Wall -Wextra -Wpedantic -Werror -Wconversion -Wshadow
OPT     ?= -O2
DEBUG   ?= -g -DDEBUG -fsanitize=address -fsanitize=undefined
LIBS    := -lm

SRC := $(wildcard *.c)
OBJ := $(SRC:.c=.o)
TARGET := recpl-core

.PHONY: all release debug test clean

all: release

release: CFLAGS += $(OPT)
release: $(TARGET)

debug: CFLAGS += $(DEBUG)
debug: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LIBS)

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

test: debug
	@./run_tests.sh

clean:
	rm -f $(OBJ) $(TARGET)
```

### 9.2 Targets obligatorios

| Target | Descripcion |
|--------|-------------|
| `all` | Compila release |
| `release` | Compilacion optimizada (-O2) |
| `debug` | Compilacion con simbolos y sanitizers |
| `test` | Compila en debug y ejecuta tests |
| `clean` | Elimina artefactos de compilacion |

---

## 10. Seguridad

### 10.1 Entrada de usuario

- Nunca confiar en entrada externa (stdin, archivos, sockets)
- Validar rangos, tamaños y formatos antes de procesar
- Usar buffers con tamaño fijo conocido; si es variable, limitar:

```c
#define MAX_INPUT_SIZE 65536

int mode_full(void) {
    char input[MAX_INPUT_SIZE];
    int  len = read_stdin(input, sizeof(input));
    if (len < 0) return 1;
    // ...
}
```

### 10.2 Funciones peligrosas prohibidas

| Prohibido | Alternativa segura |
|-----------|-------------------|
| `gets()` | `fgets()` |
| `strcpy()` | `strncpy()` o `snprintf()` |
| `strcat()` | `strncat()` o `snprintf()` |
| `sprintf()` | `snprintf()` |
| `scanf("%s", ...)` | `fgets()` + parse manual |
| `system()` | `fork()` + `exec()` o POSIX `popen()` |
| `alloca()` | `malloc()` |

### 10.3 Buffer overflow prevention checklist

- [ ] `snprintf` usa `sizeof(buf)` o el tamaño exacto
- [ ] Ninguna funcion de la lista prohibida aparece en el codigo
- [ ] Bucles de copia verifican limites antes de escribir
- [ ] Strings null-terminated despues de toda operacion

---

## 11. Pruebas

### 11.1 Estructura de tests

```
core/
├── test/
│   ├── test_lexer.c
│   ├── test_parser.c
│   ├── test_semantic.c
│   ├── test_json_builder.c
│   ├── test_hash_table.c
│   └── run_tests.sh
```

### 11.2 Framework de tests (assert simple)

```c
#include <stdio.h>
#include <string.h>

static int tests_passed = 0;
static int tests_failed = 0;

#define TEST(name, expr) do {                                   \
    if (!(expr)) {                                              \
        fprintf(stderr, "  FAIL: %s (%s:%d)\n",                 \
                name, __FILE__, __LINE__);                      \
        tests_failed++;                                         \
    } else {                                                    \
        printf("  PASS: %s\n", name);                           \
        tests_passed++;                                         \
    }                                                           \
} while (0)

#define TEST_STR_EQ(name, got, expected) \
    TEST(name, strcmp(got, expected) == 0)

#define TEST_INT_EQ(name, got, expected) \
    TEST(name, (got) == (expected))
```

### 11.3 Convenciones de tests

- Un archivo de test por modulo (`test_lexer.c` para `lexer.c`)
- Tests independientes (no compartir estado entre tests)
- Nombrar tests como `test_<funcion>_<escenario>`:

```c
void test_jb_create_null_on_zero_size(void) {
    JSONBuilder *jb = jb_create(0);
    TEST("jb_create with 0 size", jb != NULL);
    jb_free(jb);
}

void test_jb_begin_end_object(void) {
    JSONBuilder *jb = jb_create(256);
    jb_begin_object(jb);
    jb_end_object(jb);
    TEST("empty object", strcmp(jb_string(jb), "{\n}") == 0);
    jb_free(jb);
}
```

---

## 12. Modulos y patrones especificos del proyecto

### 12.1 Estructura de un modulo

```
core/
├── lexer.h           # API publica del modulo lexer
├── lexer.c           # Implementacion del DFA
├── parser.h          # API publica del modulo parser
├── parser.c          # Implementacion del recursive descent
├── hash_table.h      # API publica (generica, reutilizable)
├── hash_table.c      # Implementacion
├── json_builder.h    # API publica (generica, reutilizable)
├── json_builder.c    # Implementacion
├── common.h          # Utilidades compartidas
├── common.c
├── Makefile
└── test/
```

### 12.2 main.c — patron de dispatch

El punto de entrada debe ser un dispatcher minimalista:

```c
#include "common.h"
#include "lexer.h"
#include "parser.h"
#include "semantic.h"
#include "ir_generator.h"

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: recpl-core --mode=<mode>\n");
        return 1;
    }

    const char *mode = parse_flag(argv, "--mode");
    if (!mode) {
        fprintf(stderr, "Error: --mode is required\n");
        return 1;
    }

    if (strcmp(mode, "preprocess") == 0)  return mode_preprocess();
    if (strcmp(mode, "lex") == 0)          return mode_lex();
    if (strcmp(mode, "parse") == 0)        return mode_parse();
    if (strcmp(mode, "semantic") == 0)     return mode_semantic();
    if (strcmp(mode, "ir") == 0)           return mode_ir();
    if (strcmp(mode, "full") == 0)         return mode_full();

    fprintf(stderr, "Unknown mode: %s\n", mode);
    return 1;
}
```

### 12.3 Modo servidor (daemon)

Para modos que requieren persistencia (serve, daemon):

```c
int mode_serve(int argc, char **argv) {
    int port = parse_int_flag(argv, "--port", 9700);
    int workers = parse_int_flag(argv, "--workers", 4);

    return run_server(port, workers);
}
```

---

## 13. Ejemplo completo: Modulo json_builder

### json_builder.h

```c
#ifndef JSON_BUILDER_H
#define JSON_BUILDER_H

#include <stddef.h>

typedef struct JSONBuilder JSONBuilder;

JSONBuilder *jb_create(size_t initial_cap);
void         jb_free(JSONBuilder *jb);
void         jb_reset(JSONBuilder *jb);
const char  *jb_string(const JSONBuilder *jb);

void jb_begin_object(JSONBuilder *jb);
void jb_end_object(JSONBuilder *jb);
void jb_begin_array(JSONBuilder *jb);
void jb_end_array(JSONBuilder *jb);
void jb_key(JSONBuilder *jb, const char *key);
void jb_string_value(JSONBuilder *jb, const char *val);
void jb_int_value(JSONBuilder *jb, int val);
void jb_bool_value(JSONBuilder *jb, int val);
void jb_null_value(JSONBuilder *jb);

#endif
```

### json_builder.c

```c
#include "json_builder.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define GROWTH_FACTOR 2
#define MIN_CAPACITY  256

struct JSONBuilder {
    char  *buf;
    size_t cap;
    size_t len;
    int    depth;
    int    need_comma;
};

JSONBuilder *jb_create(size_t initial_cap) {
    JSONBuilder *jb = calloc(1, sizeof(*jb));
    if (!jb) return NULL;

    if (initial_cap < MIN_CAPACITY) {
        initial_cap = MIN_CAPACITY;
    }

    jb->buf = malloc(initial_cap);
    if (!jb->buf) {
        free(jb);
        return NULL;
    }

    jb->cap = initial_cap;
    jb->buf[0] = '\0';
    return jb;
}

void jb_free(JSONBuilder *jb) {
    if (jb) {
        free(jb->buf);
        free(jb);
    }
}

void jb_reset(JSONBuilder *jb) {
    if (jb) {
        jb->len = 0;
        jb->depth = 0;
        jb->need_comma = 0;
        jb->buf[0] = '\0';
    }
}

const char *jb_string(const JSONBuilder *jb) {
    return jb ? jb->buf : NULL;
}

static int jb_grow(JSONBuilder *jb, size_t needed) {
    if (jb->len + needed + 1 <= jb->cap) return 0;

    size_t new_cap = jb->cap;
    while (jb->len + needed + 1 > new_cap) {
        new_cap *= GROWTH_FACTOR;
    }

    char *new_buf = realloc(jb->buf, new_cap);
    if (!new_buf) return -1;

    jb->buf = new_buf;
    jb->cap = new_cap;
    return 0;
}

static void jb_emit(JSONBuilder *jb, const char *s, size_t n) {
    if (jb_grow(jb, n) != 0) return;
    memcpy(jb->buf + jb->len, s, n);
    jb->len += n;
    jb->buf[jb->len] = '\0';
}

void jb_begin_object(JSONBuilder *jb) {
    jb_emit(jb, "{", 1);
    jb->depth++;
    jb->need_comma = 0;
}

void jb_end_object(JSONBuilder *jb) {
    jb->depth--;
    jb_emit(jb, "}", 1);
}

void jb_begin_array(JSONBuilder *jb) {
    jb_emit(jb, "[", 1);
    jb->depth++;
    jb->need_comma = 0;
}

void jb_end_array(JSONBuilder *jb) {
    jb->depth--;
    jb_emit(jb, "]", 1);
}

void jb_key(JSONBuilder *jb, const char *key) {
    (void)jb;
    (void)key;
    /* implementation */
}

void jb_string_value(JSONBuilder *jb, const char *val) {
    (void)jb;
    (void)val;
    /* implementation */
}
```

---

## 14. Checklist de validacion

Antes de dar por terminado un archivo `.c` o `.h`:

- [ ] Compila sin warnings con `-Wall -Wextra -Wpedantic -Werror`
- [ ] Compila en modo debug (`make debug`) y release (`make release`)
- [ ] `valgrind --leak-check=full` — 0 leaks, 0 errors
- [ ] `cppcheck` o `clang-tidy` — sin warnings
- [ ] Toda `malloc`/`calloc`/`realloc` tiene su `free`
- [ ] Todo puntero devuelto por una funcion que reserva memoria tiene `free` documentado
- [ ] Ninguna funcion prohibida (`gets`, `strcpy`, `sprintf`, `alloca`, `system`)
- [ ] Precondiciones validadas en todas las funciones publicas
- [ ] `sizeof(*ptr)` en vez de `sizeof(Type)`
- [ ] `snprintf` en vez de `sprintf`
- [ ] Includes minimos y autocontenidos
- [ ] Include guards correctos en todos los `.h`
- [ ] Funciones de menos de 50 lineas (salvo dispatch)
- [ ] Maximo 3 niveles de indentacion por funcion
- [ ] 100 caracteres maximo por linea
- [ ] 4 espacios de indentacion, sin tabs
- [ ] Test unitario creado en `test/` para el modulo
- [ ] `make test` pasa todos los tests
