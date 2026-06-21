---
id: "116"
area: "DEV"
type: "PLAN"
module: "BEHAVIORAL_PATTERNS_REFACTOR"
version: "1.0"
status: IMPLEMENTED
tags:
  - "plan"
  - "refactor"
  - "chain-of-responsibility"
  - "command"
  - "observer"
  - "behavioral-patterns"
  - "dry"
summary: "Plan de refactorizacion del codigo base aplicando Chain of Responsibility, Command y Observer para eliminar ~770 lineas de codigo repetido y desacoplar emisores de receptores"
keywords:
  - "refactor plan"
  - "behavioral patterns"
  - "chain of responsibility"
  - "command pattern"
  - "observer pattern"
  - "dry principle"
  - "prompt chain"
  - "pipeline stages"
  - "agents"
  - "generators"
changelog:
  - "2026-06-17: Plan inicial de refactorizacion con CoR + Command + Observer"
---

# 116-PLAN-DEV-BEHAVIORAL-PATTERNS-REFACTOR-1-0-DRAFT

> **Basado en analisis de:** `docs/113_REP_DEV_STATE_VS_LESSONS_1_0_DRAFT.md`,
> `docs/114_REP_DEV_ARCHITECTURAL_REVIEW_ISO12207_1_0_DRAFT.md`
> **Codigo analizado:** ~65 archivos, ~9,886 lineas, 105 tests
> **Patrones detectados:** ~770 lineas duplicadas, 3 sistemas de error
> incompatibles, 2 sistemas de validacion duplicados

## Resumen

El analisis del codigo base revelo ~770 lineas de codigo estructuralmente
identico repartidas en ~30 archivos. Este plan propone una refactorizacion
en 3 fases usando patrones de comportamiento Gang of Four para eliminar
la duplicacion, desacoplar emisores de receptores, y alinear el sistema
con la vision de orquestador SDLC del ADR-001.

### Patrones a aplicar

| Patron | Proposito | DONDE se aplica |
|---|---|---|
| **Chain of Responsibility** | Pipeline de procesamiento con handlers encadenados | Pipeline stages (10), prompt handlers (6), fallbacks (6), generadores de codigo (6) |
| **Command** | Encapsular solicitud como objeto para diferir/encolar/loggear | Handlers del chain, tools (7), act() de cada stage, generadores |
| **Observer** | Notificar a multiples receptores sin acoplar | Metricas/feedback, coordinacion entre agentes, debug callbacks, seguridad/UX como observers transversales |

### Volumen de duplicacion eliminable

| Componente | Archivos | Lineas duplicadas | Patron a aplicar |
|---|---|---|---|
| PipelineStage 5-method skeleton | 11 nodos | ~220 | CoR + Template Method |
| Prompt handler boilerplate | 6 handlers | ~120 | Command (handler como objeto) |
| ChainOrchestrator node wrapper | 6 nodos | ~180 | CoR (cadena unificada) |
| Generator `generate()` method | 6 generadores | ~30 | Command + CoR |
| Agent dual-mode process() | 5 agentes | ~60 | CoR + Command |
| StageContext / ChainContext duplicados | 2 sistemas | ~80 | CoR (unificar bus de datos) |
| `isinstance(input_data, dict)` branching | 9 stages | ~60 | CoR (tipado en handler match) |
| **TOTAL** | **~30 archivos** | **~770** | |

---

## Arquitectura objetivo

```
┌─────────────────────────────────────────────────────┐
│                   Chain of Responsibility            │
│                                                      │
│  Request → [Handler1] → [Handler2] → ... → [HandlerN]│
│             │              │                 │        │
│             ▼              ▼                 ▼        │
│          Command         Command          Command     │
│             │              │                 │        │
│             ▼              ▼                 ▼        │
│          execute()       execute()        execute()   │
│             │              │                 │        │
│             └──────────────┴─────────────────┘        │
│                              │                        │
│                              ▼                        │
│                      Observer总线                      │
│                   (metrics, feedback, events)          │
└─────────────────────────────────────────────────────┘
```

**Flujo:**

1. **Cliente** crea una `Request` (objeto Command) y la envia a la
   cabeza de la cadena CoR
