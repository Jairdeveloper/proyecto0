---
id: 085
area: DEV
type: PROP
module: COMPILER_BOT
version: 1.0
status: IMPLEMENTED
tags:
  - sprint
  - pipeline-debug
  - data-validation
  - lexer-fix
  - parser-fix
  - error-recovery
  - debugger
  - integration
summary: >-
  Propuesta de Sprint 14 — Depuracion y refinamiento del pipeline Python
  v2.0. Correccion de falencias en el flujo de datos entre etapas,
  validacion de esquemas, mejora del lexer para espanol natural, modo
  debug, y tests de integracion con datos reales.
keywords:
  - sprint-14
  - pipeline-debug
  - lexer
  - parser
  - data-validation
  - pydantic
  - debug-mode
  - error-recovery
  - integration-tests
changelog:
  - version: '1.0'
    date: 2026-06-14
    description: Propuesta inicial Sprint 14
---

# 085_PROP_DEV_PIPELINE_DEBUG_REFINE_1_0_DRAFT

## Resumen Ejecutivo

El pipeline Python v2.0 ejecuta end-to-end (471 tests) pero presenta
**falencias de calidad** en el flujo de datos entre etapas que producen
comportamiento incorrecto: el parser falla sistematicamente porque recibe
texto reconstruido de tokens en vez de la estructura tokenizada, y
el domain enrichment del preprocessor introduce ruido que el lexer/parser
no puede procesar.

Este propuesta define un sprint de **depuracion y refinamiento** (Sprint 14)
para corregir estas inconsistencias, añadir validacion entre etapas,
implementar un modo debug, y garantizar que el pipeline produzca
resultados correctos con entradas en espanol natural.

## Diagnostico Tecnico

### Problema 1: Domain Enrichment Rompe el Parser (CRITICO)

**Sintomas:** Toda ejecucion con `--prompt` produce:
```
Parse error: No terminal matches 'w' in the current parser context
web crea nestjs prisma web app web
^
```

**Causa raiz:** `DomainEnrichmentFilter` en preprocessor.py anade texto
como "pagina web responsive con tailwind" al input del usuario. Este
texto extra pasa por el lexer, que produce tokens DOMAIN (WEB_APP, etc.)
mezclados con los tokens del usuario. Luego `ParserGLR.receive_mission()`
reconstruye texto plano desde los valores de los tokens:
```python
self._input_text = " ".join(t.get("value", "") for t in tokens)
```
Esto produce "web crea nestjs prisma web app web" — texto que el parser
GLR basado en Lark no puede analizar porque no coincide con ninguna
gramatica.

**Impacto:** El parser falla siempre que hay domain enrichment. Como el
enriquecimiento se activa para el dominio "web" (el mas comun), **el
pipeline nunca produce un AST valido para prompts reales.**

### Problema 2: Datos Entre Etapas Sin Validacion (ALTO)

**Sintomas:** No hay garantia de que el output de una etapa sea compatible
con el input de la siguiente.

**Causa raiz:** Cada etapa recibe `input_data: Any` y produce
`StageOutput.output_data: Any`. No hay:
- Schema Pydantic para el contrato entre etapas
- Validacion de tipo/campos obligatorios
- Tests que verifiquen el formato exacto del output de cada etapa

**Impacto:** Un cambio en el output de una etapa (ej. planner cambia
formato de "tasks") puede romper la etapa siguiente sin que los tests
unitarios lo detecten.

### Problema 3: Token Types Ignorados por el Parser (ALTO)

**Sintomas:** El lexer produce tokens con tipo, categoria y posicion,
pero el parser reconstruye texto plano y relega el analisis a Lark.

**Causa raiz:** `ParserGLR.receive_mission()` descarta la informacion
estructurada de los tokens:
```python
self._input_text = " ".join(t.get("value", "") for t in tokens)
```
Luego `_select_grammar()` y Lark parsean desde cero sobre texto plano.
La riqueza semantica del lexer (categorias: action, domain, tech, ui,
quality) se pierde completamente.

### Problema 4: Error Recovery Inconsistente (MEDIO)

**Sintomas:** Una etapa falla (parser) pero el pipeline continua
arrastrando datos invalidos. Las etapas aguas abajo reciben datos
incompletos y producen output deficiente.

**Causa raiz:** En `base_stage.py`, cuando `act()` lanza excepcion o
retorna `success=False`, el pipeline no se detiene. El `StateGraph`
continua inyectando el `input_data` anterior.

