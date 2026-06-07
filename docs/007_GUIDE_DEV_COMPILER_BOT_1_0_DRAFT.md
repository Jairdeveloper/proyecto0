---
id: 007
area: dev
type: GUIDE
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - action-plan
  - compiler
  - bot
  - recpl
  - implementation
summary: "Plan de accion detallado para implementar cada seccion de la propuesta 006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md. Instrucciones paso a paso para construir el bot RECPL basado en teoria de compiladores."
keywords:
  - plan-de-accion
  - instrucciones
  - implementacion
  - recpl
  - compiler-bot
  - guia
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion inicial del plan de accion del bot RECPL
---

# Plan de Accion: Bot RECPL

Instrucciones para implementar cada seccion de `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md`.
Cada seccion contiene: objetivo, acciones concretas, verificacion, y errores comunes.

---

## Seccion 1: Concepto General

**Objetivo:** Establecer la vision del sistema y asegurar que el modelo mental del
bot-compilador quede claro antes de escribir codigo.

### Acciones

1. Leer la seccion 1 y verificar que el concepto RECPL se entiende como:
   - Un bot que recibe lenguaje natural
   - Lo procesa como un compilador (lexer → parser → semantico → IR → synthesis)
   - Responde en cada ciclo del LOOP
2. Documentar en `AGENTS.md` el concepto del bot RECPL como referencia para futuras sesiones.
3. Definir los limites del sistema: que tipo de instrucciones SI procesa y cuales NO.

### Verificacion

- [ ] El modelo RECPL (READ-EVAL-PRINT-LOOP) esta descrito en lenguaje natural comprensible para un agente nuevo
- [ ] Hay ejemplos concretos de input y output esperado

### Errores comunes

- Pensar que RECPL es solo un REPL simple — cada ciclo ejecuta el pipeline compilador completo
- No definir el alcance desde el principio

---

## Seccion 2: Arquitectura General

**Objetivo:** Implementar la estructura de carpetas y modulos que reflejen el diagrama
de arquitectura (Front-end / Middle-end / Back-end).

### Acciones

1. Crear la estructura de directorios del bot:
   ```
   compiler-bot/
   ├── frontend/
   │   ├── preprocessor.sh
   │   ├── lexer.sh
   │   ├── parser.sh
   │   └── semantic.sh
   ├── middleend/
   │   ├── scorer.sh
   │   ├── ir_generator.sh
   │   └── tracer.sh
   ├── backend/
   │   └── synthesis.sh
   └── recpl.sh           # LOOP principal
   ```
2. Crear los esqueletos de cada script con header, constantes y funcion main vacia
   siguiendo `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`.
3. Escribir test de integracion del pipeline vacio (que los scripts existen y son
   ejecutables).

### Verificacion

- [ ] `ls compiler-bot/` muestra la estructura de 3 directorios + recpl.sh
- [ ] Cada script pasa `bash -n script.sh`
- [ ] Cada script tiene bloque de ayuda (`--help`)
- [ ] `compiler-bot/recpl.sh --help` muestra uso

### Errores comunes

- Poner todo en un solo archivo gigante — mantener separacion Front/Middle/Back
- No respetar el estilo shell del proyecto (no `set -e`, no `eval`)

---

## Seccion 3: RECPL — READ-EVAL-PRINT-LOOP

### 3.1 READ (scan) — Analisis Lexico

**Objetivo:** Construir el lexer que transforma lenguaje natural en tokens.

### Acciones

1. Definir el alfabeto completo (TASK-001):
   - Listar todos los tokens que el bot reconoce
   - Para cada token: escribir su expresion regular
   - Priorizar tokens: keywords > identificadores
2. Implementar el DFA (TASK-002):
   - Usar la funcion `read()` del algoritmo en la seccion 3.1
   - Aplicar maximal munch (el match mas largo gana)
   - Ignorar whitespace
3. Probar con los ejemplos de la tabla de reglas lexicas:
   - `"Crea"` → `{ACTION_CREATE, "Crea"}`
   - `"module"` → `{MODULE, "module"}`
   - `"NestJS"` → `{TECH_NESTJS, "NestJS"}`
   - `"pagos"` → `{ENTITY, "pagos"}`
4. Manejar errores: token no reconocido → mensaje claro con posicion.

### Verificacion

