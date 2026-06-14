---
id: 070
area: dev
type: GUIDE
module: python-style
version: 1.0
status: DRAFT
tags:
  - python
  - style
  - convention
  - pep8
  - workflow
summary: "Guia de estilo para codigo Python en @Proyecto0. Define convenciones de nomenclatura, estructura de archivos, manejo de errores, typing, logging y patrones de diseno para mantener codigo legible, mantenible y consistente."
keywords:
  - python
  - py
  - pep8
  - estilo
  - convencion
  - nomenclatura
  - pydantic
  - pytest
  - langchain
changelog:
  - version: 1.0
    date: 2026-06-14
    author: workflow-agent
    description: Creacion inicial de la guia de estilo Python
---

# Guia de Estilo Python — @Proyecto0 / RECPL v2.0

## 0. Filosofia

El codigo Python en este proyecto sigue tres principios fundamentales:

1. **Explicit over implicit** — Cada operacion se declara explicitamente.
   Sin imports salvajes (`from x import *`), sin mutacion silenciosa, sin
   excepciones atrapadas genericamente sin registro.

2. **Type-safe by default** — Todo codigo nuevo usa type hints. Pydantic
   valida datos en los limites del sistema. El tipado es contrato, no
   documentacion.

3. **Testable by construction** — Las funciones son puras donde sea posible.
   Las dependencias se inyectan. Los efectos secundarios se aislan en el
   borde del sistema.

---

## 1. Estructura del archivo

### 1.1 Orden de secciones

```
1. """Docstring del modulo""" (cuando aplique)
2. imports de la biblioteca estandar
3. imports de terceros (langchain, pydantic, etc.)
4. imports del proyecto (agentic_pipeline.*)
5. Constantes (SCREAMING_SNAKE_CASE)
6. Clases
7. Funciones
8. `if __name__ == "__main__":` (solo entrypoints)
```

### 1.2 Reglas de imports

```python
# Correcto — grupos separados por linea en blanco, orden alfabetico
import json
import logging
from pathlib import Path
from typing import Any, Optional

import pytest
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field

from agentic_pipeline.config import config
from agentic_pipeline.state_models import StageContext, StageOutput


# Incorrecto — mezclado, sin grupos, import salvaje
import json, os
from agentic_pipeline import *
from typing import *
```

### 1.3 Separadores visuales

```
# ============================================================================
# SECTION HEADER
# ============================================================================
```

```
# --- Sub-section ---
```

---

## 2. Convenciones de nomenclatura

### 2.1 Archivos

```
snake_case.py
```

### 2.2 Modulos y paquetes

```
snake_case — nombres cortos, sin guiones.
Ejemplos:
  state_models.py
  feedback_loop.py
  base_stage.py
```

### 2.3 Clases

```
PascalCase — sustantivo, descriptivo.
Ejemplos:
  PipelineStage
  FeedbackLoop
  AnalysisResult
  TokenFlyweightRegistry
  MultiWordTrie
```

### 2.4 Funciones y metodos

```
snake_case — verbo al inicio, seguido de sustantivo.
Ejemplos:
  receive_mission()
  reflect_and_plan()
  learn_and_improve()
  get_recent()
  memento_save()
```

### 2.5 Variables

```
snake_case — descriptiva, sin abreviaturas.
Ejemplos:
  input_data
  complexity_score
  fallback_strategy
  normalized_text
  all_tokens
```

### 2.6 Constantes

```
SCREAMING_SNAKE_CASE — valores fijos, configuraciones.
Ejemplos:
  DOMAIN_CONTEXT
  IMPLICIT_REQUIREMENTS
  VALIDATION_LEVELS
```

### 2.7 Variables privadas

```
_prefijo_con_guion_bajo — "Protected" por convencion.
Ejemplos:
  _raw_text
  _scopes
  _snapshots
  _input_text
```

### 2.8 Nombres prohibidos

- No usar `x`, `y`, `z`, `tmp`, `foo`, `bar`, `data`, `info`
- No usar nombres de una sola letra (excepto `i`, `j` en bucles muy locales)
- No usar `dict`, `list`, `str`, `type`, `object` como nombres de variable
- No usar mayusculas para variables locales

---

## 3. Formato y espaciado

### 3.1 Herramientas

El proyecto usa **ruff** para linting y **ruff** para formateo (reemplaza a
black). NO usar flake8, pylint, isort, autopep8 ni yapf.

```bash
# Linting
ruff check .

# Formateo
ruff format .

# Format check (CI)
ruff format --check .
```