2. Cada **Handler** decide si procesa la Request o la pasa al siguiente
3. El Handler ejecuta la Request via **Command.execute()**
4. El resultado se publica en el **Observer** (metricas, feedback,
   notificaciones a agentes transversales)
5. El ultimo handler de la cadena es la **red de seguridad**

---

## Fase 1 — Chain of Responsibility

### 1.1 Unificar los 6 handlers del prompt chain en una cadena CoR

**Problema:** 6 archivos (`preprocess.py`, `intent.py`, `plan.py`,
`generate.py`, `verify.py`, `format.py`) repiten ~120 lineas de
estructura identica (imports, LLM call, fallback check,
ctx.set_output).

**Solucion:** Extraer el boilerplate a una clase base `PromptHandler`
que implementa el patron CoR:

```python
class PromptHandler(ABC):
    """Handler base para la cadena de prompts.

    Cada handler puede:
    - Procesar la solicitud y retornar resultado
    - Pasar la solicitud al siguiente handler
    - Ambas (procesar parcialmente y delegar)
    """

    def __init__(self, name: str, contract: type[BaseModel],
                 fallback_name: str, llm: LLMBackend | None = None):
        self.name = name
        self.contract = contract
        self.fallback_name = fallback_name
        self._llm = llm
        self._next: PromptHandler | None = None

    def set_next(self, handler: PromptHandler) -> PromptHandler:
        self._next = handler
        return handler  # permite encadenamiento: a.set_next(b).set_next(c)

    async def handle(self, request: PromptRequest,
                     ctx: ChainContext) -> PromptResponse:
        """Procesa la solicitud o delega al siguiente."""
        result = await self._try_llm(request)
        if not result.success:
            result = await self._try_fallback(request)
        await self._publish(ctx, result)
        if self._next and result.should_delegate:
            return await self._next.handle(request, ctx)
        return result

    @abstractmethod
    async def _try_llm(self, request: PromptRequest) -> PromptResponse:
        """Intenta resolver via LLM."""

    @abstractmethod
    async def _try_fallback(self, request: PromptRequest) -> PromptResponse:
        """Intenta resolver via fallback rule-based."""

    async def _publish(self, ctx: ChainContext,
                       response: PromptResponse) -> None:
        try:
            ctx.set_output(self.name, response.data,
                           contract=self.contract)
        except Exception as exc:
            logger.warning("%s ctx.set_output failed: %s",
                           self.name, exc)
```

**Handlers concretos reducidos a:**

```python
class PreprocessHandler(PromptHandler):
    """PREPROCESS: normaliza y segmenta texto."""

    SYSTEM_PROMPT = "Eres un asistente que normaliza..."
    TEMPLATE = "Normaliza el siguiente texto:\n\n{raw_text}"
    TEMPERATURE = 0.1

    def __init__(self, llm=None):
        super().__init__("preprocess", PreprocessorContract,
                         "preprocessor_filters", llm)

    async def _try_llm(self, request: PromptRequest) -> PromptResponse:
        prompt = self.TEMPLATE.format(raw_text=request.raw_text)
        result = await self._llm.generate_structured(
            prompt=prompt, system=self.SYSTEM_PROMPT,
            output_schema=self.contract, temperature=self.TEMPERATURE,
        )
        if result.success:
            return PromptResponse(success=True,
                                  data=result.structured,
                                  should_delegate=True)
        return PromptResponse(success=False)

    async def _try_fallback(self, request: PromptRequest) -> PromptResponse:
        data = execute_fallback(self.fallback_name,
                                raw_text=request.raw_text)
        return PromptResponse(success=True, data=data,
                              should_delegate=True)
```

**Construccion de la cadena:**

```python
chain = (PreprocessHandler(llm)
         .set_next(IntentHandler(llm))
         .set_next(PlanHandler(llm))
         .set_next(GenerateHandler(llm))
         .set_next(VerifyHandler(llm))
         .set_next(FormatHandler(llm)))

response = await chain.handle(request, ctx)
```

