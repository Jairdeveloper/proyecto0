---
id: 087
area: dev
type: prop
module: compiler_bot
version: 1.0
status: IMPLEMENTED
tags:
  - sprint-15
  - nlp
  - intent
  - pipeline-refactor
  - parser-fix
  - contracts
  - error-recovery
summary: >-
  Propuesta de integracion de una capa NLP + Intent dentro del pipeline
  Python v2.0 para corregir las falencias identificadas en el Sprint 14
  (parser roto, domain enrichment ruidoso, falta de contratos entre etapas,
  error recovery inexistente). La capa NLP reemplaza el preprocessor
  actual y alimenta al lexer/parser con datos estructurados.
keywords:
  - sprint-15
  - nlp
  - intent-classifier
  - ner
  - slot-filling
  - contracts
  - pydantic
  - error-recovery
  - pipeline
  - parser-fix
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Propuesta de integracion NLP + Intent para pipeline Python v2.0
---

# 087_PROP_DEV_NLP_INTENT_PIPELINE_1_0_DRAFT

## Resumen Ejecutivo

El debugger del Sprint 14.4 confirmo 4 problemas criticos en el pipeline
Python v2.0 que impiden su funcionamiento correcto con entradas reales:

| Problema | Evidencia (debug output) | Sprint |
|----------|--------------------------|--------|
| Parser falla siempre | `Parse error: No terminal matches 'w'` | 14.1 |
| Domain enrichment ruidoso | `"web crea web app web"` en el input del parser | 14.2 |
| Sin validacion entre etapas | `error: None` cuando validator falla | 14.3 |
| Pipeline no se detiene | semantic_analyzer procesa `{}` y continua | 14.5 |

La propuesta original (doc 014) planteaba una capa NLP en shell. Dado que
el proyecto migro a Python v2.0 como stack primario, esta propuesta adapta
esa capa NLP a Python y la integra **dentro del StateGraph existente**,
reemplazando los componentes rotos y anadiendo los que faltan.

### Arquitectura Propuesta

```
INPUT → [NLP STAGE] → [FIXED LEXER] → [FIXED PARSER] → [CONTRACT VALIDATOR]
       → semantic → IR → planner → synthesis → ui → validator → [ERROR GUARD]
                                                                        ↓
                                                              Output / Error
```

Cambios clave respecto al pipeline actual:
- El **NLP Stage** reemplaza al requirement_decomposer + preprocessor
- El **lexer** recibe y produce tokens estructurados (no texto)
- El **parser** construye AST desde tokens (no reconstruye texto)
- Un **Contract Validator** Pydantic entre cada par de etapas
- Un **Error Guard** detiene el pipeline si alguna etapa falla

---

## Diagnostico de Problemas Confirmados

### Problema A: Preprocessor aplana datos estructurados (Sprint 14.2)

El `requirement_decomposer` produce un dict estructurado:

```json
{"domain": "web", "entities": [], "features": [], ...}
```

Pero `Preprocessor.receive_mission()` hace `str(input_data)` y los 4
filtros operan sobre ese string como texto plano. El resultado:

```
"domain: web, entities: , features: , ... [domain:web stack:frontend, backend, database]"
```

Esto destruye la estructura y el `DomainEnrichmentFilter` anade ruido.

### Problema B: Parser reconstruye texto desde tokens (Sprint 14.1)

`ParserGLR.receive_mission()` hace:

```python
self._input_text = " ".join(t.get("value", "") for t in tokens)
```

Descarta tipo, categoria, posicion y confianza de cada token. Luego
Lark parsea desde cero sobre texto plano reconstruido — que incluye
el ruido del enrichment.

### Problema C: Sin contratos entre etapas (Sprint 14.3)

Cada etapa recibe `input_data: Any` y produce `output_data: Any`. No
hay garantia de que el output de una etapa sea compatible con el input
de la siguiente. Ejemplo: el validator retorna `error: None` cuando
falla porque el campo no esta tipado.

### Problema D: Pipeline no se detiene en fallo (Sprint 14.5)

El parser falla → produce `{}` → semantic_analyzer procesa `{}` sin
AST → IR genera nodo vacio → planner reporta 0 tasks → synthesis
genera 0 archivos → ui_generator genera 4 CSS default (sin UI que
generar) → validator falla porque los CSS no tienen formato.
El pipeline arrastra datos invalidos hasta el final.

---

## Propuesta: NLP Stage + Refactor del Pipeline

