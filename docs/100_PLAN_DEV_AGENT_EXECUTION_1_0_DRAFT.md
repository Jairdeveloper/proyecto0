---
id: 100
area: dev
type: plan
module: agent_core
version: 1.0
status: IMPLEMENTED
tags:
  - plan
  - execution
  - nivel-1
  - nivel-2
  - nivel-3
  - tool-registry
  - agent-loop
  - spacy
  - sentence-transformers
  - world-model
  - goal-tree-planner
summary: >-
  Plan de ejecucion detallado para los niveles N1, N2 y N3 del
  agente RECPL. Cada nivel contiene tareas con archivos exactos,
  dependencias, comandos de verificacion y criterios de aceptacion
  testeables. Disenado para ejecucion autonoma: cada nivel se prueba
  y valida antes de pasar al siguiente.
keywords:
  - plan
  - execution
  - nivel-1
  - nivel-2
  - nivel-3
  - tareas
  - archivos
  - comandos
  - verificacion
  - tests
changelog:
  - version: '1.0'
    date: 2026-06-16
    description: Plan de ejecucion detallado por niveles N1-N3
---

# 100_PLAN_DEV_AGENT_EXECUTION_1_0_DRAFT

## Estructura del plan

Cada nivel contiene:

- **Tareas** numeradas con archivos exactos a crear/modificar
- **Dependencias** entre tareas del mismo nivel
- **Comandos de verificacion** (shell) para probar cada tarea
- **Criterios de aceptacion** que deben cumplirse para dar el nivel
  por completado

```
Ejecucion: N1 → (verificar) → N2.1 → (verificar) → N2.2 → (verificar) → N3
           524 tests           540+ tests         555+ tests        570+ tests
```

Cada nivel es autonomo. Si se detiene en N1, el sistema funciona como
agente conectado con herramientas y memoria. Si se detiene en N2,
anade comprension semantica profunda.

---

## Nivel 1: Solucionador de Problemas Conectado

### Dependencias entre tareas

```
N1.1 (renombrar)
  │
  ├──→ N1.2 (ToolRegistry + tools) ──→ N1.4 (AgentLoop)
  │                                       │
  └──→ N1.3 (ConversationalMemory) ──────┘
                                            │
                                            ↓
                                         N1.5 (tests)
```

### N1.1 — Renombrar componentes

**Objetivo:** Alinear nombres del pipeline con el frame conceptual de
agente. La logica interna NO cambia — solo archivos, clases, imports.

**Archivos a renombrar:**

| # | Ruta actual (shell) | Ruta nueva (Python) | Referencias a actualizar |
|---|---------------------|---------------------|-------------------------|
| 1 | `nodes/intent_stage.py` | `nodes/perception_unit.py` | `orchestrator.py`, `state_models.py`, `contracts.py` |
| 2 | `nodes/planner.py` | `nodes/reasoning_engine.py` | `orchestrator.py`, `contracts.py` |
| 3 | `nodes/synthesis.py` | `nodes/action_executor.py` | `orchestrator.py`, `contracts.py` |
| 4 | `generators/` → `tools/` | `tools/` (directorio) | `synthesis.py` → `action_executor.py` imports |

**Clases a renombrar dentro de los archivos:**

| Clase actual | Clase nueva | Archivo |
|-------------|-------------|---------|
| `IntentStage` | `PerceptionUnit` | `nodes/perception_unit.py` |
| `HybridPlanner` | `ReasoningEngine` | `nodes/reasoning_engine.py` |
| `SynthesisOrchestrator` | `ActionExecutor` | `nodes/action_executor.py` |
| `PipelineOrchestrator` | `AgentOrchestrator` | `orchestrator.py` |

**Actualizaciones en `state_models.py`:**

```python
class Stage(Enum):
    INTENT = "intent"        # mantener compatibilidad
    PERCEPTION = "perception"   # NUEVO
    ...
    PLANNER = "planner"      # mantener compatibilidad
    REASONING = "reasoning"  # NUEVO
    ...
    SYNTHESIS = "synthesis"  # mantener compatibilidad
    EXECUTION = "execution"  # NUEVO
```

**Actualizaciones en `orchestrator.py`:**

```python
NODE_MAP: dict[Stage, type[PipelineStage]] = {
    Stage.INTENT: PerceptionUnit,        # antes: IntentStage
    Stage.PLANNER: ReasoningEngine,      # antes: HybridPlanner
    Stage.SYNTHESIS: ActionExecutor,     # antes: SynthesisOrchestrator
    ...
}
```

**Comandos de verificacion:**

```bash
# Verificar que los archivos renombrados existen
ls compiler-bot/agentic_pipeline/nodes/perception_unit.py
ls compiler-bot/agentic_pipeline/nodes/reasoning_engine.py
ls compiler-bot/agentic_pipeline/nodes/action_executor.py
ls -d compiler-bot/agentic_pipeline/tools/

# Verificar que los imports funcionan
python -c "from agentic_pipeline.nodes.perception_unit import PerceptionUnit"
python -c "from agentic_pipeline.nodes.reasoning_engine import ReasoningEngine"
python -c "from agentic_pipeline.nodes.action_executor import ActionExecutor"

# Verificar que no quedan referencias a nombres viejos en imports
rg "from.*intent_stage" compiler-bot/agentic_pipeline/
rg "from.*planner import" compiler-bot/agentic_pipeline/
rg "from.*synthesis import" compiler-bot/agentic_pipeline/
# → deben dar 0 resultados

# Ruff + tests
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
```

**Verificacion de compatibilidad hacia atras:** Anadir imports
compatibles en `__init__.py` para que codigo externo que importe
`IntentStage` desde `agentic_pipeline.nodes.intent_stage` siga
funcionando:

```python
# En nodes/__init__.py o en archivos legacy
from .perception_unit import PerceptionUnit
from .reasoning_engine import ReasoningEngine
from .action_executor import ActionExecutor

# Compatibilidad hacia atras
IntentStage = PerceptionUnit
HybridPlanner = ReasoningEngine
SynthesisOrchestrator = ActionExecutor
```

---

### N1.2 — ToolRegistry y port de herramientas

**Objetivo:** Crear el sistema de herramientas que el agente usara
para interactuar con el entorno. Portar las 6 herramientas del shell.

**Archivos a crear:**

| Archivo | Contenido |
|---------|-----------|
| `agentic_pipeline/tool_registry.py` | `Tool` (ABC) + `ToolRegistry` + `ToolResult` |
| `agentic_pipeline/tools/__init__.py` | Package init |
| `agentic_pipeline/tools/base_tool.py` | `Tool` abstracto (o en tool_registry.py) |
| `agentic_pipeline/tools/read_file.py` | Port de `tool_read_file.sh` |
| `agentic_pipeline/tools/write_file.py` | Port de `tool_write_file.sh` |
| `agentic_pipeline/tools/run_command.py` | Port de `tool_run_command.sh` |
| `agentic_pipeline/tools/search_code.py` | Port de `tool_search_code.sh` |
| `agentic_pipeline/tools/generate_code.py` | Envuelve los 6 generadores existentes |
| `agentic_pipeline/tools/ask_user.py` | Port de `agent.sh` dialog |
| `agentic_pipeline/tools/explain.py` | Port de `tool_respond.sh` |

**Interfaz `ToolRegistry`:**

```python
@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)

class Tool(ABC):
    name: str
    description: str
    parameters: list[Parameter]

    @abstractmethod
    async def execute(self, params: dict) -> ToolResult: ...

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None: ...
    def get_tool(self, name: str) -> Tool: ...
    def list_available(self) -> list[dict]: ...
    def has_tool(self, name: str) -> bool: ...
    async def execute(self, name: str, params: dict) -> ToolResult: ...
```