**Archivos afectados:**
- `prompt_chain/prompts/preprocess.py` — ~78 lines → ~40 lines (-50%)
- `prompt_chain/prompts/intent.py` — ~82 lines → ~45 lines (-45%)
- `prompt_chain/prompts/plan.py` — ~109 lines → ~55 lines (-50%)
- `prompt_chain/prompts/generate.py` — ~87 lines → ~45 lines (-48%)
- `prompt_chain/prompts/verify.py` — ~96 lines → ~45 lines (-53%)
- `prompt_chain/prompts/format.py` — ~92 lines → ~45 lines (-51%)
- `prompt_chain/prompts/__init__.py` — registro simplificado
- **NUEVO:** `prompt_chain/handler_base.py` — clase base CoR (~80 lines)
- **NUEVO:** `prompt_chain/contracts.py` — PromptRequest/PromptResponse (~20 lines)

**Tests:**
- Refactorizar 33 tests existentes (cambiar llamadas a handler → chain.handle)
- +3 tests nuevos: `test_handler_chain_delegates`, `test_handler_chain_safety_net`,
  `test_handler_set_next_returns_handler`

---

### 1.2 Simplificar PipelineStage con Template Method + CoR

**Problema:** 11 PipelineStage subclases repiten ~220 lines de los 5
metodos abstractos (`receive_mission`, `analyze`, `reflect_and_plan`,
`act`, `learn_and_improve`). De estos, `analyze`, `reflect_and_plan`
y `learn_and_improve` son casi identicos en todas las subclases.

**Solucion:** Extraer los 3 metodos triviales a la clase base con
implementaciones por defecto, dejando solo `act()` como abstracto:

```python
class PipelineStage(ABC):
    def __init__(self, context: StageContext):
        self.context = context
        self._input_data: dict | None = None
        self._enriched: dict = {}

    def receive_mission(self, input_data: object) -> None:
        """Template method con hook para extraccion especifica."""
        if isinstance(input_data, dict):
            self._input_data = input_data
            self._enriched = input_data.get("enriched", {}) or {}
        else:
            self._input_data = str(input_data)  # type: ignore
            self._enriched = {}
        self._on_receive(input_data)

    def _on_receive(self, input_data: object) -> None:
        """Hook para que subclases extraigan campos especificos."""
        pass

    def analyze(self) -> AnalysisResult:
        """Default: extrae info basica del enriched."""
        obs_count = len(self._enriched) if self._enriched else 0
        return AnalysisResult(
            observations=[f"Input ready: {obs_count} enriched keys"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.1,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        """Default: plan generico."""
        return ActionPlan(
            steps=[{"action": "process", "target": "default"}],
            strategy="deterministic",
        )

    @abstractmethod
    def act(self, plan: ActionPlan) -> StageOutput:
        """UNICO metodo abstracto — logica especifica del stage."""
```

**Impacto:** Cada subclase se reduce de ~50-60 lines a ~20-30 lines.
Solo necesitan implementar `act()` y opcionalmente override `_on_receive()`.

**Archivos afectados:**
- `base_stage.py` — simplificar clase base (~64 → ~50 lines)
- Todos los 11 nodos en `nodes/` — eliminar analyze/reflect_and_plan/learn_and_improve redundantes

**Tests:** Sin cambios funcionales — los tests existentes siguen pasando.

---

### 1.3 Unificar ChainOrchestrator nodes en una cadena CoR

**Problema:** Los 6 metodos `_node_xxx` en `orchestrator.py` repiten
~180 lines de estructura identica (try/except, debug callback,
error append).

**Solucion:** Los 6 handlers convertidos a clases CoR (Fase 1.1) ya
son autocontenidos. El `ChainOrchestrator._build_graph()` puede
simplificarse a:

```python
def _build_graph(self) -> StateGraph:
    graph = StateGraph(ChainState)
    # Un solo nodo que ejecuta la cadena CoR completa
    graph.add_node("chain", self._run_chain)
    graph.set_entry_point("chain")
    graph.set_finish_point("chain")
    return graph.compile()

async def _run_chain(self, state: ChainState) -> dict:
    chain = self._build_handler_chain()
    request = PromptRequest(raw_text=state["raw_input"])
    response = await chain.handle(request, state["ctx"])
    return {"final_output": response.data}
```