### Componentes Nuevos

```
agentic_pipeline/
  ├── nlp/                          # NEW: NLP + Intent module
  │   ├── __init__.py
  │   ├── intent_classifier.py      # Clasificador de intenciones
  │   ├── ner_extractor.py          # Reconocimiento de entidades
  │   ├── slot_filler.py            # Completitud de slots
  │   ├── ambiguity_detector.py     # Deteccion de ambiguedad
  │   └── enriched_input.py         # Modelo Pydantic de entrada enriquecida
  ├── nodes/
  │   ├── intent_stage.py           # NEW: NLP como PipelineStage
  │   ├── preprocessor.py           # MODIFY: simplificar, no aplanar
  │   ├── lexer.py                  # MODIFY: trabajar con tokens estructurados
  │   └── parser.py                 # MODIFY: construir AST desde tokens
  ├── contracts.py                  # NEW: Pydantic contracts entre etapas
  ├── error_guard.py                # NEW: detener pipeline en fallo
  ├── debugger.py                   # EXISTENTE: mantener
  └── orchestrator.py               # MODIFY: integrar nuevos componentes
```

### 1. NLP Stage (reemplaza requirement_decomposer + enrichment)

Un nuevo PipelineStage que clasifica la intencion del usuario, extrae
entidades y completa slots. Produce un `EnrichedInput` estructurado.

#### Intent Classifier (`nlp/intent_classifier.py`)

Clasificador basado en reglas + patrones + scoring. Portado de la
propuesta 014 a Python puro (sin shell).

```python
class IntentClassifier:
    TAXONOMY = {
        "SCAFFOLD": ["crea", "genera", "nuevo", "necesito", "haz", "construye"],
        "QUERY": ["como", "que es", "explica", "configura", "ayuda"],
        "MODIFY": ["agrega", "cambia", "modifica", "anade"],
        "DELETE": ["borra", "elimina", "quita"],
        "EXPLORE": ["que modulos", "listame", "estado"],
        "CONFIGURE": ["configura", "usa", "por defecto"],
        "CLARIFY": ["si", "no", "el de", "con"],
    }

    def classify(self, text: str) -> IntentResult:
        scores = {}
        for intent, patterns in self.TAXONOMY.items():
            scores[intent] = self._score(text, patterns)
        confidence = max(scores.values())
        primary = max(scores, key=scores.get)
        return IntentResult(
            primary=primary,
            confidence=confidence,
            scores=scores,
            domain=self._detect_domain(text),
        )

    def _score(self, text: str, patterns: list[str]) -> float:
        matches = sum(1 for p in patterns if p in text.lower())
        return min(matches / 2.0, 1.0) if matches else 0.0
```

#### NER Extractor (`nlp/ner_extractor.py`)

Extrae entidades, tecnologias, requisitos usando listas blancas
y patrones de texto. Reemplaza el DomainEnrichmentFilter.

```python
class NERExtractor:
    TECH_WHITELIST = [
        "nestjs", "prisma", "react", "vue", "postgres", "mysql",
        "mongodb", "redis", "docker", "stripe", "jwt", "tailwind",
    ]
    REQUIREMENT_PATTERNS = [
        (r"con\s+(\w+)", "integracion"),
        (r"que tenga\s+(\w[\w\s]*\w)", "requisito"),
        (r"usando\s+(\w[\w\s]*\w)", "tecnologia"),
        (r"sin\s+(\w[\w\s]*\w)", "negacion"),
    ]

    def extract(self, text: str, intent: str) -> Entities:
        return Entities(
            modulos=self._extract_modules(text),
            techs=self._extract_techs(text),
            requisitos=self._extract_requirements(text),
        )
```

#### Slot Filler (`nlp/slot_filler.py`)

Determina si la instruccion tiene todos los campos necesarios.

```python
class SlotFiller:
    REQUIRED_SLOTS = {
        "SCAFFOLD": ["accion", "tipo", "nombre"],
        "MODIFY": ["accion", "nombre"],
        "DELETE": ["accion", "nombre"],
    }

    def fill(self, intent: IntentResult, entities: Entities) -> Slots:
        slots = Slots(
            accion=self._infer_action(intent, entities),
            tipo=self._infer_type(entities),
            nombre=self._infer_name(entities),
            tech=self._infer_tech(entities),
        )
        slots.completado = all(
            getattr(slots, s) is not None
            for s in self.REQUIRED_SLOTS.get(intent.primary, [])
        )
        slots.faltantes = [
            s for s in self.REQUIRED_SLOTS.get(intent.primary, [])
            if getattr(slots, s) is None
        ]
        return slots
```

