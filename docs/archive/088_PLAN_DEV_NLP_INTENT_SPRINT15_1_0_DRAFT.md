---
id: 088
area: DEV
type: PLAN
module: COMPILER_BOT
version: 1.0
status: DRAFT
tags:
  - sprint-15
  - nlp
  - execution-plan
  - intent
  - pipeline-refactor
  - contracts
summary: >-
  Plan de ejecucion detallado para el Sprint 15 — Integracion de capa
  NLP + Intent en el pipeline Python v2.0. Incluye orden de tareas por
  fase, dependencias, criterios de aceptacion por paso, ruta critica y
  estrategia de rollback.
keywords:
  - sprint-15
  - execution-plan
  - nlp
  - intent
  - parser-refactor
  - contracts
  - error-recovery
changelog:
  - version: '1.0'
    date: 2026-06-15
    description: Plan de ejecucion Sprint 15 — NLP + Intent Pipeline
---

# 088_PLAN_DEV_NLP_INTENT_SPRINT15_1_0_DRAFT

## Resumen

Ejecucion del Sprint 15 segun la propuesta `087_PROP_DEV_NLP_INTENT_PIPELINE`.
Tres fases consecutivas:

```
FASE 1: Fundacion NLP  ──→  FASE 2: Pipeline Refactor  ──→  FASE 3: Tests
 (3-4 dias)                  (3-4 dias)                      (2-3 dias)
```

Cada fase tiene pasos secuenciales con criterios de aceptacion propios.
Al final de cada fase se ejecuta `ruff check . && pytest tests/ -q` como
checkpoint obligatorio.

---

## Fase 1: Fundacion NLP

Objetivo: Componentes NLP puros (sin tocar el pipeline existente).

### Paso 1.1: Crear directorio `nlp/` y `enriched_input.py`

**Archivos:** `compiler-bot/agentic_pipeline/nlp/__init__.py`, `nlp/enriched_input.py`

Crear el modelo central `EnrichedInput` y sus sub-modelos. Todo el flujo
NLP produce y consume este modelo.

```python
# nlp/enriched_input.py
from pydantic import BaseModel, Field
from typing import Optional


class IntentResult(BaseModel):
    primary: str                     # "SCAFFOLD" | "QUERY" | "MODIFY" | ...
    secondary: Optional[str] = None
    confidence: float                # 0.0 - 1.0
    scores: dict[str, float] = {}    # score por cada intencion
    domain: str = "backend"          # "backend" | "frontend" | "infra"


class Entity(BaseModel):
    nombre: str
    tipo: str                        # "module" | "tech" | "requirement"
    rol: str = ""
    negado: bool = False


class Entities(BaseModel):
    modulos: list[Entity] = []
    techs: list[Entity] = []
    requisitos: list[Entity] = []


class Slots(BaseModel):
    accion: Optional[str] = None     # "create" | "update" | "delete" | ...
    tipo: Optional[str] = None       # "module" | "entity" | "project"
    nombre: Optional[str] = None
    tech: Optional[str] = None
    completado: bool = False
    faltantes: list[str] = []


class AmbiguityResult(BaseModel):
    detected: bool = False
    elementos: list[dict] = []


class ContextState(BaseModel):
    turno: int = 1
    session_id: str = ""
    historial: list[dict] = []
    ultima_entidad: str = ""
    defaults: dict = {"tech": "nestjs"}


class EnrichedInput(BaseModel):
    raw: str
    intent: IntentResult
    entities: Entities
    slots: Slots
    ambiguity: AmbiguityResult
    context: ContextState = Field(default_factory=ContextState)
```

**Verificacion:**
```bash
ruff check compiler-bot/agentic_pipeline/nlp/
python3 -c "from agentic_pipeline.nlp.enriched_input import EnrichedInput; print('OK')"
```

---

### Paso 1.2: Implementar `IntentClassifier`

**Archivo:** `compiler-bot/agentic_pipeline/nlp/intent_classifier.py`

Clasificador basado en patrones con scoring normalizado.

