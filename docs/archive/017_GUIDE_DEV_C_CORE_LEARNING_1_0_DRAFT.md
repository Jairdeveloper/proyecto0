---
id: 017
area: dev
type: guide
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - learning
  - c
  - recpl-core
  - tutorial
  - beginner
  - compiler-bot
summary: "Guia detallada de aprendizaje para implementar el nucleo C (recpl-core) del bot RECPL. Explica conceptos de C a medida que aparecen en la implementacion, con ejemplos practicos y referencias al pipeline shell existente."
keywords:
  - guia
  - aprendizaje
  - c
  - c11
  - principiante
  - recpl-core
  - punteros
  - memoria
  - estructuras
  - tutorial
  - implementacion
changelog:
  - version: 1.0
    date: 2026-06-08
    author: workflow-agent
    description: Creacion de la guia de aprendizaje para implementar recpl-core en C
---

# Guia de Aprendizaje: Implementar recpl-core en C

> **Prerequisito:** Tener un compilador C (gcc o clang) instalado.
> **Verificar con:** `gcc --version`
> **Referencia:** `015_GUIDE_DEV_C_STYLE_1_0_DRAFT.md` (convenciones de estilo)

---

## Introduccion

Esta guia te lleva de la mano por la implementacion de `recpl-core`. Cada seccion
introduce conceptos nuevos de C justo cuando los necesitas, con ejemplos que puedes
compilar y probar inmediatamente.

**Que vas a aprender:**
- Compilar un programa en C con Makefile
- Tipos de datos, enumeraciones y estructuras
- Punteros y memoria dinamica (malloc/free)
- Arreglos y strings en C
- Entrada/salida estandar (stdin, stdout)
- Parseo de argumentos CLI
- Tener un binario funcional que procesa lenguaje natural

---

## Parte 0: Tu primer programa en C

Crea `hola.c`:

```c
#include <stdio.h>

int main(void) {
    printf("Hola, mundo!\n");
    return 0;
}
```

Compila y ejecuta:
```sh
gcc -std=c11 -Wall -o hola hola.c
./hola
```

**Explicacion:**
- `#include <stdio.h>` — libreria estandar de entrada/salida
- `int main(void)` — punto de entrada. `int` = codigo de salida
- `printf` — imprime texto formateado
- `return 0` — 0 = exito, != 0 = error
- `-std=c11` — estandar C11
- `-Wall` — activa warnings (son errores en este proyecto)

**Ejercicio:** Modifica para que imprima "Hola, [tu nombre]!" y retorne 1.
Verifica con `echo $?` despues de ejecutar.

---

## Parte 1: Conceptos basicos para FASE-C1

### 1.1 Enumeraciones (enum)

Un `enum` define constantes con nombre. Perfecto para tipos de token.

```c
typedef enum {
    TOKEN_UNKNOWN = 0,
    TOKEN_ACTION_CREATE,
    TOKEN_ACTION_DELETE,
    TOKEN_ACTION_UPDATE,
    TOKEN_ACTION_READ
} TokenType;
```

- `typedef` permite usar `TokenType` directamente (sin `enum TokenType`)
- Por defecto: 0, 1, 2, 3... (puedes asignar valores explicitos)

**Ejercicio:** Declara `TokenType t = TOKEN_ACTION_CREATE;` e imprimela con
`printf("%d\n", t);`. Que numero muestra?

### 1.2 Estructuras (struct)

Un `struct` agrupa variables relacionadas.

```c
typedef struct {
    TokenType type;
    char     *lexeme;   // puntero a char (string)
    int       line;
    int       col;
} Token;
```

**Acceso a campos:**
```c
Token t;
t.type = TOKEN_ACTION_CREATE;
t.lexeme = "crea";
```

**Structs anidados:**
```c
typedef struct {
    char **entities;     // arreglo de strings
    int    entity_count;
} ModuloEspec;

typedef struct {
    char        *accion;
    ModuloEspec  objetivo;
} ASTNode;
```

**Ejercicio:** Declara un `Token`, asigna valores, imprime cada campo.

