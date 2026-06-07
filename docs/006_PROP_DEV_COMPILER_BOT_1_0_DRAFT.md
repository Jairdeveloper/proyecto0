---
id: 006
area: dev
type: PROP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - proposal
  - compiler
  - bot
  - repl
  - recpl
  - nlp
  - aho
  - dragon-book
summary: "Propuesta de implementacion de un bot RECPL (READ-EVAL-PRINT-LOOP) basado en teoria de compiladores (Aho, Dragon Book). Define lexer, parser, analizador semantico, tabla de simbolos, IR.json y synthesis para procesar instrucciones en lenguaje natural como un compilador."
keywords:
  - compilador
  - bot
  - recpl
  - repl
  - lexer
  - parser
  - analizador-semantico
  - ir
  - tokenizacion
  - aho
  - dragon-book
  - compiler-compiler
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion inicial de la propuesta del bot compilador RECPL
---

# Propuesta: Bot RECPL — Compilador de Lenguaje Natural Basado en Aho

## 1. Concepto General

Sistema que procesa instrucciones en lenguaje natural como un **compilador clasico**
(Aho, Dragon Book cap.1). El usuario escribe una orden y el sistema la tokeniza,
parsea, analiza semanticamente, y sintetiza una respuesta/accion — todo dentro de
un bucle **READ-EVAL-PRINT-LOOP** (REPL).

```
Usuario: "Crea un modulo de pagos en NestJS"
  ↓
[ REPL BOT ]
  ↓
Bot: "Generando modulo Payments en modules/payments/..."
```

---

## 2. Arquitectura General (basada en Aho cap.1)

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONT-END                              │
│                                                             │
│  INPUT (NL string)                                          │
│    ↓                                                        │
│  [PREPROCESADOR]  → normaliza, limpia, segmenta            │
│    ↓                                                        │
│  [LEXER]           → tokeniza → {token, lexema, atributo}  │
│    ↓                    READ(scan), EVAL(act),              │
│                         PRINT(print), LOOP(loop)            │
│    ↓                                                        │
│  [PARSER]          → construye AST                          │
│    ↓                                                        │
│  [ANALIZADOR       → verifica tipos, tabla de simbolos,     │
│   SEMANTICO]         ambitos, reglas semanticas             │
│    ↓                                                        │
├─────────────────────────────────────────────────────────────┤
│                      MIDDLE-END                             │
│                                                             │
│  [SCORER] (opc)   → busca acciones similares en training    │
│    ↓                                                        │
│  [IR.json]         → representacion intermedia canonica     │
│    ↓                                                        │
│  [TRACE] (opc)    → three-address code (trazabilidad)       │
│    ↓                                                        │
├─────────────────────────────────────────────────────────────┤
│                      BACK-END / SYNTHESIS                    │
│                                                             │
│  [SYNTHESIS]       → READ | EVAL | PRINT | LOOP            │
│    ↓                                                        │
│  [BOT]             → responde por chat (texto / acción)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. REPL: READ-EVAL-PRINT-LOOP (el Nucleo)

El bot opera como un **REPL** (READ-EVAL-PRINT-LOOP), analogo al REPL de Lisp
pero con un pipeline compilador completo en cada ciclo.

### 3.1 READ (scan) — Analisis Lexico

Toma una cadena de lenguaje natural y produce tokens.

**Funcion:**

```
read(input_string) → token_stream[]
```

**Reglas Lexicas** (expresiones regulares):

| Token | Patron (regex) | Lexema ejemplo |
|-------|----------------|----------------|
| `ACTION_CREATE` | `crea?r?\|creando\|generar\|make\|new` | `"Crea"` |
| `ACTION_DELETE` | `eliminar\|borrar\|delete\|remove` | `"elimina"` |
| `ACTION_UPDATE` | `actualizar\|modificar\|update\|edit` | `"modifica"` |
| `ACTION_READ` | `mostrar\|listar\|get\|show\|read` | `"listar"` |
| `MODULE` | `modulo\|module` | `"modulo"` |
| `ENTITY` | `[A-Z][a-zA-Z]+` (sustantivo propio) | `"Payments"` |
| `TECH_NESTJS` | `[Nn]est[Jj][Ss]\|NestJS` | `"NestJS"` |
| `TECH_PRISMA` | `[Pp]risma` | `"Prisma"` |
| `PREP_IN` | `en\|para\|de\|in\|for\|of` | `"en"` |
| `SEPARATOR` | `[,\\.;!?]` | `","` |
| `WS` | `[ \t\n]+` | (se ignora) |

**Algoritmo (DFA-based, como Aho p.6):**

```
function read(input):
    tokens = []
    while input not empty:
        skip whitespace
        match longest prefix against all token patterns
        if match found:
            tokens.push({type: matched_type, lexeme: matched_text})
            advance input past matched text
        else:
            error("token no reconocido en: " + input[0:10])
    return tokens
```

