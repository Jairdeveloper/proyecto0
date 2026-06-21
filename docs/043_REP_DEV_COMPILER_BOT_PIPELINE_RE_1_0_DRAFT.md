---
id: 043
area: dev
type: rep
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - report
  - reverse-engineering
  - pipeline
  - debugger
  - instrumentation
  - recpl
summary: "Reporte de ingenieria inversa del pipeline RECPL. Analisis detallado de las 6 etapas (preprocessor, lexer, parser, semantic, ir_generator, synthesis), flujo de datos, tokenizacion DFA, gramatica LL(1), tabla de simbolos, IR canonico y synthesis. Incluye metricas de rendimiento, deteccion de bordes y bugs conocidos."
keywords:
  - reporte
  - ingenieria-inversa
  - pipeline
  - lexer
  - parser
  - semantic
  - ir
  - synthesis
  - dfa
  - ll1
  - metricas
  - debugger
changelog:
  - version: 1.0
    date: 2026-06-12
    author: workflow-agent
    description: Ingenieria inversa del pipeline RECPL usando pipeline_debugger.sh — 10 escenarios, 6 etapas analizadas, 3 bugs detectados
---
# Reporte de Ingenieria Inversa: Pipeline RECPL

> **Herramienta usada:** `compiler-bot/pipeline_debugger.sh`
> **Fecha del analisis:** 2026-06-12
> **Objetivo:** Mapear el flujo interno del pipeline RECPL, identificar
> patrones, anomalias, cuellos de botella y comportamientos no documentados.

---

## 0. Resumen Ejecutivo

Se analizo el pipeline RECPL ejecutando 10 escenarios instrumentados
con `pipeline_debugger.sh`. El pipeline consta de 6 etapas secuenciales
que transforman lenguaje natural en comandos de scaffolding NestJS/Prisma.

**Hallazgos principales:**

1. El lexer DFA es la etapa mas lenta (~44% del tiempo total)
2. El guion bajo (`_`) rompe el lexer porque no es un caracter reconocido
3. La tabla de simbolos persiste en disco via `RECPL_STATE_DIR`
4. El pipeline deterministico cubre ~20 palabras clave; todo lo demas
   delega al LLM
5. El modo `--output` tiene un bug: redirige el JSON final a /dev/null

---

## 1. Arquitectura del Pipeline

### 1.1 Vista General

```
ENTRADA (texto)
    │
    ▼
┌─────────────────┐
│ preprocessor.sh │  Normalizacion: lowercase, colapso espaciado
│   (frontend)    │  Input: $1 (arg) → Output: texto normalizado
└────────┬────────┘
         │ stdout
         ▼
┌─────────────────┐
│ lexer.sh        │  DFA tokenizer: 6 tipos de token
│   (frontend)    │  Input: $1 (arg) → Output: JSON tokens (1/linea)
└────────┬────────┘
         │ stdout
         ▼
┌─────────────────┐
│ parser.sh       │  LL(1) recursive descent
│   (frontend)    │  Input: stdin (tokens) → Output: AST JSON
└────────┬────────┘
         │ stdout
         ▼
┌─────────────────┐
│ semantic.sh     │  Type checking + symbol table
│   (frontend)    │  Input: stdin (AST) → Output: AST validado
└────────┬────────┘   Lee/escribe RECPL_STATE_DIR/
         │ stdout
         ▼
┌─────────────────┐
│ ir_generator.sh │  AST → IR canonico
│   (middleend)   │  Input: stdin (AST validado) → Output: IR.json
└────────┬────────┘
         │ stdout
         ▼
┌─────────────────┐
│ synthesis.sh    │  IR → respuesta JSON del bot
│   (backend)     │  Input: stdin (IR.json) → Output: JSON final
└────────┬────────┘
         │ stdout
         ▼
    RESPUESTA (JSON)
```

### 1.2 Tipos de Input por Etapa