```python
# nlp/intent_classifier.py
import re
from .enriched_input import IntentResult


class IntentClassifier:
    TAXONOMY: dict[str, list[str]] = {
        "SCAFFOLD": [
            r"crea", r"genera", r"nuev[oa]", r"necesit[ao]", r"quier[eo]",
            r"haz", r"construye", r"implementa", r"anade", r"disena",
        ],
        "QUERY": [
            r"c[oó]mo", r"qu[eé] es", r"explica", r"configura",
            r"ayuda", r"help", r"qu[eé] son", r"muestra", r"listame",
        ],
        "MODIFY": [
            r"actualiza", r"cambia", r"modifica", r"agrega",
            r"edita", r"aniade",
        ],
        "DELETE": [
            r"borra", r"elimina", r"remove", r"delete", r"saca", r"quita",
        ],
        "EXPLORE": [
            r"qu[eé] m[oó]dulos", r"listame", r"qu[eé] tengo",
            r"estado", r"status",
        ],
        "CONFIGURE": [
            r"configura", r"usa", r"por defecto", r"cambia idioma", r"set",
        ],
        "CLARIFY": [
            r"^(s[ií]|no|ok|vale)$", r"el de", r"con ",
        ],
    }

    DOMAIN_PATTERNS: dict[str, list[str]] = {
        "backend": ["api", "servicio", "backend", "database", "db", "crud"],
        "frontend": ["frontend", "ui", "pagina", "web", "interfaz", "componente"],
        "infra": ["docker", "deploy", "ci/cd", "devops", "infra"],
    }

    def classify(self, text: str) -> IntentResult:
        text_lower = text.lower()
        scores: dict[str, float] = {}
        for intent, patterns in self.TAXONOMY.items():
            score = self._score(text_lower, patterns)
            if score > 0:
                scores[intent] = score

        if not scores:
            scores["UNKNOWN"] = 1.0

        max_score = max(scores.values())
        primary = max(scores, key=scores.get)
        domain = self._detect_domain(text_lower)

        return IntentResult(
            primary=primary,
            confidence=round(max_score, 4),
            scores=scores,
            domain=domain,
        )

    def _score(self, text: str, patterns: list[str]) -> float:
        matches = 0
        for p in patterns:
            if re.search(p, text):
                matches += 1
        return min(matches / 2.0, 1.0) if matches > 0 else 0.0

    def _detect_domain(self, text: str) -> str:
        for domain, patterns in self.DOMAIN_PATTERNS.items():
            for p in patterns:
                if p in text:
                    return domain
        return "backend"
```

**Prueba manual:**
```python
clf = IntentClassifier()
r = clf.classify("crea un modulo de pagos")
assert r.primary == "SCAFFOLD"
assert r.confidence >= 0.5
```

---

### Paso 1.3: Implementar `NERExtractor`

**Archivo:** `compiler-bot/agentic_pipeline/nlp/ner_extractor.py`

Extrae entidades, tecnologias y requisitos del texto.

