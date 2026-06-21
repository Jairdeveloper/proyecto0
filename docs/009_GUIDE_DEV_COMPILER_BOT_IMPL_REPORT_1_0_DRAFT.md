---
id: 009
area: dev
type: guide
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - implementation-report
  - compiler
  - bot
  - recpl
  - fases
  - tareas
summary: "Reporte detallado de implementacion del bot RECPL. Describe todas las acciones realizadas en cada fase y tarea del plan definido en 006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md y 007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md, incluyendo diseno, bugs encontrados, fixes aplicados y estado final de cada componente."
keywords:
  - implementacion
  - reporte
  - recpl
  - compiler-bot
  - fases
  - tareas
  - bugs
  - pipeline
  - scaffolding
  - tests
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Reporte completo de implementacion del bot RECPL, todas las fases y tareas completadas
---

# Reporte de Implementacion: Bot RECPL

## Resumen Ejecutivo

Se implemento un bot shell (RECPL) que procesa instrucciones en lenguaje natural
utilizando un pipeline compilador clasico (Aho, Dragon Book). El pipeline completo
opera como un REPL: **READ** (lexer) → **EVAL** (parser + semantico) → **PRINT** (synthesis),
todo dentro de un **LOOP** principal.

**14 tareas definidas, 12 completadas, 2 opcionales pendientes.**
**47 tests automatizados, todos pasando.**

---

## FASE-1: Nucleo RECPL (TASK-001 al TASK-005)

### TASK-001 — Definir alfabeto y conjunto de tokens

**Implementado en:** `frontend/lexer.sh` (lineas 58-66)

**Acciones:**
- Definir tokens: `ACTION_CREATE`, `ACTION_DELETE`, `ACTION_UPDATE`, `ACTION_READ`,
  `MODULE`, `ENTITY`, `TECH_NESTJS`, `TECH_PRISMA`, `PREP_IN`, `SEPARATOR`
- Cada token con su expresion regular ERE (soportada por awk)
- Prioridad: keywords evaluadas antes que ENTITY para evitar captura de palabras reservadas

**Tokens definidos:**

| Token | Patron | Prioridad |
|-------|--------|-----------|
| `ACTION_CREATE` | `creando\|crear\|crea\|generar\|make\|new` | Alta |
| `ACTION_DELETE` | `eliminar\|borrar\|delete\|remove` | Alta |
| `ACTION_UPDATE` | `actualizar\|modificar\|update\|edit` | Alta |
| `ACTION_READ` | `mostrar\|listar\|get\|show\|read` | Alta |
| `MODULE` | `modulo\|module` | Alta |
| `TECH_NESTJS` | `nestjs` | Alta |
| `TECH_PRISMA` | `prisma` | Alta |
| `PREP_IN` | `en\|para\|de\|in\|for\|of` | Alta |
| `ENTITY` | `[a-z][a-z]*` | Baja (catch-all) |
| `SEPARATOR` | `[,.;!?]` | Baja |

### TASK-002 — DFA lexer (READ)

**Implementado en:** `frontend/lexer.sh` (lineas 50-108, funcion `match_token`)

**Acciones:**
- Implementar DFA con maximal munch usando awk ERE
- La funcion `awk_match_prefix` usa `match($0, /^(pattern)/)` y `RLENGTH` para
  obtener el match mas largo
- Keywords evaluadas primero; ENTITY solo si ninguna keyword matchea mas largo
- Whitespace se salta con `awk_match_prefix` para `[ \t]+`
- Tokens no reconocidos: error a stderr con columna, no detienen el procesamiento

**Bug encontrado y fix:**
- `sed` con BRE usa `\|` para alternancia, pero NO hace maximal munch correctamente
  (toma el primer match, no el mas largo). Fix: usar awk con ERE donde `|` es
  alternancia nativa y `match()` con `RLENGTH` da la longitud exacta.

**Salida:** JSON token por linea:
```json
{"type":"ACTION_CREATE","lexeme":"crea","position":{"line":1,"col":1}}
```