| Etapa | Tipo | Mecanismo |
|-------|------|-----------|
| preprocessor | `arg` | `script.sh "$texto"` |
| lexer | `arg` | `script.sh "$texto"` |
| parser | `stdin` | `echo "$tokens" \| script.sh` |
| semantic | `stdin` | pipe desde parser |
| ir_generator | `stdin` | pipe desde semantic |
| synthesis | `stdin` | pipe desde ir_generator |

### 1.3 Tamanio del Codigo Fuente

| Script | Lineas | Rol |
|--------|--------|-----|
| pipeline_debugger.sh | 784 | Instrumentacion (este analisis) |
| recpl.sh | 352 | Bucle principal (LOOP) |
| parser.sh | 340 | Analizador sintactico LL(1) |
| semantic.sh | 245 | Analizador semantico + tabla de simbolos |
| synthesis.sh | 199 | Generacion de respuesta JSON |
| ir_generator.sh | 183 | Generador de IR canonico |
| router.sh | 177 | Ruteo deterministico/LLM |
| lexer.sh | 165 | Analizador lexico DFA |
| llm_classifier.sh | 170 | Clasificador LLM (no analizado) |
| preprocessor.sh | 94 | Normalizacion de texto |
| scaffold.sh | 91 | Generacion de archivos desde templates |
| llm_ir_mapper.sh | 81 | Mapeo LLM a IR (no analizado) |
| **Total** | **2881** | |

---

## 2. Analisis por Etapa

### 2.1 Preprocessor (`preprocessor.sh`)

**Funcion:** Normaliza la entrada del usuario.

**Transformaciones aplicadas:**
1. Trim de espacios iniciales/finales
2. Lowercase completo (`tr '[:upper:]' '[:lower:]'`)
3. Colapso de espacios multiples (`tr -s ' '`)

**Comportamiento verificado:**

| Entrada | Salida |
|---------|--------|
| `CREA UN MODULO DE PAGOS EN NESTJS` | `crea un modulo de pagos en nestjs` |
| `crea   modulo   pagos   en   nestjs` | `crea modulo pagos en nestjs` |
| `  crea modulo pagos  ` | `crea modulo pagos` |
| `HOLA MUNDO` | `hola mundo` |

**Observacion:** No elimina stopwords ("un", "de"). Es responsabilidad
del parser ignorar tokens irrelevantes.

**Tiempo:** ~8ms (3% del total).

### 2.2 Lexer (`lexer.sh`)

**Funcion:** Tokenizador DFA con maximal munch. Convierte texto en
tokens JSON.

**Tokens reconocidos:**

| Token | Ejemplo lexema | Regex implicito |
|-------|---------------|-----------------|
| `ACTION_CREATE` | crea, crear, genera, generar, make, new | `crea\|crear\|genera\|...` |
| `ACTION_DELETE` | elimina, eliminar, borra, borrar, remove, delete | `elimina\|...` |
| `ACTION_UPDATE` | actualiza, actualizar, modifica, modificar, update | `actualiza\|...` |
| `ACTION_READ` | muestra, mostrar, lista, listar, get, read | `muestra\|...` |
| `MODULE` | modulo, module, entidad, entity | `modulo\|module\|entidad\|entity` |
| `ENTITY` | *cualquier otra palabra* | `[a-z]+` |
| `PREP_IN` | en, para | `en\|para` |
| `TECH_NESTJS` | nestjs, NestJS, nest | `nestjs\|nest` |
| `TECH_PRISMA` | prisma, Prisma | `prisma` |
| `SEPARATOR` | y, e, , (coma) | `y\|e\|,` |

**Estructura del token:**

```json
{"type":"ACTION_CREATE","lexeme":"crea","position":{"line":1,"col":1}}
```

**Comportamiento con underscore:**

```
token no reconocido en col 17: '_'
```

El lexer no reconoce `_` como caracter valido. Lo trata como delim-itador
invisible. Para la instruccion `crea modulo test_module en nestjs`:

| Token esperado | Token real | Efecto |
|----------------|------------|--------|
| ENTITY `test_module` | ENTITY `test`, luego MODULE `module` | El parser interpreta 2 tokens donde esperaba 1 → error sintactico |