**Especificacion de cada tool port:**

**`read_file`:**
```python
class ReadFileTool(Tool):
    name = "read_file"
    description = "Lee el contenido de un archivo del sistema de archivos"
    parameters = [Parameter("path", "string", "Ruta del archivo")]

    async def execute(self, params: dict) -> ToolResult:
        path = Path(params["path"])
        if not path.exists():
            return ToolResult(success=False, error=f"Archivo no encontrado: {path}")
        content = path.read_text(encoding="utf-8")
        return ToolResult(success=True, data={"content": content, "size": len(content)})
```

**`write_file`:**
```python
class WriteFileTool(Tool):
    name = "write_file"
    description = "Escribe contenido en un archivo del sistema de archivos"
    parameters = [
        Parameter("path", "string", "Ruta del archivo"),
        Parameter("content", "string", "Contenido a escribir"),
    ]

    async def execute(self, params: dict) -> ToolResult:
        path = Path(params["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params["content"], encoding="utf-8")
        return ToolResult(success=True, data={"path": str(path), "bytes": len(params["content"])})
```

**`run_command`:**
```python
class RunCommandTool(Tool):
    name = "run_command"
    description = "Ejecuta un comando del sistema y retorna stdout/stderr"
    parameters = [Parameter("command", "string", "Comando a ejecutar")]

    async def execute(self, params: dict) -> ToolResult:
        import subprocess
        result = subprocess.run(
            params["command"], shell=True,  # shell=True para npm/git/etc.
            capture_output=True, text=True, timeout=30,
        )
        return ToolResult(
            success=result.returncode == 0,
            data={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            },
        )
```

**`search_code`:** Port de `tool_search_code.sh` — usa `rg` (ripgrep)
o `grep -r` para buscar patrones.

**`generate_code`:** Envuelve los 6 generadores existentes. Toma
`target` (nestjs|prisma|react|nextjs|tailwind|docker) y `params`.

**`ask_user`:** Envia una pregunta al usuario y espera respuesta.
```python
class AskUserTool(Tool):
    name = "ask_user"
    description = "Pregunta al usuario para obtener clarificacion"
    parameters = [Parameter("question", "string", "Pregunta para el usuario")]

    async def execute(self, params: dict) -> ToolResult:
        print(f"\n[AGENTE] {params['question']}")
        response = input("> ")
        return ToolResult(success=True, data={"response": response})
```

**`explain`:** Port de `tool_respond.sh`. Retorna un mensaje textual
al usuario.
```python
class ExplainTool(Tool):
    name = "explain"
    description = "Explica un concepto o responde textualmente al usuario"
    parameters = [Parameter("message", "string", "Mensaje a mostrar")]

    async def execute(self, params: dict) -> ToolResult:
        return ToolResult(success=True, data={"message": params["message"]})
```

**Comandos de verificacion:**

```bash
# Verificar que el registro funciona
python -c "
from agentic_pipeline.tool_registry import ToolRegistry
r = ToolRegistry()
print(f'Tools registradas: {len(r.list_available())}')
assert len(r.list_available()) >= 5
print('OK: ToolRegistry functional')
"

# Verificar read_file tool
python -c "
from agentic_pipeline.tool_registry import ToolRegistry
r = ToolRegistry()
result = r.execute('read_file', {'path': 'VERSION'})
print(f'read_file: {result.success}')
assert result.success
"

# Verificar write_file tool (en tmp)
python -c "
from agentic_pipeline.tool_registry import ToolRegistry
import tempfile, os
r = ToolRegistry()
tmp = os.path.join(tempfile.mkdtemp(), 'test.txt')
result = r.execute('write_file', {'path': tmp, 'content': 'hello'})
assert result.success
with open(tmp) as f: assert f.read() == 'hello'
os.remove(tmp)
print('OK: write_file functional')
"

# Verificar run_command tool
python -c "
from agentic_pipeline.tool_registry import ToolRegistry
r = ToolRegistry()
result = r.execute('run_command', {'command': 'echo hello'})
print(f'run_command: {result.success}, stdout={result.data[\"stdout\"].strip()}')
assert result.success and result.data['stdout'].strip() == 'hello'
"

# Ruff
ruff check compiler-bot/agentic_pipeline/
```

---

### N1.3 — ConversationalMemory

**Objetivo:** Portar `memory.sh` a Python. Persistencia JSON del
historial de conversacion entre invocaciones.

**Archivos a crear:**

| Archivo | Contenido |
|---------|-----------|
| `agentic_pipeline/memory.py` | `ConversationalMemory` class |

**Interfaz:**

```python
class ConversationalMemory:
    """Memoria persistente del agente. Port de memory.sh."""

    def __init__(self, storage_dir: str = ".recpl_memory"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._mem_file = self.storage_dir / "agent_memory.json"
        self.current_session = self._load_or_create()

    def _load_or_create(self) -> dict:
        if self._mem_file.exists():
            return json.loads(self._mem_file.read_text())
        return {"historial": [], "contexto": {}, "sesiones": []}

    def _save(self) -> None:
        self._mem_file.write_text(
            json.dumps(self.current_session, indent=2, ensure_ascii=False),
        )

    def save_context(self, key: str, value: Any) -> None:
        self.current_session["contexto"][key] = value
        self._save()

    def get_context(self, key: str) -> Any:
        return self.current_session["contexto"].get(key)

    def add_history(self, instruction: str, response: str) -> None:
        from datetime import datetime, timezone
        self.current_session["historial"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instruction": instruction,
            "response": response,
        })
        self._save()

    def get_recent(self, limit: int = 5) -> list[dict]:
        return self.current_session["historial"][-limit:]

    def list_sessions(self) -> list[str]:
        pattern = str(self.storage_dir / "agent_memory_*.json")
        return [p.name for p in Path(".").glob(pattern)]

    def set_session(self, name: str) -> None:
        self._mem_file = self.storage_dir / f"agent_memory_{name}.json"
        self.current_session = self._load_or_create()

    def export(self) -> str:
        return json.dumps(self.current_session, indent=2, ensure_ascii=False)
```

**Comandos de verificacion:**

```bash
# Verificar persistencia
python -c "
import tempfile, os
from agentic_pipeline.memory import ConversationalMemory
tmpdir = tempfile.mkdtemp()
m = ConversationalMemory(storage_dir=tmpdir)
m.save_context('test_key', 'test_value')
assert m.get_context('test_key') == 'test_value'
m.add_history('test instruction', 'test response')
recent = m.get_recent(1)
assert len(recent) == 1
assert recent[0]['instruction'] == 'test instruction'
print('OK: ConversationalMemory functional')
"

# Verificar que persiste entre instancias
python -c "
from agentic_pipeline.memory import ConversationalMemory
m = ConversationalMemory(storage_dir='$TMPDIR')
m.save_context('persist_test', 'works')
del m
m2 = ConversationalMemory(storage_dir='$TMPDIR')
assert m2.get_context('persist_test') == 'works'
print('OK: persistencia entre instancias')
"
```

---

### N1.4 — AgentLoop

**Objetivo:** Portar el loop principal de `recpl.sh` a Python. El
agente ejecuta una secuencia de acciones, observa resultados y decide
si necesita mas iteraciones.

**Archivos a crear:**

| Archivo | Contenido |
|---------|-----------|
| `agentic_pipeline/agent_loop.py` | `AgentLoop` class |

**Referencia directa del shell:**