### 3.2 Configuracion (pyproject.toml)

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "SIM", "ARG", "PLE", "RUF"]
ignore = ["E501"]  # manejado por formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
line-ending = "lf"
```

### 3.3 Indentacion

- Usar **4 espacios** por nivel (NO tabs)
- Maximo **100 caracteres** por linea
- Saltos de linea: uso implicito dentro de parentesis

```python
# Correcto
result = some_function(
    argument_one,
    argument_two,
    argument_three,
)

# Correcto — operadores al inicio de la linea siguiente
total = (first_term
         + second_term
         + third_term)

# Incorrecto
result = some_function(argument_one,
    argument_two, argument_three)

# Incorrecto — backslash
total = first_term + \
        second_term
```

### 3.4 Lineas en blanco

- 2 lineas en blanco entre clases y funciones top-level
- 1 linea en blanco entre metodos dentro de una clase
- 1 linea en blanco entre grupos de imports
- 1 linea en blanco antes de bloques de control (opcional, para claridad)

```python
class PipelineStage(ABC):
    name: str

    def execute(self, input_data: object) -> StageOutput:
        ...


class FeedbackLoop:
    def __init__(self):
        ...

    def record(self, stage: str, metrics: dict) -> None:
        ...
```

---

## 4. Manejo de errores

### 4.1 Regla de oro

Usar excepciones explicitas con contexto. NO atrapar `Exception`
genericamente sin registro. NO usar codigos de retorno para senalar errores.

```python
# Correcto
try:
    result = risky_operation()
except ValidationError as e:
    logger.error("Validation failed: %s", e)
    return StageOutput(stage=self.context.stage, output_data={},
                       success=False, error=str(e))

# Incorrecto
try:
    result = risky_operation()
except:
    pass

# Incorrecto — codigo de retorno
def get_data():
    if error:
        return None, "error message"
    return data, None
```

### 4.2 Jerarquia de excepciones

```python
class PipelineError(Exception):
    """Base exception for pipeline errors."""

class StageError(PipelineError):
    """Error during stage execution."""

class ValidationError(PipelineError):
    """Input or output validation error."""

class ConfigurationError(PipelineError):
    """Invalid configuration."""
```

### 4.3 Patron de error en StageOutput

El campo `StageOutput.error` se usa para errores recuperables. Excepciones
no atrapadas en `act()` deben propagarse para que el orquestador las maneje.

```python
def act(self, plan: ActionPlan) -> StageOutput:
    try:
        result = self._do_work(plan)
        return StageOutput(stage=self.context.stage,
                           output_data=result, success=True)
    except PipelineError as e:
        self.feedback.record(self.name, {"error": str(e)})
        return StageOutput(stage=self.context.stage, output_data={},
                           success=False, error=str(e))
```

### 4.4 Validacion de argumentos

Usar Pydantic para validar datos en los limites del sistema. No validar
manualmente con `if`/`assert` dentro de la logica de negocio.

```python
# Correcto — Pydantic valida al recibir
class AnalysisResult(BaseModel):
    observations: list[str]
    complexity_score: float = 0.0

# Incorrecto
def analyze(observations, score):
    if not isinstance(observations, list):
        raise TypeError("observations must be a list")
```

---

## 5. Logging

### 5.1 Logger por modulo

Cada modulo crea su propio logger. NO usar `print()` para logging.

```python
import logging

logger = logging.getLogger(__name__)
```

### 5.2 Niveles

- `logger.debug()` — detalle fino, solo desarrollo
- `logger.info()` — hitos normales del pipeline
- `logger.warning()` — recuperable, no bloqueante
- `logger.error()` — fallo recuperable, registrado en feedback
- `logger.critical()` — fallo irrecoverable, antes de exit

### 5.3 Formato estructurado

Usar formato con interpolacion diferida (%s), NO f-strings en logging.

```python
# Correcto
logger.debug("Processing stage %s with %d tokens", stage_name, token_count)

# Incorrecto
logger.debug(f"Processing stage {stage_name} with {token_count} tokens")
```

### 5.4 Eventos del pipeline

- `STAGE %s → START` — inicio de etapa
- `STAGE %s → DONE (metrics: %s)` — etapa completada
- `STAGE %s → ERROR: %s` — etapa con error
- `FEEDBACK → %s` — registro de feedback
- `STATE → %s` — cambios de estado

---

## 6. Type Hints

### 6.1 Obligatorios

Todo codigo nuevo debe tener type hints en:
- Parametros de funciones y metodos
- Valores de retorno
- Campos de clases y dataclasses

```python
# Correcto
def analyze(self) -> AnalysisResult:
    result: list[str] = []
    return AnalysisResult(observations=result, ...)