### TASK-003 — Preprocesador

**Implementado en:** `frontend/preprocessor.sh`

**Acciones:**
- Trim whitespace inicial y final
- Fold a lowercase (via `tr '[:upper:]' '[:lower:]'`)
- Colapsar puntuacion repetida (e.g., `!!` → `!`)
- Dividir en oraciones por `.;!?`
- Fallo silencioso: si falla, devuelve input original

**Pipeline:** `preprocessor.sh "texto"` → stdout → `lexer.sh "$(cat)"` ...

### TASK-004 — Gramatica BNF

**Implementado en:** `frontend/parser.sh` (comentario inicial, lineas 10-16)

**Gramatica:**
```
comando       → accion modulo_espec opcional_tech
accion        → ACTION_CREATE | ACTION_DELETE | ACTION_UPDATE | ACTION_READ
modulo_espec  → MODULE ARTICLE? PREP? ENTITY (PREP ENTITY)*
              | ENTITY
opcional_tech → PREP TECH (SEPARATOR TECH)*
              | ε
```

**Nota:** La gramatica fue modificada durante la implementacion para aceptar
`PREP` opcional antes de la `ENTITY` principal (e.g., "modulo **de** pagos").
Originalmente era solo `MODULE ARTICLE? ENTITY (PREP ENTITY)*`.

### TASK-005 — Parser recursivo descendente

**Implementado en:** `frontend/parser.sh`

**Acciones:**
- Parser LL(1) con una funcion por no-terminal:
  - `parse_comando()` — orquesta accion + modulo_espec + opcional_tech
  - `parse_accion()` — matchea ACTION_CREATE/DELETE/UPDATE/READ
  - `parse_modulo_espec()` — maneja MODULE (con o sin articulo) o ENTITY directa
  - `parse_opcional_tech()` — PREP + TECH, opcional
  - `parse_entity_list()` — helper para `[PREP] ENTITY (PREP ENTITY)*`
- Estado global via variables (`cursor`, `token_count`, etc.) en vez de subshells
  (porque subshells pierden estado)
- Lookahead para PREP+TECH: si PREP es seguido de TECH, se deja para opcional_tech

**Bug encontrado y fix:**
- **Articulos antes de MODULE:** La gramatica espera `MODULE ARTICLE?`, pero el lexer
  no tiene token `ARTICLE` — "un", "una" son `ENTITY`. El parser original solo
  reconocia articulos dentro del bloque `MODULE`. Fix: en la rama `ENTITY` de
  `parse_modulo_espec`, detectar si la ENTITY es un articulo y hacer lookahead
  para ver si le sigue MODULE. Si es asi, consumir articulo y entrar a la rama MODULE.
- **PREP antes de ENTITY:** "modulo de pagos" — el `PREP` entre MODULE y ENTITY no
  estaba permitido por la gramatica. Fix: agregar `PREP?` opcional antes de la
  ENTITY principal y refactorizar en `parse_entity_list()`.

**Salida:** AST en JSON:
```json
{"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":"nestjs"}
```

---

## FASE-2: Semantica e IR (TASK-006 al TASK-008)

### TASK-006 — Tabla de simbolos

**Implementado en:** `frontend/semantic.sh` (lineas 32-100)

**Acciones:**
- Hash table sobre archivo temporal (`SYMBOL_FILE`) con formato:
  `nombre|tipo|tech|estado|scope`
- Operaciones: `symbol_init()`, `symbol_insert()`, `symbol_lookup()`,
  `symbol_exists()`, `symbol_delete()`
- Scope stack via archivo temporal (`SCOPE_FILE`) con `scope_init()`,
  `scope_push()`, `scope_pop()`, `scope_current()`
- Persistencia entre invocaciones via variable de entorno `RECPL_STATE_DIR`
- En modo LOOP, `symbol_init()` preserva estado existente