### 1.3 Punteros: la teoria minima

Un puntero *contiene la direccion de memoria* de otra variable.

```c
int  x = 42;
int *p = &x;      // p contiene la direccion de x

printf("%d\n", x);    // 42
printf("%p\n", p);    // direccion de memoria (hex)
printf("%d\n", *p);   // 42 (valor APUNTADO por p)
```

**El operador `->`:**
Para acceder a campos de struct via puntero:
```c
Token t;
Token *ptr = &t;
(*ptr).type = TOKEN_CREATE;  // verboso
ptr->type = TOKEN_CREATE;    // comun (equivalente)
```

**Ejercicio:** Escribe `void set_type(Token *t, TokenType type)` que asigne
el tipo usando `->`. Prueba desde main.

### 1.4 Memoria dinamica: malloc y free

Reservas memoria en tiempo de ejecucion con `malloc`.

```c
#include <stdlib.h>

int *arr = malloc(10 * sizeof(int));
if (arr == NULL) {
    fprintf(stderr, "Error: no hay memoria\n");
    return 1;
}
arr[0] = 42;
free(arr);  // siempre liberar!
```

**Reglas de oro:**
1. Todo `malloc` tiene su `free`
2. Siempre verificar `NULL`
3. Usar `sizeof(*ptr)` en vez de `sizeof(Tipo)`:
   ```c
   Token *tokens = malloc(count * sizeof(*tokens));  // seguro
   Token *tokens = malloc(count * sizeof(Token));     // fragil
   ```

**Ejercicio:** Pide un numero con `scanf`, reserva arreglo de ese tamaño,
llena con 0..N-1, imprime, libera.

### 1.5 Strings en C

No hay tipo "string". Son arreglos de `char` terminados en `\0`.

```c
char *s1 = "hola";             // literal (no modificar)
char  s2[] = "mundo";          // arreglo mutable
s2[0] = 'M';                   // ahora "Mundo"

char buf[100];
snprintf(buf, sizeof(buf), "%s %s", s1, s2);  // buf = "hola Mundo"

char *dup = strdup("hola");    // reserva copia en heap
free(dup);                     // hay que liberar!
```

**Diferencia:**
- `'a'` — char (comilla simple), un caracter
- `"a"` — string (comilla doble), arreglo: `'a'` + `'\0'`

### 1.6 strncmp: comparar prefijos

```c
#include <string.h>

const char *input = "creando modulo";
if (strncmp(input, "creando", 7) == 0) {
    printf("Input empieza con 'creando'\n");
}
```

`strncmp(a, b, n)` compara los primeros `n` caracteres.
Retorna 0 si son iguales.

---

## Parte 2: FASE-C1 — Fundacion C

### 2.1 Makefile

El Makefile define como compilar. Conceptos clave:

- `CC` — compilador (`gcc`)
- `CFLAGS` — banderas (`-std=c11 -Wall -Wextra -Werror`)
- `$(SRC:.c=.o)` — reemplaza .c por .o
- `$@` — nombre del target
- `$^` — todas las dependencias
- `.PHONY` — targets que no son archivos (clean, test)

**Prueba:** Crea un `main.c` con `int main(void) { return 0; }`.
Compila con `make`, verifica `recpl-core`. Luego `make clean`.

### 2.2 Include guards

Cada `.h` necesita proteccion contra inclusion multiple:

```c
#ifndef NOMBRE_H
#define NOMBRE_H

// ... contenido ...

#endif
```

### 2.3 JSON Builder (tipos opacos)

Declaras el struct en `.h` pero lo defines en `.c`:

```c
// json_builder.h
typedef struct JSONBuilder JSONBuilder;

JSONBuilder *jb_create(size_t initial_cap);
void         jb_free(JSONBuilder *jb);
const char  *jb_string(const JSONBuilder *jb);

// json_builder.c
struct JSONBuilder {
    char  *buf;
    size_t cap;
    size_t len;
    int    depth;
};
```

Esto es **encapsulamiento**: nadie modifica los campos internos directamente.

