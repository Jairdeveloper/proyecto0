---
id: 068
area: dev
type: plan
module: compiler_bot
version: 1.0.0
status: DRAFT
tags:
  - execution
  - sprints
  - timeline
  - implementation
  - orchestration
summary: Plan de ejecucion granular por sprints para el escalamiento del pipeline RECPL v2.0
keywords: [execution-plan, sprints, milestones, tasks, verification]
changelog:
  - 2026-06-13: Documento creado
---

# Plan de Ejecucion — RECPL Compiler Bot v2.0

## Resumen

Plan de ejecucion granular derivado del documento
`067_PLAN_DEV_COMPILER_BOT_SCALE_IMPL_1_0_DRAFT.md`. Organizado en 13
sprints de 4 semanas cada uno (~52 semanas total). Cada sprint
especifica: objetivo, tareas con instrucciones de ejecucion,
dependencias, comandos, criterios de verificacion, y definicion de
done.

---

## Convenciones del Plan

### Estructura de cada Sprint

```
SPRINT N (Semanas X-Y)

Goal: <que se logra al final>

Tasks from 067: <lista de IDs de tareas>

Files to create:
  - <ruta>

Key decisions: <patrones, librerias, APIs>

Execution steps:
  1. <paso con comando si aplica>
  2. ...

Verification:
  - <checklist>

Definition of done:
  - [ ] <item>
```

### Entorno de Desarrollo

```
Python: 3.12+
Package manager: pip / poetry
Core deps: langchain==0.3.x, langgraph==0.2.x, pydantic==2.x, httpx
Test runner: pytest==8.x + pytest-asyncio, pytest-cov
Linter: ruff
Formatter: black
Repo: compiler-bot/agentic_pipeline/
```

### Convencion de Commits

```
<|----- 50 chars -----|------------ 72 chars ------------>
exec(<sprint>): <componente> — <accion concreta>

- <detalle 1>
- <detalle 2>
```

---

## SPRINT 1 — Fundacion del Proyecto (Semanas 1-4)

**Goal:** Proyecto Python configurado, clase base PipelineStage con
loop de 5 pasos, esqueleto del StateGraph compilando.

**Tasks from 067:** 0.1.1, 0.1.2, 0.1.3, 0.1.4, 0.1.5, 0.1.6,
0.2.1, 0.2.2, 0.2.3, 0.2.4

### Semana 1-2: Estructura del Proyecto

**Files to create:**
```
compiler-bot/agentic_pipeline/
  __init__.py
  pyproject.toml
  config.py
  state_models.py
  orchestrator.py
  base_stage.py
  feedback_loop.py
nodes/
  __init__.py
tools/
  __init__.py
tests/
  __init__.py
  conftest.py
  test_config.py
  test_state_models.py
  test_base_stage.py
  test_orchestrator_empty.py
```

**Key decisions:**
- Usar `pydantic.BaseModel` para todos los state models
- `PipelineStage` como ABC con Template Method en `execute()`
- `StateGraph` de LangGraph como orquestador central
- Config via `pydantic-settings` (`.env` support)

**Execution steps:**

1. Crear `pyproject.toml`:
```toml
[project]
name = "agentic-pipeline"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "langchain>=0.3.0",
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0",
    "ruff>=0.5.0",
    "black>=24.0",
]
```

2. Instalar dependencias:
```bash
cd compiler-bot/agentic_pipeline
pip install -e ".[dev]"
```

3. Crear `config.py`:
```python
from pydantic_settings import BaseSettings

class PipelineConfig(BaseSettings):
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    log_level: str = "info"
    memory_dir: str = "/tmp/agentic_memory"
    max_retries: int = 3
    cache_enabled: bool = True

    class Config:
        env_prefix = "AGENTIC_"
        env_file = ".env"

config = PipelineConfig()
```

4. Crear `state_models.py` con todos los tipos compartidos:
```python
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional
from datetime import datetime

class Stage(Enum):
    REQUIREMENT_DECOMPOSER = "requirement_decomposer"
    PREPROCESSOR = "preprocessor"
    LEXER = "lexer"
    PARSER = "parser"
    SEMANTIC_ANALYZER = "semantic_analyzer"
    IR_GENERATOR = "ir_generator"
    PLANNER = "planner"
    SYNTHESIS = "synthesis"
    UI_GENERATOR = "ui_generator"
    VALIDATOR = "validator"

class StageContext(BaseModel):
    mission_id: str = Field(default_factory=lambda: datetime.now().isoformat())
    stage: Stage
    input_data: Any
    previous_output: Optional[Any] = None
    config_overrides: dict = {}

class AnalysisResult(BaseModel):
    observations: list[str]
    detected_patterns: list[str]
    risks: list[str]
    complexity_score: float = 0.0

class ActionPlan(BaseModel):
    steps: list[dict]
    strategy: str  # "deterministic" | "llm_assisted"
    fallback_strategy: str = "deterministic"
    estimated_cost: float = 0.0

class StageOutput(BaseModel):
    stage: Stage
    output_data: Any
    metrics: dict = {}
    feedback: dict = {}
    success: bool = True
    error: Optional[str] = None

class Token(BaseModel):
    value: str
    type: str
    category: str  # "domain" | "action" | "tech" | "ui" | "quality"
    position: int
    confidence: float = 1.0
    context: dict = {}

class DesignTokens(BaseModel):
    primary_color: str = "#6366F1"
    secondary_color: str = "#10B981"
    font_family: str = "'Inter', sans-serif"
    border_radius: str = "8px"
    spacing_unit: str = "4px"
```

5. Crear `base_stage.py`:
```python
from abc import ABC, abstractmethod
from .state_models import StageContext, AnalysisResult, ActionPlan, StageOutput

class PipelineStage(ABC):
    name: str

    def __init__(self, context: StageContext):
        self.context = context

    @abstractmethod
    def receive_mission(self, input_data: object) -> None: ...

    @abstractmethod
    def analyze(self) -> AnalysisResult: ...

    @abstractmethod
    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan: ...

    @abstractmethod
    def act(self, plan: ActionPlan) -> StageOutput: ...

    @abstractmethod
    def learn_and_improve(self, feedback: object) -> None: ...

    def execute(self, input_data: object) -> StageOutput:
        self.receive_mission(input_data)
        analysis = self.analyze()
        plan = self.reflect_and_plan(analysis)
        output = self.act(plan)
        self.learn_and_improve(output.feedback)
        return output
```

6. Crear `orchestrator.py` con StateGraph placeholder:
```python
from langgraph.graph import StateGraph
from .state_models import StageContext

class PipelineOrchestrator:
    def __init__(self):
        self.graph = StateGraph(StageContext)
        self._build()

    def _build(self):
        self.graph.set_entry_point("input")
        self.graph.add_node("input", lambda x: x)
        self.graph.add_node("output", lambda x: x)
        self.graph.add_edge("input", "output")
        self.graph.set_finish_point("output")
        self.compiled = self.graph.compile()

    async def run(self, user_input: str) -> dict:
        return await self.compiled.ainvoke(StageContext(input_data=user_input))
```