**Bug encontrado y fix:**
- **Persistencia:** `symbol_init()` hacia `: > "$SYMBOL_FILE"` que truncaba el
  archivo en cada invocacion, perdiendo el estado previo. Fix: en modo
  `RECPL_STATE_DIR`, si el archivo ya existe y no esta vacio, preservarlo.

### TASK-007 — Analizador semantico

**Implementado en:** `frontend/semantic.sh` (lineas 144-201, funcion `semantic_analyzer`)

**Acciones:**
- Recibe AST JSON del parser por stdin
- Valida tech stack contra lista blanca: `NestJS` o `Prisma`
- Para `CREATE|UPDATE`: inserta entidades en tabla de simbolos (error si duplicado)
- Para `DELETE|READ`: verifica que la entidad exista (error si no existe)
- Normaliza tech a capitalizada: "nestjs" → "NestJS", "prisma" → "Prisma"
- Genera salida combinada: AST validado + snapshot de tabla de simbolos

**Bug encontrado y fix:**
- **Subshell en `validate_tech`:** La funcion se llamaba via `$()`:
  `tech=$(validate_tech "$raw_tech")`. El `exit 1` dentro de `validate_tech`
  solo salia del subshell, no del script. Fix: usar variable global
  `g_tech_validated` + flag `g_tech_error` para comunicar el resultado.
- **Extraccion de `obj_tipo`:** `json_field` buscaba el primer `"tipo"` en el JSON,
  que era el del nodo raiz (`"Comando"`), no el de `objetivo.tipo` (`"module"`).
  Fix: extraer el valor desde el sub-objeto `"objetivo"` con awk:
  `awk -F'"objetivo":' '{print $2}' | awk -F'"tipo":"' '{print $2}' | awk -F'"' '{print $1}'`

**Salida:** JSON combinado:
```json
{"ast":{...},"symbol_table":{"pagos":{"tipo":"module","tech":"NestJS","estado":"pending",...}}}
```

### TASK-008 — Generador IR.json

**Implementado en:** `middleend/ir_generator.sh`

**Acciones:**
- Recibe AST validado + symbol table del semantic.sh
- Mapea acciones: CREATE → `scaffold`, DELETE → `delete`, UPDATE → `update`, READ → `read`
- Mapea template segun tipo+tech: `module-nestjs`, `entity-nestjs`, `module-prisma`, etc.
- Genera `trace_id` unico: `trc_<timestamp>_<PID>`
- Extrae entidades y symbol table del JSON combinado

**Bug encontrado y fix:**
- **Extraccion de campos desde JSON combinado:** El `json_field` original buscaba
  keys en el JSON completo (ast+symbol_table), encontrando campos en symbol_table
  que no correspondian. Fix: extraer solo el objeto `"ast"` con sed antes de
  buscar campos, y usar funciones especificas: `extract_ast_field()`,
  `extract_nested_ast_field()`, `extract_ast_entities()`.
- **JSON quoting de entidades:** `"entidades": [$entidades]` producia
  `[pagos]` sin comillas. Fix: loop con IFS para quoteo explicito.

**Salida:** IR.json canonico:
```json
{
  "accion": "scaffold",
  "tipo": "module",
  "nombre": "pagos",
  "tech": "nestjs",
  "template": "module-nestjs",
  "entidades": ["pagos"],
  "dependencias": [],
  "score": null,
  "trace_id": "trc_1780863334_12825",
  "symbol_table": {...}
}
```

---

## FASE-3: Synthesis y Output (TASK-010, TASK-013)

### TASK-010 — Synthesis/PRINT

**Implementado en:** `backend/synthesis.sh`

**Acciones:**
- Recibe IR.json del ir_generator.sh por stdin
- Funciones por tipo de accion:
  - `execute_scaffold()` — CREATE: mensaje "Generando ..." + payload scaffold
  - `execute_delete()` — DELETE: mensaje "Eliminando ..."
  - `execute_update()` — UPDATE: mensaje "Modificando ..."
  - `execute_read()` — READ: mensaje "Mostrando ..." (tipo_respuesta: "info")