### 2.4 Hash Table (void*)

`void *` es un puntero generico — apunta a cualquier tipo.

```c
void *ptr;
int x = 42;
ptr = &x;
printf("%d\n", *(int*)ptr);  // castear de vuelta
```

**Hash function djb2:**
```c
unsigned long hash(const char *str) {
    unsigned long h = 5381;
    int c;
    while ((c = *str++)) h = ((h << 5) + h) + c;
    return h;
}
```

### 2.5 Leer de stdin

```c
int read_stdin(char *buf, size_t size) {
    if (!buf || size == 0) return -1;
    size_t i = 0;
    int c;
    while ((c = getchar()) != EOF && i < size - 1)
        buf[i++] = (char)c;
    buf[i] = '\0';
    return (int)i;
}
```

**Ejercicio:** Programa que lee stdin y lo imprime en mayusculas
(usa `toupper()` de `<ctype.h>`).

### 2.6 Main dispatch

```c
int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Uso: recpl-core --mode=<mode>\n");
        return 1;
    }
    const char *mode = parse_flag(argv, "--mode");
    if (strcmp(mode, "lex") == 0) return mode_lex();
    // ...
}
```

**Parseo manual de flags:**
```c
const char *parse_flag(char **argv, const char *flag) {
    int flen = strlen(flag);
    for (int i = 1; argv[i]; i++) {
        if (strncmp(argv[i], flag, flen) == 0 && argv[i][flen] == '=')
            return argv[i] + flen + 1;
    }
    return NULL;
}
```

---

## Parte 3: FASE-C2 — Lexer

### 3.1 Anatomia

El lexer recorre el input caracter por caracter. En cada posicion,
busca el prefijo mas largo contra una lista de palabras clave.

**Flujo:**
```
Input: "crea modulo pagos en nestjs"
         ^ pos=0
1. Saltar whitespace (no hay)
2. Matchear keywords:
   "crear"  → match! length=5
   "crea"   → match! length=4 (pero "crear" gana por maximal munch)
3. Match mas largo: "crear" (5 chars), type=ACTION_CREATE
4. Avanzar pos=5
```

### 3.2 Arreglo de keywords

```c
typedef struct {
    const char *pattern;
    TokenType   type;
} KeywordEntry;

static const KeywordEntry keywords[] = {
    {"creando",   TOKEN_ACTION_CREATE},
    {"crear",     TOKEN_ACTION_CREATE},
    {"crea",      TOKEN_ACTION_CREATE},
    {"generar",   TOKEN_ACTION_CREATE},
    {"make",      TOKEN_ACTION_CREATE},
    {"new",       TOKEN_ACTION_CREATE},
    {"eliminar",  TOKEN_ACTION_DELETE},
    {"borrar",    TOKEN_ACTION_DELETE},
    {"delete",    TOKEN_ACTION_DELETE},
    {"remove",    TOKEN_ACTION_DELETE},
    {"actualizar", TOKEN_ACTION_UPDATE},
    {"modificar",  TOKEN_ACTION_UPDATE},
    {"update",    TOKEN_ACTION_UPDATE},
    {"edit",      TOKEN_ACTION_UPDATE},
    {"mostrar",   TOKEN_ACTION_READ},
    {"listar",    TOKEN_ACTION_READ},
    {"get",       TOKEN_ACTION_READ},
    {"show",      TOKEN_ACTION_READ},
    {"read",      TOKEN_ACTION_READ},
    {"modulo",    TOKEN_MODULE},
    {"module",    TOKEN_MODULE},
    {"nestjs",    TOKEN_TECH_NESTJS},
    {"prisma",    TOKEN_TECH_PRISMA},
    {"express",   TOKEN_TECH_EXPRESS},
    {"fastapi",   TOKEN_TECH_FASTAPI},
    {"react",     TOKEN_TECH_REACT},
    {"vue",       TOKEN_TECH_VUE},
    {"postgres",  TOKEN_TECH_POSTGRES},
    {"mongodb",   TOKEN_TECH_MONGODB},
    {"docker",    TOKEN_TECH_DOCKER},
    {"k8s",       TOKEN_TECH_K8S},
    {"graphql",   TOKEN_TECH_GRAPHQL},
    {"next",      TOKEN_TECH_NEXT},
    {"django",    TOKEN_TECH_DJANGO},
    {"flask",     TOKEN_TECH_FLASK},
    {"spring",    TOKEN_TECH_SPRING},
    {"gin",       TOKEN_TECH_GIN},
    {"svelte",    TOKEN_TECH_SVELTE},
    {"en",        TOKEN_PREP_IN},
    {"para",      TOKEN_PREP_IN},
    {"de",        TOKEN_PREP_IN},
    {"in",        TOKEN_PREP_IN},
    {"for",       TOKEN_PREP_IN},
    {"of",        TOKEN_PREP_IN},
};
static const int keyword_count = sizeof(keywords) / sizeof(keywords[0]);
```