O, alternativamente, eliminar LangGraph por completo para el chain
prompt y usar la cadena CoR directamente:

```python
async def run(self, raw_input: str) -> dict:
    ctx = ChainContext()
    chain = self._build_handler_chain()
    request = PromptRequest(raw_text=raw_input)
    response = await chain.handle(request, ctx)
    return response.data
```

**Archivos afectados:**
- `prompt_chain/orchestrator.py` — ~313 lines → ~80 lines (-75%)
- **NUEVO:** `prompt_chain/handler_base.py` (compartido con Fase 1.1)

**Tests:**
- Refactorizar `test_chain_orchestrator.py` (8 tests)
- +2 tests nuevos: `test_chain_build_handler_chain`, `test_chain_safety_net_catches`

---

## Fase 2 — Command Pattern

### 2.1 Prompt Handlers como Commands

**Problema:** Cada handler del prompt chain sigue el mismo flujo:
LLM → fallback → publicar. Este flujo puede encapsularse como un
Command que puede ser diferido, loggeado, o encolado.

**Solucion:** Cada `PromptHandler` concreto implementa `Command`:

```python
class Command(ABC):
    @abstractmethod
    async def execute(self) -> CommandResult: ...

class PreprocessCommand(Command):
    def __init__(self, raw_text: str, llm: LLMBackend | None = None):
        self._raw_text = raw_text
        self._llm = llm

    async def execute(self) -> CommandResult:
        handler = PreprocessHandler(self._llm)
        request = PromptRequest(raw_text=self._raw_text)
        response = await handler._try_llm(request)
        if response.success:
            return CommandResult(success=True, data=response.data)
        response = await handler._try_fallback(request)
        return CommandResult(success=response.success,
                             data=response.data,
                             fallback_used=True)
```

**Beneficio:** Los Commands pueden ser:
- **Loggeados** (CommandHistory para debug/replay)
- **Encolados** (cola de reparacion para reintentos)
- **Compuestos** (MacroCommand con varios sub-commands)
- **Deshechos** (Command+Memento para undo)

**Archivos afectados:**
- **NUEVO:** `prompt_chain/command_base.py` — Command interface (~30 lines)
- **NUEVO:** `prompt_chain/command_history.py` — CommandHistory para debug (~40 lines)
- Modificar handlers existentes para implementar Command

**Tests:**
- +4 tests: `test_command_execute`, `test_command_history`,
  `test_macro_command`, `test_command_logged_on_failure`

---

### 2.2 Tools existentes como Commands

**Problema:** 7 tools (`read_file`, `write_file`, `run_command`, etc.)
ya implementan `async def execute(params) -> ToolResult`. Tienen la
forma de Command pero sin la interfaz formal.

**Solucion:** Definir interfaz `ToolCommand(Command)` y hacer que los
7 tools la implementen explicitamente. El ToolRegistry actual es un
**Command Invoker** natural.

```python
class ToolCommand(Command):
    @abstractmethod
    async def execute(self) -> ToolResult: ...

class ReadFileCommand(ToolCommand):
    def __init__(self, path: str):
        self._path = path

    async def execute(self) -> ToolResult:
        try:
            content = await self._read_file(self._path)
            return ToolResult(success=True, data={"content": content})
        except FileNotFoundError:
            return ToolResult(success=False, error="File not found")
```

**Archivos afectados:**
- `tools/__init__.py` — registro de commands
- `tools/tool_registry.py` — Command Invoker
- `tools/read_file.py`, `tools/write_file.py`, etc. — interfaz Command

**Tests:** Sin cambios funcionales.

---

### 2.3 PipelineStage.act() como Command

**Problema:** Cada stage ejecuta su logica en `act()` pero no hay una
representacion del "comando ejecutado" que pueda ser reutilizada.

**Solucion:** `act()` retorna `StageOutput` que implementa `CommandResult`.
El pipeline completo es un `MacroCommand` que contiene N sub-commands
(uno por stage).