- Capitaliza nombre de entidad (primera letra mayuscula)
- Integra con scaffold.sh para generacion real de archivos

**Bug encontrado y fix:**
- **Lectura multi-linea:** IR.json es multi-linea. El patron `while read line; do
  ast_line="$line"; done` solo capturaba la ultima linea. Fix: concatenar todas
  las lineas en una sola variable con `ir_json="$ir_json$line"`.

### TASK-011 — LOOP principal (integrado en FASE-3)

**Implementado en:** `recpl.sh`

**Acciones:**
- Modo interactivo: prompt `> `, lee input del usuario, ejecuta pipeline, muestra respuesta
- Modo batch: lee stdin, procesa multiples instrucciones secuencialmente
- Comandos especiales: `quit`, `salir`, `exit`, `q`, `help`, `version`
- Estado persistente via `RECPL_STATE_DIR=/tmp/recpl_state_$$`
- Manejo de errores: cada etapa del pipeline verifica exit code; si falla,
  muestra error y continua con la siguiente instruccion
- Trap para limpieza en INT/TERM

### TASK-013 — Template scaffolding

**Implementado en:** `backend/scaffold.sh` + `templates/`

**Acciones:**
- Crear directorios de templates:
  - `templates/module-nestjs/` — 3 archivos: module, controller, service
  - `templates/entity-nestjs/` — 1 archivo: entity
  - `templates/module-prisma/` — 1 archivo: prisma model
- Placeholders: `__NAME__` (PascalCase) y `__LOWERNAME__` (camelCase)
- `scaffold.sh` copia templates, reemplaza placeholders, escribe en `modules/<name>/`
- Integrado en synthesis.sh: cuando se genera un scaffold, llama a scaffold.sh
  automaticamente y reporta los archivos generados en el payload

---

## FASE-4: Trazabilidad y Scoring (TASK-009, TASK-012)

**Estado:** PENDIENTE (opcional)

Tareas no implementadas por ser componentes opcionales:

- **TASK-009 (Tracer):** generacion de codigo de tres direcciones (TAC) para
  trazabilidad de operaciones. No necesario para el funcionamiento base del bot.
- **TASK-012 (Scorer):** busqueda de patrones similares en historial de entrenamiento.
  Funcionalidad avanzada para recomendaciones.

---

## FASE-5: End-to-end y Tests (TASK-014)

### TASK-014 — Tests

**Implementado en:** `tests/run_tests.sh`

**47 tests, todos pasando.**

| Grupo | Tests | Descripcion |
|-------|-------|-------------|
| Sintaxis | 8 | `bash -n` en todos los scripts |
| Preprocesador | 3 | trim, lowercase, split sentences |
| Lexer | 8 | token count, cada token, case insensitive via preprocessor, maximal munch |
| Parser | 5 | AST con CREATE, MODULE, entity directa, tech, entidad |
| Pipeline completo | 5 | respuesta JSON, scaffold, template generic |
| Errores semanticos | 2 | READ undefined, invalid tech |
| LOOP batch | 4 | CREATE, READ, scaffold en payload, error recovery |
| Scaffolding | 3 | archivos generados, module.ts, existencia en disco |
| Persistencia | 1 | CREATE + READ entre invocaciones |
| Ejecutables | 8 | todos los scripts con permiso +x |

---

## Lecciones Aprendidas / Discoveries

### Shell scripting

1. **Subshells pierden estado:** `$(func)` ejecuta en subshell; `exit`, `return`,
   cambios de variables no afectan al shell padre. Usar variables globales para
   comunicacion entre funciones.

2. **Subshells y `exit 1`:** Llamar `exit 1` dentro de `$()` solo termina el
   subshell, no el script. El script continua como si nada hubiera pasado.

