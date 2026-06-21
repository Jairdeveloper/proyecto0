---
id: 010
area: dev
type: guide
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - runbook
  - compiler
  - bot
  - recpl
  - usage
summary: "Runbook de uso operativo del bot RECPL. Describe modos de ejecucion, instrucciones soportadas, manejo de errores, troubleshooting y procedimientos comunes."
keywords:
  - runbook
  - uso
  - operacion
  - recpl
  - compiler-bot
  - troubleshooting
  - ejemplos
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion del runbook de uso del bot RECPL
---

# Runbook: RECPL Compiler Bot

## 1. Modos de Ejecucion

### 1.1 Modo Interactivo

```sh
./compiler-bot/recpl.sh
```

Inicia un REPL con prompt `> `. Procesa instrucciones una por una.

```
RECPL Compiler Bot v1.0.0
Escribe 'quit' para salir.

> crea modulo payments en nestjs
{
  "tipo_respuesta": "action",
  "mensaje": "Generando module Payments en nestjs...",
  "payload": {
    "accion": "scaffold:module",
    ...
  }
}

> mostrar payments
{
  "tipo_respuesta": "info",
  "mensaje": "Mostrando entity Payments...",
  ...
}

> quit
```

### 1.2 Modo Batch

```sh
echo "crea modulo payments en nestjs" | ./compiler-bot/recpl.sh
```

Procesa stdin y termina. Estado persistente entre lineas:

```sh
printf "crea modulo payments en nestjs\nmostrar payments\nquit\n" | ./compiler-bot/recpl.sh
```

### 1.3 Pipeline Manual (debugging)

Ejecutar componentes individualmente para inspeccionar cada etapa:

```sh
# Solo preprocesador
./compiler-bot/frontend/preprocessor.sh "CREA UN MODULO DE PAGOS"

# Preprocesador + lexer
input=$(./compiler-bot/frontend/preprocessor.sh "crea un modulo de pagos en nestjs")
./compiler-bot/frontend/lexer.sh "$input"

# Hasta parser
./compiler-bot/frontend/lexer.sh "$input" | ./compiler-bot/frontend/parser.sh

# Pipeline completo hasta synthesis
./compiler-bot/frontend/lexer.sh "$input" | \
  ./compiler-bot/frontend/parser.sh | \
  ./compiler-bot/frontend/semantic.sh | \
  ./compiler-bot/middleend/ir_generator.sh | \
  ./compiler-bot/backend/synthesis.sh
```

### 1.4 Ayuda y Version

```sh
./compiler-bot/recpl.sh --help
./compiler-bot/recpl.sh --version
```

---

## 2. Instrucciones Soportadas

### 2.1 CREATE — Crear modulos y entidades

Crea una entrada en la tabla de simbolos y genera archivos via scaffolding.

```
crea modulo payments
crea modulo payments en nestjs
crea un modulo de pagos en NestJS
crea modulo de usuarios en prisma
crear entidad productos
generar modulo auth en NestJS
make module users in NestJS
new entity product
```

**Salida exitosa:**
```json
{
  "tipo_respuesta": "action",
  "mensaje": "Generando module Usuarios en prisma...",
  "payload": {
    "accion": "scaffold:module",
    "params": {
      "nombre": "Usuarios",
      "tech": "prisma",
      "template": "module-prisma"
    },
    "archivos": [
      "modules/usuarios/usuarios.prisma"
    ]
  }
}
```

### 2.2 DELETE — Eliminar modulos

Requiere que la entidad exista en la tabla de simbolos (debe haberse creado antes en la misma sesion).

```
eliminar modulo payments
borrar entidad usuarios
remove module users
```

**Error si no existe:**
```
Error semantico al procesar: eliminar modulo payments
```

### 2.3 UPDATE — Actualizar modulos

```
actualizar modulo payments
modificar entidad usuarios
update entity products
```

### 2.4 READ — Consultar modulos

Requiere que la entidad exista en la tabla de simbolos.

```
mostrar payments
listar usuarios
get module users
read entity products
```

**Salida exitosa:**
```json
{
  "tipo_respuesta": "info",
  "mensaje": "Mostrando entity Payments...",
  "payload": {
    "accion": "read:entity",
    "params": {
      "nombre": "Payments"
    },
    "archivos": []
  }
}
```

### 2.5 Comandos Especiales

| Comando | Efecto |
|---------|--------|
| `quit`, `salir`, `exit`, `q` | Termina el bucle |
| `help` | Muestra ayuda |
| `version` | Muestra version |
| `Ctrl+D` | Termina el bucle (EOF) |
| Enter (vacio) | No hace nada, muestra nuevo prompt |

