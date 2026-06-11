---
id: 025
area: dev
type: GUIDE
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - pipeline
  - compiler
  - recpl
  - architecture
  - dfa
  - ll1
  - ir
  - synthesis
  - aho
  - dragon-book
summary: "Descripcion teorica del pipeline RECPL (READ-EVAL-PRINT Compiler Loop). Explica los fundamentos de cada etapa del compilador: preprocesamiento, analisis lexico con DFA y maximal munch, parsing LL(1) recursivo descendente, analisis semantico con tabla de simbolos, generacion de IR canonico, synthesis/scaffolding, y el bucle principal. Basado en los principios del Dragon Book de Aho, Sethi y Ullman."
keywords:
  - recpl
  - pipeline
  - compilador
  - preprocesador
  - lexer
  - parser
  - semantico
  - ir
  - synthesis
  - scaffold
  - dfa
  - ll1
  - recursive-descent
  - maximal-munch
  - dragon-book
  - aho
  - teoria-de-compiladores
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Descripcion teorica completa del pipeline RECPL
---

# Pipeline RECPL — Descripcion Teorica

> **RECPL** (READ-EVAL-PRINT Compiler Loop) es un compilador de lenguaje
> natural a codigo. Implementa las fases clasicas de un compilador descritas
> en el Dragon Book (Aho, Sethi, Ullman) adaptadas para procesar instrucciones
> en espanol y generar scaffolding de proyectos NestJS/Prisma.

---

## 0. Arquitectura General

El pipeline RECPL sigue la estructura clasica de un compilador de una sola
pasada (one-pass compiler):

```
                    ENTRADA (lenguaje natural)
                            │
                            ▼
┌─────────────────────────────────────────────────┐
│                  FRONT-END                       │
│                                                   │
│  1. PREPROCESADOR  → normalizacion, segmentacion │
│  2. LEXER (READ)   → DFA + maximal munch        │
│  3. PARSER (EVAL)  → LL(1) recursive descent    │
│  4. SEMANTICO      → tabla de simbolos + typos  │
└─────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────┐
│                  MIDDLE-END                      │
│                                                   │
│  5. IR GENERATOR   → representacion intermedia   │
└─────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────┐
│                  BACK-END                        │
│                                                   │
│  6. SYNTHESIS (PRINT) → respuesta del bot        │
│  7. SCAFFOLD         → generacion de archivos    │
└─────────────────────────────────────────────────┘
                            │
                            ▼
                    SALIDA (codigo NestJS/Prisma)
```

Cada etapa recibe JSON por stdin y produce JSON por stdout.
El estado compartido (tabla de simbolos) se almacena en disco
via `RECPL_STATE_DIR`.

---

## 1. Preprocesador

### Proposito

Normalizar y segmentar el texto en lenguaje natural antes del
analisis lexico. El preprocesador es la primera barrera contra
la variabilidad del input humano.

### Algoritmo

```
texto crudo
    │
    ▼
┌─────────────┐
│ TRIM        │  Elimina espacios iniciales y finales
└──────┬──────┘
       ▼
┌─────────────┐
│ LOWERCASE   │  Convierte a minusculas (ASCII-safe con tr)
└──────┬──────┘
       ▼
┌─────────────┐
│ COLLAPSE    │  Reduce puntuacion repetida: "???" → "?"
└──────┬──────┘
       ▼
┌─────────────┐
│ SPLIT       │  Divide en oraciones por [.;!?]
└──────┬──────┘
       ▼
texto normalizado (una oracion por linea)
```

### Decision de diseno

El preprocesador maneja **todo el case folding**. El lexer recibe
input en minusculas y es case-sensitive. Esto simplifica el DFA:
cada patron se define solo en minusculas y no hay ambiguedad
por mayusculas.

### Fallo silencioso

Si el preprocesador falla (por ejemplo, por un caracter que `tr`
no puede manejar), devuelve el input original intacto. Esto
sigue el principio de **fail soft**: es mejor procesar texto sin
normalizar que rechazar una instruccion valida.

---

## 2. Lexer (READ)

### Proposito

Tokenizar el texto normalizado usando un automata finito
determinista (DFA) con la estrategia de **maximal munch**
(la coincidencia mas larga gana).

### Fundamentos teoricos