El warning se emite a **stderr**, no al stdout. El pipeline oficial
lo silencia con `2>/dev/null`, ocultando la causa raiz.

**Metricas de rendimiento:**

| Instruccion | Tiempo (ms) | Tokens | bytes |
|-------------|-------------|--------|-------|
| `crea modulo pagos en nestjs` | ~104 | 5 | 339 |
| `crea modulo test_module en nestjs` | ~140 | 6 | 405 |
| `crea modulo usuarios en prisma` | ~112 | 5 | ~340 |

El lexer es la etapa mas costosa: **~44% del tiempo total del pipeline**.

### 2.3 Parser (`parser.sh`)

**Funcion:** Analizador sintactico LL(1) recursivo descendente. Lee
tokens JSON de stdin y produce un AST.

**Gramatica BNF (del codigo fuente):**

```
comando       → accion modulo_espec opcional_tech
accion        → ACTION_CREATE | ACTION_DELETE | ACTION_UPDATE | ACTION_READ
modulo_espec  → MODULE ARTICLE? ENTITY (PREP ENTITY)*
              | ENTITY
opcional_tech → PREP TECH (SEPARATOR TECH)*
              | ε
```

**AST generado por instruccion:**

| Instruccion | AST |
|-------------|-----|
| `crea modulo pagos en nestjs` | `{"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":"nestjs"}` |
| `mostrar pagos` | `{"tipo":"Comando","accion":"READ","objetivo":{"tipo":"entity","entidades":["pagos"]},"tech":null}` |
| `eliminar modulo pagos` | `{"tipo":"Comando","accion":"DELETE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":null}` |
| `actualizar modulo pagos en prisma` | `{"tipo":"Comando","accion":"UPDATE","objetivo":{"tipo":"module","entidades":["pagos"]},"tech":"prisma"}` |

**Observaciones:**

- El parser infiere `objetivo.tipo` basado en presencia de token
  `MODULE`: si aparece, es "module"; si no, es "entity"
- `tech` se omite si la instruccion no especifica tecnologia
- El parser usa un archivo temporal (`/tmp/recpl_tokens_PID.tmp`) para
  almacenar tokens — posible race condition en alta concurrencia

**Bug detectado: Multi-entidad no soportada**

La instruccion `crea modulo auth y users en nestjs y prisma` falla:

```
Error sintactico en token 3: se esperaba fin de entrada, se encontro 'ENTITY' ('y')
```

El parser espera que el primer token `SEPARATOR` (y) sea para separar
tecnologias, no entidades. La gramatica no soporta multiples entidades
en una sola instruccion.

### 2.4 Semantic (`semantic.sh`)

**Funcion:** Validacion semantica y gestion de tabla de simbolos.

**Tabla de simbolos:**

Persistida en `RECPL_STATE_DIR` (default: `/tmp/recpl_state_PID`) como
archivos planos:

```
/tmp/recpl_report_state/
  scope.tmp      ← ambito actual
  symbols.tmp    ← simbolos registrados
```

**Estructura del AST validado:**

```json
{
  "ast": {"tipo":"Comando","accion":"CREATE","objetivo":{...}},
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

**Comportamiento por accion:**

| Accion | Validacion |
|--------|-----------|
| CREATE | Crea entrada en symbol table. Siempre OK. |
| READ | Requiere que la entidad exista. Si no: `Error semantico: undefined: pagos` |
| DELETE | Requiere que la entidad exista. |
| UPDATE | Requiere que la entidad exista. |

**Estado compartido entre instrucciones:**

Se verifico con estado persistente:

```sh
RECPL_STATE_DIR=/tmp/mi_estado ./pipeline_debugger.sh "crea modulo pagos en nestjs"
RECPL_STATE_DIR=/tmp/mi_estado ./pipeline_debugger.sh "mostrar pagos"
```

La segunda instruccion encuentra `pagos` en la tabla y responde OK.
Sin el CREATE previo, la segunda falla con error semantico.

### 2.5 IR Generator (`ir_generator.sh`)

**Funcion:** Traduce el AST validado a un IR canonico listo para
synthesis.

**Estructura del IR:**

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
  "trace_id": "trc_1781284784_107052",
  "symbol_table": {...}
}
```