---

## 3. Arquitectura del Pipeline

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  INPUT       │     │  TOKENS      │     │  AST         │
│  "crea..."   │ ──→ │  JSON        │ ──→ │  JSON        │
└──────────────┘     └──────────────┘     └──────────────┘
       ↓                    ↓                    ↓
 preprocessor.sh       lexer.sh             parser.sh
 (normaliza input)     (DFA + maximal       (LL(1) recursive
                        munch)               descent)

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  AST +       │     │  IR.json     │     │  Bot         │
│  Symbol Tbl  │ ──→ │  canonico    │ ──→ │  Response    │
└──────────────┘     └──────────────┘     └──────────────┘
       ↓                    ↓                    ↓
 semantic.sh          ir_generator.sh       synthesis.sh
 (type checking +     (mapea acciones,      (genera respuesta
  tabla simbolos)      templates, trace)     + scaffolding)
```

### Formato de datos entre etapas

| Etapa | Formato | Ejemplo |
|-------|---------|---------|
| preprocessor → lexer | String plano | `"crea modulo pagos en nestjs"` |
| lexer → parser | JSON tokens (uno por linea) | `{"type":"ACTION_CREATE","lexeme":"crea",...}` |
| parser → semantic | AST JSON | `{"tipo":"Comando","accion":"CREATE",...}` |
| semantic → IR | AST + symbol table JSON | `{"ast":{...},"symbol_table":{...}}` |
| IR → synthesis | IR.json multi-linea | `{"accion":"scaffold","tipo":"module",...}` |
| synthesis → output | Bot response JSON | `{"tipo_respuesta":"action","mensaje":"...",...}` |

---

## 4. Manejo de Errores

### 4.1 Errores Lexicos

**Causa:** Caracter o palabra no reconocida por el lexer.
**Sintoma:** Mensaje de error lexico en stderr.
**Recuperacion:** El LOOP captura el error y continua.

```
Error lexico: token no reconocido en col 1: 'xyzzy'
{"tipo_respuesta":"error","mensaje":"Error lexico al procesar: ...","payload":null}
```

### 4.2 Errores Sintacticos

**Causa:** Estructura de instruccion invalida (e.g., accion sin objetivo).
**Sintoma:** Mensaje de error con posicion del token.

```
Error sintactico en token 1: se esperaba ENTITY, se encontro 'EOF' ('')
{"tipo_respuesta":"error","mensaje":"Error sintactico al procesar: ...","payload":null}
```

### 4.3 Errores Semanticos

**Causa:** Referencia a entidad inexistente, tech stack no soportado, duplicado.
**Sintoma:** Error semantico en stderr.

```
Error semantico: undefined: nonexistent
Error semantico: tech stack no soportado: InvalidTech
Error semantico: modulo duplicado: payments
```

### 4.4 Tabla de Errores

| Error | Causa | Solucion |
|-------|-------|----------|
| `token no reconocido` | Palabra no esta en el lexicon | Revisar ortografia. Usar verbos soportados (crea, eliminar, mostrar, etc.) |
| `se esperaba ENTITY` | Falta nombre de entidad | Ej: "crea modulo" → "crea modulo **payments**" |
| `se esperaba fin de entrada` | Sobran tokens al final | Revisar que la instruccion no tenga palabras extra |
| `se esperaba una accion` | Falta verbo al inicio | Ej: "modulo payments" → "**crea** modulo payments" |
| `undefined: X` | Entidad no existe en la tabla de simbolos | Crear la entidad antes de referenciarla (CREATE antes de READ/DELETE) |
| `tech stack no soportado` | Tecnologia no reconocida | Usar NestJS o Prisma |
| `modulo duplicado: X` | Entidad ya existe | Usar UPDATE en vez de CREATE |
| `no hay tokens` o `no hay AST` | Pipeline recibe entrada vacia | Verificar que la etapa anterior produjo salida |

---

## 5. Troubleshooting

### 5.1 El pipeline no produce salida

Verificar cada etapa individualmente:

```sh
# 1. El preprocesador funciona?
./compiler-bot/frontend/preprocessor.sh "crea modulo payments"
# Deberia mostrar: crea modulo payments

# 2. El lexer produce tokens?
input=$(./compiler-bot/frontend/preprocessor.sh "crea modulo payments")
./compiler-bot/frontend/lexer.sh "$input"
# Deberia mostrar 3 lineas JSON