```python
# nlp/ner_extractor.py
import re
from .enriched_input import Entities, Entity


class NERExtractor:
    TECH_WHITELIST: list[str] = [
        "nestjs", "prisma", "react", "vue", "nextjs", "nuxt",
        "express", "fastapi", "django", "flask", "spring",
        "postgres", "mysql", "mongodb", "redis", "sqlite",
        "docker", "kubernetes", "k8s", "aws", "gcp", "azure",
        "stripe", "paypal", "jwt", "oauth", "tailwind",
        "graphql", "rest", "grpc", "rabbitmq", "kafka",
    ]

    REQUIREMENT_PATTERNS: list[tuple[str, str]] = [
        (r"con\s+(autenticacion\s+\w+)", "autenticacion"),
        (r"con\s+(cache)", "cache"),
        (r"con\s+(\w+)", "integracion"),
        (r"que tenga\s+([\w\s]+?)(?:$| y |,)", "requisito"),
        (r"usando\s+([\w\s]+?)(?:$| y |,)", "tecnologia"),
        (r"sin\s+([\w\s]+?)(?:$| y |,)", "negacion"),
        (r"integrado con\s+(\w+)", "integracion"),
        (r"que soporte\s+([\w\s]+?)(?:$| y |,)", "requisito"),
    ]

    def extract(self, text: str) -> Entities:
        text_lower = text.lower()
        return Entities(
            modulos=self._extract_modules(text_lower),
            techs=self._extract_techs(text_lower),
            requisitos=self._extract_requirements(text_lower),
        )

    def _extract_modules(self, text: str) -> list[Entity]:
        entities: list[Entity] = []
        for match in re.finditer(
            r"(?:modulo\s+de\s+(\w+)|entidad\s+(\w+)|sistema\s+de\s+(\w+))",
            text,
        ):
            name = next(g for g in match.groups() if g)
            entities.append(Entity(nombre=name, tipo="module"))
        if not entities:
            for match in re.finditer(
                r"(?:crea|genera|nuevo)\s+(?:un\s+)?(?:modulo\s+)?(?:de\s+)?(\w+)",
                text,
            ):
                name = match.group(1)
                if name not in self.TECH_WHITELIST:
                    entities.append(Entity(nombre=name, tipo="module"))
        return entities

    def _extract_techs(self, text: str) -> list[Entity]:
        found: list[Entity] = []
        for tech in self.TECH_WHITELIST:
            if tech in text:
                found.append(Entity(nombre=tech, tipo="tech", rol=tech))
        return found

    def _extract_requirements(self, text: str) -> list[Entity]:
        found: list[Entity] = []
        for pattern, tipo in self.REQUIREMENT_PATTERNS:
            for match in re.finditer(pattern, text):
                valor = match.group(1).strip()
                is_neg = "sin" in pattern or "negacion" in tipo
                found.append(Entity(
                    nombre=valor, tipo=tipo, rol=tipo, negado=is_neg,
                ))
        return found
```

---

### Paso 1.4: Implementar `SlotFiller`

**Archivo:** `compiler-bot/agentic_pipeline/nlp/slot_filler.py`

Determina si la instruccion tiene todos los slots requeridos.

```python
# nlp/slot_filler.py
from .enriched_input import IntentResult, Entities, Slots


class SlotFiller:
    REQUIRED: dict[str, list[str]] = {
        "SCAFFOLD": ["accion", "tipo", "nombre"],
        "MODIFY": ["accion", "nombre"],
        "DELETE": ["accion", "nombre"],
        "QUERY": ["dominio"],
    }

    ACTION_MAP: dict[str, str] = {
        "SCAFFOLD": "create",
        "MODIFY": "update",
        "DELETE": "delete",
        "EXPLORE": "read",
        "QUERY": "read",
        "CONFIGURE": "configure",
    }

    TYPE_MAP: dict[str, str] = {
        "modulo": "module",
        "entidad": "entity",
        "proyecto": "project",
        "sistema": "project",
    }

    def fill(self, intent: IntentResult, entities: Entities) -> Slots:
        slots = Slots(
            accion=self.ACTION_MAP.get(intent.primary),
            tipo=self._infer_type(intent, entities),
            nombre=self._infer_name(entities),
            tech=self._infer_tech(entities),
        )
        required = self.REQUIRED.get(intent.primary, [])
        slots.faltantes = [
            s for s in required
            if getattr(slots, s) is None
        ]
        slots.completado = len(slots.faltantes) == 0
        return slots

    def _infer_type(self, intent: IntentResult, entities: Entities) -> str | None:
        if entities.modulos:
            return "module"
        if intent.primary == "SCAFFOLD":
            return "module"
        return None

    def _infer_name(self, entities: Entities) -> str | None:
        if entities.modulos:
            return entities.modulos[0].nombre
        return None

    def _infer_tech(self, entities: Entities) -> str | None:
        if entities.techs:
            return entities.techs[0].nombre
        return None
```

---

### Paso 1.5: Implementar `AmbiguityDetector`

**Archivo:** `compiler-bot/agentic_pipeline/nlp/ambiguity_detector.py`