- [ ] `./lexer.sh "Crea un modulo de pagos en NestJS"` produce 7 tokens
- [ ] `./lexer.sh "xyzzy"` produce error de token no reconocido
- [ ] Case insensitive: `"CREA"` y `"crea"` producen el mismo token
- [ ] Maximal munch: `"crear"` produce `ACTION_CREATE`, no se rompe en `"crea"+"r"`

### Errores comunes

- No implementar maximal munch (usar match mas corto en vez del mas largo)
- Confundir ENTITY con palabras reservadas — las keywords tienen prioridad
- Olvidar que el input puede venir con mayusculas, acentos, o punctuation raro

---

### 3.2 EVAL (act) — Analisis Sintactico + Semantico

**Objetivo:** Construir el parser que valida la estructura de la instruccion y el
analizador semantico que verifica tipos y gestiona la tabla de simbolos.

### Acciones

1. Definir la gramatica BNF completa (TASK-004):
   - Escribir todas las producciones de `comando`, `accion`, `modulo_espec`, `opcional_tech`
   - Incluir producciones para errores comunes (entrada vacia, accion sin objetivo)
2. Implementar parser recursivo descendente (TASK-005):
   - Una funcion por cada no-terminal: `parse_comando()`, `parse_accion()`, etc.
   - Cada funcion consume tokens del stream y avanza el cursor
   - Si no hay match: error sintactico con posicion y tokens esperados
3. Implementar tabla de simbolos (TASK-006):
   - Usar hash table (diccionario) con O(1) para insert/lookup/delete
   - Cada entrada: `{ tipo, tech, estado, dependencias, scope }`
   - Soportar ambitos anidados (scope stack)
4. Implementar analisis semantico (TASK-007):
   - Visitar cada nodo del AST
   - Para cada identificador: lookup en tabla de simbolos
   - Si no existe y es declaracion: insertar
   - Si no existe y es referencia: error
   - Type checking: verificar que el tech stack sea soportado

### Verificacion

- [ ] `./parser.sh "Crea modulo Payments en NestJS"` produce AST valido
- [ ] `./parser.sh "Haz algo"` produce error sintactico (accion no reconocida)
- [ ] `./parser.sh "Crea modulo Payments en TecnologiaInexistente"` produce error
      semantico (tech no soportado)
- [ ] Tabla de simbolos: insertar "Payments", lookup "Payments" → existe
- [ ] Scope: declaraciones en modulos diferentes no colisionan

### Errores comunes

- Parser que solo funciona con input perfecto — cubrir errores sintacticos obvios
- Tabla de simbolos sin soporte de ambitos (scope) — lleva a colisiones de nombres
- No distinguir entre declaracion y referencia en el AST

---

### 3.3 PRINT — Synthesis

**Objetivo:** Implementar la sintesis que traduce el AST/IR en respuesta del bot.

### Acciones

1. Implementar `print(ast_node, ir_json)` (TASK-010):
   - Case por tipo de accion: CREATE, DELETE, UPDATE, READ
   - Cada caso produce: mensaje + payload de accion
2. Para acciones de scaffolding (CREATE):
   - Buscar template correspondiente segun tech stack
   - Generar estructura de archivos
   - Retornar JSON con resultado
3. Formatear salida como JSON estructurado (ver formato en seccion 3.3).

### Verificacion

- [ ] `./synthesis.sh "CREATE" "module" "Payments" "NestJS"` produce JSON valido
- [ ] El JSON tiene campos: `tipo_respuesta`, `mensaje`, `payload`
- [ ] Para CREATE: payload incluye `accion: "scaffold:module"` y `archivos[]`

### Errores comunes

- No estructurar la salida como JSON — el bot necesita un formato parseable
- Mezclar responsabilidades: PRINT solo sintetiza, no ejecuta directamente

---

### 3.4 LOOP — El bucle principal

**Objetivo:** Implementar el ciclo infinito que conecta READ → EVAL → PRINT.

### Acciones

1. Implementar `loop()` (TASK-011):
   - `while true`: leer input → READ → EVAL → GENERATE_IR → PRINT → mostrar respuesta
   - Manejar EOF (Ctrl+D) para salir del bucle
   - Manejar `quit` / `salir` comando especial para salir gracefulmente
2. Asegurar que cada iteracion maneja errores sin romper el bucle:
   - Error lexico: mostrar mensaje y continuar
   - Error sintactico: mostrar mensaje y continuar
   - Error semantico: mostrar mensaje y continuar
   - Error de ejecucion: mostrar mensaje y continuar