`sizeof(keywords) / sizeof(keywords[0])` calcula cuantos elementos
tiene el arreglo.

### 3.3 Maximal munch

```c
int match_keyword(const char *input, TokenType *type, int *length) {
    *type = TOKEN_UNKNOWN;
    *length = 0;

    for (int i = 0; i < keyword_count; i++) {
        int plen = strlen(keywords[i].pattern);
        if (strncmp(input, keywords[i].pattern, plen) == 0) {
            if (plen > *length) {   // mas largo → mejor match
                *length = plen;
                *type = keywords[i].type;
            }
        }
    }
    return *length > 0;
}
```

### 3.4 Funcion lex() completa

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
            tokens[count].type = type;
            tokens[count].lexeme = strndup(input + pos, length);
            tokens[count].line = 1;
            tokens[count].col = col;
            count++; pos += length; col += length;
        } else if (input[pos] >= 'a' && input[pos] <= 'z') {
            // ENTITY: palabra minuscula no keyword
            int start = pos;
            while (input[pos] >= 'a' && input[pos] <= 'z') pos++;
            length = pos - start;
            tokens[count].type = TOKEN_ENTITY;
            tokens[count].lexeme = strndup(input + start, length);
            tokens[count].line = 1;
            tokens[count].col = col;
            count++; col += length;
        } else if (strchr(",.;!?", input[pos])) {
            // SEPARATOR
            tokens[count].type = TOKEN_SEPARATOR;
            tokens[count].lexeme = strndup(input + pos, 1);
            tokens[count].line = 1;
            tokens[count].col = col;
            count++; pos++; col++;
        } else {
            fprintf(stderr, "Error lexico en col %d: '%c'\n", col, input[pos]);
            pos++; col++;
        }
    }
    return count;
}
```

### 3.5 strndup manual

`strndup` reserva memoria, copia hasta n chars, agrega `\0`.

```c
char *my_strndup(const char *s, size_t n) {
    char *r = malloc(n + 1);
    if (!r) return NULL;
    memcpy(r, s, n);
    r[n] = '\0';
    return r;
}
```

---

## Parte 4: FASE-C3 — Parser

### 4.1 Recursive descent

Una funcion por cada no-terminal de la gramatica.

**Gramatica:**
```
comando → accion modulo_espec opcional_tech
```

**En C:**
```c
int parse_comando(Parser *p) {
    if (parse_accion(p) != 0) return -1;
    if (parse_modulo_espec(p) != 0) return -1;
    if (parse_opcional_tech(p) != 0) return -1;
    return 0;
}
```

### 4.2 Estructura del Parser

```c
typedef struct {
    const Token *tokens;
    int          count;
    int          cursor;
    ASTNode     *ast;
} Parser;

static Token current_token(Parser *p) {
    if (p->cursor >= p->count)
        return (Token){TOKEN_EOF, NULL, 0, 0};  // struct literal
    return p->tokens[p->cursor];
}

static void advance(Parser *p) { p->cursor++; }