```python
# nlp/ambiguity_detector.py
import re
from .enriched_input import IntentResult, Entities, Slots, AmbiguityResult


class AmbiguityDetector:
    PRONOMBRES: list[str] = ["lo", "le", "la", "ello", "eso", "le"]

    def detect(
        self,
        text: str,
        intent: IntentResult,
        entities: Entities,
        slots: Slots,
    ) -> AmbiguityResult:
        result = AmbiguityResult()

        if intent.confidence < 0.6:
            result.detected = True
            result.elementos.append({
                "tipo": "intencion_baja",
                "descripcion": "No se puede determinar la intencion principal",
                "sugerencia": "¿Quieres crear, consultar, modificar o eliminar algo?",
            })

        top_two = sorted(intent.scores.items(), key=lambda x: -x[1])
        if len(top_two) >= 2 and (top_two[0][1] - top_two[1][1]) < 0.1:
            result.detected = True
            result.elementos.append({
                "tipo": "multi_intencion",
                "descripcion": f"{top_two[0][0]} y {top_two[1][0]} tienen scores similares",
                "opciones": [top_two[0][0], top_two[1][0]],
            })

        if slots.faltantes:
            result.detected = True
            result.elementos.append({
                "tipo": "slot_faltante",
                "descripcion": f"Faltan slots: {', '.join(slots.faltantes)}",
                "faltantes": slots.faltantes,
            })

        for p in self.PRONOMBRES:
            if re.search(rf"\b{p}\b", text.lower()):
                result.detected = True
                result.elementos.append({
                    "tipo": "referencia_pendiente",
                    "descripcion": f"Pronombre '{p}' sin antecedente",
                    "sugerencia": "¿A que modulo te refieres?",
                })
                break

        return result
```

---

### Paso 1.6: Tests de la capa NLP

**Archivos:** `compiler-bot/agentic_pipeline/tests/test_nlp_classifier.py`,
`tests/test_nlp_ner.py`, `tests/test_nlp_slots.py`, `tests/test_nlp_ambiguity.py`

Crear tests unitarios para cada componente:

```python
# test_nlp_classifier.py
from agentic_pipeline.nlp.intent_classifier import IntentClassifier

class TestIntentClassifier:
    def test_scaffold_detected(self):
        clf = IntentClassifier()
        r = clf.classify("crea un modulo de pagos")
        assert r.primary == "SCAFFOLD"
        assert r.confidence >= 0.5

    def test_query_detected(self):
        clf = IntentClassifier()
        r = clf.classify("como se configura nestjs")
        assert r.primary == "QUERY"

    def test_delete_detected(self):
        clf = IntentClassifier()
        r = clf.classify("borra modulo payments")
        assert r.primary == "DELETE"

    def test_empty_input_returns_unknown(self):
        clf = IntentClassifier()
        r = clf.classify("")
        assert r.primary == "UNKNOWN"

    def test_domain_detection(self):
        clf = IntentClassifier()
        r = clf.classify("crea una api rest")
        assert r.domain == "backend"
```

**Checkpoint Fase 1:**
```bash
ruff check compiler-bot/agentic_pipeline/nlp/
python3 -m pytest compiler-bot/agentic_pipeline/tests/test_nlp_*.py -v
# Esperado: 15-20 tests pasando
```

---

## Fase 2: Pipeline Refactor

Objetivo: Integrar la capa NLP en el pipeline existente, refactorizar
parser y preprocessor, anadir contratos y error guard.

### Paso 2.1: Crear `IntentStage` (PipelineStage)

**Archivo:** `compiler-bot/agentic_pipeline/nodes/intent_stage.py`

Nuevo PipelineStage que encapsula el clasificador, NER, slot filler y
ambiguity detector. Se inserta como etapa 0 del pipeline.