Un **DFA** (Automata Finito Determinista) es un modelo de
computacion con las siguientes propiedades:

- Conjunto finito de estados
- Alfabeto de entrada finito
- Funcion de transicion determinista (δ: Q × Σ → Q)
- Unico estado inicial
- Conjunto de estados de aceptacion

En RECPL, el DFA se implementa como una serie de patrones ERE
(Extended Regular Expressions) evaluados secuencialmente. Para
cada posicion en el texto:

1. Se prueban todos los patrones
2. Se selecciona el que produce la coincidencia **mas larga**
3. Se avanza esa longitud
4. Se repite hasta consumir todo el input

### Conjunto de tokens

| Token | Patron ERE | Ejemplo |
|-------|-----------|---------|
| ACTION_CREATE | `creando\|crear\|crea\|generar\|make\|new` | "crea" |
| ACTION_DELETE | `eliminar\|borrar\|delete\|remove` | "eliminar" |
| ACTION_UPDATE | `actualizar\|modificar\|update\|edit` | "actualizar" |
| ACTION_READ | `mostrar\|listar\|get\|show\|read` | "listar" |
| MODULE | `modulo\|module` | "modulo" |
| TECH_NESTJS | `nestjs` | "nestjs" |
| TECH_PRISMA | `prisma` | "prisma" |
| PREP_IN | `en\|para\|de\|in\|for\|of` | "en" |
| ENTITY | `[a-z][a-z]*` | "pagos" |
| SEPARATOR | `[,.;!?]` | "," |
| EOF | (fin de entrada) | — |

### Maximal munch en accion

Para el input "crea modulo pagos en nestjs":

```
Posicion 0: "crea" → ACTION_CREATE (len 4)
Posicion 4: "modulo" → MODULE (len 6)
Posicion 10: "pagos" → ENTITY (len 5)
Posicion 15: "en" → PREP_IN (len 2)
Posicion 17: "nestjs" → TECH_NESTJS (len 6)
Posicion 23: EOF
```

Si hubiera ambiguedad (ej: "crear" coincide con ACTION_CREATE
pero "crea" tambien), maximal munch elige la mas larga.

### Estructura del token JSON

```json
{
  "type": "ACTION_CREATE",
  "lexeme": "crea",
  "position": { "line": 1, "col": 1 }
}
```

---

## 3. Parser (EVAL)

### Proposito

Construir un AST (Abstract Syntax Tree) a partir de la secuencia
de tokens usando un parser **LL(1) recursivo descendente**.

### Fundamentos teoricos

Un parser LL(1) es un parser descendente que:

- Lee la entrada de **izquierda a derecha** (L)
- Produce una derivacion **mas a la izquierda** (L)
- Usa **1 token de lookahead** (1)

Es "recursivo descendente" porque hay una funcion por cada
no-terminal de la gramatica, y se llaman recursivamente
siguiendo las producciones.

### Gramatica BNF

```
comando       → accion modulo_espec opcional_tech
accion        → ACTION_CREATE
              | ACTION_DELETE
              | ACTION_UPDATE
              | ACTION_READ
modulo_espec  → MODULE ARTICLE? ENTITY (PREP ENTITY)*
              | ENTITY
opcional_tech → PREP TECH (SEPARATOR TECH)*
              | ε  (vacio)
```

### Funciones del parser

Cada no-terminal tiene una funcion:

1. **parse_comando()**: Punto de entrada. Llama a parse_accion,
   parse_modulo_espec, parse_opcional_tech en ese orden.

2. **parse_accion()**: Reconoce ACTION_CREATE/DELETE/UPDATE/READ.
   Si no encuentra ninguna, emite error sintactico.

3. **parse_modulo_espec()**: Dos caminos:
   - Si el token es MODULE, consume MODULE + ARTICLE opcional
     + lista de entidades
   - Si el token es ENTITY directamente, trata el comando como
     entidad sin tipo explicito

4. **parse_entity_list()**: Consume entidades separadas por
   preposiciones, con cuidado de no consumir una preposicion
   que pertenezca a `opcional_tech` (PREP seguida de TECH se
   deja para la siguiente fase).

5. **parse_opcional_tech()**: Consume PREP + TECH, y luego
   (SEPARATOR TECH)* para listas de tecnologias.

### AST generado