static int expect(Parser *p, TokenType type) {
    Token t = current_token(p);
    if (t.type != type) {
        fprintf(stderr, "Error: esperaba %s, encontre %s\n",
                token_type_name(type), token_type_name(t.type));
        return 0;
    }
    advance(p);
    return 1;
}
```

**Struct literal:** `(Token){TOKEN_EOF, NULL, 0, 0}` crea un Token temporal.
Caracteristica de C99/C11.

### 4.3 Parseo de accion

```c
static int parse_accion(Parser *p) {
    Token t = current_token(p);
    switch (t.type) {
    case TOKEN_ACTION_CREATE:
        p->ast->accion = strdup("CREATE"); advance(p); return 0;
    case TOKEN_ACTION_DELETE:
        p->ast->accion = strdup("DELETE"); advance(p); return 0;
    case TOKEN_ACTION_UPDATE:
        p->ast->accion = strdup("UPDATE"); advance(p); return 0;
    case TOKEN_ACTION_READ:
        p->ast->accion = strdup("READ");   advance(p); return 0;
    default:
        fprintf(stderr, "Error: se esperaba una accion\n");
        return -1;
    }
}
```

**switch:** cada `case` necesita `break` (o `return`). Sin break, "cae"
al siguiente caso (fallthrough).

### 4.4 Arreglo dinamico con realloc

Para entidades multiples:
```c
static int add_entity(ModuloEspec *m, const char *name) {
    char **new_ents = realloc(m->entities,
                              (m->entity_count + 1) * sizeof(*new_ents));
    if (!new_ents) return -1;
    m->entities = new_ents;
    m->entities[m->entity_count] = strdup(name);
    m->entity_count++;
    return 0;
}
```

### 4.5 Formatear AST como JSON

Usando `json_builder`:
```c
char *ast_to_json(const ASTNode *ast) {
    JSONBuilder *jb = jb_create(512);
    jb_begin_object(jb);
    jb_key(jb, "accion");   jb_string_value(jb, ast->accion);
    jb_key(jb, "objetivo"); jb_begin_object(jb);
    jb_key(jb, "tipo");     jb_string_value(jb, ast->obj_tipo);
    jb_key(jb, "entidades"); jb_begin_array(jb);
    for (int i = 0; i < ast->objetivo.entity_count; i++)
        jb_string_value(jb, ast->objetivo.entities[i]);
    jb_end_array(jb);
    jb_end_object(jb);
    jb_key(jb, "tech");
    if (ast->techs.tech_count > 0)
        jb_string_value(jb, ast->techs.techs[0]);
    else
        jb_null_value(jb);
    jb_end_object(jb);
    const char *s = jb_string(jb);
    char *result = strdup(s);
    jb_free(jb);
    return result;
}
```

---

## Parte 5: FASE-C4 a C6 — Resto del pipeline

### 5.1 Semantic analyzer

Usa la `HashTable` para la tabla de simbolos:

```c
int semantic_analyze(ASTNode *ast, HashTable *symbols, const char *state_dir) {
    // Validar tech contra lista blanca
    const char *allowed[] = {"NestJS", "Prisma"};
    int allowed_count = 2;

    for (int i = 0; i < ast->techs.tech_count; i++) {
        int valid = 0;
        for (int j = 0; j < allowed_count; j++) {
            if (strcasecmp(ast->techs.techs[i], allowed[j]) == 0)
                valid = 1;
        }
        if (!valid) {
            fprintf(stderr, "Error: tech no soportado: %s\n",
                    ast->techs.techs[i]);
            return -1;
        }
    }

    // Insertar en tabla de simbolos (CREATE/UPDATE)
    if (strcmp(ast->accion, "CREATE") == 0 || strcmp(ast->accion, "UPDATE") == 0) {
        for (int i = 0; i < ast->objetivo.entity_count; i++) {
            SymbolEntry *entry = calloc(1, sizeof(*entry));
            entry->name  = strdup(ast->objetivo.entities[i]);
            entry->tipo  = strdup(ast->obj_tipo);
            entry->tech  = strdup(ast->techs.techs[0]);
            entry->estado = strdup("pending");
            entry->scope = strdup("global");
            ht_insert(symbols, entry->name, entry);
        }
    }

    return 0;
}
```

### 5.2 IR Generator

Usa `json_builder` para construir el IR:

```c
char *generate_ir(const ASTNode *ast, const HashTable *symbols) {
    JSONBuilder *jb = jb_create(1024);
    jb_begin_object(jb);
    jb_key(jb, "accion"); jb_string_value(jb, map_action(ast->accion));
    jb_key(jb, "tipo");   jb_string_value(jb, ast->obj_tipo);
    jb_key(jb, "nombre"); jb_string_value(jb, ast->objetivo.entities[0]);
    jb_key(jb, "tech");   jb_string_value(jb, ast->techs.techs[0]);
    jb_key(jb, "template");
    jb_string_value(jb, map_template(ast->obj_tipo, ast->techs.techs[0]));
    jb_key(jb, "trace_id");
    char tid[64];
    snprintf(tid, sizeof(tid), "trc_%ld_%d", time(NULL), getpid());
    jb_string_value(jb, tid);
    jb_end_object(jb);
    // ...
}
```

### 5.3 mode_full() — pipeline completo

```c
int mode_full(void) {
    char input[65536];
    int len = read_stdin(input, sizeof(input));
    if (len <= 0) return 5;

    char *normalized = preprocess(input);
    Token tokens[256];
    int nt = lex(normalized, tokens, 256);
    free(normalized);

    ASTNode ast;
    memset(&ast, 0, sizeof(ast));
    if (parse(tokens, nt, &ast) != 0) return 3;

    HashTable *symbols = ht_create(64);
    if (semantic_analyze(&ast, symbols, NULL) != 0) {
        ht_free(symbols); ast_free(&ast); return 4;
    }

    char *ir_json = generate_ir(&ast, symbols);
    printf("%s\n", ir_json);

    free(ir_json);
    ht_free(symbols);
    ast_free(&ast);
    return 0;
}
```

---

## Tips de debugging y herramientas

### Compilar con debug
```sh
make debug
```
Incluye `-g` (simbolos) y `-fsanitize=address` (detecta buffer overflows).

### Detectar memory leaks
```sh
valgrind --leak-check=full ./recpl-core --mode=full < input.txt
```

### Comparar con shell
```sh
echo "crea modulo pagos en nestjs" > /tmp/in.txt
./recpl-core --mode=full < /tmp/in.txt > /tmp/c_out.txt
# vs shell:
echo "crea modulo pagos en nestjs" | compiler-bot/recpl.sh > /tmp/sh_out.txt
diff /tmp/c_out.txt /tmp/sh_out.txt
```

### Errores comunes de principiante

| Error | Causa | Solucion |
|-------|-------|----------|
| `Segmentation fault` | Acceder a NULL o memoria liberada | Verificar punteros con `if (ptr)` antes de usarlos |
| `Use of undeclared identifier 'X'` | Falta `#include` | Incluir el header correcto |
| `Undefined reference to 'func'` | Falta linkear el .o | Agregar archivo al Makefile |
| `uninitialized value` | Variable sin asignar | Inicializar siempre: `int x = 0;` |
| `double free` | Llamar free dos veces | Poner `ptr = NULL;` despues de free |
| `buffer overflow` | Escribir mas alla del tamaño | Usar `snprintf`, verificar indices |

### Orden sugerido para escribir y probar

No escribas todo de golpe. Por cada modulo:

1. **Escribe el .h** (declaraciones)
2. **Escribe el .c** (implementacion)
3. **Escribe un test minimo** en main.c que llame a la funcion
4. **Compila** con `make debug`
5. **Prueba** con entrada conocida
6. **Compara** con el output del script shell equivalente
7. Solo entonces pasa al siguiente modulo

### Para validar contra los tests existentes

```sh
# Despues de FASE-C6, ejecuta los tests originales:
compiler-bot/tests/run_tests.sh

# Deberian pasar igual que con el pipeline shell.
# Si fallan, el output de diff te dice exactamente que difiere.
```