**Ejemplo:**

```
Input: "Crea un modulo de pagos en NestJS"
Tokens:
  {ACTION_CREATE, "Crea"}
  {ARTICLE, "un"}
  {MODULE, "modulo"}
  {PREP, "de"}
  {ENTITY, "pagos"}
  {PREP, "en"}
  {TECH_NESTJS, "NestJS"}
```

### 3.2 EVAL (act) — Analisis Sintactico + Semantico

Toma el stream de tokens y construye un AST (arbol sintactico) + verifica reglas semanticas.

**Funcion:**

```
eval(token_stream, symbol_table) → ast_node
```

#### Gramatica Sintactica (BNF)

```
comando     → accion modulo_espec opcional_tech

accion      → ACTION_CREATE
             | ACTION_DELETE
             | ACTION_UPDATE
             | ACTION_READ

modulo_espec → MODULE ARTICLE? ENTITY (PREP ENTITY)*
             | ENTITY

opcional_tech → PREP TECH (SEPARATOR TECH)*
              | ε
```

**Reglas Sintacticas:**

| Regla | Descripcion |
|-------|-------------|
| `comando → accion modulo_espec` | Todo comando requiere una accion + un objetivo |
| `modulo_espec → MODULE ENTITY` | "modulo Payments" → modulo específico |
| `modulo_espec → ENTITY` | "Payments" → entidad directa |
| `opcional_tech → PREP TECH` | "en NestJS" → tecnologia destino |
| `ε` | La tecnologia es opcional |

#### AST Generado:

```
Comando
├── Accion: CREATE
├── Objetivo: Modulo
│   └── Entidad: "Payments"
└── TechStack:
    └── "NestJS"
```

#### Reglas Semanticas (atributos heredados y sintetizados):

| Produccion | Accion Semantica | Tipo |
|------------|-----------------|------|
| `comando → accion modulo_espec` | `comando.accion = accion.val; comando.objetivo = modulo_espec.val` | Sintetizado |
| `accion → ACTION_CREATE` | `accion.val = "CREATE"; accion.tipo = "write"` | Heredado (constante) |
| `modulo_espec → MODULE ENTITY` | `modulo_espec.val = {tipo: "module", entidad: ENTITY.lexema}` | Sintetizado |
| `modulo_espec → ENTITY` | `modulo_espec.val = {tipo: "entity", entidad: ENTITY.lexema}` | Sintetizado |
| `opcional_tech → PREP TECH` | `opcional_tech.val = TECH.lexema` | Sintetizado |

#### Tabla de Simbolos:

```
symbol_table = {
  "Payments": {
    tipo: "module",
    tech: "NestJS",
    estado: "pending",
    dependencias: []
  }
}
```

### 3.3 PRINT — Synthesis

Toma el AST validado semanticamente y produce la salida del bot.

**Funcion:**

```
print(ast_node, ir_json) → bot_response (string + acciones)
```

**Reglas de Sintesis:**

| Token AST | Accion del Bot |
|-----------|---------------|
| `CREATE` + module | "Generando modulo {entidad}..." + crear estructura de archivos |
| `DELETE` + module | "Eliminando modulo {entidad}..." + borrar estructura |
| `UPDATE` + entity | "Modificando {entidad}..." + parchear archivos |
| `READ` + entity | "Mostrando {entidad}..." + listar/cargar datos |

**Formato de salida:**

```json
{
  "tipo_respuesta": "accion",
  "mensaje": "Generando modulo Payments en NestJS...",
  "payload": {
    "accion": "scaffold:module",
    "params": { "nombre": "Payments", "tech": "NestJS" },
    "archivos": ["modules/payments/", "modules/payments/payments.module.ts"]
  }
}
```

### 3.4 LOOP — El bucle principal

**Funcion:**

```
loop():
    while true:
        input = read_user_input()
        tokens = READ(input)           # lexer
        ast = EVAL(tokens)             # parser + semantica
        ir = GENERATE_IR(ast)          # representacion intermedia
        response = PRINT(ast, ir)      # sintesis
        send_response(response)        # output
```

**Diagrama:**

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  READ    │ → │  EVAL    │ → │  PRINT   │ → │  LOOP    │
│ (lexer)  │   │ (parser+ │   │(synthesis│   │(recursivo│
│          │   │ semant)  │   │   + IR)  │   │  ciclo)  │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
      ↑                                            │
      └────────────────────────────────────────────┘
```

---

## 4. Pipeline de Compilacion Completo

```
INPUT: "Crea un modulo de pagos en NestJS"
  │
  ▼
[1. PREPROCESADOR]
  - Normalizar a minusculas
  - Eliminar signos de puntuacion redundantes
  - Segmentar por oraciones
  OUTPUT: "crea un modulo de pagos en nestjs"
  │
  ▼