**Mapeo AST → IR:**

| Campo AST | Campo IR | Transformacion |
|-----------|----------|---------------|
| `accion` CREATE | `accion` scaffold | Constante |
| `accion` READ | `accion` read | Constante |
| `objetivo.tipo` | `tipo` | Directo |
| `objetivo.entidades[0]` | `nombre` | Primer entidad |
| `tech` nestjs | `template` module-nestjs | Mapeo 1:1 |
| `tech` prisma | `template` module-prisma | Mapeo 1:1 |
| — | `trace_id` | Generado: `trc_PID_segundos` |

**Caso borde:** Si el AST no tiene `entidades` (instruccion mal formada),
el IR usa `nombre=null` y synthesis produce respuesta invalida.

### 2.6 Synthesis (`synthesis.sh`)

**Funcion:** Genera la respuesta JSON final del bot a partir del IR.

**Estructura de respuesta:**

```json
{
  "tipo_respuesta": "action",
  "mensaje": "Generando module Pagos en nestjs...",
  "payload": {
    "accion": "scaffold:module",
    "params": {
      "nombre": "Pagos",
      "tech": "nestjs",
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

**Mapeo IR → respuesta final:**

| Tipo respuesta | Condicion | Payload |
|---------------|-----------|---------|
| `action` | `IR.accion` = "scaffold" | Scaffold paths con template |
| `info` | `IR.accion` = "read" | Nombre de entidad sin archivos |
| `error` | Error en etapa anterior | Mensaje de error |

**Observaciones:**

- `nombre` se capitaliza: `pagos` → `Pagos`
- Las rutas de archivos se construyen desde templates configurados
  en `templates/`
- `tipo_respuesta: "action"` implica que se ejecutara scaffolding
  real (escritura a disco)

---

## 3. Metricas de Rendimiento

### 3.1 Tiempos por Etapa (10 ejecuciones)

| Etapa | Min (ms) | Max (ms) | Avg (ms) | % del total |
|-------|----------|----------|----------|-------------|
| preprocessor | 6 | 10 | 8 | 3% |
| lexer | 103 | 140 | 115 | **44%** |
| parser | 38 | 52 | 44 | 17% |
| semantic | 16 | 22 | 19 | 7% |
| ir_generator | 26 | 30 | 28 | 11% |
| synthesis | 29 | 42 | 35 | 14% |
| overhead debugger | — | — | ~5 | 2% |
| **Total** | **218** | **256** | **255** | **100%** |

### 3.2 Cuello de Botella

El lexer DFA consume ~44% del tiempo porque:

1. Implementa maximal munch — intenta匹配 cada palabra contra
   multiples patrones hasta encontrar el mas largo
2. No usa tablas de transicion compiladas; la logica DFA es
   una cascada de `case`/`if-else` en shell
3. El timestamp (`date`) se llama repetidamente para logging

### 3.3 Rendimiento por Tipo de Instruccion

| Instruccion | Tiempo (ms) | Etapas OK | Notas |
|-------------|-------------|-----------|-------|
| CREATE (`crea modulo pagos en nestjs`) | ~255 | 6/6 | Caso feliz |
| CREATE (`crea modulo usuarios en prisma`) | ~240 | 6/6 | Similar |
| READ (`mostrar pagos`) con estado | ~220 | 6/6 | Depende de CREATE previo |
| DELETE (`eliminar modulo pagos`) | ~230 | 6/6 | Similar |
| UPDATE (`actualizar modulo pagos en prisma`) | ~240 | 6/6 | Similar |
| Underscore (`crea modulo test_module en nestjs`) | ~192 | 2/6 | Falla en parser |
| Sin estado (`mostrar pagos` sin CREATE) | ~210 | 4/6 | Falla en semantic |
| Multi-entidad (`crea modulo auth y users...`) | ~239 | 2/6 | Falla en parser |
| Palabras no reconocidas (`HOLA MUNDO`) | — | 0/6 | Sin tokens accion |

---

## 4. Bugs y Anomalias Detectados

### 4.1 Bug: Underscore rompe el lexer (GRAVEDAD: ALTA)

**Sintoma:** `crea modulo test_module en nestjs` produce error
sintactico.

**Causa raiz:** El lexer no reconoce `_` como caracter de palabra.
Lo trata como delimitador externo, emite warning a stderr, y produce
dos tokens separados (`ENTITY test`, `MODULE module`) donde deberia
haber uno (`ENTITY test_module`).

**Impacto:** Cualquier entidad con guion bajo es imposible de crear
por el pipeline deterministico.

**Mitigacion:** Agregar `_` al conjunto de caracteres de palabra en
el DFA del lexer (linea ~140 de `lexer.sh`).

### 4.2 Bug: Multi-entidad no soportada (GRAVEDAD: MEDIA)

**Sintoma:** `crea modulo auth y users en nestjs` falla con error
sintactico.

**Causa raiz:** La gramatica BNF solo permite una entidad por
instruccion. El token `SEPARATOR` (y) se reserva para separar
tecnologias, no entidades.

**Impacto:** No se pueden crear multiples modulos en una instruccion.

**Mitigacion:** Extender la gramatica: `modulo_espec → MODULE ENTITY
(SEPARATOR ENTITY)*`.

### 4.3 Bug: --output redirige el JSON final a /dev/null (GRAVEDAD: MEDIA)

**Sintoma:** El JSON final del pipeline se descarta.

**Causa raiz:** En `main()`, `--output` ejecuta:

```sh
if $_output_only; then
    debug_trace "$_instruction" >/dev/null 2>&1
    exit 0