# 3. El parser produce AST?
./compiler-bot/frontend/lexer.sh "$input" | ./compiler-bot/frontend/parser.sh
# Deberia mostrar JSON con "accion":"CREATE"
```

### 5.2 Error "Permission denied"

Los scripts deben ser ejecutables:

```sh
chmod +x compiler-bot/**/*.sh compiler-bot/*.sh
```

### 5.3 Error "comando no encontrado" con awk

El bot requiere `awk` (especialmente para funcion `match()` con ERE). Verificar:

```sh
which awk
awk --version
```

### 5.4 El scaffolding no genera archivos

Verificar que el template existe:

```sh
ls compiler-bot/templates/
# Deberia mostrar: entity-nestjs/  module-nestjs/  module-prisma/
```

Si el template no existe, synthesis.sh reporta `"archivos": []`.

### 5.5 La tabla de simbolos no persiste entre instrucciones

En el LOOP (`recpl.sh`), el estado persiste automaticamente via `RECPL_STATE_DIR`.
En pipeline manual, el estado es efimero (cada invocacion de semantic.sh usa un
archivo temporal nuevo). Para persistencia manual:

```sh
export RECPL_STATE_DIR=/tmp/recpl_mi_sesion
mkdir -p "$RECPL_STATE_DIR"
echo '{"tipo":"Comando","accion":"CREATE",...}' | ./compiler-bot/frontend/semantic.sh
echo '{"tipo":"Comando","accion":"READ",...}' | ./compiler-bot/frontend/semantic.sh
```

### 5.6 Tests fallan

Ejecutar tests con verbose:

```sh
./compiler-bot/tests/run_tests.sh 2>&1 | grep -E "PASS|FAIL"
```

Para depurar un test especifico, ejecutar el comando manualmente:

```sh
# Ej: depurar test de lexer
./compiler-bot/frontend/lexer.sh "crea modulo pagos en nestjs"
```

---

## 6. Procedimientos Operativos

### 6.1 Iniciar sesion interactiva

```sh
./compiler-bot/recpl.sh
```

Flujo tipico:

```
> crea modulo usuarios en NestJS    # Crear modulo
> crea modulo productos en Prisma   # Crear otro modulo
> listar usuarios                   # Consultar
> listar productos                  # Consultar
> eliminar modulo usuarios          # Eliminar
> quit                              # Salir
```

### 6.2 Procesar lista de instrucciones (batch)

```sh
# Crear archivo con instrucciones
cat > /tmp/comandos.txt << 'EOF'
crea modulo payments en NestJS
crea modulo usuarios en NestJS
crea modulo productos en Prisma
listar payments
listar usuarios
quit
EOF

# Ejecutar batch
./compiler-bot/recpl.sh < /tmp/comandos.txt
```

### 6.3 Generar scaffolding manualmente

Sin el LOOP, invocar scaffold.sh directamente:

```sh
# Template NestJS Module
./compiler-bot/backend/scaffold.sh \
  compiler-bot/templates/module-nestjs \
  Payments \
  modules/payments

# Template Prisma Model
./compiler-bot/backend/scaffold.sh \
  compiler-bot/templates/module-prisma \
  Product \
  modules/product
```

### 6.4 Limpiar archivos generados

```sh
rm -rf modules/
```

### 6.5 Ejecutar tests de regresion

```sh
./compiler-bot/tests/run_tests.sh
echo "Exit code: $?"  # 0 = todos pasaron
```

### 6.6 Validar sintaxis de todos los scripts

```sh
for s in compiler-bot/**/*.sh compiler-bot/*.sh; do
  bash -n "$s" && echo "OK: $s" || echo "FAIL: $s"
done
```

---

## 7. Referencia Rapida

### 7.1 Verbos Soportados

| Accion | Verbos (es/en) |
|--------|----------------|
| CREATE | crea, crear, creando, generar, make, new |
| DELETE | eliminar, borrar, delete, remove |
| UPDATE | actualizar, modificar, update, edit |
| READ | mostrar, listar, get, show, read |

### 7.2 Tech Stack Soportados

| Tech | Token | Template |
|------|-------|----------|
| NestJS | `nestjs`, `NestJS` | `module-nestjs`, `entity-nestjs` |
| Prisma | `prisma`, `Prisma` | `module-prisma` |

### 7.3 Preposiciones

`en`, `para`, `de`, `in`, `for`, `of` — se ignoran semanticamente, solo
estructuran la instruccion.

### 7.4 Articulos

`un`, `una`, `el`, `la`, `los`, `las` — se ignoran semanticamente.

---

## 8. Limitaciones Conocidas

- **Una instruccion por linea.** Comandos compuestos (e.g., "crea X y Y") no
  estan soportados. Usar modo batch con multiples lineas.
- **Solo tech NestJS y Prisma.** Intentar usar otra tecnologia produce error
  semantico.
- **Tabla de simbolos volatil en pipeline manual.** Sin `RECPL_STATE_DIR`,
  cada invocacion de semantic.sh empieza con tabla vacia.
- **No hay undo.** El scaffolding escribe archivos directamente. No hay comando
  para revertir. Usar `rm -rf modules/` manualmente.
- **Case folding via preprocesador.** El lexer es case-sensitive. Siempre usar
  el preprocesador antes del lexer (el LOOP lo hace automaticamente).

---

## 9. Modo LLM (Integracion con IA)

El RECPL Compiler Bot puede usar LLMs (Claude, OpenAI) para procesar
instrucciones que el pipeline deterministico no entiende.

### 9.1 Cuando se usa el LLM

| Situacion | Sin LLM | Con LLM |
|-----------|---------|---------|
| "crea modulo pagos en nestjs" | OK (deterministico) | OK (deterministico, mas rapido) |
| "necesito un sistema de pagos" | ERROR | OK (LLM entiende la intencion) |
| "que modulos tengo?" | ERROR | OK (responde como texto) |
| "agregale auth al modulo pagos" | ERROR | OK (requiere contexto) |
| "como se configura nestjs?" | ERROR | OK (responde guia) |

En modo `auto` (default), el LLM solo se usa cuando:
- La instruccion tiene mas de 10 palabras
- El lexer no reconoce las palabras clave
- El parser falla al analizar la gramatica

### 9.2 Configuracion

```sh
# 1. Configurar API key (Claude o OpenAI)
export ANTHROPIC_API_KEY="sk-ant-..."
# o
export OPENAI_API_KEY="sk-..."

# 2. Opcional: seleccionar proveedor
export RECPL_LLM_PROVIDER="claude"    # o "openai"
export RECPL_LLM_MODE="auto"          # o "llm" o "deterministic"
```

### 9.3 Modos de uso

```sh
# Modo interactivo hibrido (auto: deterministico, fallback a LLM)
./compiler-bot/recpl.sh

# Forzar modo LLM para todas las instrucciones
./compiler-bot/recpl.sh --llm

# Modo comando con LLM
./compiler-bot/recpl.sh --llm -c "crea un modulo de pagos en NestJS"

# Modo comando con proveedor especifico
./compiler-bot/recpl.sh --provider openai -c "explica que es un modulo"

# Solo deterministico (sin LLM, sin API key)
./compiler-bot/recpl.sh
```

### 9.4 Variables de Entorno

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `RECPL_LLM_MODE` | `auto` | `auto`, `llm`, o `deterministic` |
| `RECPL_LLM_PROVIDER` | `claude` | `claude` o `openai` |
| `ANTHROPIC_API_KEY` | — | API key para Claude (obligatorio si provider=claude) |
| `OPENAI_API_KEY` | — | API key para OpenAI (obligatorio si provider=openai) |

### 9.5 Flags CLI

| Flag | Efecto |
|------|--------|
| `--llm` | Fuerza modo LLM para todas las instrucciones |
| `--provider claude\|openai` | Selecciona el proveedor LLM |

Los flags se pueden combinar:
```sh
./compiler-bot/recpl.sh --llm -c "crea un modulo de pagos en NestJS"
./compiler-bot/recpl.sh --provider claude -f instrucciones.txt
```

### 9.6 Arquitectura

La integracion LLM sigue el patron Adapter: cada proveedor (Claude,
OpenAI) tiene un adapter que normaliza las diferencias de API a un
formato interno comun. Un router inteligente decide que camino
(deterministico o LLM) es el apropiado para cada instruccion.

```
INPUT → preprocessor → router ─┬─ deterministic (lexer→parser→semantic→IR)
                                └─ LLM (classifier → provider → mapper → IR)
                                ↓
                           synthesis → scaffold → OUTPUT
```

### 9.7 Costos

- **Pipeline deterministico:** ~50ms, sin costo
- **LLM (Claude Sonnet):** ~1-3s, ~$0.005/instruccion
- **LLM (OpenAI GPT-4o):** ~1-3s, ~$0.004/instruccion

En modo `auto`, ~80% de las instrucciones se procesan con el pipeline
deterministico (gratis). El LLM solo se usa para ~20% de los casos.