### Verificacion

- [ ] `./recpl.sh` inicia el bucle, muestra prompt
- [ ] Input valido: procesa y muestra respuesta, vuelve al prompt
- [ ] Input invalido: muestra error y vuelve al prompt (no se cuelga)
- [ ] `quit` o Ctrl+D: termina con exit 0

### Errores comunes

- Error en una iteracion rompe todo el bucle — cada fase debe tener try/catch
- No mostrar prompt al usuario (parece que el programa se colgo)
- No limpiar estado entre iteraciones (tabla de simbolos se acumula)

---

## Seccion 4: Pipeline de Compilacion Completo

**Objetivo:** Verificar que el pipeline completo funciona end-to-end con un caso real.

### Acciones

1. Escribir test de integracion para el pipeline completo:
   ```
   Input: "Crea un modulo de pagos en NestJS"
   Esperado:
     - 8 tokens en el lexer
     - AST con 3 nodos (accion=CREATE, objetivo=Modulo(pagos), tech=NestJS)
     - IR.json valido
     - Respuesta JSON del bot
   ```
2. Probar los 9 pasos del pipeline secuencialmente (seccion 4):
   - Cada paso recibe la salida del paso anterior
   - Verificar que los formatos de datos coinciden entre fases
3. Documentar los formatos de intercambio entre fases:
   - PREPROCESADOR → LEXER: `string`
   - LEXER → PARSER: `token[]`
   - PARSER → SEMANTICO: `ast_node`
   - SEMANTICO → IR: `validated_ast`
   - IR → SYNTHESIS: `ir_json`
   - SYNTHESIS → BOT: `bot_response`

### Verificacion

- [ ] Script de test ejecuta los 9 pasos sin errores
- [ ] Output final contiene mensaje de exito y estructura generada
- [ ] Cada formato de intercambio esta documentado en la seccion 5

### Errores comunes

- Las fases esperan formatos de datos incompatibles (tipos incorrectos)
- No considerar que algunas fases son opcionales (SCORER, TRACE)

---

## Seccion 5: Especificacion de Componentes

**Objetivo:** Implementar cada componente siguiendo la especificacion detallada.

### 5.1 Preprocesador

**Objetivo:** Normalizar el input antes del lexer.

### Acciones

1. Implementar `preprocess()` segun el algoritmo de la seccion 5.1:
   - trim whitespace
   - normalize unicode (NFKC)
   - lowercase fold
   - remove repeated punctuation
   - split on sentence boundaries
2. El preprocesador debe fallar silenciosamente (si no puede normalizar,
   pasar el input original al lexer).

### Verificacion

- [ ] `"  CREA   MODULO!! "` → `"crea modulo"`
- [ ] Caracteres Unicode se normalizan
- [ ] Oraciones multiples separadas por `;` o `.` producen arrays

---

### 5.2 Lexer (READ)

**Objetivo:** Implementar el DFA del lexer segun el algoritmo en 5.2.

### Acciones

1. Traducir el pseudocodigo del DFA a shell/awk/python:
   ```
   estado = 0
   para cada caracter c en input:
       estado = transicion(estado, c)
       si estado es de aceptacion:
           registrar match
       si estado es muerto:
           retroceder al ultimo match valido
           emitir token
           estado = 0
   ```
2. Implementar la funcion `transicion(estado, c)` como tabla de transiciones:
   - Usar case/switch para cada estado
   - Cada estado tiene transiciones para cada simbolo del alfabeto
3. La estructura de salida debe ser JSON (como la del ejemplo en 5.2).

### Verificacion

- [ ] DFA acepta todos los tokens definidos en TASK-001
- [ ] DFA rechaza secuencias invalidas con error
- [ ] Output token tiene campos: `type`, `lexeme`, `position`, `literal`

---

### 5.3 Parser (EVAL — sintactico)

**Objetivo:** Implementar parser recursivo descendente.

### Acciones

1. Implementar `parser(tokens)`:
   - cursor = 0
   - llamar a `parse_comando()`
   - verificar que cursor == len(tokens)