```python
# nodes/intent_stage.py
from ..base_stage import PipelineStage
from ..nlp.intent_classifier import IntentClassifier
from ..nlp.ner_extractor import NERExtractor
from ..nlp.slot_filler import SlotFiller
from ..nlp.ambiguity_detector import AmbiguityDetector
from ..nlp.enriched_input import EnrichedInput, ContextState
from ..state_models import StageContext, StageOutput, AnalysisResult, ActionPlan
from datetime import datetime


class IntentStage(PipelineStage):
    name = "intent"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_text = ""
        self._classifier = IntentClassifier()
        self._ner = NERExtractor()
        self._slots = SlotFiller()
        self._ambiguity = AmbiguityDetector()

    def receive_mission(self, input_data: object) -> None:
        self._input_text = str(input_data) if input_data else ""

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Input: {self._input_text[:50]}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.1,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        intent = self._classifier.classify(self._input_text)
        entities = self._ner.extract(self._input_text)
        slots = self._slots.fill(intent, entities)
        ambiguity = self._ambiguity.detect(
            self._input_text, intent, entities, slots,
        )

        enriched = EnrichedInput(
            raw=self._input_text,
            intent=intent,
            entities=entities,
            slots=slots,
            ambiguity=ambiguity,
            context=ContextState(
                turno=1,
                session_id=datetime.now().isoformat(),
            ),
        )

        return StageOutput(
            stage=self.context.stage,
            output_data=enriched.model_dump(),
            metrics={
                "intent": intent.primary,
                "confidence": intent.confidence,
                "domain": intent.domain,
                "entities": len(entities.modulos) + len(entities.techs),
                "slots_complete": slots.completado,
            },
            success=not ambiguity.detected,
            error=(
                "; ".join(e["descripcion"] for e in ambiguity.elementos)
                if ambiguity.detected else None
            ),
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
```

---

### Paso 2.2: Simplificar `Preprocessor`

**Archivo:** `compiler-bot/agentic_pipeline/nodes/preprocessor.py`

Eliminar `DomainEnrichmentFilter` y `ImplicitRequirementFilter`.
`receive_mission()` recibe `EnrichedInput` en vez de hacer `str()`.

**Cambios concretos:**

1. En `build_filter_chain()`: eliminar `DomainEnrichmentFilter()`
2. En `Preprocessor.receive_mission()`:

```python
def receive_mission(self, input_data: object) -> None:
    if isinstance(input_data, dict) and "raw" in input_data:
        self._input_text = input_data["raw"]  # texto limpio del NLP
        self._domain = input_data.get("intent", {}).get("domain", "web")
    else:
        self._input_text = str(input_data)
        self._domain = "web"
```

3. En `Preprocessor.act()`: el output incluye el `EnrichedInput` intacto:

```python
def act(self, plan: ActionPlan) -> StageOutput:
    result = self._input_text
    for f in self.filters:
        result = f.process(result, {"domain": self._domain})
    return StageOutput(
        stage=self.context.stage,
        output_data={
            "normalized_text": result,
            "domain": self._domain,
        },
        metrics={
            "filters_applied": len(self.filters),
            "input_len": len(self._input_text),
        },
    )
```

**Verificacion:** Los tests existentes de preprocessor pueden fallar si
dependian del enrichment. Actualizar `test_preprocessor_filters.py` para
reflejar el nuevo comportamiento.

---

### Paso 2.3: Refactor `ParserGLR` para recibir tokens

**Archivo:** `compiler-bot/agentic_pipeline/nodes/parser.py`

**Cambio critico:** No reconstruir texto plano desde tokens. En vez de:

```python
# ACTUAL (roto):
self._input_text = " ".join(t.get("value", "") for t in tokens)
```

El parser recibe los tokens directamente y construye el AST:

```python
# NUEVO:
class ParserGLR(PipelineStage):
    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            tokens_raw = input_data.get("tokens", input_data)
            if isinstance(tokens_raw, list):
                self._tokens = tokens_raw
            else:
                self._tokens = []
            self._enriched = input_data.get("enriched", {})
        else:
            self._tokens = []
            self._enriched = {}

    def act(self, plan: ActionPlan) -> StageOutput:
        if not self._tokens:
            return StageOutput(
                stage=self.context.stage,
                output_data={},
                success=False,
                error="No tokens received from lexer",
            )
        ast = self._build_ast_from_tokens(self._tokens)
        return StageOutput(
            stage=self.context.stage,
            output_data={"ast": ast, "grammar": self._select_grammar(self._tokens)},
            metrics={"tokens": len(self._tokens), "ast_nodes": len(ast.get("nodes", []))},
        )

    def _build_ast_from_tokens(self, tokens: list[dict]) -> dict:
        actions = []
        entities = []
        for t in tokens:
            cat = t.get("category", "")
            if cat == "action":
                actions.append(t.get("value", ""))
            elif cat in ("entity", "domain"):
                entities.append(t.get("value", ""))
        return {
            "type": "project" if entities else "unknown",
            "actions": actions,
            "entities": entities,
            "nodes": [{"type": "action", "value": a} for a in actions]
                     + [{"type": "entity", "value": e} for e in entities],
        }
```