#### Modelo EnrichedInput (`nlp/enriched_input.py`)

```python
class EnrichedInput(BaseModel):
    raw: str
    intent: IntentResult
    entities: Entities
    slots: Slots
    ambiguity: AmbiguityResult
    context: ContextState
```

### 2. Preprocessor Simplificado

El preprocessor actual se simplifica drasticamente:
- Eliminar `DomainEnrichmentFilter` (el NER lo reemplaza)
- Eliminar `ImplicitRequirementFilter` (el slot filler lo maneja)
- Mantener solo `NormalizationFilter` (trim, lowercase)
- `receive_mission()` recibe `EnrichedInput`, no `str(input_data)`

```python
class Preprocessor(PipelineStage):
    def receive_mission(self, input_data: object) -> None:
        # input_data es EnrichedInput del NLP Stage
        enriched = EnrichedInput.model_validate(input_data)
        self._normalized = self._normalize(enriched.raw)
        self._enriched = enriched

    def act(self, plan: ActionPlan) -> StageOutput:
        return StageOutput(
            stage=self.context.stage,
            output_data={
                "normalized_text": self._normalized,
                "enriched": self._enriched.model_dump(),
                "domain": self._enriched.intent.domain,
            },
        )
```

### 3. Lexer → Parser con Tokens Estructurados

El lexer produce `list[Token]` como antes, pero el parser **no**
reconstruye texto plano. En vez de:

```python
# Actual (ROTO):
self._input_text = " ".join(t.get("value", "") for t in tokens)
```

Usa los tokens directamente:

```python
# Propuesto:
class ParserGLR(PipelineStage):
    def receive_mission(self, input_data: object) -> None:
        data = TokensOutput.model_validate(input_data)
        self._tokens = data.tokens  # list[Token] con tipo, categoria, posicion
        self._enriched = data.enriched  # EnrichedInput del NLP stage

    def act(self, plan: ActionPlan) -> StageOutput:
        grammar = self._select_grammar(self._tokens)
        ast = self._build_ast(self._tokens, grammar)
        # ast se construye desde Token.type + Token.category
        # sin pasar por Lark
        return StageOutput(stage=self.context.stage, output_data={"ast": ast, "grammar": grammar})
```

### 4. Contractos Pydantic Entre Etapas (contracts.py)

```python
class NLPOutput(BaseModel):
    enriched: EnrichedInput
    intent: str
    confidence: float

class PreprocessorOutput(BaseModel):
    normalized_text: str
    enriched: EnrichedInput
    domain: str

class LexerOutput(BaseModel):
    tokens: list[Token]
    enriched: EnrichedInput

class ParserOutput(BaseModel):
    ast: dict
    grammar: str
    enriched: EnrichedInput

class SemanticOutput(BaseModel):
    ast: dict
    symbol_table: list[dict]
    semantic_errors: list[str]
    warnings: list[str]

class IROutput(BaseModel):
    ir_tree: dict
    ir_json: str

class PlannerOutput(BaseModel):
    tasks: list[dict]
    commands: list[dict]
    complexity: str

class SynthesisOutput(BaseModel):
    generated_files: list[str]
    errors: list[str]

class UIOutput(BaseModel):
    generated_files: list[str]
    components: list[str]

class ValidatorOutput(BaseModel):
    results: list[dict]
    should_retry: bool
```

Cada `PipelineStage.act()` valida su output contra el contrato antes
de retornar:

```python
def execute(self, input_data: object) -> StageOutput:
    self.receive_mission(input_data)
    analysis = self.analyze()
    plan = self.reflect_and_plan(analysis)
    output = self.act(plan)
    # Validar contrato de salida
    contract = STAGE_CONTRACTS.get(self.context.stage)
    if contract:
        contract.model_validate(output.output_data)
    return output
```

### 5. Error Guard (error_guard.py)

El Error Guard se inserta como un nodo de routing en el StateGraph
que verifica `success` despues de cada etapa y decide si continuar
o terminar:

```python
class ErrorGuard:
    @staticmethod
    def should_continue(state: StageContext) -> Literal["continue", "abort"]:
        if state.last_error:
            return "abort"
        return "continue"
```

En el StateGraph:

```python
def _build(self) -> None:
    stages = list(Stage)
    self.graph.set_entry_point(stages[0].value)
    for stage in stages:
        self.graph.add_node(stage.value, self._make_node(stage))
        # Conditional edge: si falla → a END
        self.graph.add_conditional_edges(
            stage.value,
            ErrorGuard.should_continue,
            {"continue": next_stage, "abort": END},
        )
```

El CLI muestra el error con sugerencia:

```
$ ./compiler-bot/agentic --prompt "web crea web app web"
Error en etapa parser: No se pudo analizar la instruccion.
Sugerencia: prueba con una instruccion mas simple como
  'crea un modulo de pagos'
```

---

## Integracion con el Debugger Existente

El `PipelineDebugger` del Sprint 14.4 se mantiene intacto y es
compatible con los nuevos componentes. Con `--debug trace --show-output`
se vera el flujo NLP:

```
  [intent] OK  (523B)  ← nodes/intent_stage.py:42
    metrics: intent=SCAFFOLD confidence=0.92 domain=web
    ── output:
      {
        "intent": {"primary": "SCAFFOLD", "confidence": 0.92},
        "entities": {"modulos": ["pagos"], "techs": ["nestjs"]},
        "slots": {"accion": "create", "tipo": "module", "nombre": "pagos"}
      }
  [preprocessor] OK  (201B)  ← nodes/preprocessor.py:44
    ── output:
      {
        "normalized_text": "crea un modulo de pagos",
        "domain": "web"
      }
  [lexer] OK  (412B)  ← nodes/lexer.py:65
    metrics: tokens_count=4
    ── output:
      {
        "tokens": [
          {"value": "crea", "type": "CREATE", "category": "action"},
          {"value": "un", "type": "ARTICLE", "category": "grammar"},
          {"value": "modulo", "type": "MODULE", "category": "entity"},
          {"value": "pagos", "type": "ENTITY", "category": "domain"}
        ]
      }
  [parser] OK  (1.2KB)  ← nodes/parser.py:36
    ── output:
      {
        "ast": {"type": "module", "name": "pagos", "actions": ["create"]},
        "grammar": "project"
      }
```

---

## Plan de Implementacion

### Fase 1: Fundacion NLP (3-4 dias)

| ID | Tarea | Archivo | Dependencias |
|----|-------|---------|--------------|
| NLP-01 | Crear modelo `EnrichedInput` Pydantic | `nlp/enriched_input.py` | — |
| NLP-02 | Implementar `IntentClassifier` con taxonomia completa | `nlp/intent_classifier.py` | NLP-01 |
| NLP-03 | Implementar `NERExtractor` con listas blancas + patrones | `nlp/ner_extractor.py` | NLP-01 |
| NLP-04 | Implementar `SlotFiller` con slots requeridos/opcionales | `nlp/slot_filler.py` | NLP-01, NLP-02, NLP-03 |
| NLP-05 | Implementar `AmbiguityDetector` | `nlp/ambiguity_detector.py` | NLP-02, NLP-03, NLP-04 |
| NLP-06 | Tests: classifier, NER, slots, ambiguity | `tests/test_nlp_*.py` | NLP-02..NLP-05 |

### Fase 2: Pipeline Refactor (3-4 dias)

| ID | Tarea | Archivo | Dependencias |
|----|-------|---------|--------------|
| PIPE-01 | Crear `IntentStage` (PipelineStage) | `nodes/intent_stage.py` | NLP-06 |
| PIPE-02 | Simplificar `Preprocessor` (eliminar enrichment) | `nodes/preprocessor.py` | — |
| PIPE-03 | Refactor `ParserGLR` para recibir tokens | `nodes/parser.py` | — |
| PIPE-04 | Crear `contracts.py` con todos los modelos | `contracts.py` | — |
| PIPE-05 | Anadir validacion de contrato en `base_stage.execute()` | `base_stage.py` | PIPE-04 |
| PIPE-06 | Crear `ErrorGuard` con routing condicional | `error_guard.py` | — |
| PIPE-07 | Actualizar `orchestrator.py`: nuevo orden de etapas + error guard | `orchestrator.py` | PIPE-01..PIPE-06 |

### Fase 3: Tests y Hardening (2-3 dias)