```python
class PipelineMacroCommand(Command):
    def __init__(self, stages: list[type[PipelineStage]]):
        self._stages = stages

    async def execute(self) -> list[CommandResult]:
        results = []
        for stage_cls in self._stages:
            stage = stage_cls(self._context)
            output = stage.execute(self._input)
            results.append(CommandResult(
                success=output.success,
                data=output.output_data,
                error=output.error,
            ))
            self._input = output.output_data
        return results
```

**Archivos afectados:**
- `orchestrator.py` — usar PipelineMacroCommand en vez de construir el grafo manualmente

---

## Fase 3 — Observer Pattern

### 3.1 Sistema de metricas como Observer

**Problema:** Las metricas estan acopladas directamente al codigo
(`base_stage.py` llama a `get_global_feedback().record_stage()`,
`ChainOrchestrator` llama a `self._optimizer.metrics.record_prompt()`).
Cada nueva metrica requiere modificar el stage.

**Solucion:** Los Stages/Handlers publican eventos en un bus Observer.
Los subscriptores (MetricsStore, PromptOptimizer, Dashboard) se
registran independientemente.

```python
class StageSubject:
    def __init__(self):
        self._observers: list[StageObserver] = []

    def attach(self, observer: StageObserver) -> None:
        self._observers.append(observer)

    def detach(self, observer: StageObserver) -> None:
        self._observers.remove(observer)

    async def notify(self, event: StageEvent) -> None:
        for observer in self._observers:
            await observer.on_event(event)

class StageObserver(ABC):
    @abstractmethod
    async def on_event(self, event: StageEvent) -> None: ...

# Observers concretos:
class MetricsObserver(StageObserver):
    async def on_event(self, event: StageEvent) -> None:
        store.record_stage(event.stage, {
            "duration": event.duration,
            "success": event.success,
            "error": event.error,
        })

class DebugObserver(StageObserver):
    async def on_event(self, event: StageEvent) -> None:
        if debug_callback:
            debug_callback(event.stage, event.output)

class PromptOptimizerObserver(StageObserver):
    async def on_event(self, event: StageEvent) -> None:
        if event.stage in ("prompt:preprocess", "prompt:intent", ...):
            store.record_prompt(event.stage, {
                "success": event.success,
                "duration": event.duration,
                "fallback_used": event.fallback_used,
            })
```

**Construccion:**

```python
subject = StageSubject()
subject.attach(MetricsObserver())
subject.attach(DebugObserver(callback))
subject.attach(PromptOptimizerObserver(optimizer))

await subject.notify(StageEvent(
    stage="preprocess",
    duration=0.5,
    success=True,
    output={"normalized": "crea modulo"},
))
```

**Archivos afectados:**
- **NUEVO:** `prompt_chain/observer_base.py` — StageSubject, StageObserver, StageEvent (~50 lines)
- `base_stage.py` — reemplazar `get_global_feedback().record_stage()` por `subject.notify()`
- `orchestrator.py` — reemplazar debug_callback directo por observer
- `feedback_loop.py` — MetricsObserver
- `metrics_store.py` — sin cambios (es el storage, no el observer)

**Tests:**
- +4 tests: `test_observer_attach_detach`, `test_observer_notifies_all`,
  `test_metrics_observer_records`, `test_debug_observer_invokes_callback`

---

### 3.2 Coordinacion entre agentes via Observer

**Problema:** Actualmente 4 agentes (PerceptionAgent, ReasoningAgent,
ExecutionAgent, ValidatorAgent) publican en SharedContext via
`self.context.publish(topic, data)`. El SupervisorAgent lee estos
topics. Esto ya es un Observer Pub/Sub pero implementado
artesanalmente.

**Solucion:** Formalizar el SharedContext como un `EventBus` (Observer
con topicos):

```python
class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = {}

    def subscribe(self, topic: str, callback: Callable) -> None:
        self._subscribers.setdefault(topic, []).append(callback)

    def unsubscribe(self, topic: str, callback: Callable) -> None:
        self._subscribers[topic].remove(callback)

    async def publish(self, topic: str, data: Any) -> None:
        for cb in self._subscribers.get(topic, []):
            await cb(data)
```

Los agentes son al mismo tiempo Subjects (publican resultados) y
Observers (reaccionan a eventos de otros agentes).