# Incorrecto
def analyze(self):
    result = []
    return ...
```

### 6.2 Import de tipos

Usar `from __future__ import annotations` para permitir sintaxis moderna
de tipos en Python 3.11:

```python
from __future__ import annotations

from typing import Any, Optional

def process(data: list[dict[str, Any]]) -> Optional[str]:
    ...
```

### 6.3 Tipos complejos

```python
from typing import Any, Optional, TypeAlias

JSON: TypeAlias = dict[str, Any]
TokenList: TypeAlias = list[Token]

def tokenize(self, text: str, start_pos: int = 0) -> TokenList:
    ...
```

### 6.4 Avoid over-specification

No anotar variables locales obvias. El tipo se infiere del valor.

```python
# Correcto
tokens = self.dfas["domain"].tokenize(text)

# Incorrecto — redundante
tokens: list[Token] = self.dfas["domain"].tokenize(text)
```

---

## 7. Clases y Objetos

### 7.1 Clases base abstractas

Usar `abc.ABC` y `@abstractmethod`. NO usar duck typing para interfaces.

```python
from abc import ABC, abstractmethod

class PipelineStage(ABC):
    name: str

    @abstractmethod
    def receive_mission(self, input_data: object) -> None: ...

    @abstractmethod
    def analyze(self) -> AnalysisResult: ...
```

### 7.2 Dataclasses vs Pydantic

- Usar **Pydantic** para datos que cruzan limites del sistema (input/output,
  config, state)
- Usar **dataclasses** para estructuras internas sin validacion

```python
# Pydantic — validacion en los bordes
class StageContext(BaseModel):
    mission_id: str
    stage: Stage
    input_data: Any

# dataclass — estructura interna
@dataclass
class InternalMetrics:
    tokens_processed: int
    elapsed_ms: float
```

### 7.3 Properties y metodos privados

```python
class TokenRegistry:
    def __init__(self):
        self._cache: dict[tuple, Token] = {}

    @property
    def size(self) -> int:
        return len(self._cache)

    def _make_key(self, value: str, type: str, category: str) -> tuple:
        return (value, type, category)
```

### 7.4 Metodos de clase vs estaticos

- `@classmethod` — cuando el metodo necesita acceso a la clase (factory)
- `@staticmethod` — cuando el metodo es independiente pero pertenece al
  contexto de la clase (evitar, preferir funcion libre)

---

## 8. Patrones de diseno

### 8.1 Template Method (PipelineStage)

```python
class PipelineStage(ABC):
    def execute(self, input_data: object) -> StageOutput:
        self.receive_mission(input_data)
        analysis = self.analyze()
        plan = self.reflect_and_plan(analysis)
        output = self.act(plan)
        self.learn_and_improve(output.feedback)
        return output
```

### 8.2 Strategy (Preprocessor filters)

```python
class PreprocessingFilter(ABC):
    @abstractmethod
    def process(self, text: str, context: dict = None) -> str: ...

class NormalizationFilter(PreprocessingFilter):
    def process(self, text: str, context: dict = None) -> str:
        ...
```

### 8.3 Composite (AST/IR nodes)

```python
class ASTNode(ABC):
    def __init__(self, name: str = ""):
        self.name = name
        self.children: list[ASTNode] = []
        self.parent: Optional[ASTNode] = None

    def add(self, child: ASTNode) -> None:
        self.children.append(child)
        child.parent = self

    @abstractmethod
    def evaluate(self) -> dict: ...
```

### 8.4 Chain of Responsibility (Validator)

```python
class Validator(ABC):
    def __init__(self):
        self.next_validator: Optional[Validator] = None

    def set_next(self, validator: Validator) -> Validator:
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
```

### 8.5 Memento (SymbolTable)

```python
class SymbolTable:
    def memento_save(self) -> None:
        self._snapshots.append(deepcopy(self._scopes))

    def memento_restore(self) -> None:
        if self._snapshots:
            self._scopes = self._snapshots.pop()
```

---

## 9. Async

### 9.1 Reglas

- Usar `async def` solo para operaciones I/O-bound (LLM calls, API, file)
- Usar `asyncio.run()` en entrypoints, NO `loop.run_until_complete()`
- Tests asincronos con `pytest-asyncio` y decorador `@pytest.mark.asyncio`

```python
@pytest.mark.asyncio
async def test_orchestrator_run():
    orch = PipelineOrchestrator()
    result = await orch.run("test prompt")
    assert result is not None
```

### 9.2 Timeouts

```python
import httpx