[2. LEXER (READ)]
  - DFA sobre el stream de caracteres
  - Match mas largo (maximal munch)
  OUTPUT: [{ACTION_CREATE,"crea"},{ARTICLE,"un"},{MODULE,"modulo"},
           {PREP,"de"},{ENTITY,"pagos"},{PREP,"en"},{TECH_NESTJS,"nestjs"}]
  │
  ▼
[3. PARSER (sintactico)]
  - BNF recursivo descendente (LL(1))
  - Construye AST
  OUTPUT:
    Comando(accion=CREATE, objetivo=Modulo("pagos"), tech=NestJS)
  │
  ▼
[4. ANALIZADOR SEMANTICO]
  - Verificar que entidad "pagos" esta en tabla de simbolos (scope)
  - Resolver tecnologia: NestJS → template NestJS module
  - Si no existe: crear entrada en tabla de simbolos
  OUTPUT: AST validado + symbol_table actualizada
  │
  ▼
[5. SCORER (opcional)]
  - Busca acciones similares en historial de training
  - Si hay match >80%: sugiere accion predefinida
  - Si no: procede con generacion desde cero
  OUTPUT: score + suggested_actions[]
  │
  ▼
[6. IR.json]
  Representacion intermedia canonica:
  {
    "accion": "scaffold",
    "tipo": "module",
    "nombre": "pagos",
    "tech": "nestjs",
    "template": "module-nestjs",
    "dependencias": [],
    "score": null,
    "trace_id": "trc_001"
  }
  │
  ▼
[7. TRACE (opcional)]
  Codigo de tres direcciones (three-address code):
  t1 = lookup_template("module-nestjs")
  t2 = resolve_path("pagos", t1.path)
  t3 = generate_files(t2, {nombre: "pagos"})
  OUTPUT: secuencia lineal de instrucciones TAC
  │
  ▼