fi
```

Redirige **todo** el stdout a `/dev/null`, incluido el `echo "$_final_output"`
que deberia ser la salida del flag.

**Impacto:** El flag `--output` no produce salida. No se puede usar
para piping.

**Mitigacion:** Reemplazar con ejecucion silenciosa del pipeline pero
emitiendo solo el JSON final a stdout.

### 4.4 Anomalia: Stderr silenciado en pipeline normal

El pipeline oficial (`recpl.sh`) redirige `2>/dev/null` en todas las
llamadas. Esto oculta:

- Los warnings del lexer (ej: underscore)
- Errores de parseo intermedios
- Logs de depuracion de semantic.sh

**Efecto:** El usuario final ve solo el JSON de error final, sin
saber cual etapa fallo ni por que.

**Recomendacion:** En modo debug (variable `RECPL_DEBUG=1`), emitir
stderr de cada etapa en vez de silenciarlo.

### 4.5 Anomalia: Race condition en archivos temporales

El parser usa `/tmp/recpl_tokens_PID.tmp` con `$$` en el nombre, lo
cual es seguro para procesos secuenciales. Sin embargo:

- No hay limpieza en caso de `kill -9` (trap captura INT/TERM pero no KILL)
- Si dos instancias del pipeline se ejecutan en el mismo proceso
  (subshells), el PID se repite y los archivos colisionan

---

## 5. Patrones de Diseno Identificados

### 5.1 Pipeline (Chain of Responsibility)

Cada etapa recibe la entrada, la procesa, y pasa el resultado a la
siguiente via stdout/stdin. No hay acoplamiento entre etapas.

### 5.2 Strategy (Router)

`router.sh` implementa el patron Strategy con 3 estrategias:
- `deterministic-first` (default)
- `llm-first`
- `deterministic-only`

La seleccion se configura via variable de entorno `RECPL_LLM_MODE`.

### 5.3 Symbol Table (Repository)

La tabla de simbolos es un repositorio en disco. Cada instruccion
lee/escribe archivos en `RECPL_STATE_DIR`. Esto permite compartir
estado entre instrucciones sin necesidad de un proceso demonio.

### 5.4 Template Method (Scaffold)

`scaffold.sh` define el esqueleto de generacion de archivos. Los
detalles especificos (que archivos crear, que remplazar) se definen
en los templates en `templates/`.

---

## 6. Mapa de Flujo de Datos

```
                    ┌──────────────┐
                    │  Usuario     │
                    │ "crea modulo │
                    │  pagos en    │
                    │  nestjs"     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │ preprocessor │─── lowercase, trim, collapse
                    │   (94 lines) │
                    └──────┬───────┘
                           │ "crea modulo pagos en nestjs"
                           │
                    ┌──────▼───────┐
                    │    lexer     │─── DFA maximal munch
                    │  (165 lines) │
                    └──────┬───────┘
                           │ {"type":"ACTION_CREATE",...}
                           │ {"type":"MODULE",...}
                           │ ...
                    ┌──────▼───────┐
                    │    parser    │─── LL(1) recursive descent
                    │  (340 lines) │
                    └──────┬───────┘
                           │ {"tipo":"Comando","accion":"CREATE",...}
                           │
                    ┌──────▼───────┐
                    │   semantic   │─── type checking + symbol table
                    │  (245 lines) │◄────► RECPL_STATE_DIR/
                    └──────┬───────┘
                           │ {"ast":{...},"symbol_table":{...}}
                           │
                    ┌──────▼───────┐
                    │ ir_generator │─── AST → IR canonico
                    │  (183 lines) │
                    └──────┬───────┘
                           │ {"accion":"scaffold","template":"module-nestjs",...}
                           │
                    ┌──────▼───────┐
                    │  synthesis   │─── IR → respuesta final
                    │  (199 lines) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   RESPUESTA  │
                    │ JSON final   │
                    └──────────────┘