| Patron shell | Equivalente Python |
|-------------|-------------------|
| `recpl.sh:96-127` `process_instruction()` | `AgentOrchestrator.run()` |
| `recpl.sh:166` `command_mode()` | `AgentLoop.run()` modo comando |
| `recpl.sh:222-283` `interactive_mode()` | `AgentLoop.run()` modo interactivo |
| `agent.sh` `classify → execute → respond` | `AgentLoop._classify → _execute → _respond` |

**Interfaz:**

```python
@dataclass
class AgentOutput:
    status: Literal["completed", "needs_clarification",
                    "action_executed", "max_iterations_reached",
                    "error"]
    data: dict = field(default_factory=dict)
    message: str = ""
    iterations: int = 0

class AgentLoop:
    """Bucle principal del agente. Port de recpl.sh y agent.sh."""

    def __init__(
        self,
        orchestrator: AgentOrchestrator | None = None,
        tools: ToolRegistry | None = None,
        memory: ConversationalMemory | None = None,
        max_iterations: int = 5,
        interactive: bool = False,
    ):
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.tools = tools or ToolRegistry()
        self.memory = memory or ConversationalMemory()
        self.max_iterations = max_iterations
        self.interactive = interactive

    async def run(self, prompt: str) -> AgentOutput:
        """Ejecuta el prompt a traves del pipeline con loop agente."""
        iteration = 0
        context = {"history": self.memory.get_recent()}

        while iteration < self.max_iterations:
            output = await self.orchestrator.run(prompt, context)

            if output.status == "completed":
                self.memory.add_history(prompt, str(output.data))
                return AgentOutput(
                    status="completed",
                    data=output.data,
                    iterations=iteration + 1,
                )

            if output.status == "needs_clarification":
                if self.interactive:
                    result = await self.tools.execute(
                        "ask_user",
                        {"question": output.clarification_prompt},
                    )
                    if result.success:
                        prompt = result.data["response"]
                        context["history"].append(
                            {"role": "user", "content": prompt},
                        )
                else:
                    return AgentOutput(
                        status="needs_clarification",
                        message=output.clarification_prompt,
                        iterations=iteration + 1,
                    )
                iteration += 1
                continue

            if output.status == "action_executed":
                observation = self._observe(output)
                if observation["success"] and not output.needs_followup:
                    self.memory.add_history(prompt, str(output.data))
                    return AgentOutput(
                        status="completed",
                        data=output.data,
                        iterations=iteration + 1,
                    )
                prompt = self._refine_plan(output, observation)
                iteration += 1

        return AgentOutput(
            status="max_iterations_reached",
            message=f"No se completo en {self.max_iterations} iteraciones",
            iterations=self.max_iterations,
        )

    def _observe(self, output: StageOutput) -> dict:
        """Observa el resultado de una accion ejecutada."""
        files_created = output.output_data.get("generated_files", [])
        return {
            "success": output.success,
            "files_created": files_created,
            "errors": output.error,
        }

    def _refine_plan(self, output: StageOutput, observation: dict) -> str:
        """Refina el plan basado en la observacion."""
        if observation["errors"]:
            return f"corrige el error: {observation['errors']}. {output.clarification_prompt}"
        return output.clarification_prompt

    async def run_interactive(self) -> None:
        """Modo interactivo: loop REPL como recpl.sh interactive_mode()."""
        print("RECPL Agent v2.0 — Escribe 'quit' para salir.")
        while True:
            try:
                prompt = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if prompt.lower() in ("quit", "salir", "exit", "q"):
                break
            if not prompt.strip():
                continue

            result = await self.run(prompt)
            print(json.dumps(result.data, indent=2, default=str))
```

**Comandos de verificacion:**

```bash
# Verificar loop con prompt simple
python -c "
import asyncio
from agentic_pipeline.agent_loop import AgentLoop
async def test():
    loop = AgentLoop(max_iterations=3)
    result = await loop.run('crea un modulo de pagos')
    print(f'Estado: {result.status}, Iteraciones: {result.iterations}')
    assert result.status in ('completed', 'max_iterations_reached')
    assert result.iterations <= 3
    print('OK: AgentLoop functional')
asyncio.run(test())
"

# Verificar que el modo interactivo arranca (sin input)
echo "quit" | python -c "
import asyncio
from agentic_pipeline.agent_loop import AgentLoop
async def test():
    loop = AgentLoop(max_iterations=3)
    await loop.run_interactive()
asyncio.run(test())
"
```

---

### N1.5 — Tests unitarios

**Objetivo:** Anadir tests que verifiquen cada componente de N1.

| Test file | Que prueba | Tests esperados |
|-----------|-----------|-----------------|
| `tests/test_tool_registry.py` | Registro + ejecucion de tools | 8-10 tests |
| `tests/test_memory.py` | CRUD persistencia, sesiones, historial | 6-8 tests |
| `tests/test_agent_loop.py` | Loop simple, clarificacion, max iteraciones | 4-6 tests |

**Total tests esperados N1:** 524 + 18-24 ≈ **540+ tests**

**Comandos de verificacion finales N1:**

```bash
# Suite completa
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short

# Verificacion manual de tools
python -c "
from agentic_pipeline.tool_registry import ToolRegistry
r = ToolRegistry()
tools = r.list_available()
assert any(t['name'] == 'read_file' for t in tools)
assert any(t['name'] == 'write_file' for t in tools)
assert any(t['name'] == 'run_command' for t in tools)
assert any(t['name'] == 'search_code' for t in tools)
assert any(t['name'] == 'explain' for t in tools)
print(f'N1 completo: {len(tools)} herramientas registradas')
"

# Verificacion memoria
python -c "
from agentic_pipeline.memory import ConversationalMemory
import tempfile
m = ConversationalMemory(storage_dir=tempfile.mkdtemp())
m.add_history('test', 'response')
assert len(m.get_recent(1)) == 1
assert m.list_sessions() is not None
print('N1 completo: memoria funcional')
"

# Verificacion loop
python -c "
import asyncio
from agentic_pipeline.agent_loop import AgentLoop
async def test():
    loop = AgentLoop(max_iterations=3)
    result = await loop.run('test prompt')
    assert result.iterations >= 1
    print(f'N1 completo: loop funcional ({result.status})')
asyncio.run(test())
"
```

### Criterios de aceptacion N1

```
CHECKLIST N1:
[ ] N1.1 — Renombres completados: archivos, clases, imports
[ ] N1.1 — `ruff check .` = 0 errores
[ ] N1.2 — ToolRegistry registra ≥ 5 herramientas
[ ] N1.2 — read_file lee archivos del sistema
[ ] N1.2 — write_file escribe archivos correctamente
[ ] N1.2 — run_command ejecuta comandos y captura output
[ ] N1.2 — search_code busca patrones en el codigo
[ ] N1.2 — ask_user permite dialogo bidireccional
[ ] N1.3 — ConversationalMemory persiste entre instancias
[ ] N1.3 — ConversationalMemory.add_history/get_recent funcional
[ ] N1.3 — ConversationalMemory.list_sessions funcional
[ ] N1.4 — AgentLoop ejecuta ≥ 1 iteracion sin errores
[ ] N1.4 — AgentLoop termina con 'completed' o 'max_iterations_reached'
[ ] N1.5 — Test suite: 540+ tests, todos pasando
```

---

## Nivel 2.1: Percepcion Enriquecida

### Dependencias entre tareas

```
N2.1a (spaCy)
  │
  ├──→ N2.1b (SentenceTransformers)
  │
  └──→ N2.1c (WordNet)
         │
         ↓
      N2.1d (tests + verificacion)
```