7. Crear `feedback_loop.py`:
```python
import json
import logging
from datetime import datetime
from pathlib import Path
from .config import config

logger = logging.getLogger(__name__)

class FeedbackLoop:
    def __init__(self):
        self.log_path = Path(config.memory_dir) / "feedback"
        self.log_path.mkdir(parents=True, exist_ok=True)

    def record(self, stage: str, metrics: dict) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "metrics": metrics,
        }
        log_file = self.log_path / f"{stage}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        logger.debug(f"Feedback recorded for {stage}: {metrics}")

    def get_recent(self, stage: str, limit: int = 10) -> list[dict]:
        log_file = self.log_path / f"{stage}.jsonl"
        if not log_file.exists():
            return []
        with open(log_file) as f:
            lines = f.readlines()[-limit:]
        return [json.loads(l) for l in lines]
```

### Semana 3-4: Tests y Verificacion

**Commands to run:**
```bash
cd compiler-bot/agentic_pipeline
python -c "from agentic_pipeline.config import config; print(config)"
python -c "from agentic_pipeline.base_stage import PipelineStage; print(PipelineStage)"
python -c "from agentic_pipeline.orchestrator import PipelineOrchestrator; print('OK')"
```

**Tests:**
```python
# tests/test_base_stage.py
import pytest
from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.state_models import StageContext, Stage

class MockStage(PipelineStage):
    name = "mock"
    def receive_mission(self, input_data): self.mission = input_data
    def analyze(self): return {"ok": True}
    def reflect_and_plan(self, analysis): return {"steps": []}
    def act(self, plan): return {"done": True}
    def learn_and_improve(self, feedback): pass

def test_mock_stage_executes():
    ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="test")
    stage = MockStage(ctx)
    result = stage.execute("hello")
    assert result is not None
```

```bash
pytest tests/ -v --cov=agentic_pipeline
```

**Definition of done:**
- [ ] `pip install -e ".[dev]"` funciona
- [ ] `pytest tests/` pasa con 3+ tests
- [ ] StateGraph se compila sin errores
- [ ] Config carga variables de `.env`
- [ ] FeedbackLoop escribe y lee JSONL

---

## SPRINT 2 — RequirementDecomposer (Semanas 5-8)

**Goal:** Componente RequirementDecomposer funcional con LLMOrchestrator,
DomainClassifier, EntityExtractor, FeatureIdentifier.

**Tasks from 067:** 1.1.1, 1.1.2, 1.1.3, 1.1.4, 1.1.5, 1.1.6

### Semana 5: LLMOrchestrator + RequirementGraph

**Files to create:**
```
agentic_pipeline/
  tools/
    llm_tools.py
  nodes/
    requirement_decomposer.py
tests/
  test_llm_orchestrator.py
  test_requirement_decomposer.py
```

**Key decisions:**
- `LLMOrchestrator` usa `langchain.chat_models` con parser JSON
- `RequirementGraph` es un Pydantic model con validacion
- Los prompts se almacenan en `prompts/` como templates `.jinja2`

**Execution steps:**

1. Crear `tools/llm_tools.py`:
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from ..config import config
from ..state_models import Token, DesignTokens

class LLMOrchestrator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.llm_model,
            temperature=config.llm_temperature,
        )

    def classify_domain(self, text: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Clasifica el dominio del siguiente requerimiento. "
                       "Responde solo con una palabra: web, mobile, api, cli, data, infra."),
            ("human", "{text}"),
        ])
        chain = prompt | self.llm
        return chain.invoke({"text": text}).content.strip().lower()

    def extract_entities(self, text: str) -> list[dict]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Extrae las entidades del requerimiento. "
                       "Responde como JSON array: [{\"name\": str, \"type\": str, \"attributes\": [str]}]"),
            ("human", "{text}"),
        ])
        chain = prompt | self.llm | PydanticOutputParser(pydantic_object=...)  # noqa
        return chain.invoke({"text": text})
```

2. Crear `state_models.py` — add RequirementGraph:
```python
class RequirementGraph(BaseModel):
    domain: str
    entities: list[dict] = []
    features: list[str] = []
    constraints: list[str] = []
    user_stories: list[str] = []
    raw_text: str = ""
```

3. Crear `nodes/requirement_decomposer.py`:
```python
from ..base_stage import PipelineStage
from ..state_models import StageContext, AnalysisResult, ActionPlan, StageOutput, RequirementGraph
from ..tools.llm_tools import LLMOrchestrator
from ..feedback_loop import FeedbackLoop