**Caso de uso:** SecurityEngineer y UXDesigner como Observers
transversales. Cuando Coder publica `"pr_created"`, SecurityEngineer
y UXDesigner reciben el evento automaticamente:

```python
event_bus.subscribe("pr_created", security_agent.review_pr)
event_bus.subscribe("pr_created", ux_agent.review_design)
```

**Archivos afectados:**
- `agents/base_agent.py` — integrar EventBus
- `agents/supervisor_agent.py` — coordinar via eventos
- **NUEVO:** `agents/event_bus.py` — EventBus (~40 lines)

**Tests:** +3 tests: `test_event_bus_publish_subscribe`,
`test_event_bus_multiple_subscribers`, `test_event_bus_unsubscribe`

---

### 3.3 Dashboard como Observer

**Problema:** El dashboard web (T4 del plan post-F5) necesita leer
metricas del MetricsStore. Actualmente esto es pull (el dashboard
consulta el store). Con Observer, el dashboard recibe actualizaciones
en tiempo real.

**Solucion:** El dashboard se registra como Observer del StageSubject.
Cuando ocurre un evento, el dashboard actualiza su estado en memoria
y notifica via WebSocket a los clientes conectados.

```python
class DashboardObserver(StageObserver):
    def __init__(self):
        self._recent_events: deque[StageEvent] = deque(maxlen=1000)
        self._ws_clients: list[WebSocket] = []

    async def on_event(self, event: StageEvent) -> None:
        self._recent_events.append(event)
        # Broadcast a clientes WebSocket
        for ws in self._ws_clients:
            await ws.send_json(event.to_dict())
```

---

## Roadmap

```
Fase 1 — Chain of Responsibility (3 sesiones)
├── 1.1 Handler base CoR + 6 handlers refactorizados  → 1 sesion
├── 1.2 PipelineStage simplificado                    → 1 sesion
└── 1.3 ChainOrchestrator simplificado                → 0.5 sesion
    └── Tests: 33 refactor + 5 nuevos

Fase 2 — Command (2 sesiones)
├── 2.1 Command interface + Prompt Commands            → 0.5 sesion
├── 2.2 Tool Commands                                  → 0.5 sesion
└── 2.3 PipelineMacroCommand                           → 0.5 sesion
    └── Tests: 4 nuevos

Fase 3 — Observer (2 sesiones)
├── 3.1 StageSubject + MetricsObserver                 → 0.5 sesion
├── 3.2 EventBus para agentes                          → 0.5 sesion
└── 3.3 DashboardObserver                              → 1 sesion
    └── Tests: 7 nuevos

Total: ~7 sesiones, ~16 tests nuevos
```

### Verificacion post-fase

```bash
# Fase 1: tests del prompt chain + orchestrator
python -m pytest compiler-bot/agentic_pipeline/tests/ \
  -k "chain or prompt or preprocess or intent or plan or generate or verify or format" -q
# Expected: 38 passed (33 refactor + 5 nuevos)

# Fase 2: tests de command + tools
python -m pytest compiler-bot/agentic_pipeline/tests/ \
  -k "command or tool" -q
# Expected: 4 passed

# Fase 3: tests de observer + event bus
python -m pytest compiler-bot/agentic_pipeline/tests/ \
  -k "observer or event" -q
# Expected: 7 passed

# Total: ~105 + 16 = 121 tests, ruff 0 errores
ruff check compiler-bot/agentic_pipeline/ && echo "OK"
ruff format --check compiler-bot/agentic_pipeline/ && echo "OK"
```

### Criterios de exito

- [ ] 0 errores ruff
- [ ] Todos los tests existentes pasan sin modificaciones (backward compat)
- [ ] Tests nuevos pasan
- [ ] `python compiler-bot/agentic -p "crea modulo" --chain` funciona igual que antes
- [ ] `python compiler-bot/agentic -p "crea modulo"` (pipeline clasico) funciona igual que antes
- [ ] Las ~770 lineas duplicadas identificadas se reducen en al menos un 60%
- [ ] No hay imports rotos ni APIs publicas modificadas