### N2.1a — spaCy como preprocesador semantico

**Objetivo:** Anadir POS tagging, dependencias gramaticales, lemmas
y NER a los tokens del preprocessor. spaCy se carga bajo demanda (lazy)
para no afectar tiempo de inicio.

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `agentic_pipeline/nodes/preprocessor.py` | Anadir `SpacyProcessor` como etapa opcional |
| `agentic_pipeline/pyproject.toml` | Anadir `spacy>=3.7` a dependencies |

**Implementacion en `preprocessor.py`:**

```python
class SpacyProcessor:
    """Procesador NLP con spaCy. Carga lazy."""
    _nlp = None

    @classmethod
    def get_nlp(cls):
        if cls._nlp is None:
            import spacy
            cls._nlp = spacy.load("es_core_news_sm")
        return cls._nlp

    def process(self, text: str) -> dict | None:
        try:
            doc = self.get_nlp()(text)
            return {
                "tokens": [
                    {
                        "text": t.text, "pos": t.pos_, "lemma": t.lemma_,
                        "dep": t.dep_, "head": t.head.text,
                        "is_stop": t.is_stop,
                    }
                    for t in doc
                ],
                "entities": [
                    {"text": ent.text, "label": ent.label_,
                     "start": ent.start_char, "end": ent.end_char}
                    for ent in doc.ents
                ],
                "sentences": [str(s) for s in doc.sents],
            }
        except Exception:
            return None
```

**Integracion en Preprocessor.act():**

```python
class Preprocessor(PipelineStage):
    def act(self, plan: ActionPlan) -> StageOutput:
        raw = self._input_data.get("raw", "")
        # Filtros existentes (se mantienen)
        normalized = self._apply_filters(raw)

        # spaCy enrichment (NUEVO, opcional)
        spacy_output = SpacyProcessor().process(raw)

        return StageOutput(
            output_data={
                "normalized_text": normalized,
                "spacy": spacy_output,  # puede ser None si falla
                "token_count": len(normalized.split()),
            },
            metrics={"spacy_enriched": spacy_output is not None},
        )
```

**Comandos de verificacion:**

```bash
# Instalar modelo spaCy espanol
python -m spacy download es_core_news_sm

# Verificar procesamiento
python -c "
from agentic_pipeline.nodes.preprocessor import SpacyProcessor
p = SpacyProcessor()
result = p.process('crea un modulo de pagos en NestJS')
assert result is not None
tokens = result['tokens']
verbs = [t for t in tokens if t['pos'] == 'VERB']
nouns = [t for t in tokens if t['pos'] == 'NOUN' or t['pos'] == 'PROPN']
print(f'Tokens: {len(tokens)}, Verbos: {len(verbs)}, Nombres: {len(nouns)}')
for t in tokens:
    print(f'  {t[\"text\"]:15s} POS={t[\"pos\"]:8s} LEMMA={t[\"lemma\"]:10s} DEP={t[\"dep\"]}')
assert any(t['pos'] == 'VERB' for t in tokens)
print('OK: spaCy enrichment functional')
"

# Verificar lazy loading
python -c "
import time
from agentic_pipeline.nodes.preprocessor import SpacyProcessor
start = time.time()
p = SpacyProcessor()
load_time = time.time() - start
print(f'Primera carga: {load_time:.2f}s')
start = time.time()
p.process('test')
process_time = time.time() - start
print(f'Procesamiento: {process_time:.3f}s')
"
```

---

### N2.1b — Clasificador con SentenceTransformers

**Objetivo:** Reemplazar clasificador por regex con embeddings
semanticos. Detecta intenciones por similitud de coseno entre el
prompt y ejemplos de referencia. Mide confianza.

**Archivos a modificar/crear:**

| Archivo | Cambio |
|---------|--------|
| `agentic_pipeline/nodes/perception_unit.py` | Reemplazar `_extract_keywords()` con `SentenceTransformerClassifier` |
| `agentic_pipeline/pyproject.toml` | Anadir `sentence-transformers>=3.0` a dependencies |

**Implementacion en `perception_unit.py`:**

```python
from sentence_transformers import SentenceTransformer, util

class SentenceTransformerClassifier:
    """Clasificador de intencion por embeddings semanticos."""

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer(cls.MODEL_NAME)
        return cls._model

    def __init__(self):
        self.model = self.get_model()
        self.references = self._build_references()

    def _build_references(self) -> dict[str, list]:
        refs = {
            "CREATE": [
                "crea un modulo de pagos",
                "quiero generar una entidad usuario",
                "haz un nuevo controlador para autenticacion",
                "necesito un crud de productos",
                "construye un sistema de login",
            ],
            "READ": [
                "muestrame el contenido del archivo",
                "que hay en este directorio",
                "listame los modulos existentes",
                "dime que archivos hay en pagos",
                "leeme el archivo de configuracion",
            ],
            "UPDATE": [
                "agrega un campo email a la entidad usuario",
                "modifica el controlador de auth",
                "anade una nueva ruta al modulo",
                "cambia el nombre del servicio",
                "actualiza el schema de prisma",
            ],
            "DELETE": [
                "elimina el modulo de pagos",
                "borra la entidad temporal",
                "quita el campo edad del schema",
                "remueve el controlador viejo",
                "limpia los archivos temporales",
            ],
            "EXPLAIN": [
                "explica como funciona el pipeline",
                "que hace este componente",
                "dime como se conectan los stages",
                "como se anade un nuevo generador",
                "describe la arquitectura del sistema",
            ],
        }
        return {
            intent: self.model.encode(examples, convert_to_tensor=True)
            for intent, examples in refs.items()
        }

    def classify(self, text: str) -> tuple[str, float]:
        emb = self.model.encode(text, convert_to_tensor=True)
        best_intent, best_score = "UNKNOWN", 0.0

        for intent, refs in self.references.items():
            scores = util.cos_sim(emb, refs)
            max_score = scores.max().item()
            if max_score > best_score:
                best_score = max_score
                best_intent = intent

        return best_intent, best_score
```

**Integracion en PerceptionUnit:**

```python
class PerceptionUnit(PipelineStage):
    def __init__(self):
        super().__init__()
        self.classifier = SentenceTransformerClassifier()

    def classify(self, prompt: str) -> tuple[str, float, str]:
        intent, score = self.classifier.classify(prompt)

        if score >= 0.7:
            return intent, score, "high_confidence"
        elif score >= 0.6:
            return intent, score, "medium_confidence"
        else:
            return intent, score, "low_confidence"
    # ...
```

**Comandos de verificacion:**

```bash
# Verificar clasificacion de parafrasis
python -c "
from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
clf = SentenceTransformerClassifier()
tests = [
    ('crea un modulo de pagos', 'CREATE'),
    ('haz un modulo de pagos', 'CREATE'),
    ('quiero generar un CRUD', 'CREATE'),
    ('construye un sistema de auth', 'CREATE'),
    ('listame los archivos', 'READ'),
    ('elimina el modulo', 'DELETE'),
    ('explica el pipeline', 'EXPLAIN'),
]
for prompt, expected in tests:
    intent, score = clf.classify(prompt)
    ok = '✓' if intent == expected else '✗'
    print(f'{ok} {prompt:40s} → {intent:8s} (score={score:.3f})')
    assert intent == expected, f'Esperado {expected}, obtenido {intent}'
print('OK: clasificador semantico funcional')
"

# Verificar umbral de confianza
python -c "
from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier
clf = SentenceTransformerClassifier()
# Prompt ambiguo debe dar score bajo
intent, score = clf.classify('hmm')
print(f'Ambiguo: {intent} (score={score:.3f})')
assert score < 0.6, 'Prompt ambiguo debe tener score bajo'
print('OK: deteccion de ambigüedad funcional')
"
```