```

---

## 7. Vulnerabilidades de Seguridad

1. **Inyeccion de comandos via nombre de entidad:** El nombre de la
   entidad se interpola directamente en rutas de archivos:
   `modules/${nombre}/`. Un nombre como `../../etc/passwd` podria
   escalar a escritura fuera del directorio previsto.

2. **Archivos temporales predecibles:** `/tmp/recpl_tokens_PID.tmp`
   usa PID predecible. Un atacante local podria crear symlinks para
   interceptar o modificar tokens.

3. **Sin sanitizacion de entrada:** El preprocessor solo hace
   lowercase y colapso de espacios. No elimina caracteres de control
   o secuencias de escape shell.

---

## 8. Recomendaciones

| Prioridad | Recomendacion | Componente | Esfuerzo |
|-----------|--------------|------------|----------|
| ALTA | Agregar `_` al conjunto de caracteres del lexer | lexer.sh | 1 linea |
| ALTA | Sanitizar nombres de entidad (solo `[a-z0-9-]`) | preprocessor.sh | 5 lineas |
| MEDIA | Fix `--output` para emitir JSON final | pipeline_debugger.sh | 3 lineas |
| MEDIA | Soportar multi-entidad en gramatica | parser.sh | ~20 lineas |
| MEDIA | Variable `RECPL_DEBUG` para stderr visible | recpl.sh | 5 lineas |
| BAJA | Limpieza de temporales en signal KILL | parser.sh | 2 lineas |
| BAJA | Documentar palabras clave del lexer | docs/ | — |

---

## 9. Referencias

- `compiler-bot/pipeline_debugger.sh` — Herramienta usada para el analisis
- `compiler-bot/frontend/lexer.sh` — Lexer DFA (token no reconocido: linea 146)
- `compiler-bot/frontend/parser.sh` — Parser LL(1) (gramatica: lineas 10-17)
- `compiler-bot/frontend/semantic.sh` — Tabla de simbolos
- `compiler-bot/middleend/ir_generator.sh` — IR canonico
- `compiler-bot/backend/synthesis.sh` — Synthesis
- `compiler-bot/frontend/router.sh` — Router Strategy (clasificacion: lineas 42-66)
- `docs/025_GUIDE_DEV_COMPILER_BOT_PIPELINE_1_0_DRAFT.md` — Pipeline teorico
- `docs/041_REP_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_1_0_ACTIVE.md` — Reporte del debugger
- `docs/042_GUIDE_DEV_COMPILER_BOT_PIPELINE_DEBUGGER_RUNBOOK_1_0_DRAFT.md` — Runbook del debugger