async def call_llm(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(LLM_URL, json={"prompt": prompt})
        response.raise_for_status()
        return response.json()
```

---

## 10. Tests

### 10.1 Estructura

```
tests/
  __init__.py
  conftest.py          # Fixtures compartidos
  test_config.py       # Tests de configuracion
  test_state_models.py # Tests de modelos
  test_base_stage.py   # Tests de clase base
  test_orchestrator.py # Tests de orquestador
  test_<componente>.py # Tests por componente
```

### 10.2 Convenciones

- Nombrar archivos: `test_<modulo>.py`
- Nombrar funciones: `test_<funcionalidad>`
- Un assert por test (o asserts logicamente relacionados)
- Usar fixtures para contexto compartido, NO setup clases

```python
# Correcto
def test_mock_stage_executes():
    ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="test")
    stage = MockStage(ctx)
    result = stage.execute("hello")
    assert result is not None
    assert result.success is True

# Incorrecto — multiples conceptos no relacionados
def test_stage():
    # test 1
    assert True
    # test 2
    assert False
```

### 10.3 Comandos

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=agentic_pipeline --cov-report=term-missing

# Test especifico
pytest tests/test_base_stage.py -v -k "test_mock_stage_executes"
```

---

## 11. Seguridad

### 11.1 NO hardcodear secretos

```python
# Prohibido
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgres://admin:password@localhost:5432/db"
```

### 11.2 Variables de entorno

```python
# Correcto — via pydantic-settings con prefijo
class PipelineConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENTIC_")

    llm_api_key: str = ""
    database_url: str = ""

# Uso
config.llm_api_key  # Lee AGENTIC_LLM_API_KEY del entorno
```

### 11.3 Validacion de entrada

Toda entrada de usuario debe pasar por Pydantic antes de ser procesada.
NO confiar en datos sin validar.

```python
# Correcto
class UserInput(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)

# Incorrecto
def process(prompt: str):
    # prompt sin validar
    ...
```

### 11.4 Ejecucion de comandos

Para ejecutar comandos externos (synthesis), usar `subprocess.run` con
`shell=False` y lista de argumentos. NO `shell=True` con strings.

```python
# Correcto
subprocess.run(["npx", "prettier", "--check", str(output_dir)],
               capture_output=True, text=True, timeout=30)

# Incorrecto — shell injection vector
subprocess.run(f"npx prettier --check {output_dir}", shell=True)
```

---

## 12. Ejemplo completo

```python
"""example.py - Example module following @Proyecto0 Python style."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# ============================================================================
# MODELS
# ============================================================================


class ProcessResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None


# ============================================================================
# BASE CLASS
# ============================================================================


class BaseProcessor(ABC):
    """Abstract processor with template method."""

    name: str

    def __init__(self, context: dict | None = None):
        self.context = context or {}
        self._result: ProcessResult | None = None

    @abstractmethod
    def process(self, input_data: Any) -> ProcessResult:
        ...

    def execute(self, input_data: Any) -> ProcessResult:
        logger.info("PROCESSOR %s → START", self.name)
        try:
            self._result = self.process(input_data)
            logger.info("PROCESSOR %s → DONE", self.name)
        except Exception as e:
            logger.error("PROCESSOR %s → ERROR: %s", self.name, e)
            self._result = ProcessResult(success=False, error=str(e))
        return self._result


# ============================================================================
# CONCRETE IMPLEMENTATION
# ============================================================================


class Tokenizer(BaseProcessor):
    name = "tokenizer"

    def process(self, input_data: str) -> ProcessResult:
        tokens = input_data.lower().split()
        return ProcessResult(success=True, data={"tokens": tokens})
```

---

## 13. Checklist de validacion

Antes de dar por terminado un archivo:

- [ ] `ruff check .` — 0 errores
- [ ] `ruff format --check .` — 0 errores
- [ ] Todos los imports siguen el orden estandar → terceros → locales
- [ ] No hay imports salvajes (`from x import *`)
- [ ] Todas las funciones tienen type hints
- [ ] No hay nombres de una sola letra (excepto `i`, `j` en bucles)
- [ ] No hay `print()` para logging (usar `logger`)
- [ ] No hay secretos hardcodeados
- [ ] No hay `shell=True` en subprocess
- [ ] Los strings de logging usan `%s` NO f-strings
- [ ] Los errores tienen mensaje descriptivo en log
- [ ] Las clases estan en PascalCase
- [ ] Las funciones/metodos estan en snake_case
- [ ] Las constantes estan en SCREAMING_SNAKE_CASE
- [ ] La indentacion es de 4 espacios
- [ ] Maximo 100 caracteres por linea
- [ ] Los tests pasan: `pytest tests/ -v`