---

### N2.1c — Desambiguacion con WordNet

**Objetivo:** Desambiguar terminos que aparecen en multiples
gramaticas usando el algoritmo de Lesk.

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `agentic_pipeline/nodes/parser.py` | Anadir `disambiguate_term()` antes de seleccionar gramatica |
| `agentic_pipeline/nodes/parser.py` | `_select_grammar()` usa desambiguacion |
| `agentic_pipeline/pyproject.toml` | Anadir `nltk>=3.8` a dependencies |

**Implementacion:**

```python
from nltk.corpus import wordnet as wn
from nltk.wsd import lesk
from nltk.data import find as nltk_find

def ensure_nltk_data():
    """Descarga wordnet si no esta instalado."""
    try:
        nltk_find("wordnet")
    except LookupError:
        import nltk
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)

DOMAIN_MAP = {
    "software": {"grammar": "project", "description": "modulo de software"},
    "entity":   {"grammar": "data",    "description": "entidad de datos"},
    "ui":       {"grammar": "ui",      "description": "interfaz de usuario"},
    "infra":    {"grammar": "infra",   "description": "infraestructura"},
}

def infer_domain(synset) -> str:
    name = synset.name().lower()
    if any(k in name for k in ("computer", "software", "program")):
        return "software"
    if any(k in name for k in ("entity", "person", "object")):
        return "entity"
    if any(k in name for k in ("interface", "gui", "window")):
        return "ui"
    if any(k in name for k in ("infrastructure", "network", "database")):
        return "infra"
    return "entity"

def disambiguate_term(term: str, context: list[str]) -> dict:
    """Algoritmo de Lesk: synset mas probable segun contexto."""
    ensure_nltk_data()
    sentence = " ".join(context[-5:])  # ultimas 5 oraciones de contexto
    synset = lesk(sentence, term, lang="spa")
    if synset:
        domain = infer_domain(synset)
        grammar_info = DOMAIN_MAP.get(domain, DOMAIN_MAP["entity"])
        return {
            "term": term,
            "synset": synset.name(),
            "definition": synset.definition(),
            "domain": domain,
            "grammar": grammar_info["grammar"],
        }
    return {"term": term, "synset": None, "domain": "unknown", "grammar": None}
```

**Integracion en parser:**

```python
def _resolve_ambiguous_grammar(self, tokens: list[dict], context: list[str]) -> str:
    """Si los tokens sugieren multiples gramaticas, desambigua con WordNet."""
    ambiguous_terms = self._find_ambiguous_terms(tokens)
    if not ambiguous_terms:
        return self._select_grammar_by_pattern(tokens)

    for term in ambiguous_terms:
        result = disambiguate_term(term, context)
        if result["grammar"]:
            return result["grammar"]

    return self._select_grammar_by_pattern(tokens)
```

**Comandos de verificacion:**

```bash
# Descargar datos NLTK
python -c "from agentic_pipeline.nodes.parser import ensure_nltk_data; ensure_nltk_data()"

# Verificar desambiguacion
python -c "
from agentic_pipeline.nodes.parser import disambiguate_term
tests = [
    ('modulo', ['crea', 'un', 'modulo', 'de', 'pagos']),
    ('entidad', ['crea', 'una', 'entidad', 'usuario']),
]
for term, context in tests:
    result = disambiguate_term(term, context)
    domain = result.get('domain', 'unknown')
    print(f'  {term:10s} → {domain:10s} ({result[\"grammar\"]})')
    assert result['grammar'] is not None
print('OK: desambiguacion funcional')
"
```

---

### N2.1d — Tests de percepcion enriquecida

| Test file | Que prueba | Tests esperados |
|-----------|-----------|-----------------|
| `tests/test_spacy_processor.py` | Procesamiento spaCy, lazy loading, NER | 4-6 tests |
| `tests/test_sentence_classifier.py` | Clasificacion, parafrasis, confianza, umbrales | 6-8 tests |
| `tests/test_wordnet_disambiguation.py` | Desambiguacion por dominio, terminos ambiguos | 4-6 tests |

**Total tests esperados N2.1:** 540 + 14-20 ≈ **555+ tests**

**Comandos de verificacion finales N2.1:**

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short

# E2E: pipeline completo con prompt real
python -c "
import asyncio
from agentic_pipeline.orchestrator import AgentOrchestrator
async def test():
    o = AgentOrchestrator()
    result = await o.run('crea un modulo de pagos')
    print(f'Pipeline E2E: success={result.success}')
    assert result.success
asyncio.run(test())
"
```

### Criterios de aceptacion N2.1

```
CHECKLIST N2.1:
[ ] N2.1a — spaPy anade POS, lemma, dep, NER a los tokens
[ ] N2.1a — Carga lazy: no afecta tiempo de inicio
[ ] N2.1b — SentenceTransformers clasifica ≥ 5 parafrasis correctamente
[ ] N2.1b — Score < 0.6 en prompts ambiguos
[ ] N2.1b — Score > 0.7 en prompts claros
[ ] N2.1c — WordNet desambigua "modulo" → software, "entidad" → data
[ ] N2.1c — ≥ 80% precision en tests de desambiguacion
[ ] N2.1d — `ruff check .` = 0 errores
[ ] N2.1d — Test suite: 555+ tests, todos pasando
```

---

## Nivel 2.2: Planificacion Estrategica

### Dependencias entre tareas

```
N2.2a (WorldModel)
  │
  ├──→ N2.2b (GoalTreePlanner)
  │       │
  │       ↓
  │    N2.2c (Context Engineering)
  │
  └──→ N2.2d (tests + verificacion)
```

### N2.2a — WorldModel

**Objetivo:** Crear la representacion interna del estado del entorno
que el agente actualiza con cada accion.

**Archivos a crear:**

| Archivo | Contenido |
|---------|-----------|
| `agentic_pipeline/world_model.py` | `WorldModel`, `FileNode`, `DecisionRecord` |

**Implementacion:**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
import hashlib


@dataclass
class FileNode:
    path: str
    file_type: Literal["file", "directory"]
    hash: str | None = None
    created_by: str | None = None
    timestamp: str | None = None


@dataclass
class DecisionRecord:
    goal_id: str
    action: str
    rationale: str
    params: dict = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


@dataclass
class WorldDelta:
    added: list[FileNode] = field(default_factory=list)
    modified: list[FileNode] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)


class WorldModel:
    """Representacion interna del estado del entorno."""

    def __init__(self):
        self.files: dict[str, FileNode] = {}
        self.decisions: list[DecisionRecord] = []
        self.goals: list[dict] = []
        self.constraints: list[dict] = []

    def initialize(self, scan_path: str = ".") -> None:
        """Escanea el directorio de trabajo y construye estado inicial."""
        base = Path(scan_path).resolve()
        for p in base.rglob("*"):
            if any(part.startswith(".") for part in p.parts):
                continue
            rel = str(p.relative_to(base))
            if p.is_dir():
                self.files[rel] = FileNode(path=rel, file_type="directory")
            else:
                content = p.read_bytes() if p.exists() else b""
                self.files[rel] = FileNode(
                    path=rel,
                    file_type="file",
                    hash=hashlib.md5(content).hexdigest(),
                )

    def apply_action(self, action: dict) -> WorldDelta:
        """Actualiza estado segun accion ejecutada. Retorna el cambio."""
        delta = WorldDelta()
        action_type = action.get("type", "")
        path = action.get("path", "")

        if action_type in ("create", "write"):
            node = FileNode(
                path=path,
                file_type="file",
                hash=action.get("hash"),
                created_by=action.get("goal_id"),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self.files[path] = node
            delta.added.append(node)

        elif action_type == "delete":
            if path in self.files:
                del self.files[path]
                delta.removed.append(path)

        elif action_type == "mkdir":
            node = FileNode(path=path, file_type="directory")
            self.files[path] = node
            delta.added.append(node)

        self.decisions.append(DecisionRecord(
            goal_id=action.get("goal_id", "unknown"),
            action=action_type,
            rationale=action.get("rationale", ""),
            params=action,
        ))
        return delta

    def query(self, question: str) -> str:
        """Responde preguntas sobre el estado (sintaxis natural simple)."""
        q = question.lower()
        if "existe" in q or "exist" in q:
            # "existe modules/auth/?"
            for word in q.split():
                if word in self.files:
                    return f"Si, {word} existe"
                if word.endswith("?") and word[:-1] in self.files:
                    return f"Si, {word[:-1]} existe"
            return f"No encontrado: {question}"
        if "cuantos" in q or "list" in q:
            return f"Hay {len(self.files)} archivos/directorios conocidos"
        return f"No se como responder: {question}"

    def snapshot(self) -> dict:
        return {
            "files": list(self.files.keys()),
            "decisions": len(self.decisions),
            "goals": len(self.goals),
        }
```