Para "crea un modulo de pagos en NestJS" el AST es:

```json
{
  "tipo": "Comando",
  "accion": "CREATE",
  "objetivo": {
    "tipo": "module",
    "entidades": ["pagos"]
  },
  "tech": "NestJS"
}
```

### Manejo de errores sintacticos

El parser reporta errores con el formato:

```
Error sintactico en token N: se esperaba 'X', se encontro 'Y' (lexema: 'Z')
```

Y termina con exit code 1. El LOOP principal captura este error
y devuelve un JSON de error en lugar del AST.

---

## 4. Analizador Semantico

### Proposito

Validar semanticamente el AST y mantener una **tabla de simbolos**
persistente. Es la segunda fase de EVAL.

### Tabla de simbolos

La tabla de simbolos es un hash en disco (archivo de texto
delimitado por `|`) con los campos:

```
nombre|tipo|tech|estado|scope
```

| Campo | Significado |
|-------|------------|
| nombre | Identificador de la entidad (ej: "pagos") |
| tipo | "module" o "entity" |
| tech | "NestJS", "Prisma", o vacio |
| estado | "pending" inicialmente |
| scope | "global" o nombre del scope padre |

### Persistencia entre invocaciones

Cuando se usa el LOOP principal, `RECPL_STATE_DIR` apunta a un
directorio persistente. La tabla de simbolos se preserva entre
invocaciones, permitiendo que instrucciones posteriores
referencien modulos creados antes.

### Reglas semanticas

| Accion | Regla |
|--------|-------|
| CREATE/UPDATE | La entidad NO debe existir en la tabla de simbolos |
| DELETE/READ | La entidad DEBE existir en la tabla de simbolos |
| Cualquiera | El tech stack debe estar en la lista blanca: NestJS, Prisma |

### Type checking

`validate_tech()` normaliza el nombre del tech y lo compara
contra la lista blanca `ALLOWED_TECHS`. Si no es reconocido,
emite error semantico y termina.

### Stack de scopes

El analizador mantiene un scope stack (archivo en disco) para
soportar anidamiento. Inicialmente solo existe "global".

---

## 5. Generador de IR

### Proposito

Transformar el AST validado + tabla de simbolos en una
**representacion intermedia canonica (IR.json)**. Esta
representacion es autocontenida: no necesita los modulos
anteriores para ser interpretada.

### Estructura del IR

```json
{
  "accion": "scaffold",
  "tipo": "module",
  "nombre": "pagos",
  "tech": "NestJS",
  "template": "module-nestjs",
  "entidades": ["pagos"],
  "dependencias": [],
  "score": null,
  "trace_id": "trc_1718000000_12345",
  "symbol_table": { ... }
}
```

### Mapeos del IR

| Entrada | Salida |
|---------|--------|
| accion=CREATE | `"accion": "scaffold"` |
| accion=DELETE | `"accion": "delete"` |
| tipo=module, tech=NestJS | `"template": "module-nestjs"` |
| tipo=entity, tech=NestJS | `"template": "entity-nestjs"` |
| tipo=module, tech=Prisma | `"template": "module-prisma"` |

### Por que una representacion intermedia

El IR desacopla el front-end (analisis) del back-end (generacion).
Esto permite:

- Agregar nuevos back-ends sin modificar el analisis
- Cachear el IR para evitar reprocesar entradas identicas
- Inspeccionar y depurar el pipeline en cualquier punto
- Serializar y almacenar decisiones del compilador

---

## 6. Synthesis (PRINT)

### Proposito

Recibir el IR.json y producir la **respuesta del bot** en formato
JSON. Es la fase PRINT del ciclo RECPL: genera el mensaje para
el usuario y ejecuta las acciones correspondientes.

### Tipos de respuesta

| tipo_respuesta | Significado |
|----------------|-------------|
| `"action"` | El bot ejecuto una accion (scaffold, delete, update, read) |
| `"info"` | El bot responde con informacion (READ) |
| `"error"` | Ocurrio un error en el procesamiento |

### Estructura de respuesta

```json
{
  "tipo_respuesta": "action",
  "mensaje": "Generando modulo Pagos en NestJS...",
  "payload": {
    "accion": "scaffold:module",
    "params": {
      "nombre": "Pagos",
      "tech": "NestJS",
      "template": "module-nestjs"
    },
    "archivos": [
      "modules/pagos/pagos.controller.ts",
      "modules/pagos/pagos.module.ts",
      "modules/pagos/pagos.service.ts"
    ]
  }
}
```