3. **Shadowing de variables en funciones:** En POSIX sh, las variables de
   funcion son globales. Un parametro `result="$2"` en una funcion `assert()`
   SOBREESCRIBE la variable global `result`. Usar prefijo `_` para parametros
   de funciones de test.

4. **`sed` BRE vs ERE:** `sed` usa BRE por defecto donde `|` no es alternancia
   sino `\|`. Para maximal munch, usar awk con ERE donde `|` es alternancia nativa
   y `match()`/`RLENGTH` dan la longitud exacta.

### Diseño del pipeline

5. **Token ARTICLE no necesario:** El lexer no necesita token `ARTICLE` — las
   palabras "un", "una", "el", "la" se tokenizan como `ENTITY` y el parser las
   reconoce contextualmente mediante `is_article()`.

6. **Gramatica necesita lookahead:** En `parse_modulo_espec`, al encontrar un
   token `PREP`, el parser debe mirar el siguiente token. Si es `TECH`, el PREP
   pertenece a `opcional_tech`, no a `modulo_espec`.

7. **PREP opcional antes de ENTITY:** "modulo de pagos" requiere `PREP?` antes
   de la ENTITY principal. La gramatica original solo tenia `(PREP ENTITY)*`
   despues de la ENTITY principal.

### JSON handling

8. **`json_field` con `awk -F'"'`:** Funciona para JSON plano pero falla con
   valores `null` (sin quotes) y objetos anidados. Para el JSON combinado
   `{"ast":{...},"symbol_table":{...}}`, extraer primero el sub-objeto con `sed`.

---

## Inventario de Archivos

```
compiler-bot/
├── frontend/
│   ├── preprocessor.sh     # Normaliza input (trim, lowercase, split)
│   ├── lexer.sh            # DFA tokenizer con maximal munch
│   ├── parser.sh           # Parser LL(1) recursivo descendente
│   └── semantic.sh         # Tabla de simbolos + analisis semantico
├── middleend/
│   └── ir_generator.sh     # AST validado → IR.json canonico
├── backend/
│   ├── synthesis.sh        # IR.json → respuesta del bot (PRINT)
│   └── scaffold.sh         # Renderiza templates → archivos
├── templates/
│   ├── module-nestjs/      # NestJS module scaffold (3 files)
│   ├── entity-nestjs/      # NestJS entity scaffold (1 file)
│   └── module-prisma/      # Prisma model scaffold (1 file)
├── recpl.sh                # LOOP principal (interactivo/batch)
└── tests/
    └── run_tests.sh        # Suite de 47 tests
```

---

## Estado Final de Tareas

| ID | Tarea | Estado | Componente | Lineas de codigo |
|----|-------|--------|------------|-----------------|
| TASK-001 | Alfabeto/tokens | COMPLETED | lexer.sh | ~10 (definiciones) |
| TASK-002 | DFA lexer | COMPLETED | lexer.sh | ~110 |
| TASK-003 | Preprocesador | COMPLETED | preprocessor.sh | ~60 |
| TASK-004 | Gramatica BNF | COMPLETED | parser.sh | ~20 (comentarios + codigo) |
| TASK-005 | Parser recursivo | COMPLETED | parser.sh | ~240 |
| TASK-006 | Tabla de simbolos | COMPLETED | semantic.sh | ~70 |
| TASK-007 | Analizador semantico | COMPLETED | semantic.sh | ~60 |
| TASK-008 | Generador IR | COMPLETED | ir_generator.sh | ~130 |
| TASK-009 | Tracer (TAC) | PENDING | — | — |
| TASK-010 | Synthesis/PRINT | COMPLETED | synthesis.sh | ~170 |
| TASK-011 | LOOP principal | COMPLETED | recpl.sh | ~150 |
| TASK-012 | Scorer | PENDING | — | — |
| TASK-013 | Template scaffolding | COMPLETED | scaffold.sh + templates/ | ~80 + 5 templates |
| TASK-014 | Tests | COMPLETED | tests/run_tests.sh | ~250, 47 tests |