**Comandos de verificacion:**

```bash
# Verificar inicializacion
python -c "
from agentic_pipeline.world_model import WorldModel
import tempfile, os
tmpdir = tempfile.mkdtemp()
# Crear algunos archivos de prueba
Path(tmpdir, 'test.txt').write_text('hello')
os.makedirs(Path(tmpdir, 'subdir'))
w = WorldModel()
w.initialize(tmpdir)
print(f'Archivos conocidos: {len(w.files)}')
assert any('test.txt' in k for k in w.files)
print('OK: WorldModel.initialize functional')
"

# Verificar apply_action y query
python -c "
from agentic_pipeline.world_model import WorldModel
w = WorldModel()
delta = w.apply_action({'type': 'create', 'path': 'modules/auth/auth.module.ts',
                        'goal_id': 'goal1', 'rationale': 'crear modulo auth'})
assert len(delta.added) == 1
assert w.query('existe modules/auth/auth.module.ts?') == 'Si, modules/auth/auth.module.ts existe'
print(w.query('cuantos archivos'))
print('OK: WorldModel.apply_action y query functional')
"
```

---

### N2.2b — GoalTreePlanner

**Objetivo:** Reemplazar el planner de pasos fijos con un planificador
estrategico que descompone objetivos en subobjetivos con verificacion
post-ejecucion y replanificacion.

**Archivos a modificar/crear:**

| Archivo | Cambio |
|---------|--------|
| `agentic_pipeline/nodes/reasoning_engine.py` | Reemplazar `HybridPlanner` con `GoalTreePlanner` |
| `agentic_pipeline/nodes/reasoning_engine.py` | Anadir `Goal` dataclass y `GoalTreePlanner` class |

**Implementacion:**

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Literal, Optional
from agentic_pipeline.world_model import WorldModel
from agentic_pipeline.memory import MemoryStore


@dataclass
class Goal:
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "failed", "blocked"]
    dependencies: list[str] = field(default_factory=list)
    subtasks: list[Goal] = field(default_factory=list)
    verification_criteria: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None


class GoalTreePlanner:
    """Planificador estrategico con descomposicion, verificacion y replan."""

    def __init__(self, memory: Optional[MemoryStore] = None):
        self.memory = memory
        # Planes predefinidos para intenciones conocidas
        self._plan_templates = {
            "create_module": self._plan_create_module,
            "create_entity": self._plan_create_entity,
            "create_crud": self._plan_create_crud,
            "explain": self._plan_explain,
        }

    def decompose(self, objective: str, intent: str,
                  entities: list[dict], world: WorldModel) -> Goal:
        """Objetivo abstracto → arbol de subobjetivos."""
        # Buscar plan similar en memoria
        plan = self._retrieve_similar_plan(objective)
        if plan:
            return self._instantiate(plan, entities, world)

        # Construir plan desde template
        template_key = self._match_template(intent, entities)
        builder = self._plan_templates.get(template_key, self._plan_generic)
        return builder(objective, entities, world)

    def verify(self, goal: Goal, world: WorldModel) -> bool:
        """Verifica post-ejecucion contra criterios."""
        if not goal.verification_criteria:
            return True
        for criterion in goal.verification_criteria:
            result = world.query(criterion)
            if "Si" not in result and "Si," not in result:
                return False
        return True

    def replan(self, goal: Goal, world: WorldModel, error: str) -> Goal:
        """Si un subobjetivo falla, replanifica."""
        goal.status = "failed"
        goal.error = error
        # Anadir un subobjetivo correctivo
        fix = Goal(
            id=f"{goal.id}_fix",
            description=f"corregir: {error}",
            status="pending",
            dependencies=goal.dependencies,
        )
        goal.subtasks.append(fix)
        return goal

    def _retrieve_similar_plan(self, objective: str) -> list[Goal] | None:
        """Busca en memoria planes exitosos similares."""
        if not self.memory:
            return None
        plans = self.memory.recall("successful_plans") or []
        for plan in plans:
            if any(word in objective.lower() for word in plan.get("keywords", [])):
                return plan.get("goals")
        return None

    def _instantiate(self, plan: list[Goal], entities: list[dict],
                     world: WorldModel) -> Goal:
        """Instancia un plan recuperado de memoria con entidades actuales."""
        # Implementacion: reemplazar placeholders con entidades reales
        import copy
        root = copy.deepcopy(plan[0]) if plan else self._plan_generic(...)
        root.id = f"goal_{datetime.now().timestamp()}"
        return root

    def _plan_create_module(self, objective: str, entities: list[dict],
                            world: WorldModel) -> Goal:
        module_name = self._extract_module_name(objective, entities)
        return Goal(
            id="create_module",
            description=f"Crear modulo {module_name}",
            status="pending",
            verification_criteria=[
                f"existe modules/{module_name}/{module_name}.module.ts?",
                f"existe modules/{module_name}/{module_name}.controller.ts?",
                f"existe modules/{module_name}/{module_name}.service.ts?",
            ],
            subtasks=[
                Goal(id="create_dir", description=f"Crear directorio modules/{module_name}",
                     status="pending", verification_criteria=[f"existe modules/{module_name}?"]),
                Goal(id="create_module_file", description="Crear archivo .module.ts",
                     status="pending", dependencies=["create_dir"]),
                Goal(id="create_controller", description="Crear archivo .controller.ts",
                     status="pending", dependencies=["create_dir"]),
                Goal(id="create_service", description="Crear archivo .service.ts",
                     status="pending", dependencies=["create_dir"]),
            ],
        )

    # ... otros templates
```

**Comandos de verificacion:**

```bash
# Verificar descomposicion
python -c "
from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
from agentic_pipeline.world_model import WorldModel
planner = GoalTreePlanner()
world = WorldModel()
world.initialize()
goal = planner.decompose(
    'crea un modulo de pagos',
    'CREATE',
    [{'name': 'pagos', 'type': 'module'}],
    world,
)
print(f'Goal: {goal.description}')
print(f'Subtasks: {len(goal.subtasks)}')
print(f'Verification criteria: {goal.verification_criteria}')
assert len(goal.subtasks) >= 2, 'Debe tener al menos 2 subtareas'
print('OK: GoalTreePlanner decompose functional')
"