**Nota:** El AST builder puede refinarse progresivamente. La version
inicial produce un AST plano. Versiones futuras pueden anadir jerarquia.

---

### Paso 2.4: Crear `contracts.py`

**Archivo:** `compiler-bot/agentic_pipeline/contracts.py`

Modelos Pydantic que validan el output de cada etapa:

```python
# contracts.py
from pydantic import BaseModel, Field
from typing import Any, Optional


class NLPContract(BaseModel):
    raw: str
    intent: dict
    entities: dict
    slots: dict
    ambiguity: dict

class PreprocessorContract(BaseModel):
    normalized_text: str
    domain: str

class LexerContract(BaseModel):
    tokens: list[dict]
    enriched: Optional[dict] = None

class ParserContract(BaseModel):
    ast: dict
    grammar: str

class SemanticContract(BaseModel):
    ast: dict
    semantic_errors: list[str]
    warnings: list[str]

class IRContract(BaseModel):
    ir_json: str

class PlannerContract(BaseModel):
    tasks: list[dict]
    commands: list[dict]
    complexity: str

class SynthesisContract(BaseModel):
    generated_files: list[str]
    errors: list[str]

class UIContract(BaseModel):
    generated_files: list[str]

class ValidatorContract(BaseModel):
    results: list[dict]
    should_retry: bool


STAGE_CONTRACTS: dict[str, type[BaseModel]] = {
    "intent": NLPContract,
    "preprocessor": PreprocessorContract,
    "lexer": LexerContract,
    "parser": ParserContract,
    "semantic_analyzer": SemanticContract,
    "ir_generator": IRContract,
    "planner": PlannerContract,
    "synthesis": SynthesisContract,
    "ui_generator": UIContract,
    "validator": ValidatorContract,
}
```

---

### Paso 2.5: Anadir validacion de contrato en `base_stage.py`

```python
# En base_stage.py, anadir al final de execute():
from .contracts import STAGE_CONTRACTS

def execute(self, input_data: object) -> StageOutput:
    self.receive_mission(input_data)
    analysis = self.analyze()
    plan = self.reflect_and_plan(analysis)
    t0 = time.time()
    try:
        output = self.act(plan)
        # ← NUEVO: validar contrato
        contract = STAGE_CONTRACTS.get(self.name)
        if contract and output.success:
            contract.model_validate(output.output_data)
        # fin nuevo
        duration = time.time() - t0
        ...
```

---

### Paso 2.6: Crear `ErrorGuard`

**Archivo:** `compiler-bot/agentic_pipeline/error_guard.py`

```python
# error_guard.py
from typing import Literal
from .state_models import StageContext


class ErrorGuard:
    @staticmethod
    def should_continue(state: StageContext) -> Literal["continue", "abort"]:
        if state.last_error:
            return "abort"
        return "continue"
```

**Nota:** `StageContext` necesita un campo `last_error: Optional[str] = None`.
Anadirlo a `state_models.py`.

---

### Paso 2.7: Actualizar `orchestrator.py`

**Archivo:** `compiler-bot/agentic_pipeline/orchestrator.py`

Cambios:

1. Anadir `INTENT` al enum `Stage` en `state_models.py`:

```python
class Stage(Enum):
    INTENT = "intent"                    # NUEVA etapa 0
    PREPROCESSOR = "preprocessor"
    ...
```

2. Anadir `IntentStage` al `NODE_MAP`:

```python
from .nodes.intent_stage import IntentStage

NODE_MAP: dict[Stage, type[PipelineStage]] = {
    Stage.INTENT: IntentStage,           # NUEVO
    Stage.PREPROCESSOR: Preprocessor,
    ...
}
```

3. En `_make_node()`, propagar `last_error` al `StageContext`:

```python
def node_fn(ctx: StageContext) -> dict[str, Any]:
    ctx.stage = stage
    ctx.config_overrides["output_dir"] = self._output_dir
    instance = cls(ctx)
    output = instance.execute(ctx.input_data)
    if self._stream_callback:
        self._stream_callback(stage.value, output)
    updated: dict[str, Any] = {"input_data": output.output_data}
    if not output.success:
        ctx.last_error = output.error  # ← NUEVO
        logger.warning("Stage %s failed: %s", stage.value, output.error)
    else:
        ctx.last_error = None           # ← NUEVO
    return updated
```

4. En `_build()`, anadir conditional edges con ErrorGuard:

```python
from .error_guard import ErrorGuard
from langgraph.graph import END

def _build(self) -> None:
    stages = list(Stage)
    self.graph.set_entry_point(stages[0].value)
    for i, stage in enumerate(stages):
        self.graph.add_node(stage.value, self._make_node(stage))
        if i < len(stages) - 1:
            next_stage = stages[i + 1].value
            self.graph.add_conditional_edges(
                stage.value,
                ErrorGuard.should_continue,
                {"continue": next_stage, "abort": END},
            )
        else:
            self.graph.set_finish_point(stage.value)
    self.compiled = self.graph.compile()
```

5. Anadir flag `--dialog` al CLI para modo interactivo:

```python
# En compiler-bot/agentic
parser.add_argument(
    "--dialog", action="store_true",
    help="Enable interactive dialog mode for ambiguous prompts",
)
```

---

### Checkpoint Fase 2

```bash
ruff check compiler-bot/agentic_pipeline/
python3 -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
# Esperado: tests existentes actualizados + nuevos tests NLP pasando
# Pueden fallar tests que dependian del enrichment o del parser old
```

---

## Fase 3: Tests y Hardening

### Paso 3.1: Tests de integracion NLP + pipeline

**Archivo:** `tests/test_integration_nlp.py`

```python
class TestIntegrationNLP:
    @pytest.mark.asyncio
    async def test_pipeline_with_nlp_succeeds(self):
        orch = PipelineOrchestrator()
        result = await orch.run("crea un modulo de pagos")
        assert result["success"]
        assert "output" in result

    @pytest.mark.asyncio
    async def test_pipeline_with_query_intent(self):
        orch = PipelineOrchestrator()
        result = await orch.run("como se configura nestjs")
        # QUERY no pasa al pipeline completo
        assert "output" in result

    @pytest.mark.asyncio
    async def test_debugger_shows_intent_stage(self, capsys):
        debugger = PipelineDebugger(mode="trace", show_output=True)
        await debugger.run("crea un modulo")
        captured = capsys.readouterr()
        assert "[intent]" in captured.err
```

### Paso 3.2: Tests de contratos

**Archivo:** `tests/test_contracts.py`

Testear que cada etapa produce output validable por su contrato:

```python
class TestContracts:
    def test_intent_contract_valid(self):
        data = {"raw": "text", "intent": {}, "entities": {},
                "slots": {}, "ambiguity": {}}
        NLPContract.model_validate(data)  # no raise

    def test_intent_contract_invalid(self):
        with pytest.raises(Exception):
            NLPContract.model_validate({})  # missing fields
```

### Paso 3.3: Tests de error recovery

**Archivo:** `tests/test_error_recovery.py`

```python
class TestErrorRecovery:
    @pytest.mark.asyncio
    async def test_pipeline_stops_on_parser_failure(self):
        orch = PipelineOrchestrator()
        result = await orch.run("")  # empty input → parser falla
        assert not result["success"]

    @pytest.mark.asyncio
    async def test_error_message_contains_stage_name(self):
        orch = PipelineOrchestrator()
        result = await orch.run("")
        assert "error" in result
```