class RequirementDecomposer(PipelineStage):
    name = "requirement_decomposer"

    def __init__(self, context: StageContext):
        super().__init__(context)
        self.llm = LLMOrchestrator()
        self.feedback = FeedbackLoop()
        self._raw_text = ""

    def receive_mission(self, input_data: object) -> None:
        self._raw_text = str(input_data)

    def analyze(self) -> AnalysisResult:
        domain = self.llm.classify_domain(self._raw_text)
        return AnalysisResult(
            observations=[f"Domain detected: {domain}"],
            detected_patterns=[domain],
            risks=[],
            complexity_score=0.3,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(
            steps=[{"action": "extract_entities"}, {"action": "identify_features"},
                   {"action": "detect_constraints"}, {"action": "generate_stories"}],
            strategy="llm_assisted",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        entities = self.llm.extract_entities(self._raw_text)
        graph = RequirementGraph(
            domain=self.llm.classify_domain(self._raw_text),
            entities=entities,
            raw_text=self._raw_text,
        )
        return StageOutput(
            stage=self.context.stage,
            output_data=graph.model_dump(),
            metrics={"entities": len(entities)},
        )

    def learn_and_improve(self, feedback: object) -> None:
        self.feedback.record(self.name, {"input_len": len(self._raw_text)})
```

### Semana 6-8: Subclasificadores y Tests

**Execution steps:**

4. Implementar DomainClassifier con subclases Strategy

5. Implementar EntityExtractor con patrones regex + LLM fallback

6. Implementar FeatureIdentifier con lista blanca de features SaaS

7. Implementar ConstraintDetector con keywords por constraint

**Commands to run:**
```bash
cd compiler-bot/agentic_pipeline
python -c "
from agentic_pipeline.nodes.requirement_decomposer import RequirementDecomposer
from agentic_pipeline.state_models import StageContext, Stage
ctx = StageContext(stage=Stage.REQUIREMENT_DECOMPOSER, input_data='')
rd = RequirementDecomposer(ctx)
result = rd.execute('Diseña una pagina web para acortar enlaces con auth y QR')
print(result.output_data)
"
```

**Verification (prompt del acortador):**
- Dominio: `web`
- Entidades: `[{"name": "User", ...}, {"name": "Link", ...}, {"name": "Click", ...}]`
- Features: contiene `auth`, `link_shortening`, `qr_generation`, `analytics`, `dashboard`

**Definition of done:**
- [ ] LLMOrchestrator clasifica dominio correctamente
- [ ] RequirementDecomposer produce RequirementGraph valido
- [ ] RequirementGraph contiene al menos 3 entidades del prompt objetivo
- [ ] Tests: `test_llm_orchestrator.py`, `test_requirement_decomposer.py`

---

## SPRINT 3 — Preprocessor (Semanas 9-12)

**Goal:** Preprocessor con Chain of Responsibility de filtros y
Strategy por dominio.

**Tasks from 067:** 1.2.1, 1.2.2, 1.2.3, 1.2.4, 1.2.5, 1.2.6,
1.2.7, 1.2.8, 1.2.9, 1.2.10

### Semana 9-10: Filtros Base

**Files to create:**
```
agentic_pipeline/nodes/preprocessor.py
tests/test_preprocessor_filters.py
```

**Key decisions:**
- `PreprocessingFilter` como clase base abstracta con metodo `process(text) -> text`
- Cadena armada en `Preprocessor.__init__()` via Strategy segun dominio
- EmbeddingEnricher usa `langchain.embeddings` con FAISS vectorstore local

**Execution steps:**

1. Crear `nodes/preprocessor.py`:
```python
from abc import ABC, abstractmethod
import re
from ..base_stage import PipelineStage
from ..state_models import StageContext, AnalysisResult, ActionPlan, StageOutput

class PreprocessingFilter(ABC):
    @abstractmethod
    def process(self, text: str, context: dict = None) -> str: ...

class NormalizationFilter(PreprocessingFilter):
    def process(self, text: str, context: dict = None) -> str:
        text = text.strip().lower()
        text = re.sub(r'[^\w\sáéíóúñü,.!?;:-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text

class DomainEnrichmentFilter(PreprocessingFilter):
    DOMAIN_CONTEXT = {
        "web": {"stack": ["frontend", "backend", "database"]},
        "mobile": {"stack": ["mobile_app", "api_backend"]},
    }

    def process(self, text: str, context: dict = None) -> str:
        domain = (context or {}).get("domain", "web")
        enrichments = self.DOMAIN_CONTEXT.get(domain, {})
        return text + f" [domain:{domain}]"

class ImplicitRequirementFilter(PreprocessingFilter):
    IMPLICIT = {
        "auth": ["User model", "JWT", "login/signup", "session"],
        "qr": ["qrcode library"],
        "pagos": ["Payment model", "transaction log"],
    }

    def process(self, text: str, context: dict = None) -> str:
        additions = []
        for keyword, reqs in self.IMPLICIT.items():
            if keyword in text:
                additions.extend(reqs)
        if additions:
            text += " [implicit: " + ", ".join(additions) + "]"
        return text

class SegmentationFilter(PreprocessingFilter):
    def process(self, text: str, context: dict = None) -> str:
        sentences = re.split(r'[.!?]+', text)
        segments = [s.strip() for s in sentences if s.strip()]
        return " [SEG] ".join(segments)

class Preprocessor(PipelineStage):
    name = "preprocessor"

    def __init__(self, context: StageContext):
        super().__init__(context)
        domain = (context.input_data or {}).get("domain", "web")
        self.filters = self._build_chain(domain)
        self._input_text = ""

    def _build_chain(self, domain: str) -> list[PreprocessingFilter]:
        # Strategy: different chains per domain
        base = [NormalizationFilter(), ImplicitRequirementFilter(), SegmentationFilter()]
        if domain in ("web", "mobile"):
            base.insert(1, DomainEnrichmentFilter())
        return base

    def receive_mission(self, input_data: object) -> None:
        self._input_text = str(input_data)

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Input length: {len(self._input_text)}"],
            detected_patterns=[], risks=[], complexity_score=0.1,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        result = self._input_text
        for f in self.filters:
            result = f.process(result, {"domain": "web"})
        return StageOutput(
            stage=self.context.stage,
            output_data={"normalized_text": result, "filters_applied": len(self.filters)},
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
```

### Semana 11-12: EmbeddingEnricher + Integracion LangGraph

**Execution steps:**

2. Implementar EmbeddingEnricher con FAISS:
```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

class EmbeddingEnricher(PreprocessingFilter):
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = FAISS.from_texts(
            ["pagina web responsive con tailwind", "api rest con nestjs",
             "autenticacion jwt", "base de datos postgresql"],
            self.embeddings,
        )

    def process(self, text: str, context: dict = None) -> str:
        docs = self.vectorstore.similarity_search(text, k=2)
        similar = [d.page_content for d in docs]
        return text + f" [similar: {'; '.join(similar)}]"
```

3. Loop de 5 pasos completo (recibir, analizar, planificar, actuar, aprender)

4. Conectar Preprocessor como nodo en `orchestrator.py`:
```python
# orchestrator.py — add_node
from .nodes.preprocessor import Preprocessor

class PipelineOrchestrator:
    def _build(self):
        ...  # previous code
        self.graph.add_node("preprocessor", lambda ctx: Preprocessor(ctx).execute(ctx.input_data))
        self.graph.add_edge("requirement_decomposer", "preprocessor")
```

**Definition of done:**
- [ ] NormalizationFilter: trim, lowercase, colapso ok
- [ ] ImplicitRequirementFilter: "auth" → agrega User+JWT+session
- [ ] SegmentationFilter: divide por oraciones
- [ ] Preprocessor con Strategy segun dominio
- [ ] Integrado como nodo LangGraph

---

## SPRINT 4 — Lexer (Semanas 13-16)

**Goal:** Lexer con 120+ tokens, 5 sub-DFAs, MultiWordTrie.

**Tasks from 067:** 1.3.1, 1.3.2, 1.3.3, 1.3.4, 1.3.5, 1.3.6,
1.3.7, 1.3.8, 1.3.9, 1.3.10, 1.3.11

### Semana 13-14: Sub-DFAs por Categoria

**Files to create:**
```
agentic_pipeline/nodes/lexer.py
agentic_pipeline/nodes/sub_dfa.py
tests/test_lexer_sub_dfas.py
```

**Key decisions:**
- DFA implementado como dict de transiciones `{state: {char: next_state}}`
- Cada sub-DFA en su propria clase que hereda de `BaseDFA`
- Flyweight via `TokenRegistry` con cache LRU
- MultiWordTrie como `pygtrie` o implementacion custom

**Execution steps:**

1. Crear `nodes/sub_dfa.py`:
```python
from abc import ABC, abstractmethod
from ..state_models import Token

class BaseDFA(ABC):
    def __init__(self):
        self.transitions: dict[int, dict[str, int]] = {}
        self.accepting_states: dict[int, str] = {}
        self._build()

    @abstractmethod
    def _build(self): ...

    def tokenize(self, text: str, start_pos: int = 0) -> list[Token]:
        tokens = []
        pos = start_pos
        while pos < len(text):
            state = 0
            token_start = pos
            last_accept = None
            while pos < len(text) and state in self.transitions:
                ch = text[pos]
                if ch in self.transitions[state]:
                    state = self.transitions[state][ch]
                    pos += 1
                    if state in self.accepting_states:
                        last_accept = (pos, self.accepting_states[state])
                else:
                    break
            if last_accept:
                end, token_type = last_accept
                tokens.append(Token(
                    value=text[token_start:end],
                    type=token_type,
                    category=self.category,
                    position=token_start,
                ))
                pos = end
            else:
                pos += 1
        return tokens

class DomainDFA(BaseDFA):
    category = "domain"
    def _build(self):
        self.transitions = {
            0: {"w": 1, "a": 2, "s": 3},
            1: {"e": 4},  4: {"b": 5},  5: {"_": 6},  6: {"a": 7},  7: {"p": 8},  8: {"p": 9},
            9: self._accept("WEB_APP"),
            2: {"p": 10}, 10: {"i": 11}, 11: self._accept("API"),
            3: {"a": 12}, 12: {"a": 13}, 13: {"s": 14}, 14: self._accept("SAAS"),
        }
    def _accept(self, token_type):
        self.accepting_states[max(self.transitions) + 1] = token_type
        return max(self.transitions)
```

2. Crear `nodes/lexer.py`:
```python
from ..base_stage import PipelineStage
from ..state_models import StageContext, AnalysisResult, ActionPlan, StageOutput, Token
from .sub_dfa import DomainDFA, ActionDFA, TechDFA, UIDFA, QualityDFA

class TokenFlyweightRegistry:
    _cache: dict[tuple, Token] = {}

    @classmethod
    def get(cls, value: str, type: str, category: str, pos: int) -> Token:
        key = (value, type, category)
        if key not in cls._cache:
            cls._cache[key] = Token(value=value, type=type, category=category, position=pos)
        return cls._cache[key].model_copy(update={"position": pos})

class MultiWordTrie:
    def __init__(self):
        self.root = {}
    def insert(self, phrase: str, token_type: str):
        node = self.root
        for char in phrase.lower().split():
            node = node.setdefault(char, {})
        node["__type__"] = token_type
    def lookup(self, words: list[str], start: int) -> tuple:
        node = self.root
        i = start
        last_match = None
        while i < len(words) and words[i] in node:
            node = node[words[i]]
            i += 1
            if "__type__" in node:
                last_match = (i, node["__type__"])
        return last_match

class Lexer(PipelineStage):
    name = "lexer"

    def __init__(self, context: StageContext):
        super().__init__(context)
        self.dfas = {
            "domain": DomainDFA(),
            "action": ActionDFA(),
            "tech": TechDFA(),
            "ui": UIDFA(),
            "quality": QualityDFA(),
        }
        self.trie = MultiWordTrie()
        self._init_trie()
        self._text = ""

    def _init_trie(self):
        phrases = [
            ("panel de control", "DASHBOARD"),
            ("codigo qr", "QR_CODE"),
            ("acortamiento de enlaces", "URL_SHORTENER"),
        ]
        for phrase, ttype in phrases:
            self.trie.insert(phrase, ttype)

    def receive_mission(self, input_data: object) -> None:
        self._text = str(input_data)

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Text length: {len(self._text)}"],
            detected_patterns=[], risks=[], complexity_score=0.2,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        # Activate sub-DFAs based on domain context
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        all_tokens = []
        for dfa in self.dfas.values():
            all_tokens.extend(dfa.tokenize(self._text))
        all_tokens.sort(key=lambda t: t.position)
        return StageOutput(
            stage=self.context.stage,
            output_data={"tokens": [t.model_dump() for t in all_tokens]},
            metrics={"tokens_count": len(all_tokens)},
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
```

3. Tests de lexer:
```python
def test_domain_dfa():
    dfa = DomainDFA()
    tokens = dfa.tokenize("web_app api saas")
    assert any(t.type == "WEB_APP" for t in tokens)

def test_multitoken():
    trie = MultiWordTrie()
    trie.insert("panel de control", "DASHBOARD")
    result = trie.lookup(["panel", "de", "control", "con", "tabla"], 0)
    assert result == (3, "DASHBOARD")
```

**Definition of done:**
- [ ] 5 sub-DFAs implementados con ~20+ tokens cada uno
- [ ] MultiWordTrie resuelve "panel de control" → DASHBOARD
- [ ] TokenFlyweightRegistry cachea tokens correctamente
- [ ] "crea modulo pagos en nestjs con auth" → 7+ tokens
- [ ] Loop de 5 pasos implementado
- [ ] Integrado como nodo en StateGraph

---

## SPRINT 5 — Parser GLR (Semanas 17-20)

**Goal:** Parser GLR con Lark, 4 gramaticas, AST Composite, error recovery.

**Tasks from 067:** 2.1.1, 2.1.2, 2.1.3, 2.1.4, 2.1.5, 2.1.6,
2.1.7, 2.1.8, 2.1.9

### Semana 17-18: AST Nodes + Gramaticas Lark

**Files to create:**
```
agentic_pipeline/nodes/parser.py
agentic_pipeline/nodes/ast_nodes.py
agentic_pipeline/grammars/
  __init__.py
  project_grammar.lark
  ui_grammar.lark
  data_grammar.lark
  infra_grammar.lark
tests/test_parser_project.py
tests/test_parser_ui.py
```

**Key decisions:**
- Lark como parser GLR (`lark.Lark(grammar, parser="lalr")` o `earley`)
- AST nodes con patrón Composite (todos heredan de `ASTNode`)
- Gramatica Lark con reglas para cada dominio

**Execution steps:**

1. Instalar Lark: `pip install lark`

2. Crear `grammars/project_grammar.lark`:
```lark
start: project_section+

project_section: "pagina"i CNAME "con"i? component_list
                | "modulo"i CNAME
                | "api"i CNAME

component_list: component ("y"i component)*
component: "formulario"i ("de"i)? CNAME?
         | "tabla"i ("de"i)? CNAME?
         | "grafico"i ("de"i)? CNAME?
         | "navbar"
         | "sidebar"
         | "modal" ("de"i)? CNAME?

%import common.CNAME
%import common.WS
%ignore WS
```

3. Crear `nodes/ast_nodes.py`:
```python
from abc import ABC, abstractmethod
from typing import Any

class ASTNode(ABC):
    def __init__(self, name: str = ""):
        self.name = name
        self.children: list[ASTNode] = []
        self.parent: ASTNode = None

    def add(self, child: "ASTNode"):
        self.children.append(child)
        child.parent = self

    @abstractmethod
    def evaluate(self) -> dict: ...
    @abstractmethod
    def validate(self) -> list[str]: ...
    @abstractmethod
    def to_ir(self) -> dict: ...

class ProjectNode(ASTNode):
    def evaluate(self) -> dict:
        return {"type": "project", "pages": [c.evaluate() for c in self.children]}
    def validate(self) -> list[str]:
        errors = []
        for c in self.children:
            errors.extend(c.validate())
        return errors
    def to_ir(self) -> dict:
        return {"node_type": "project", "children": [c.to_ir() for c in self.children]}

class PageNode(ASTNode):
    def evaluate(self) -> dict:
        return {"type": "page", "name": self.name, "components": [c.evaluate() for c in self.children]}
    def validate(self) -> list[str]:
        return [f"Page {self.name} has no components" if not self.children else ""]
    def to_ir(self) -> dict:
        return {"node_type": "page", "name": self.name, "children": [c.to_ir() for c in self.children]}

class ComponentNode(ASTNode):
    def __init__(self, name: str, component_type: str):
        super().__init__(name)
        self.component_type = component_type
    def evaluate(self) -> dict:
        return {"type": "component", "name": self.name, "component_type": self.component_type}
    def validate(self) -> list[str]:
        return []
    def to_ir(self) -> dict:
        return {"node_type": "component", "name": self.name, "component_type": self.component_type}
```

4. Crear `nodes/parser.py`:
```python
from pathlib import Path
from lark import Lark, Tree
from ..base_stage import PipelineStage
from ..state_models import StageContext, AnalysisResult, ActionPlan, StageOutput
from .ast_nodes import ProjectNode, PageNode, ComponentNode

class ParserGLR(PipelineStage):
    name = "parser"

    def __init__(self, context: StageContext):
        super().__init__(context)
        grammar_dir = Path(__file__).parent.parent / "grammars"
        self.parser = Lark(
            (grammar_dir / "project_grammar.lark").read_text(),
            parser="earley",  # GLR = earley mode
            maybe_placeholders=True,
        )
        self._tokens = []

    def _build_ast(self, tree: Tree) -> ASTNode:
        if tree.data == "project_section":
            if tree.children[0].data == "pagina":
                page = PageNode(str(tree.children[0].children[0]))
                # traverse component children
                return page
        return ASTNode()

    def receive_mission(self, input_data: object) -> None:
        self._tokens = input_data.get("tokens", []) if isinstance(input_data, dict) else []

    def analyze(self) -> AnalysisResult:
        text = " ".join(t.get("value", "") for t in self._tokens)
        return AnalysisResult(observations=[], detected_patterns=[], risks=[], complexity_score=0.3)

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        text = " ".join(t.get("value", "") for t in self._tokens)
        tree = self.parser.parse(text)
        ast = self._build_ast(tree)
        return StageOutput(
            stage=self.context.stage,
            output_data={"ast": ast.to_ir(), "errors": ast.validate()},
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
```

### Semana 19-20: Gramaticas UI, Data, Infra + Error Recovery

5. Crear `grammars/data_grammar.lark`:
```lark
start: entity_def+

entity_def: "entidad"i CNAME ("con"i attribute_list)?
attribute_list: attribute ("y"i attribute)*
attribute: CNAME ":" ("string"i | "int"i | "boolean"i | "date"i | "relation"i)
```

**Definition of done:**
- [ ] Lark parsea gramatica de proyecto correctamente
- [ ] AST nodes con patrón Composite funcionales
- [ ] "pagina de login con formulario" → AST: Project > Page(login) > Component(form)
- [ ] 4 gramaticas Lark creadas
- [ ] Error recovery con LLM (panic mode + sugerencia)

---

## SPRINT 6 — Semantic Analyzer (Semanas 21-24)

**Goal:** Semantic Analyzer con type checking multi-dominio, SymbolTable,
Visitor, Memento.

**Tasks from 067:** 2.2.1, 2.2.2, 2.2.3, 2.2.4, 2.2.5, 2.2.6,
2.2.7, 2.2.8, 2.2.9, 2.2.10, 2.2.11

**Files to create:**
```
agentic_pipeline/nodes/semantic_analyzer.py
agentic_pipeline/nodes/symbol_table.py
agentic_pipeline/nodes/type_systems.py
tests/test_semantic_visitor.py
tests/test_type_systems.py
tests/test_scope_analyzer.py
```

**Key decisions:**
- SymbolTable: dict-based con `enter_scope()` / `exit_scope()` (stack)
- TypeRegistry: registra tipos por dominio con validacion
- SemanticVisitor: recorre AST con pattern Visitor
- Memento: snapshots serializados a JSON

**Execution steps:**

1. Crear `nodes/symbol_table.py`:
```python
import json
from copy import deepcopy

class SymbolTable:
    def __init__(self):
        self._scopes = [{}]
        self._snapshots = []

    def enter_scope(self):
        self._scopes.append({})

    def exit_scope(self):
        return self._scopes.pop()

    def define(self, name: str, symbol: dict):
        self._scopes[-1][name] = symbol

    def lookup(self, name: str) -> dict:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def memento_save(self):
        self._snapshots.append(deepcopy(self._scopes))

    def memento_restore(self):
        if self._snapshots:
            self._scopes = self._snapshots.pop()
```

2. Crear `nodes/type_systems.py`:
```python
class TypeRegistry:
    def __init__(self):
        self._types = {}

    def register(self, domain: str, type_name: str, validator: callable):
        self._types.setdefault(domain, {})[type_name] = validator

    def validate(self, domain: str, type_name: str, value: dict) -> list[str]:
        validator = self._types.get(domain, {}).get(type_name)
        if validator:
            return validator(value)
        return [f"Unknown type {type_name} in domain {domain}"]

def ui_component_validator(value: dict) -> list[str]:
    errors = []
    required_props = {"name", "type", "children"}
    missing = required_props - set(value.keys())
    if missing:
        errors.append(f"Missing required props: {missing}")
    return errors
```

**Definition of done:**
- [ ] SymbolTable con scopes anidados y Memento
- [ ] UITypeSystem, DataTypeSystem, InfraTypeSystem registrados
- [ ] CrossDomainTypeChecker: frontend-backend consistency
- [ ] SemanticVisitor recorre AST y recolecta tipos
- [ ] ScopeAnalyzer con herencia de scope global

---

## SPRINT 7 — IR Generator (Semanas 25-28)

**Goal:** IR basado en Composite con 5 capas, Builder, Bridge, grafo de
dependencias.

**Tasks from 067:** 2.3.1, 2.3.2, 2.3.3, 2.3.4, 2.3.5, 2.3.6,
2.3.7, 2.3.8, 2.3.9, 2.3.10, 2.3.11

**Files to create:**
```
agentic_pipeline/nodes/ir_generator.py
agentic_pipeline/nodes/ir_nodes.py
agentic_pipeline/nodes/ir_builder.py
agentic_pipeline/nodes/ir_serializer.py
tests/test_ir_nodes.py
tests/test_ir_builder.py
tests/test_ir_dependencies.py
```

**Key decisions:**
- IRNode abstracto con `to_code(target)`, `validate()`, `dependencies()`
- IRBuilder construye paso a paso con validacion
- Bridge pattern: IRSerializer separa representacion (JSON/YAML/DOT)
- DependencyGraph: topologic sort para planner

**Execution steps:**

1. Crear `nodes/ir_nodes.py`:
```python
from abc import ABC, abstractmethod
from typing import List

class IRNode(ABC):
    def __init__(self, name: str):
        self.name = name
        self.children: List[IRNode] = []

    def add(self, child: "IRNode"):
        self.children.append(child)

    @abstractmethod
    def to_code(self, target: str) -> str: ...
    @abstractmethod
    def validate(self) -> List[str]: ...
    @abstractmethod
    def dependencies(self) -> List[str]: ...

class IRProject(IRNode):
    def to_code(self, target: str) -> str:
        return "\n".join(c.to_code(target) for c in self.children)
    def validate(self) -> List[str]:
        errors = []
        for c in self.children:
            errors.extend(c.validate())
        return errors
    def dependencies(self) -> List[str]:
        return [c.name for c in self.children]

class IRPage(IRNode):
    def to_code(self, target: str) -> str:
        if target == "react":
            return f"export default function {self.name}() {{\n  return <div>{self.name}</div>\n}}"
        return f"<!-- {self.name} -->"
    def validate(self) -> List[str]:
        return [f"Page {self.name}: no components" if not self.children else ""]
    def dependencies(self) -> List[str]:
        return [c.name for c in self.children]

class IREntity(IRNode):
    def __init__(self, name: str, attributes: list = None):
        super().__init__(name)
        self.attributes = attributes or []
    def to_code(self, target: str) -> str:
        if target == "prisma":
            attrs = "\n  ".join(f"{a['name']} {a['type']}" for a in self.attributes)
            return f"model {self.name} {{\n  {attrs}\n}}"
        return f"// entity {self.name}"
    def validate(self) -> List[str]:
        return [f"Entity {self.name}: no attributes" if not self.attributes else ""]
    def dependencies(self) -> List[str]:
        return []
```

**Definition of done:**
- [ ] 5 capas IR implementadas (Config, Domain, UI, API, Infra)
- [ ] IRBuilder produce grafo valido
- [ ] `dependencies()` de IRPage("Login") → ["User entity", "Auth API"]
- [ ] Grafo aciclico validado
- [ ] IRSerializer produce JSON/YAML/DOT

---

## SPRINT 8 — Planner Hibrido (Semanas 29-32)

**Goal:** Planner hibrido (heuristico + LLM) con grafo de tareas,
Command pattern, PlanExecutor, rollback.

**Tasks from 067:** 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5, 3.1.6,
3.1.7, 3.1.8, 3.1.9, 3.1.10, 3.1.11

**Files to create:**
```
agentic_pipeline/nodes/planner.py
agentic_pipeline/nodes/plan_executor.py
agentic_pipeline/nodes/task_command.py
tests/test_heuristic_planner.py
tests/test_llm_planner.py
tests/test_plan_executor.py
tests/test_rollback.py
```

**Key decisions:**
- TaskCommand: `execute()` produce archivos, `undo()` los elimina
- PlanExecutor: Template Method con `pre_execute`, `post_execute`, `on_error`
- TopologicalSorter: `graphlib.TopologicalSorter` de Python 3.9+
- HybridPlanner: si dependencias > 5 → LLM, si no → heuristico

**Execution steps:**

1. Crear `nodes/planner.py` Task model:
```python
from enum import Enum
from pydantic import BaseModel
from typing import List, Optional

class TaskState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"

class Task(BaseModel):
    id: str
    description: str
    dependencies: List[str] = []
    generator: str = ""
    target: str = ""
    state: TaskState = TaskState.PENDING
    output_path: str = ""
    validation_rules: List[str] = []
```

**Definition of done:**
- [ ] HeuristicPlanner: casos 1-3 tareas sin dependencias
- [ ] LLMPlanner: >3 tareas produce grafo valido
- [ ] PlanExecutor: ejecuta en orden topologico
- [ ] Rollback: undo en orden inverso (archivos eliminados)
- [ ] PlanObserver: logging de cambios de estado

---

## SPRINT 9 — Synthesis Multi-Target (Semanas 33-36)

**Goal:** 6 generadores AST-based (React, Next.js, Tailwind, Prisma,
NestJS, Docker) con Abstract Factory, CodeFormatter.

**Tasks from 067:** 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.5, 3.2.6,
3.2.7, 3.2.8, 3.2.9, 3.2.10, 3.2.11, 3.2.12, 3.3.1, 3.3.2, 3.3.3, 3.3.4

**Files to create:**
```
agentic_pipeline/nodes/synthesis.py
agentic_pipeline/generators/
  __init__.py
  base_generator.py
  react_generator.py
  nextjs_generator.py
  tailwind_generator.py
  prisma_generator.py
  nestjs_generator.py
  docker_generator.py
  code_formatter.py
tests/test_react_generator.py
tests/test_prisma_generator.py
tests/test_nestjs_generator.py
tests/test_docker_generator.py
tests/test_generator_factory.py
```

**Key decisions:**
- GeneratorFactory: Abstract Factory que devuelve familia segun target
- Cada generador produce AST del lenguaje target (no strings)
- CodeFormatter wrappea prettier/eslint/black
- Scaffold eliminado: templates/ → templates/archive/

**Execution steps:**

1. Crear `generators/base_generator.py`:
```python
from abc import ABC, abstractmethod
from pathlib import Path

class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, ir_node: object, output_dir: Path) -> list[Path]:
        """Generate files from IR node. Returns list of created paths."""
        ...

class GeneratorFactory:
    @staticmethod
    def get_generator(target: str) -> BaseGenerator:
        if target == "react":
            from .react_generator import ReactGenerator
            return ReactGenerator()
        if target == "prisma":
            from .prisma_generator import PrismaGenerator
            return PrismaGenerator()
        raise ValueError(f"Unknown target: {target}")
```

**Definition of done:**
- [ ] ReactGenerator produce componente JSX con Tailwind
- [ ] PrismaGenerator produce schema `prisma validate` OK
- [ ] NestJSGenerator produce controller con decoradores
- [ ] DockerGenerator produce `docker-compose up` funcional
- [ ] CodeFormatter pasa prettier/black
- [ ] GeneratorFactory crea familia correcta
- [ ] Scaffold deprecado con warning

---

## SPRINT 10 — Output Validator (Semanas 37-40)

**Goal:** Validador con Chain of Responsibility (syntax, typecheck,
integration, security, format).

**Tasks from 067:** 4.1.1, 4.1.2, 4.1.3, 4.1.4, 4.1.5, 4.1.6,
4.1.7, 4.1.8, 4.1.9

**Files to create:**
```
agentic_pipeline/nodes/validator.py
tests/test_syntax_validator.py
tests/test_type_checker.py
tests/test_security_scanner.py
tests/test_validator_chain.py
```

**Key decisions:**
- Cada validador es un eslabon de la cadena
- Resultados: PASS, WARNING, ERROR
- ERROR detiene la cadena y retroalimenta a synthesis para regenerar
- SecurityScanner: regex patterns + trufflehog wrapper

**Execution steps:**

1. Crear `nodes/validator.py`:
```python
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
import subprocess
from ..base_stage import PipelineStage

class ValidationLevel(str, Enum):
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"

class ValidationResult:
    def __init__(self, level: ValidationLevel, message: str = "", details: list = None):
        self.level = level
        self.message = message
        self.details = details or []

class Validator(ABC):
    def __init__(self):
        self.next_validator: Validator = None

    def set_next(self, validator: "Validator") -> "Validator":
        self.next_validator = validator
        return validator

    @abstractmethod
    def validate(self, output_dir: Path) -> ValidationResult: ...

    def check(self, output_dir: Path) -> ValidationResult:
        result = self.validate(output_dir)
        if result.level == ValidationLevel.ERROR:
            return result
        if self.next_validator:
            return self.next_validator.check(output_dir)
        return result

class SyntaxValidator(Validator):
    def validate(self, output_dir: Path) -> ValidationResult:
        result = subprocess.run(
            ["npx", "prettier", "--check", str(output_dir)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return ValidationResult(ValidationLevel.ERROR, "Syntax errors found",
                                    result.stdout.split("\n")[:5])
        return ValidationResult(ValidationLevel.PASS, "Syntax OK")

class TypeChecker(Validator):
    def validate(self, output_dir: Path) -> ValidationResult:
        tsconfig = output_dir / "tsconfig.json"
        if not tsconfig.exists():
            return ValidationResult(ValidationLevel.WARNING, "No tsconfig found")
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--project", str(tsconfig)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return ValidationResult(ValidationLevel.ERROR, "Type errors",
                                    result.stdout.split("\n")[:10])
        return ValidationResult(ValidationLevel.PASS, "Types OK")
```

**Definition of done:**
- [ ] SyntaxValidator detecta errores de prettier
- [ ] TypeChecker detecta errores de TypeScript
- [ ] SecurityScanner detecta secretos hardcodeados
- [ ] Cadena completa: ERROR detiene entrega
- [ ] Integrado como nodo LangGraph

---

## SPRINT 11 — UI Generator (Semanas 41-44)

**Goal:** UI Generator con Builder pattern, Design Tokens, responsive
engine, accessibility, animations.

**Tasks from 067:** 4.2.1, 4.2.2, 4.2.3, 4.2.4, 4.2.5, 4.2.6,
4.2.7, 4.2.8

**Files to create:**
```
agentic_pipeline/nodes/ui_generator.py
agentic_pipeline/generators/ui_component_builder.py
agentic_pipeline/generators/design_tokens.py
agentic_pipeline/generators/responsive_engine.py
tests/test_ui_builder.py
tests/test_responsive_engine.py
tests/test_accessibility_injector.py
```

**Key decisions:**
- UIComponentBuilder: 5 pasos (structure → styles → behavior → a11y → animation)
- DesignTokens: paleta SaaS moderna (indigo + emerald)
- ResponsiveEngine: mobile-first, breakpoints sm/md/lg/xl
- AccessibilityInjector: ARIA labels, roles, focus management
- AnimationInjector: CSS transitions + Framer Motion opcional

**Execution steps:**

1. Crear DesignTokens:
```python
class DesignTokens:
    COLORS = {
        "primary": "#6366F1",    # Indigo
        "secondary": "#10B981",  # Emerald
        "background": "#FFFFFF",
        "surface": "#F9FAFB",
        "text": "#111827",
        "text_secondary": "#6B7280",
        "border": "#E5E7EB",
        "error": "#EF4444",
    }
    FONTS = {"sans": "'Inter', sans-serif", "mono": "'JetBrains Mono', monospace"}
    BORDER_RADIUS = "8px"
    SPACING = {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "48px"}
    BREAKPOINTS = {"sm": "640px", "md": "768px", "lg": "1024px", "xl": "1280px"}
```

2. Crear UIComponentBuilder:
```python
class UIComponentBuilder:
    def __init__(self, component_type: str):
        self.component = {"type": component_type, "props": {}, "children": []}

    def build_structure(self, name: str, props: dict = None):
        self.component["name"] = name
        self.component["props"] = props or {}
        return self

    def apply_styles(self, styles: dict = None):
        self.component["styles"] = styles or {}
        return self

    def add_behavior(self, events: dict = None):
        self.component["events"] = events or {}
        return self

    def add_accessibility(self, aria: dict = None):
        self.component["aria"] = aria or {"label": self.component.get("name", "")}
        return self

    def add_animations(self, animations: dict = None):
        self.component["animations"] = animations or {"enter": "fadeIn", "duration": "0.3s"}
        return self

    def build(self) -> dict:
        return self.component
```

**Definition of done:**
- [ ] UIComponentBuilder produce estructura completa (5 pasos)
- [ ] DesignTokens aplicados consistentemente
- [ ] Componente Form: inputs + boton + validacion + ARIA + animacion
- [ ] Componente Table: responsive con sort
- [ ] Integrado con ReactGenerator en Synthesis

---

## SPRINT 12 — Feedback Loop + Refinamiento (Semanas 45-48)

**Goal:** Sistema de feedback global, persistencia de metricas, cache
de ASTs, ajuste de pesos.

**Tasks from 067:** 4.3.1, 4.3.2, 4.3.3, mas tareas de optimizacion
y refinamiento de componentes previos.

**Files to create:**
```
agentic_pipeline/feedback_loop.py  (ampliar)
agentic_pipeline/metrics_store.py
tests/test_feedback_loop.py
```

**Key decisions:**
- SQLite como store de metricas (via aiosqlite o sqlite3)
- Cache de ASTs: `joblib.Memory` o dict LRU
- Ajuste de pesos: registrar frecuencias de tokens y patrones

**Execution steps:**

1. Implementar MetricsStore con SQLite:
```python
import sqlite3
import json
from pathlib import Path

class MetricsStore:
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path("/tmp/agentic_metrics.db")
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stage_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stage TEXT,
                    timestamp TEXT,
                    metrics TEXT
                )
            """)

    def record(self, stage: str, metrics: dict):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO stage_metrics (stage, timestamp, metrics) VALUES (?, ?, ?)",
                (stage, __import__("datetime").datetime.now().isoformat(), json.dumps(metrics)),
            )
```

**Definition of done:**
- [ ] MetricsStore escribe y lee desde SQLite
- [ ] GlobalFeedbackLoop ajusta pesos del lexer
- [ ] Cache de ASTs reduce tiempo de generacion en 30%+
- [ ] Toda etapa registra metricas

---

## SPRINT 13 — Integracion Final + Beta (Semanas 49-52)

**Goal:** Pipeline completo funcional, CLI, streaming, beta con prompt
del acortador de enlaces.

**Tasks from 067:** 5.1.1, 5.1.2, 5.1.3, 5.1.4, 5.2.1, 5.2.2,
5.2.3, 5.2.4, 5.3.1, 5.3.2, 5.3.3

### Semana 49-50: Integracion StateGraph

**Execution steps:**

1. Conectar todos los nodos en `orchestrator.py`:
```python
class PipelineOrchestrator:
    def _build(self):
        self.graph = StateGraph(StageContext)
        self.graph.set_entry_point("requirement_decomposer")
        # Add all nodes
        for stage in Stage:
            self.graph.add_node(stage.value, self._make_node(stage))
        # Add sequential edges
        stages = list(Stage)
        for i in range(len(stages) - 1):
            self.graph.add_edge(stages[i].value, stages[i+1].value)
        self.graph.set_finish_point(Stage.VALIDATOR.value)
        self.compiled = self.graph.compile()

    def _make_node(self, stage: Stage):
        NODE_MAP = {
            Stage.REQUIREMENT_DECOMPOSER: RequirementDecomposer,
            Stage.PREPROCESSOR: Preprocessor,
            Stage.LEXER: Lexer,
            Stage.PARSER: ParserGLR,
            Stage.SEMANTIC_ANALYZER: SemanticAnalyzer,
            Stage.IR_GENERATOR: IRGenerator,
            Stage.PLANNER: HybridPlanner,
            Stage.SYNTHESIS: SynthesisOrchestrator,
            Stage.UI_GENERATOR: UIGenerator,
            Stage.VALIDATOR: OutputValidator,
        }
        cls = NODE_MAP[stage]
        return lambda ctx: cls(ctx).execute(ctx.input_data)
```

2. CLI entrypoint (`compiler-bot/agentic`):
```python
#!/usr/bin/env python3
import asyncio
import argparse
from agentic_pipeline.orchestrator import PipelineOrchestrator

async def main():
    parser = argparse.ArgumentParser(description="RECPL Compiler Bot v2.0")
    parser.add_argument("--prompt", "-p", type=str, help="User requirement prompt")
    parser.add_argument("--file", "-f", type=str, help="Read prompt from file")
    parser.add_argument("--output", "-o", type=str, default="./output", help="Output directory")
    parser.add_argument("--stream", action="store_true", help="Stream progress")
    args = parser.parse_args()

    if args.file:
        prompt = open(args.file).read()
    else:
        prompt = args.prompt

    orchestrator = PipelineOrchestrator()
    result = await orchestrator.run(prompt)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### Semana 51-52: Beta Testing

**Execution steps:**

3. Ejecucion beta con el prompt objetivo:
```bash
./agentic --prompt "Disena una pagina web moderna, profesional y \
totalmente responsive para un servicio de acortamiento de enlaces. \
La pagina debe tener una interfaz limpia con un formulario principal \
donde el usuario pueda introducir una URL larga y obtener un enlace \
corto. Incluye una seccion de estadisticas que muestre clics, fecha \
de creacion, pais y dispositivo de acceso. Agrega autenticacion de \
usuarios, panel de control, historial de enlaces, codigos QR para \
cada enlace y opciones de enlaces personalizados." --output ./output/shortener
```

4. Validacion manual:
```bash
cd output/shortener
npm install && npm run build  # React/Next.js
docker-compose up -d          # Docker
npx prisma validate           # Prisma
npx tsc --noEmit              # TypeScript
npm run test                  # Tests generados
```

**Verification checklist:**
- [ ] Pipeline produce ~40-80 archivos
- [ ] Codigo compila sin errores
- [ ] `docker-compose up` levanta el stack completo
- [ ] Login/registro funcional
- [ ] Formulario de acortamiento genera link corto
- [ ] Estadisticas muestran clics, pais, dispositivo
- [ ] QR code se genera para cada link
- [ ] Panel de control muestra historial
- [ ] Diseno responsive (mobile + desktop)
- [ ] Paleta de colores moderna y coherente

**Definition of done (final):**
- [ ] Pipeline completo ejecuta end-to-end con StateGraph
- [ ] CLI `./agentic --prompt "..."` funciona
- [ ] Streaming de progreso por etapa
- [ ] Beta del acortador produce codigo funcional
- [ ] Todos los tests pasan (55+ tests, cobertura >80%)
- [ ] Documentacion de API y guia de uso escrita

---

## Summary: Mapa de Sprints

| Sprint | Semanas | Componente | Tareas 067 | Archivos nuevos |
|--------|---------|-----------|------------|-----------------|
| 1 | 1-4 | Foundation | 0.1.1-0.2.4 | 10 |
| 2 | 5-8 | RequirementDecomposer | 1.1.1-1.1.6 | 4 |
| 3 | 9-12 | Preprocessor | 1.2.1-1.2.10 | 3 |
| 4 | 13-16 | Lexer | 1.3.1-1.3.11 | 4 |
| 5 | 17-20 | Parser | 2.1.1-2.1.9 | 8 |
| 6 | 21-24 | Semantic Analyzer | 2.2.1-2.2.11 | 5 |
| 7 | 25-28 | IR Generator | 2.3.1-2.3.11 | 5 |
| 8 | 29-32 | Planner | 3.1.1-3.1.11 | 5 |
| 9 | 33-36 | Synthesis | 3.2.1-3.3.4 | 10 |
| 10 | 37-40 | Output Validator | 4.1.1-4.1.9 | 4 |
| 11 | 41-44 | UI Generator | 4.2.1-4.2.8 | 5 |
| 12 | 45-48 | Feedback Loop | 4.3.1-4.3.3 | 3 |
| 13 | 49-52 | Integration + Beta | 5.1.1-5.3.3 | 3 |

## Daily Workflow Recomendado

```bash
# Inicio del dia
git pull
cd compiler-bot/agentic_pipeline

# Trabajar en tarea especifica
# [implementar codigo]

# Tests
pytest tests/ -v --cov=agentic_pipeline --cov-report=term-missing

# Linter + formatter
ruff check .
black .

# Commit
git add -A
git commit -m "exec(SprintN): Componente — descripcion"
```

## Protocolo de Excepciones

Si una tarea no puede completarse en el sprint:

1. Abrir issue con:
   - Bloqueador identificado
   - Alternativas evaluadas
   - Impacto en sprints siguientes
2. Mover tarea a backlog del sprint siguiente
3. Ajustar estimaciones del roadmap

Si una dependencia externa (LangChain, Lark) cambia la API:

1. Congelar version en `requirements.txt`
2. Evaluar migracion con test de integracion
3. Documentar breaking changes en `CHANGELOG.md`