# Verificar verificacion
python -c "
from agentic_pipeline.nodes.reasoning_engine import Goal, GoalTreePlanner
from agentic_pipeline.world_model import WorldModel
planner = GoalTreePlanner()
world = WorldModel()
world.apply_action({'type': 'create', 'path': 'test.txt'})
goal = Goal(id='test', description='test', status='pending',
            verification_criteria=['existe test.txt?'])
assert planner.verify(goal, world) == True
print('OK: GoalTreePlanner verify functional')
"

# Verificar replanificacion
python -c "
from agentic_pipeline.nodes.reasoning_engine import Goal, GoalTreePlanner
planner = GoalTreePlanner()
goal = Goal(id='fail', description='algo', status='in_progress')
result = planner.replan(goal, None, 'error de prueba')
assert result.status == 'failed'
assert result.error == 'error de prueba'
assert len(result.subtasks) == 1
assert result.subtasks[0].description == 'corregir: error de prueba'
print('OK: GoalTreePlanner replan functional')
"
```

---

### N2.2c — Context Engineering

**Objetivo:** Cada etapa del pipeline recibe solo la informacion
relevante para su funcion. El agente construye el contexto optimo.

**Archivos a modificar:**

| Archivo | Cambio |
|---------|--------|
| `agentic_pipeline/orchestrator.py` | Anadir `ContextWindow` y `build_context()` |
| `agentic_pipeline/state_models.py` | Anadir `ContextWindow` dataclass |

**Implementacion en `state_models.py`:**

```python
@dataclass
class ContextWindow:
    """Contexto optimizado para un stage especifico."""
    relevant_history: list[dict]
    world_snapshot: dict
    task_focus: str
```

**Implementacion en `orchestrator.py`:**

```python
from .state_models import ContextWindow

def build_context(stage: Stage, full_context: dict,
                  world: WorldModel | None = None) -> ContextWindow:
    """Construye el contexto optimo para cada stage."""
    history = full_context.get("history", [])
    world_snapshot = world.snapshot() if world else {}

    if stage in (Stage.INTENT, Stage.PERCEPTION):
        return ContextWindow(
            relevant_history=history[-3:],
            world_snapshot={},
            task_focus="parse user intent and classify",
        )
    elif stage in (Stage.PLANNER, Stage.REASONING):
        return ContextWindow(
            relevant_history=[],
            world_snapshot=world_snapshot,
            task_focus="decompose goal with current world state",
        )
    elif stage in (Stage.SYNTHESIS, Stage.EXECUTION):
        return ContextWindow(
            relevant_history=[],
            world_snapshot=world_snapshot.get("files", []),
            task_focus="generate code per plan, avoid overwrites",
        )
    elif stage in (Stage.PREPROCESSOR, Stage.LEXER, Stage.PARSER):
        return ContextWindow(
            relevant_history=[],
            world_snapshot={},
            task_focus="syntactic analysis without context bias",
        )
    return ContextWindow(
        relevant_history=history,
        world_snapshot=world_snapshot,
        task_focus="general processing",
    )
```

**Comandos de verificacion:**

```python
python -c "
from agentic_pipeline.state_models import Stage
from agentic_pipeline.orchestrator import build_context
from agentic_pipeline.world_model import WorldModel

world = WorldModel()
world.initialize()
full_context = {
    'history': [{'role': 'user', 'content': 'crea modulo'}, {'role': 'assistant', 'content': 'ok'}],
}

ctx_perception = build_context(Stage.INTENT, full_context, world)
assert len(ctx_perception.relevant_history) <= 3
assert ctx_perception.task_focus == 'parse user intent and classify'
print(f'Perception context: focus={ctx_perception.task_focus}, history={len(ctx_perception.relevant_history)}')

ctx_planning = build_context(Stage.PLANNER, full_context, world)
assert len(ctx_planning.relevant_history) == 0  # planner no necesita historial
assert 'files' in ctx_planning.world_snapshot
print(f'Planner context: focus={ctx_planning.task_focus}, world_files={len(ctx_planning.world_snapshot.get(\"files\", []))}')

print('OK: Context engineering functional')
"
```

---

### N2.2d — Tests de planificacion estrategica

| Test file | Que prueba | Tests esperados |
|-----------|-----------|-----------------|
| `tests/test_world_model.py` | Init, apply_action, query, snapshot | 6-8 tests |
| `tests/test_goal_tree_planner.py` | Decompose, verify, replan, templates | 8-10 tests |
| `tests/test_context_engineering.py` | Contexto por stage, aislamiento | 4-6 tests |

**Total tests esperados N2.2:** 555 + 18-24 ≈ **570+ tests**

**Comandos de verificacion finales N2.2:**

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short

# E2E: GoalTreePlanner + WorldModel integrados
python -c "
from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
from agentic_pipeline.world_model import WorldModel
planner = GoalTreePlanner()
world = WorldModel()
world.initialize()
goal = planner.decompose('crea modulo pagos', 'CREATE',
                          [{'name': 'pagos', 'type': 'module'}], world)
print(f'Objetivo: {goal.description}')
print(f'Subtareas ({len(goal.subtasks)}):')
for sub in goal.subtasks:
    print(f'  - {sub.description} ({sub.status})')
# Simular ejecucion exitosa
world.apply_action({'type': 'create', 'path': 'modules/pagos/pagos.module.ts'})
assert planner.verify(goal.subtasks[0], world)  # el dir existe
print('OK: planificacion estrategica integrada')
"
```

### Criterios de aceptacion N2.2

```
CHECKLIST N2.2:
[ ] N2.2a — WorldModel.initialize() escanea directorio y reporta archivos
[ ] N2.2a — WorldModel.apply_action() actualiza estado correctamente
[ ] N2.2a — WorldModel.query() responde preguntas sobre el estado
[ ] N2.2b — GoalTreePlanner.decompose() produce ≥ 3 subobjetivos
[ ] N2.2b — GoalTreePlanner.verify() verifica contra criterios
[ ] N2.2b — GoalTreePlanner.replan() corrige fallos con subtareas
[ ] N2.2c — ContextWindow entrega contexto distinto por stage
[ ] N2.2c — Stage de razonamiento no recibe historial innecesario
[ ] N2.2d — `ruff check .` = 0 errores
[ ] N2.2d — Test suite: 570+ tests, todos pasando
```

---

## Nivel 3: Sistema Multiagente Colaborativo

### Dependencias entre tareas

```
N3.1 (Agent base class)
  │
  ├──→ N3.2a (PerceptionAgent)
  ├──→ N3.2b (ReasoningAgent)
  ├──→ N3.2c (ExecutionAgent)
  ├──→ N3.2d (ValidatorAgent)
  │
  ├──→ N3.3 (SharedContext bus)
  │
  └──→ N3.4 (SupervisorAgent)
         │
         ↓
      N3.5 (tests + verificacion)
```

### N3.1 — Clase base Agent

**Archivo:** `agentic_pipeline/agents/base_agent.py`

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    id: str
    description: str
    agent: str
    params: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"


@dataclass
class TaskResult:
    task_id: str
    success: bool
    data: Any = None
    error: str | None = None


class SharedContext:
    """Bus de contexto compartido entre agentes."""
    def __init__(self):
        self._data: dict[str, Any] = {}
        self._subscribers: dict[str, list] = {}

    def publish(self, topic: str, data: Any) -> None:
        self._data[topic] = data

    def subscribe(self, topic: str) -> Any:
        return self._data.get(topic)

    def get_snapshot(self) -> dict:
        return dict(self._data)