2. Implementar funciones por no-terminal:
   - `parse_comando()` → accion + modulo_espec + opcional_tech
   - `parse_accion()` → match ACTION_CREATE | ACTION_DELETE | ...
   - `parse_modulo_espec()` → MODULE ENTITY | ENTITY
   - `parse_opcional_tech()` → PREP TECH | ε
3. Cada funcion debe reportar errores con:
   - `"Syntax error: se esperaba X, se encontro Y en posicion Z"`

### Verificacion

- [ ] Input valido produce AST con estructura correcta
- [ ] Input con tokens faltantes produce error descriptivo
- [ ] Input con tokens extra al final produce error ("se esperaba fin de input")

---

### 5.4 Analizador Semantico (EVAL — semantico)

**Objetivo:** Implementar la verificacion semantica.

### Acciones

1. Implementar `semantic_analyzer(ast, symbol_table)`:
   - Recorrer AST en postorden (hijos antes que padres)
   - Para cada identificador: lookup en tabla de simbolos
   - Si es declaracion y no existe: insertar
   - Si es referencia y no existe: error
2. Type checking:
   - Verificar que `tech` esta en la lista de tecnologias soportadas
   - Verificar que `accion` es compatible con `objetivo`
   - Verificar unicidad de nombres de modulo

### Verificacion

- [ ] Referencia a entidad no declarada produce error semantico
- [ ] Tech stack no soportado produce error
- [ ] Modulo duplicado produce error

---

### 5.5 Generador IR

**Objetivo:** Traducir AST validado a IR.json.

### Acciones

1. Implementar `generate_ir(ast)`:
   - Extraer accion, scope, entity, tech del AST
   - Resolver dependencias
   - Tomar snapshot de tabla de simbolos
   - Generar JSON canonico

### Verificacion

- [ ] IR.json contiene todos los campos del formato en 5.5
- [ ] El JSON es parseable y autocontenido
- [ ] Dependencias se resuelven correctamente

---

### 5.6 Tracer (opcional — three-address code)

**Objetivo:** Generar codigo de tres direcciones para trazabilidad.

### Acciones

1. Implementar `trace(ir_json)`:
   - Por cada operacion en IR, generar instruccion TAC
   - Secuenciar con temporales `t1, t2, t3, ...`
   - Cada instruccion: `result = op(arg1, arg2, ...)`

### Verificacion

- [ ] TAC es una secuencia lineal de instrucciones
- [ ] Cada instruccion tiene resultado, operacion, argumentos
- [ ] Ejemplo de "crear modulo pagos" produce 4 instrucciones TAC

---

### 5.7 Synthesis (PRINT)

**Objetivo:** Ejecutar las acciones sintetizadas y responder al usuario.

### Acciones

1. Implementar `synthesis(ir_json, tac[])`:
   - Case por `ir_json.action`
   - Cada case ejecuta la accion correspondiente
   - Retorna JSON con tipo, mensaje, payload
2. Para scaffolding: crear directorios y archivos desde templates

### Verificacion

- [ ] CREATE module produce directorio `modules/<nombre>/` con archivos
- [ ] READ entity lista informacion sin modificar archivos
- [ ] DELETE module elimina (con confirmacion)
- [ ] Respuesta del bot tiene formato JSON estructurado

---

## Seccion 6: Reglas del Sistema

**Objetivo:** Codificar las reglas lexicas, sintacticas y semanticas como
validaciones en los componentes correspondientes.

### 6.1 Reglas Lexicas

### Acciones

1. En el lexer, implementar las reglas:
   - **Maximal munch**: al compilar el DFA, priorizar las transiciones mas largas
   - **Prioridad de keywords**: las regex de keywords se evaluan antes que ENTITY
   - **Whitespace**: estado "skip" en el DFA que ignora `[ \t\n]+`
   - **Case insensitive**: normalizar a lowercase en el preprocesador

### 6.2 Reglas Sintacticas

### Acciones

1. En el parser, validar:
   - **Unicidad de accion**: solo un ACTION por comando
   - **Objetivo requerido**: despues de ACTION debe venir MODULE o ENTITY
   - **Tech binding**: PREP TECH se asocia al modulo mas cercano en el AST
   - **Separacion**: `;` separa comandos (crear ciclo para multiples comandos)

### 6.3 Reglas Semanticas

### Acciones

1. En el analizador semantico, validar:
   - **Declaracion before use**: lookup antes de usar, insert si es decl
   - **Type checking**: tech stack valido contra lista blanca
   - **Scope**: por modulo, no por sesion completa
   - **Unicidad**: insert falla si ya existe