[8. SYNTHESIS (PRINT)]
  Ejecutar acciones:
  - mkdir -p modules/payments/
  - cp template/* modules/payments/
  - sed -i "s/__NAME__/Payments/g" modules/payments/*
  OUTPUT: respuesta del bot
  │
  ▼
OUTPUT: "✅ Modulo Payments creado en modules/payments/"

[9. LOOP]
  Vuelve a READ para la siguiente instruccion
```

---

## 5. Especificacion de Componentes

### 5.1 Preprocesador

```
preprocess(raw_input):
    1. trim leading/trailing whitespace
    2. normalize unicode (NFKC)
    3. fold to lowercase (opcional, segun idioma)
    4. remove repeated punctuation
    5. split on sentence boundaries (.;!?)
    6. return clean string[]
```

### 5.2 Lexer (READ)

```
lexer(input_string) → token[]:
    1. init DFA state = 0
    2. for each char:
         advance DFA state
         if accepting state: record match
         if dead state: backtrack to last accept
    3. emit token for matched lexeme
    4. repeat until input exhausted
```

**Estructura Token:**

```json
{
  "type": "ACTION_CREATE",
  "lexeme": "crea",
  "position": { "line": 1, "col": 1 },
  "literal": null
}
```

### 5.3 Parser (EVAL — sintactico)

```
parser(tokens) → ast:
    1. init cursor = 0
    2. call parse_comando()
    3. if cursor != len(tokens): error("syntax error at token " + cursor)
    4. return ast_root

parse_comando():
    accion = parse_accion()
    objetivo = parse_modulo_espec()
    tech = parse_opcional_tech()
    return AST("Comando", [accion, objetivo, tech])
```

### 5.4 Analizador Semantico (EVAL — semantico)

```
semantic_analyzer(ast, symbol_table) → validated_ast:
    1. visit each AST node
    2. for each identifier: lookup in symbol_table
    3. if not found and is declaration: insert into symbol_table
    4. if not found and is reference: error("undefined: " + name)
    5. type check: verificar compatibilidad
    6. return validated_ast
```

### 5.5 Generador IR

```
generate_ir(ast) → ir_json:
    {
      "action": ast.accion.tipo,
      "scope": ast.objetivo.tipo,
      "entity": ast.objetivo.entidad,
      "tech": ast.tech?.nombre,
      "params": extract_params(ast),
      "symbols": symbol_table.snapshot(),
      "dependencies": resolve_deps(ast)
    }
```

### 5.6 Tracer (opcional — three-address code)

```
trace(ir_json) → tac[]:
    1. for each operation in ir_json:
         tN = operation(params)
         tac.append({ "result": tN, "op": operation.name, "args": params })
    2. return tac

Ejemplo para "crear modulo pagos NestJS":
  t1 = validate_name("pagos")
  t2 = template_path("module", "nestjs")
  t3 = copy_template(t2, "modules/pagos")
  t4 = configure_module("modules/pagos/payments.module.ts")
```

### 5.7 Synthesis (PRINT)

```
synthesis(ir_json, tac[]) → bot_response:
    case ir_json.action:
      "scaffold" → execute_scaffold(ir_json)
      "delete"   → execute_delete(ir_json)
      "update"   → execute_update(ir_json)
      "read"     → execute_read(ir_json)
    return {
      "type": "action" | "info" | "error",
      "message": formatear_mensaje(result),
      "payload": result
    }
```

---

## 6. Reglas del Sistema

### 6.1 Reglas Lexicas (resumen)

| Regla | Formula | Ejemplo |
|-------|---------|---------|
| Maximal munch | El match mas largo gana | `"crear"` no se confunde con `"crea"` |
| Prioridad de keywords | Keywords > identificadores | `"module"` es MODULE, no ENTITY |
| Whitepace | `[ \t\n]+` se ignora | `"crea  module"` = `"crea module"` |
| Case insensitive | `[Cc][Rr][Ee][Aa]` | `"CREA"` = `"crea"` |

### 6.2 Reglas Sintacticas (resumen)

| Regla | Formula |
|-------|---------|
| Unicidad de accion | Un solo ACTION por comando |
| Objetivo requerido | Todo ACTION debe tener un objetivo |
| Tech binding | PREP TECH se liga al modulo mas cercano |
| Separacion | `;` separa comandos multiples |

### 6.3 Reglas Semanticas (resumen)

| Regla | Formula |
|-------|---------|
| Declaracion before use | La entidad debe existir o ser creada |
| Type checking | Tech stack debe ser soportado |
| Scope | Cada modulo tiene su propio scope de nombres |
| Unicidad | No duplicar modulos con el mismo nombre |

---

## 7. Tabla de Tareas

| ID | Tarea | Componente | Depende de | Esfuerzo | Estado |
|----|-------|------------|------------|----------|--------|
| TASK-001 | Definir alfabeto y conjunto de tokens del lenguaje NL | Lexer | — | M | pending |
| TASK-002 | Implementar DFA del lexer (READ) | Lexer | TASK-001 | L | pending |
| TASK-003 | Implementar preprocesador de entrada | Preproc | — | S | pending |
| TASK-004 | Definir gramatica BNF del lenguaje de comandos | Parser | TASK-001 | M | pending |
| TASK-005 | Implementar parser recursivo descendente (EVAL) | Parser | TASK-004 | L | pending |
| TASK-006 | Implementar tabla de simbolos (hash table) | Semantico | — | M | pending |
| TASK-007 | Implementar analizador semantico con type checking | Semantico | TASK-005, TASK-006 | L | pending |
| TASK-008 | Implementar generador IR.json | IR | TASK-007 | M | pending |
| TASK-009 | Implementar tracer (three-address code) | Trace | TASK-008 | S | pending |
| TASK-010 | Implementar synthesis (PRINT) | Synthesis | TASK-008 | M | pending |
| TASK-011 | Implementar el bucle LOOP principal | RECPL | TASK-002, TASK-005, TASK-010 | M | pending |
| TASK-012 | Implementar scorer (busqueda de patrones similares) | Scorer | TASK-008 | L | pending |
| TASK-013 | Integrar con sistema de templates (scaffolding NestJS) | Synthesis | TASK-010 | M | pending |
| TASK-014 | Pruebas unitarias de cada fase del pipeline | Testing | TASK-011 | L | pending |

---

## 8. Fases de Implementacion

| Fase | Nombre | Tareas | Duracion est. |
|------|--------|--------|---------------|
| FASE-1 | Nucleo RECPL | TASK-001 al TASK-005, TASK-011 (parcial) | 5-7 dias |
| FASE-2 | Semantica e IR | TASK-006 al TASK-008 | 3-4 dias |
| FASE-3 | Synthesis y Output | TASK-010, TASK-013 | 2-3 dias |
| FASE-4 | Trazabilidad y Scoring | TASK-009, TASK-012 | 2-3 dias |
| FASE-5 | End-to-end y Tests | TASK-011 (completar), TASK-014 | 3-4 dias |

---

## 9. Referencias

- **Aho, Sethi, Ullman.** *Compilers: Principles, Techniques, and Tools* (Dragon Book), cap.1-4.
- **Louden.** *Compiler Construction: Principles and Practice*, caps.1-2.
- **005_SPEC_DOC_COMPILADORTHEORY_1.0_ACTIVE.md** — Teoria de compiladores del proyecto.
- **004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md** — Especificacion del procesador de documentacion.
- **003_PROP_DOC_DOC_PROCESSOR_1.0_DRAFT.md** — Propuesta inicial del procesador.
- **000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md** — Guia de estilo shell (en docs/).