class Agent(ABC):
    name: str = ""
    role: str = ""

    def __init__(self, context: SharedContext, **kwargs):
        self.context = context
        for k, v in kwargs.items():
            setattr(self, k, v)

    @abstractmethod
    async def process(self, task: Task) -> TaskResult: ...
```

### N3.2 — Agentes especializados

**Archivos a crear:**

| Archivo | Clase | Tools asociadas |
|---------|-------|-----------------|
| `agents/perception_agent.py` | `PerceptionAgent` | spaCy, SentenceTransformers, WordNet |
| `agents/reasoning_agent.py` | `ReasoningAgent` | GoalTreePlanner, WorldModel query |
| `agents/execution_agent.py` | `ExecutionAgent` | generate_code, read_file, write_file, run_command |
| `agents/validator_agent.py` | `ValidatorAgent` | file_checker, syntax_validator |
| `agents/supervisor_agent.py` | `SupervisorAgent` | task_delegator, conflict_resolver |

**Implementacion resumida:**

```python
# agents/supervisor_agent.py
class SupervisorAgent(Agent):
    name = "supervisor"
    role = "coordinar, delegar y consolidar"

    def __init__(self, context: SharedContext, agents: dict[str, Agent]):
        super().__init__(context)
        self.agents = agents

    async def process(self, task: Task) -> TaskResult:
        # Descomponer el objetivo en tareas para especialistas
        subtasks = self._decompose(task)

        # Ejecutar en orden de dependencias
        results = {}
        for sub in subtasks:
            agent = self.agents.get(sub.agent)
            if not agent:
                return TaskResult(task.id, False, error=f"Agente no encontrado: {sub.agent}")
            result = await agent.process(sub)
            results[sub.id] = result
            if not result.success:
                return TaskResult(task.id, False, error=result.error)

        return TaskResult(task.id, True, data=results)

    def _decompose(self, task: Task) -> list[Task]:
        return [
            Task("perceive", "Analizar entrada del usuario", "perception_agent"),
            Task("reason", "Descomponer objetivo", "reasoning_agent",
                 dependencies=["perceive"]),
            Task("execute", "Ejecutar acciones", "execution_agent",
                 dependencies=["reason"]),
            Task("validate", "Verificar resultados", "validator_agent",
                 dependencies=["execute"]),
        ]
```

### N3.3 — SharedContext bus

Ya incluido en `base_agent.py`. Opcionalmente, version con
pub/sub asincrono:

```python
class AsyncSharedContext(SharedContext):
    def __init__(self):
        super().__init__()
        self._channels: dict[str, list] = {}

    async def publish(self, topic: str, data: Any) -> None:
        self._data[topic] = data
        for cb in self._channels.get(topic, []):
            await cb(topic, data)

    def subscribe(self, topic: str, callback) -> None:
        if topic not in self._channels:
            self._channels[topic] = []
        self._channels[topic].append(callback)
```

### N3.4 — Tests multiagente

| Test file | Que prueba | Tests esperados |
|-----------|-----------|-----------------|
| `tests/test_multiagent.py` | Supervisor delega, agentes colaboran, SharedContext | 8-12 tests |

**Total tests esperados N3:** 570 + 8-12 ≈ **580+ tests** (600+ con tests adicionales)

**Comandos de verificacion finales N3:**

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short

# E2E multiagente
python -c "
import asyncio
from agentic_pipeline.agents.base_agent import SharedContext, Task
from agentic_pipeline.agents.supervisor_agent import SupervisorAgent
async def test():
    ctx = SharedContext()
    # Registrar agentes mock
    agents = {}
    supervisor = SupervisorAgent(ctx, agents)
    task = Task('test', 'crea modulo pagos', 'supervisor')
    result = await supervisor.process(task)
    print(f'Resultado: {result.success}')
asyncio.run(test())
"
```

### Criterios de aceptacion N3

```
CHECKLIST N3:
[ ] N3.1 — Clase base Agent con process() abstracto
[ ] N3.2 — PerceptionAgent + ReasoningAgent + ExecutionAgent implementados
[ ] N3.2 — ValidatorAgent implementado
[ ] N3.3 — SharedContext propaga estado entre agentes
[ ] N3.4 — SupervisorAgent delega tareas a ≥ 3 agentes especializados
[ ] N3.4 — Flujo multiagente completo: percibir → razonar → ejecutar → validar
[ ] N3.4 — SupervisorAgent replanifica si un sub-agente falla
[ ] N3.5 — `ruff check .` = 0 errores
[ ] N3.5 — Test suite: 580+ tests, todos pasando
```

---

## Resumen de comandos por nivel

### Verificacion N0 (estado actual)

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
python compiler-bot/agentic --prompt "crea un modulo de pagos" --metrics table
```

### Verificacion final N1

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
python -c "from agentic_pipeline.tool_registry import ToolRegistry; r = ToolRegistry(); assert len(r.list_available()) >= 5"
python -c "from agentic_pipeline.memory import ConversationalMemory; import tempfile; m = ConversationalMemory(storage_dir=tempfile.mkdtemp()); m.add_history('test','ok'); assert len(m.get_recent(1)) == 1"
python -c "import asyncio; from agentic_pipeline.agent_loop import AgentLoop; async def t(): a = AgentLoop(max_iterations=3); r = await a.run('test'); print(r.status); assert r.iterations >= 1; asyncio.run(t())"
```

### Verificacion final N2.1

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
python -c "from agentic_pipeline.nodes.preprocessor import SpacyProcessor; p = SpacyProcessor(); r = p.process('crea modulo'); assert r and any(t['pos'] == 'VERB' for t in r['tokens'])"
python -c "from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier; c = SentenceTransformerClassifier(); i,s = c.classify('crea modulo pagos'); assert i == 'CREATE' and s > 0.7"
python -c "from agentic_pipeline.nodes.parser import disambiguate_term; r = disambiguate_term('modulo', ['crea','modulo','pagos']); assert r['grammar'] is not None"
```

### Verificacion final N2.2

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
python -c "from agentic_pipeline.world_model import WorldModel; w = WorldModel(); w.initialize(); delta = w.apply_action({'type':'create','path':'test.txt'}); assert w.query('existe test.txt?').startswith('Si')"
python -c "from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner; p = GoalTreePlanner(); from agentic_pipeline.world_model import WorldModel; g = p.decompose('crea modulo','CREATE',[],WorldModel()); assert len(g.subtasks) >= 2"
```

### Verificacion final N3

```bash
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
python -c "import asyncio; from agentic_pipeline.agents.supervisor_agent import SupervisorAgent; from agentic_pipeline.agents.base_agent import SharedContext, Task; async def t(): ctx = SharedContext(); s = SupervisorAgent(ctx, {}); r = await s.process(Task('t','test','supervisor')); print(r.success); asyncio.run(t())"
```

---

## Roadmap de ejecucion

| Nivel | Tareas | Archivos | Tests | Esfuerzo |
|-------|--------|----------|-------|----------|
| **N1** | N1.1-N1.5 | ~20 archivos (10 crear, 10 modificar) | 540+ | 4 dias |
| **N2.1** | N2.1a-N2.1d | ~5 archivos modificar + 3 test files | 555+ | 3 dias |
| **N2.2** | N2.2a-N2.2d | ~5 archivos (3 crear, 2 modificar) + 3 test files | 570+ | 5 dias |
| **N3** | N3.1-N3.5 | ~8 archivos crear + 1 test file | 580+ | 5 dias |

**Total esfuerzo estimado:** ~17 dias
**Total tests finales:** 580+