---

## Seccion 7: Tabla de Tareas

**Objetivo:** Ejecutar las tareas en orden, siguiendo las dependencias.

### Acciones

1. Procesar las tareas en orden topologico:
   ```
   TASK-003 → (independiente, arranca ya)
   TASK-006 → (independiente, arranca ya)
   TASK-001 → TASK-002 → TASK-004 → TASK-005
   TASK-005 + TASK-006 → TASK-007
   TASK-007 → TASK-008
   TASK-008 → TASK-009, TASK-010, TASK-012
   TASK-002 + TASK-005 + TASK-010 → TASK-011
   TASK-010 → TASK-013
   TASK-011 → TASK-014
   ```
2. Marcar estado de cada tarea en la tabla:
   - `pending` → `in_progress` al empezar
   - `in_progress` → `completed` al pasar verificacion
3. Si una tarea se bloquea, documentar el blocker en el changelog.

### Verificacion

- [ ] Las tareas sin dependencias (TASK-003, TASK-006) son las primeras en empezar
- [ ] TASK-014 (tests) es la ultima en completarse
- [ ] Cada tarea tiene evidencia de verificacion (output de test, screenshot)

---

## Seccion 8: Fases de Implementacion

**Objetivo:** Organizar las tareas en fases entregables.

### Acciones

1. Completar FASE-1 (Nucleo RECPL) antes de empezar FASE-2:
   - TASK-001, TASK-003, TASK-002, TASK-004, TASK-005
   - TASK-011 parcial: el bucle LOOP funciona aunque sin semantica completa
2. Demo de FASE-1: lexer + parser que tokeniza y parsea comandos basicos
3. Completar FASE-2 (Semantica e IR):
   - TASK-006, TASK-007, TASK-008
4. Demo de FASE-2: pipeline lexer → parser → semantico → IR.json
5. Continuar con FASE-3, FASE-4, FASE-5 siguiendo el orden de la tabla

### Verificacion

- [ ] FASE-1 produce output visible (tokens + AST en pantalla)
- [ ] FASE-2 muestra IR.json valido
- [ ] Cada fase tiene una demo ejecutable
- [ ] No se salta una fase sin completar la anterior

---

## Seccion 9: Referencias

**Objetivo:** Usar las referencias para resolver dudas tecnicas durante la implementacion.

### Acciones

1. Leer Dragon Book (Aho) caps.1-4 para entender:
   - Cap.1: arquitectura general de compiladores
   - Cap.2: analisis lexico y DFA
   - Cap.3: analisis sintactico y parsing LL(1)
   - Cap.4: analisis semantico y tabla de simbolos
2. Leer `005_SPEC_DOC_COMPILADORTHEORY_1.0_ACTIVE.md` para:
   - Repasar conceptos de automatas (DFA, NFA)
   - Ejemplos de lexer en C (funcion `ObtenerOpRel`)
   - Estructura de tabla de simbolos y hash table
3. Leer `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` para:
   - Recordar las reglas de estilo shell
   - No usar `set -e`, no usar `eval`
4. Mantener las referencias a mano durante toda la implementacion.

---

## Checklist Final de Implementacion

- [ ] Seccion 1: Concepto documentado y compartido
- [ ] Seccion 2: Estructura de directorios creada y scripts esqueleto listos
- [ ] Seccion 3.1: Lexer (READ) implementado y probado
- [ ] Seccion 3.2: Parser + Semantico (EVAL) implementados y probados
- [ ] Seccion 3.3: Synthesis (PRINT) implementada y probada
- [ ] Seccion 3.4: LOOP principal implementado y probado
- [ ] Seccion 4: Pipeline completo probado end-to-end
- [ ] Seccion 5: Cada componente (preprocesador, lexer, parser, semantico, IR, tracer, synthesis) implementado segun spec
- [ ] Seccion 6: Reglas lexicas, sintacticas y semanticas codificadas en los componentes
- [ ] Seccion 7: Tabla de tareas completada al 100%
- [ ] Seccion 8: Fases entregadas en orden, con demos por fase
- [ ] Seccion 9: Referencias consultadas durante la implementacion
- [ ] Todos los scripts pasan `bash -n` y `shellcheck`
- [ ] `AGENTS.md` actualizado con el estado del bot RECPL