---

## 7. Scaffold

### Proposito

Generar archivos en disco a partir de templates, reemplazando
placeholders con los valores del IR.

### Sistema de templates

Cada template es un directorio con archivos que contienen
placeholders:

| Placeholder | Reemplazo | Ejemplo |
|-------------|-----------|---------|
| `__NAME__` | PascalCase | `Pagos` |
| `__LOWERNAME__` | camelCase | `pagos` |

### Proceso de scaffolding

1. Localizar el directorio de template (`templates/<template>/`)
2. Crear el directorio de salida (`modules/<lowername>/`)
3. Para cada archivo en el template:
   a. Reemplazar `__LOWERNAME__` en el nombre del archivo
   b. Reemplazar `__NAME__` y `__LOWERNAME__` en el contenido
   c. Escribir el archivo de salida
4. Devolver la lista de archivos generados

### Templates disponibles

| Template | Archivos generados |
|----------|-------------------|
| `module-nestjs/` | `__LOWERNAME__.controller.ts`, `__LOWERNAME__.module.ts`, `__LOWERNAME__.service.ts` |
| `entity-nestjs/` | `__LOWERNAME__.entity.ts` |
| `module-prisma/` | `__LOWERNAME__.prisma` |

---

## 8. LOOP Principal (recpl.sh)

### Proposito

Orquestar el pipeline completo en dos modos de operacion:
interactivo y batch.

### Modo interactivo

```
$ ./recpl.sh
RECPL Compiler Bot v1.0.0
Escribe 'quit' para salir.

> crea un modulo de pagos en NestJS
{ "tipo_respuesta": "action", ... }
>
```

Caracteristicas:

- Prompt `> ` para entrada del usuario
- Comandos especiales: `quit`, `salir`, `exit`, `q`, `help`, `version`
- Estado persistente entre instrucciones (via RECPL_STATE_DIR)
- Logging a `/tmp/recpl_loop.log`

### Modo batch

```sh
echo "crea un modulo de pagos en NestJS" | ./recpl.sh
```

Procesa cada linea del stdin como una instruccion independiente.
Termina al encontrar `quit` o EOF.

### Pipeline de procesamiento

```
process_instruction(input)
    │
    ├─ preprocessor.sh    (normalizar)
    ├─ lexer.sh           (tokenizar)
    ├─ parser.sh          (construir AST)
    ├─ semantic.sh        (validar + tabla simbolos)
    ├─ ir_generator.sh    (generar IR)
    └─ synthesis.sh       (responder + scaffolding)
```

Cada etapa captura errores y devuelve un mensaje JSON de error
si falla, permitiendo que el LOOP continue con la siguiente
instruccion.

---

## 9. Flujo Completo (Ejemplo)

### Input

```
crea un modulo de pagos en NestJS
```

### Paso a paso

**Preprocesador:**
```
crea un modulo de pagos en nestjs
```

**Lexer (tokens):**
```json
{"type":"ACTION_CREATE","lexeme":"crea","position":{"line":1,"col":1}}
{"type":"MODULE","lexeme":"modulo","position":{"line":1,"col":6}}
{"type":"ENTITY","lexeme":"un","position":{"line":1,"col":13}}
{"type":"ENTITY","lexeme":"pagos","position":{"line":1,"col":16}}
{"type":"PREP_IN","lexeme":"en","position":{"line":1,"col":22}}
{"type":"TECH_NESTJS","lexeme":"nestjs","position":{"line":1,"col":25}}
```

**Parser (AST):**
```json
{
  "tipo": "Comando",
  "accion": "CREATE",
  "objetivo": { "tipo": "module", "entidades": ["pagos"] },
  "tech": "NestJS"
}
```

**Semantico (AST + symbol table):**
```json
{
  "ast": { ... },
  "symbol_table": {
    "pagos": {
      "tipo": "module",
      "tech": "NestJS",
      "estado": "pending",
      "dependencias": [],
      "scope": "global"
    }
  }
}
```