### Paso 3.4: Actualizar tests existentes

- `test_parser_project.py`, `test_parser_ui.py`: actualizar mocks para
  que el parser reciba tokens en vez de texto
- `test_preprocessor_filters.py`: eliminar tests de DomainEnrichment
- `test_lexer_sub_dfas.py`: verificar que los DFAs siguen funcionando
- `test_debugger.py`: verificar que el debugger muestra el nuevo stage
  `intent` correctamente

### Paso 3.5: Debugger verification

Ejecutar manualmente:

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos" --debug trace --show-output
```

Verificar que la salida muestra:

```
  [intent] OK  (...)  ← nodes/intent_stage.py:...
    metrics: intent=SCAFFOLD confidence=...
    ── output:
      {
        "intent": {"primary": "SCAFFOLD", ...},
        "entities": {"modulos": [...], ...},
        "slots": {"completado": true, ...}
      }
  [preprocessor] OK  (...)  ← nodes/preprocessor.py:...
    ── output:
      {
        "normalized_text": "crea un modulo de pagos",
        ...
      }
  [lexer] OK  (...)  ← nodes/lexer.py:...
  [parser] OK  (...)  ← nodes/parser.py:...
    ── output:
      {
        "ast": {...},
        ...
      }
  ...
```

---

## Ruta Critica

La secuencia que BLOQUEA el avance si falla:

```
Paso 1.1 (EnrichedInput)
  ↓
Paso 1.2 (IntentClassifier) ─┐
Paso 1.3 (NERExtractor) ─────┤
  ↓                           ↓
Paso 1.4 (SlotFiller) ←──────┘
  ↓
Paso 1.5 (AmbiguityDetector)
  ↓
Paso 2.1 (IntentStage) ──── dependencias NLP-06
  ↓
Paso 2.3 (Parser refactor) ── puede hacerse en paralelo con 2.2
  ↓
Paso 2.7 (Orchestrator) ──── integra todo
  ↓
Paso 3.1 (Integration tests)
```

**Parser refactor (2.3)** y **Preprocessor simplify (2.2)** se pueden
hacer en paralelo con **Contracts (2.4)** y **ErrorGuard (2.6)**.

---

## Estrategia de Rollback

Si algo falla en Fase 2 o 3, el plan de rollback depende del paso:

| Paso | Rollback |
|------|----------|
| 2.1 IntentStage | No insertar en `NODE_MAP`; pipeline sigue con requirement_decomposer |
| 2.2 Preprocessor | Restaurar `build_filter_chain()` original desde git |
| 2.3 Parser | Revertir `receive_mission()` a reconstruir texto; git checkout |
| 2.4 Contracts | No importar contracts en base_stage; borrar contracts.py |
| 2.5 base_stage | Comentar bloque de validacion de contrato |
| 2.6 ErrorGuard | No usar conditional edges; volver a edges secuenciales simples |
| 2.7 Orchestrator | `git checkout compiler-bot/agentic_pipeline/orchestrator.py` |

En general: cada cambio en Fase 2 afecta archivos existentes. Hacer
commits parciales por cada paso permite revertir individualmente.

---

## Criterios de Aceptacion Finales

- [ ] NLP clasifica SCAFFOLD, QUERY, MODIFY, DELETE con >= 80% precision
- [ ] NER extrae modulos, techs y requisitos del texto
- [ ] SlotFiller detecta slots faltantes correctamente
- [ ] AmbiguityDetector detecta intencion baja y referencias pronominales
- [ ] Parser construye AST desde tokens (no desde texto reconstruido)
- [ ] Pipeline con `--prompt "crea un modulo de pagos"` produce AST valido
- [ ] Sin `Parse error: No terminal matches` en prompts reales
- [ ] Contracts validan output de cada etapa (Pydantic)
- [ ] Pipeline se detiene si una etapa reporta `success=False`
- [ ] `ruff check .` = 0 errores
- [ ] pytest: 100% tests pasando
- [ ] `--debug trace --show-output` muestra el flujo NLP completo
- [ ] `--dialog` disponible en CLI para modo interactivo