### Problema 5: Sin Modo Debug/Inspeccion (MEDIO)

**Sintomas:** No hay forma de inspeccionar el estado intermedio del
pipeline. Cuando algo falla, no hay visibilidad de que produjo cada
etapa.

**Contexto:** Shell v1.0 tenia `pipeline_debugger.sh` con 5 modos
(trace, step, timing, inspect, xtrace). Python v2.0 no tiene nada
equivalente.

### Problema 6: Cobertura de Lexer para Espanol (BAJO)

**Sintomas:** Palabras comunes en espanol como "disena", "pagina",
"interfaz", "formulario" no estan en los DFAs.

**Causa raiz:** Los DFAs en `sub_dfa.py` tienen ~100 palabras.
Muchas variantes de verbos conjugados faltan.

---

## Plan de Implementacion

### Sprint 14.1: Corregir Flujo Lexer → Parser (CRITICO)

**Objetivo:** El parser debe recibir tokens estructurados, no texto plano.

**Cambios:**
1. `ParserGLR.receive_mission()` — conservar tokens como lista de
   `Token` objects, no reconstruir texto plano
2. `ParserGLR.act()` — usar `Token.type` y `Token.category` para
   construir el AST directamente desde los tokens, no via Lark
3. `_select_grammar()` — usar categorias de tokens (action, domain,
   tech, ui) para seleccionar gramatica, no substring matching
4. Eliminar `_clean_text()` — ya no es necesario si se trabaja con tokens

**Archivos:** `nodes/parser.py`
**Tests:** Actualizar `test_parser_project.py`, `test_parser_ui.py`

### Sprint 14.2: Desactivar Domain Enrichment (CRITICO)

**Objetivo:** Eliminar la fuente de ruido que rompe el parser.

**Cambios:**
1. `DomainEnrichmentFilter.process()` — retornar text sin anadir
   (el proposito del enrichment debe cumplirlo el lexer, no el preprocessor)
2. O alternativamente: mover el enrichment a una etapa posterior,
   despues del parser, para que no interfiera con el analisis sintactico

**Decision:** Desactivar temporalmente. El enrichment se reintroducira
en Sprint 14.5 como parte del "context augmenter" post-parseo.

**Archivos:** `nodes/preprocessor.py` (lineas 71-82)
**Tests:** `test_preprocessor_filters.py`

### Sprint 14.3: Validacion de Datos Entre Etapas (ALTO)

**Objetivo:** Garantizar contratos de datos entre etapas del pipeline.

**Cambios:**
1. Crear `contracts.py` con modelos Pydantic para el output de cada etapa:
   - `LexerOutput`: tokens: list[Token]
   - `ParserOutput`: ast: ASTNode, grammar: str
   - `SemanticOutput`: ast: ASTNode, symbol_table: dict
   - `IROutput`: ir_tree: IRNode
   - `PlannerOutput`: tasks: list[Task], commands: list[Command], ir_tree: IRNode
   - `SynthesisOutput`: files: list[str], errors: list[str]
   - `UIOutput`: files: list[str], components: list[str]
2. Modificar `PipelineStage.execute()` para validar contracto de salida
3. Tests de contrato entre etapas acopladas

**Archivos:** `contracts.py` (nuevo), `base_stage.py` (modificado)
**Tests:** `test_contracts.py` (nuevo)

### Sprint 14.4: Modo Debug para Pipeline Python (ALTO)

**Objetivo:** Proveer visibilidad del estado intermedio del pipeline,
equivalente al `pipeline_debugger.sh` de Shell v1.0.

**Cambios:**
1. Crear `debugger.py` con:
   - `PipelineDebugger` class que wrappea `PipelineOrchestrator`
   - `trace` mode: imprime entrada/salida de cada etapa
   - `step` mode: pausa entre etapas (requiere confirmacion)
   - `timing` mode: muestra tiempo por etapa
   - `inspect` mode: muestra contenido del StageContext post-etapa
2. Integrar via `--debug` flag en CLI:
   ```
   ./compiler-bot/agentic --prompt "..." --debug trace
   ./compiler-bot/agentic --prompt "..." --debug timing
   ```
3. Snapshot de estado: `StageContext.model_dump()` serializado a JSON
   en `debug_output/` por etapa

**Archivos:** `debugger.py` (nuevo), `compiler-bot/agentic` (modificado),
`orchestrator.py` (modificado)
**Tests:** `test_debugger.py` (nuevo)

### Sprint 14.5: Fallback y Recovery Robusto (MEDIO)