| ID | Tarea | Archivo | Dependencias |
|----|-------|---------|--------------|
| TEST-01 | Tests de integracion: NLP + pipeline completo | `tests/test_integration_nlp.py` | PIPE-07 |
| TEST-02 | Tests de contratos entre cada par de etapas | `tests/test_contracts.py` | PIPE-04 |
| TEST-03 | Tests de error recovery (cada etapa falla individualmente) | `tests/test_error_recovery.py` | PIPE-06 |
| TEST-04 | Actualizar tests existentes (parser, preprocessor, lexer) | varios | PIPE-02, PIPE-03 |
| TEST-05 | Verificar debugger con nuevo pipeline | `tests/test_debugger.py` | PIPE-07 |

---

## Orden de Etapas del Pipeline Actualizado

```
0. INTENT               (NUEVO)  — clasifica, extrae, completa slots
1. PREPROCESSOR         (MODIFICADO) — solo normalizacion, sin enrichment
2. LEXER                (MODIFICADO) — produce tokens + pasa EnrichedInput
3. PARSER               (REFACTOR) — AST desde tokens, no desde texto
4. SEMANTIC_ANALYZER    (SIN CAMBIOS)
5. IR_GENERATOR         (SIN CAMBIOS)
6. PLANNER              (SIN CAMBIOS)
7. SYNTHESIS            (SIN CAMBIOS)
8. UI_GENERATOR         (SIN CAMBIOS)
9. VALIDATOR            (SIN CAMBIOS)
   ERROR_GUARD          (NUEVO) — routing condicional entre cada etapa
```

El `ErrorGuard` se ejecuta **entre** cada etapa via conditional edges
del StateGraph. Si cualquier etapa retorna `success=False`, el grafo
termina y se muestra el error.

---

## Archivos del Sprint

| Archivo | Accion |
|---------|--------|
| `nlp/__init__.py` | NUEVO |
| `nlp/intent_classifier.py` | NUEVO |
| `nlp/ner_extractor.py` | NUEVO |
| `nlp/slot_filler.py` | NUEVO |
| `nlp/ambiguity_detector.py` | NUEVO |
| `nlp/enriched_input.py` | NUEVO |
| `nodes/intent_stage.py` | NUEVO |
| `contracts.py` | NUEVO |
| `error_guard.py` | NUEVO |
| `nodes/preprocessor.py` | MODIFICAR — eliminar enrichment, recibir EnrichedInput |
| `nodes/lexer.py` | MODIFICAR — pasar EnrichedInput al parser |
| `nodes/parser.py` | MODIFICAR — construir AST desde tokens |
| `base_stage.py` | MODIFICAR — validar contrato en execute() |
| `orchestrator.py` | MODIFICAR — nuevo orden, conditional edges |
| `compiler-bot/agentic` | MODIFICAR — flag `--dialog` para modo interactivo |
| `tests/test_nlp_classifier.py` | NUEVO |
| `tests/test_nlp_ner.py` | NUEVO |
| `tests/test_nlp_slots.py` | NUEVO |
| `tests/test_nlp_ambiguity.py` | NUEVO |
| `tests/test_contracts.py` | NUEVO |
| `tests/test_error_recovery.py` | NUEVO |
| `tests/test_integration_nlp.py` | NUEVO |

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigacion |
|--------|---------|------------|
| NLP clasifica mal (falso positivo) | Crea modulo equivocado | Threshold 0.8 para modo directo; mostrar confirmacion |
| NLP clasifica mal (falso negativo) | Usuario frustrado | Modo QUERY responde con ayuda; sugerir comandos validos |
| Refactor del parser rompe tests existentes | Regresion | Tests de parser actualizados primero; comparar AST antes/despues |
| Contracts Pydantic demasiado restrictivos | Etapas fallan por campos opcionales | Usar `Field(default=None)` en todos los opcionales |
| Error Guard detiene pipeline prematuramente | Falso fallo por etapa parcial | Solo detener en errores de etapa, no en warnings |

---

## Criterios de Aceptacion

- [ ] `ruff check .` = 0 errores
- [ ] pytest: 100% tests pasando (existentes + nuevos)
- [ ] NLP clasifica correctamente SCAFFOLD, QUERY, MODIFY, DELETE
- [ ] NER extrae entidades, techs y requisitos del texto
- [ ] Parser construye AST desde tokens sin reconstruir texto
- [ ] Contracts validan output de cada etapa
- [ ] Pipeline se detiene si una etapa reporta `success=False`
- [ ] `--debug trace --show-output` muestra el flujo NLP completo
- [ ] `--prompt "crea un modulo de pagos"` produce AST valido (sin error de parser)