**IR Generator:**
```json
{
  "accion": "scaffold",
  "tipo": "module",
  "nombre": "pagos",
  "tech": "NestJS",
  "template": "module-nestjs",
  "entidades": ["pagos"],
  "dependencias": [],
  "score": null,
  "trace_id": "trc_1718000000_12345",
  "symbol_table": { ... }
}
```

**Synthesis:**
```json
{
  "tipo_respuesta": "action",
  "mensaje": "Generando modulo Pagos en NestJS...",
  "payload": {
    "accion": "scaffold:module",
    "params": {
      "nombre": "Pagos",
      "tech": "NestJS",
      "template": "module-nestjs"
    },
    "archivos": [
      "modules/pagos/pagos.controller.ts",
      "modules/pagos/pagos.module.ts",
      "modules/pagos/pagos.service.ts"
    ]
  }
}
```

**Output en disco:**
```
modules/pagos/
├── pagos.controller.ts
├── pagos.module.ts
└── pagos.service.ts
```

---

## 10. Decisiones de Diseno

### 10.1 Datos estructurados como JSON

Cada etapa se comunica mediante JSON por stdin/stdout. Esto hace
que el pipeline sea:

- **Pipeable:** Se puede conectar con `|` en shell
- **Depurable:** Se puede inspeccionar la salida de cada etapa
- **Extensible:** Se pueden agregar nuevas etapas entre dos existentes
- **Lenguaje-agnostico:** Cualquier lenguaje que procese JSON puede
  integrarse

### 10.2 Estado en disco, no en memoria

La tabla de simbolos se almacena en archivos de texto en disco.
Esto permite:

- Compartir estado entre invocaciones sin un servidor
- Recuperarse de fallos sin perder la tabla
- Inspeccionar el estado del compilador con herramientas UNIX
  (cat, grep, awk)

### 10.3 Sin ARTICLE token

Las palabras "un", "una", "el", "la" no tienen un tipo de token
propio. Se reconocen contextualmente como ENTITY en el parser.
Esto simplifica el DFA y evita ambiguedades.

### 10.4 Fallo silencioso en preprocesador

Si el preprocesador falla, devuelve el input original. En el
lexer, los caracteres no reconocidos se registran a stderr pero
no detienen el procesamiento. Esto sigue el principio de **robustez
ante entrada mal formada**.

### 10.5 Preprocesador hace case folding

Todo el texto se convierte a minusculas en el preprocesador.
Esto significa que el lexer solo necesita patrones en minusculas,
reduciendo el tamano del DFA a la mitad.

---

## 11. Relacion con el Dragon Book

| Fase RECPL | Fase Dragon Book | Diferencia |
|------------|-----------------|------------|
| Preprocesador | Preprocessor | Ad-hoc (no hay estandar para NLP) |
| Lexer | Analisis lexico | DFA en shell, no generado por Lex/flex |
| Parser | Analisis sintactico | LL(1) manual, no generado por Yacc/bison |
| Semantico | Analisis semantico | Tabla de simbolos en disco |
| IR Generator | Generacion de codigo intermedio | IR canonico en JSON |
| Synthesis | Generacion de codigo final | Scaffolding de archivos NestJS |
| (no implementado) | Optimizacion | No necesaria para scaffolding |
| LOOP principal | (n/a) | REPL: bucle READ-EVAL-PRINT |

El pipeline RECPL omite la fase de optimizacion porque el output
es scaffolding de codigo, no codigo maquina. No hay necesidad de
optimizar registros o instrucciones cuando se generan archivos
TypeScript.

---

## 12. Limitaciones Conocidas

| Limitacion | Causa | Solucion propuesta |
|------------|-------|-------------------|
| Solo 2 techos (NestJS, Prisma) | El lexer reconoce mas techs pero no hay templates | Agregar templates para Express, FastAPI, etc. |
| Sin cache de IR | Cada invocacion reprocesa todo | Cachear IR por hash del input |
| Sin validacion de codigo generado | scaffold.sh no ejecuta el compilador | Agregar paso de validacion post-scaffold |
| Sin recuperacion de errores en parser | Error sintactico = aborto | Implementar panic mode recovery |
| Sin tipado entre etapas | JSON pasa como strings | Validar schema JSON en cada etapa |
| Estado en `/tmp/` | Se pierde al reiniciar | Usar directorio configurable en el proyecto |