**Objetivo:** Pipeline no debe producir output corrupto cuando una
etapa falla.

**Cambios:**
1. En `PipelineStage.execute()`: si `success=False`, detener pipeline
   y retornar error informativo con la etapa que fallo
2. En `orquestador._make_node()`: propagar error al StateGraph como
   estado terminal
3. CLI: mostrar error con sugerencia (ej. "Parser fallo: prueba con
   una instruccion mas simple como 'crea un modulo'")

**Archivos:** `base_stage.py`, `orchestrator.py`, `compiler-bot/agentic`
**Tests:** `test_error_recovery.py` (nuevo)

### Sprint 14.6: Expandir Lexer para Espanol Natural (BAJO)

**Objetivo:** Reconocer mas variantes del espanol en los DFAs.

**Cambios:**
1. `ActionDFA`: anadir conjugaciones faltantes
   - "disena", "disenar" → CREATE
   - "genera", "generar" → CREATE
   - "construye", "construir" → CREATE
   - "anade", "anadir" → CREATE
2. `UIDFA`: anadir terminos de UI comunes
   - "formulario", "form" → FORM
   - "tabla", "table" → TABLE
   - "boton", "button" → BUTTON
   - "modal" → MODAL
   - "card", "tarjeta" → CARD
   - "navbar", "barra" → NAVBAR
   - "footer", "pie" → FOOTER
3. `DomainDFA`: anadir variantes
   - "sitio", "site" → WEB_APP
   - "sistema", "system" → SAAS
4. `TechDFA`: anadir tecnologias
   - "tailwind" → TAILWIND (ya existe?)
   - "next", "nextjs" → NEXTJS

**Archivos:** `nodes/sub_dfa.py`
**Tests:** `test_lexer_sub_dfas.py` (actualizar)

---

## Definition of Done

- [ ] **14.1** — Parser recibe tokens estructurados y construye AST
       sin reconstruir texto plano. `test_parser_*.py` actualizados.
- [ ] **14.2** — Domain enrichment desactivado. Parser no falla por
       ruido textual. `test_preprocessor_filters.py` actualizado.
- [ ] **14.3** — Contractos Pydantic entre etapas. `test_contracts.py`
       verifica formato de output de cada etapa.
- [ ] **14.4** — `--debug trace|timing|inspect` funcional en CLI.
       `PipelineDebugger` captura snapshots de estado.
- [ ] **14.5** — Pipeline se detiene en primera etapa fallida con
       mensaje claro. `test_error_recovery.py` pasa.
- [ ] **14.6** — Lexer reconoce ~30 palabras nuevas en espanol.
       `test_lexer_sub_dfas.py` actualizado.
- [ ] Pipeline completo ejecuta sin errores con prompt en espanol
- [ ] **ruff check .** = 0 errores
- [ ] **pytest** = todos pasan

## Archivos del Sprint

| Archivo | Accion |
|---------|--------|
| `nodes/parser.py` | MODIFICAR — flujo basado en tokens |
| `nodes/preprocessor.py` | MODIFICAR — desactivar enrichment |
| `contracts.py` | NUEVO — modelos Pydantic de contrato |
| `base_stage.py` | MODIFICAR — validacion de contrato + error recovery |
| `debugger.py` | NUEVO — modo debug con trace/step/timing/inspect |
| `orchestrator.py` | MODIFICAR — integracion con debugger y error recovery |
| `compiler-bot/agentic` | MODIFICAR — flag `--debug` |
| `nodes/sub_dfa.py` | MODIFICAR — nuevos terminos espanol |
| `tests/test_contracts.py` | NUEVO |
| `tests/test_debugger.py` | NUEVO |
| `tests/test_error_recovery.py` | NUEVO |
| `tests/test_parser_project.py` | MODIFICAR |
| `tests/test_parser_ui.py` | MODIFICAR |
| `tests/test_lexer_sub_dfas.py` | MODIFICAR |
| `tests/test_preprocessor_filters.py` | MODIFICAR |

## Riesgos

| Riesgo | Mitigacion |
|--------|------------|
| Refactor del parser rompe gramaticas Lark existentes | Tests de regresion en `test_parser_*.py` |
| Desactivar enrichment reduce calidad del RequirementGraph | El enrichment se reintroducira post-parseo en sprint futuro |
| Modo debug anade latencia | Solo activo con `--debug`, no afecta modo normal |
| Contractos Pydantic pueden ser demasiado restrictivos | Usar `Field(default=...)` para backward compatibility |
