---
id: 104
area: dev
type: GUIDE
module: AGENT_CORE
version: 1.0
status: ACTIVE
tags:
  - guide
  - runbook
  - usage
  - multiagent
  - cli
  - pipeline
  - tools
summary: "Runbook de uso operativo del sistema RECPL v2.0+ multi-agente. Describe CLI, pipeline compilador, herramientas, agentes, memoria, WorldModel, modos de ejecucion, troubleshooting y procedimientos comunes."
keywords:
  - runbook
  - uso
  - operacion
  - recpl
  - multiagent
  - cli
  - pipeline
  - troubleshooting
  - ejemplos
changelog:
  - version: 1.0
    date: 2026-06-16
    author: workflow-agent
    description: Creacion del runbook v2.0+ multi-agente
---

# Runbook: RECPL v2.0+ — Sistema Multi-Agente

> **Versión del sistema:** 2.3.0
> **Componentes:** Pipeline compilador (10 stages) + Sistema multi-agente (5 agentes) + ToolRegistry (7 herramientas)

---

## 1. Modos de Ejecucion

### 1.1 CLI — Pipeline Directo

Ejecuta el pipeline compilador completo de una instruccion:

```sh
# Prompt directo
python compiler-bot/agentic --prompt "crea un modulo de pagos en NestJS"

# Desde archivo
python compiler-bot/agentic --file instruccion.txt

# Con salida a directorio especifico
python compiler-bot/agentic -p "crea un modulo de pagos" -o ./salida

# Con streaming de progreso a stderr
python compiler-bot/agentic -p "crea un modulo de pagos" --stream
```

**Salida tipica:**
```json
{
  "output": {
    "normalized_text": "crea un modulo de pagos en nestjs [SEG] ...",
    "ast": { "node_type": "project", "children": [...] },
    "commands": [{ "task_id": "pagos", "type": "scaffold", "path": "modules/pagos" }]
  },
  "success": true
}
```

### 1.2 CLI — Modo Debug

```sh
# Trace: muestra cada etapa del pipeline
python compiler-bot/agentic -p "crea modulo" --debug trace

# Step: pausa entre etapas
python compiler-bot/agentic -p "crea modulo" --debug step

# Timing: muestra tiempo por etapa
python compiler-bot/agentic -p "crea modulo" --debug timing

# Inspect: inspecciona datos entre etapas
python compiler-bot/agentic -p "crea modulo" --debug inspect --show-output
```

### 1.3 CLI — Metricas

```sh
# Resumen en JSON
python compiler-bot/agentic --metrics json

# Resumen en tabla
python compiler-bot/agentic --metrics table
```

Salida tabla:
```
=== Pipeline Metrics Summary ===
Total records: 42
Total errors:  3
Success rate:  92.9%
Per-stage:
  intent: 5 records
  preprocessor: 5 records
  lexer: 5 records
  parser: 5 records
  ...
```

### 1.4 Modo Interactivo (AgentLoop)

```python
from agentic_pipeline.agent_loop import AgentLoop
import asyncio

async def main():
    loop = AgentLoop(max_iterations=5, interactive=True)
    await loop.run_interactive()

asyncio.run(main())
```

Inicia un REPL con prompt `> `:

```
RECPL Agent v2.0 — Escribe 'quit' para salir.
> crea un modulo de pagos
{
  "output": {
    "normalized_text": "crea un modulo de pagos ...",
    ...
  },
  "success": true
}
> quit
```

### 1.5 Modo Comando (AgentLoop)

```python
from agentic_pipeline.agent_loop import AgentLoop
import asyncio

async def main():
    loop = AgentLoop(max_iterations=3)
    result = await loop.run("crea un modulo de pagos")
    print(f"Estado: {result.status}, iteraciones: {result.iterations}")

asyncio.run(main())
```

---

## 2. Pipeline Compilador (10 Stages)

### 2.1 Arquitectura

```
INPUT "crea un modulo de pagos"
  │
  ▼
┌──────────────────────────────┐
│ 1. INTENT (PerceptionUnit)   │  ← clasifica intencion + entidades
│    - IntentClassifier        │     (o SentenceTransformerClassifier)
│    - NERExtractor            │
│    - SlotFiller              │
│    - AmbiguityDetector       │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 2. PREPROCESSOR              │  ← normaliza texto
│    - NormalizationFilter     │     + spaCy enrichment (opcional)
│    - SegmentationFilter      │     + SpacyProcessor (POS, lemma, NER)
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 3. LEXER                     │  ← DFA tokenizer
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 4. PARSER (ParserGLR)        │  ← Lark GLR parser
│    - Gramatica project/ui/   │     + WordNet disambiguation
│      data/infra              │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 5. SEMANTIC ANALYZER         │  ← type checking
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 6. IR GENERATOR              │  ← AST → IR canonico
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 7. PLANNER (ReasoningEngine) │  ← GoalTreePlanner
│    - HeuristicPlanner        │     + descomposicion estrategica
│    - TaskGraph               │
│    - GoalTreePlanner         │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 8. SYNTHESIS (ActionExecutor)│  ← genera codigo
│    - 6 generadores           │     (NestJS, Prisma, React, etc.)
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│ 9. UI GENERATOR              │  ← Builder pattern
│    - DesignTokens            │     + ResponsiveEngine
│    - UIComponentBuilder      │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│10. VALIDATOR                 │  ← Chain of Responsibility
│    - SyntaxValidator         │
│    - TypeChecker             │
│    - SecurityScanner         │
└──────────┬───────────────────┘
           ▼
       OUTPUT (JSON + archivos generados)
```

### 2.2 Formato de datos entre etapas

| Etapa | Campo clave en output_data |
|-------|---------------------------|
| PerceptionUnit | `intent`, `entities`, `slots`, `ambiguity` |
| Preprocessor | `normalized_text`, `spacy` (opcional), `token_count` |
| Lexer | `tokens` (lista de Token) |
| Parser | `ast`, `grammar` |
| SemanticAnalyzer | `symbol_table`, `validated_ast` |
| IRGenerator | `ir_tree`, `dependency_order` |
| ReasoningEngine | `tasks`, `execution_order`, `commands`, `goal_tree` |
| ActionExecutor | `generated_files`, `errors` |
| UIGenerator | `ui_components`, `design_tokens` |
| ValidatorPipeline | `validation_errors`, `warnings` |

---

## 3. ToolRegistry (7 Herramientas)

### 3.1 Uso programatico

```python
from agentic_pipeline.tool_registry import ToolRegistry
import asyncio

async def ejemplo():
    r = ToolRegistry.build_default()

    # Leer archivo
    res = await r.execute("read_file", {"path": "VERSION"})
    print(res.data["content"])

    # Escribir archivo
    res = await r.execute("write_file", {
        "path": "/tmp/test.txt", "content": "hola mundo",
    })

    # Ejecutar comando
    res = await r.execute("run_command", {"command": "ls -la"})
    print(res.data["stdout"])

    # Buscar en codigo
    res = await r.execute("search_code", {
        "pattern": "class ToolRegistry",
        "path": "compiler-bot/agentic_pipeline",
    })
    print(f"Matches: {res.data['count']}")

    # Explicar
    res = await r.execute("explain", {"message": "Esto es una prueba"})

asyncio.run(ejemplo())
```

### 3.2 Referencia rapida

| Herramienta | Parametros | Descripcion |
|-------------|-----------|-------------|
| `read_file` | `path` (string) | Lee contenido de archivo |
| `write_file` | `path`, `content` | Escribe archivo (crea directorios) |
| `run_command` | `command` (string) | Ejecuta comando shell (timeout 30s) |
| `search_code` | `pattern`, `path` (opcional) | Busca con ripgrep/grep |
| `generate_code` | `target`, `params` | Genera codigo (nestjs/prisma/react/etc) |
| `ask_user` | `question` (string) | Pregunta al usuario por stdin |
| `explain` | `message` (string) | Retorna respuesta textual |

---

## 4. ConversationalMemory

### 4.1 Uso

```python
from agentic_pipeline.memory import ConversationalMemory

mem = ConversationalMemory(storage_dir="./mi_memoria")

# Guardar historial
mem.add_history("crea modulo pagos", "modulo creado exitosamente")

# Recuperar ultimas entradas
reciente = mem.get_recent(3)
for entry in reciente:
    print(f"{entry['instruction']} → {entry['response']}")

# Contexto persistente
mem.save_context("project", "pagos")
print(mem.get_context("project"))  # "pagos"

# Multi-sesion
mem.set_session("sesion2")
mem.add_history("crea modulo auth", "ok")

# Listar sesiones
print(mem.list_sessions())

# Exportar todo
print(mem.export())
```

### 4.2 Estructura del archivo JSON

```json
{
  "historial": [
    {
      "timestamp": "2026-06-16T12:00:00Z",
      "instruction": "crea modulo pagos",
      "response": "modulo creado"
    }
  ],
  "contexto": {
    "project": "pagos"
  },
  "sesiones": ["default", "sesion2"]
}
```

---

## 5. WorldModel

### 5.1 Uso

```python
from agentic_pipeline.world_model import WorldModel

w = WorldModel()

# Escanear estado inicial
w.initialize("./")

# Registrar acciones
w.apply_action({"type": "create", "path": "modules/pagos/pagos.module.ts",
                "goal_id": "g1", "rationale": "crear modulo pagos"})

# Consultar estado
print(w.query("existe modules/pagos/pagos.module.ts?"))
# "Si, modules/pagos/pagos.module.ts existe"

print(w.query("cuantos archivos"))
# "Hay 1 archivos/directorios conocidos"

# Snapshot
print(w.snapshot())
```

---

## 6. GoalTreePlanner

### 6.1 Uso

```python
from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner
from agentic_pipeline.world_model import WorldModel

planner = GoalTreePlanner()
world = WorldModel()

# Descomponer objetivo
goal = planner.decompose(
    "crea un modulo de pagos",
    "CREATE",
    [{"name": "pagos", "type": "module"}],
    world,
)

print(f"Objetivo: {goal.description}")
print(f"Subtareas ({len(goal.subtasks)}):")
for sub in goal.subtasks:
    print(f"  - {sub.description} ({sub.status})")

# Verificar post-ejecucion
world.apply_action({"type": "mkdir", "path": "modules/pagos"})
print(f"Directorio creado: {planner.verify(goal.subtasks[0], world)}")

# Replanificar en caso de fallo
goal = planner.replan(goal, world, "error de prueba")
print(f"Replan: {goal.status}, subtarea correctiva anadida")
```

### 6.2 Templates disponibles

| Template | Subtareas | Criterios de verificacion |
|----------|-----------|---------------------------|
| `create_module` | 4 (dir, .module.ts, .controller.ts, .service.ts) | 3 (existe cada archivo) |
| `create_entity` | 1 (schema prisma) | 1 (existe schema) |
| `create_crud` | 3 (module, entity, service) | 4 (module + controller + service + schema) |
| `explain` | 0 | Ninguno |
| `generic` | 0 | Ninguno |

---

## 7. Sistema Multi-Agente

### 7.1 Arquitectura

```
Usuario
  │
  ▼
┌─────────────────────────────────────────────┐
│            SupervisorAgent                   │
│  coordina, delega y consolida               │
└────┬──────────┬──────────┬──────────────────┘
     │          │          │
     ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│Percep- │ │Reason- │ │Execution │ │Validator │
│tion    │ │ing     │ │Agent     │ │Agent     │
│Agent   │ │Agent   │ │          │ │          │
└────────┘ └────────┘ └──────────┘ └──────────┘
  spaCy      Goal        Tool      WorldModel
  ST         Tree        Registry  query
  WordNet    Planner
```

### 7.2 Flujo completo

```python
from agentic_pipeline.agents.base_agent import SharedContext, Task
from agentic_pipeline.agents.perception_agent import PerceptionAgent
from agentic_pipeline.agents.reasoning_agent import ReasoningAgent
from agentic_pipeline.agents.execution_agent import ExecutionAgent
from agentic_pipeline.agents.validator_agent import ValidatorAgent
from agentic_pipeline.agents.supervisor_agent import SupervisorAgent
from agentic_pipeline.world_model import WorldModel
import asyncio

async def main():
    ctx = SharedContext()
    world = WorldModel()

    agents = {
        "perception_agent": PerceptionAgent(ctx, world),
        "reasoning_agent": ReasoningAgent(ctx, world),
        "execution_agent": ExecutionAgent(ctx, world),
        "validator_agent": ValidatorAgent(ctx, world),
    }
    supervisor = SupervisorAgent(ctx, agents)
    result = await supervisor.process(
        Task("test", "crea un modulo de pagos", "supervisor")
    )
    print(f"Exito: {result.success}")

asyncio.run(main())
```

### 7.3 Agentes disponibles

| Agente | Rol | Componentes internos |
|--------|-----|---------------------|
| `PerceptionAgent` | Analizar entrada NLP | SpacyProcessor, SentenceTransformerClassifier, WordNet |
| `ReasoningAgent` | Descomponer objetivos | GoalTreePlanner, WorldModel |
| `ExecutionAgent` | Ejecutar acciones | ToolRegistry (7 tools), WorldModel |
| `ValidatorAgent` | Verificar resultados | WorldModel.query() |
| `SupervisorAgent` | Coordinar flujo completo | Delegacion + replan |

---

## 8. Context Engineering

Cada etapa del pipeline recibe contexto optimizado segun su funcion:

```python
from agentic_pipeline.orchestrator import build_context
from agentic_pipeline.state_models import Stage

ctx = build_context(Stage.INTENT, {"history": [...]}, world)
print(ctx.task_focus)         # "parse user intent and classify"
print(ctx.relevant_history)   # solo ultimas 3 entradas
print(ctx.world_snapshot)     # solo para stages de planificacion
```

| Stage | task_focus | relevant_history | world_snapshot |
|-------|-----------|-----------------|----------------|
| INTENT/PERCEPTION | clasificar intencion | ultimas 3 | vacio |
| PLANNER/REASONING | descomponer objetivo | vacio | archivos |
| SYNTHESIS/EXECUTION | generar codigo | vacio | archivos |
| PREPROCESSOR/LEXER/PARSER | analisis sintactico | vacio | vacio |

---

## 9. Instrucciones Soportadas

### 9.1 CREATE

```
crea modulo payments
crea modulo payments en nestjs
crea un modulo de pagos en NestJS
generar modulo auth en NestJS
crear entidad productos
crea un crud de usuarios
```

### 9.2 READ

```
mostrar payments
listame los modulos existentes
muestrame el contenido del archivo
dime que archivos hay en pagos
```

### 9.3 UPDATE

```
agrega un campo email a la entidad usuario
modifica el controlador de auth
anade una nueva ruta al modulo
actualiza el schema de prisma
```

### 9.4 DELETE

```
elimina el modulo de pagos
borra la entidad temporal
quita el campo edad del schema
```

### 9.5 EXPLAIN

```
explica como funciona el pipeline
que hace este componente
dime como se conectan los stages
describe la arquitectura del sistema
```

---

## 10. Manejo de Errores

### 10.1 Errores del pipeline

| Error | Causa | Solucion |
|-------|-------|----------|
| `No tokens received from lexer` | Input vacio o solo stop words | Verificar que el prompt contiene palabras significativas |
| `Lark parse failed` | Gramatica no cubre la instruccion | Reformular con vocabulario del dominio |
| `Validation errors` | Archivos generados no pasan check | Revisar logs del validator para detalles |
| `max_iterations_reached` | No se completo en N iteraciones | Aumentar `max_iterations` o simplificar instruccion |
| `needs_clarification` | Prompt ambiguo | Usar modo `--dialog` o ser mas especifico |

### 10.2 Errores de herramientas

| Error | Causa | Solucion |
|-------|-------|----------|
| `Archivo no encontrado` | Ruta inexistente | Verificar path con `search_code` o `read_file` previo |
| `rg (ripgrep) no instalado` | Falta dependencia | `sudo apt install ripgrep` o confia en fallback a grep |
| `ni rg ni grep estan instalados` | Sin herramienta de busqueda | Instalar grep (viene en cualquier Linux) |

### 10.3 Errores de memoria

| Error | Causa | Solucion |
|-------|-------|----------|
| `FileNotFoundError` en storage | Directorio de memoria eliminado | `ConversationalMemory()` lo recrea automaticamente |
| JSON corrupto | Escritura concurrente | Usar una instancia de memoria por proceso |

---

## 11. Troubleshooting

### 11.1 El pipeline no reconoce mi instruccion

```
Problema: "crea un modulo de pagos" retorna error de parsing
Solucion:
  1. Verificar que el preprocesador normaliza correctamente:
     python -c "from agentic_pipeline.nodes.preprocessor import SpacyProcessor; p = SpacyProcessor(); print(p.process('crea modulo pagos'))"
  2. Verificar que el lexer produce tokens:
     python -c "from agentic_pipeline.nodes.lexer import Lexer; ..."
  3. Probar con --debug trace para ver cada etapa
```

### 11.2 Los tests no pasan

```
Problema: pytest muestra errores
Solucion:
  1. Ejecutar solo tests nuevos:
     python -m pytest compiler-bot/agentic_pipeline/tests/test_tool_registry.py -v
  2. Verificar dependencias:
     pip install -e "compiler-bot/agentic_pipeline[dev]"
  3. Verificar ruff:
     ruff check compiler-bot/agentic_pipeline/
```

### 11.3 Dependencias faltantes

| Dependencia | Instalacion | Notas |
|-------------|-------------|-------|
| spaCy + modelo es | `pip install spacy && python -m spacy download es_core_news_sm` | Opcional, pipeline funciona sin el |
| sentence-transformers | `pip install sentence-transformers` | Opcional, clasificacion por regex como fallback |
| nltk | `pip install nltk` | Opcional, parser usa gramatica directa como fallback |
| ripgrep | `sudo apt install ripgrep` | Opcional, fallback a grep |

### 11.4 Comandos de diagnostico

```bash
# Verificar version del sistema
python compiler-bot/agentic --version

# Verificar salud del pipeline
python -c "
from agentic_pipeline.orchestrator import AgentOrchestrator
import asyncio
async def t():
    o = AgentOrchestrator()
    r = await o.run('test')
    print(f'Pipeline OK: success={r[\"success\"]}')
asyncio.run(t())
"

# Verificar herramientas
python -c "
from agentic_pipeline.tool_registry import ToolRegistry
r = ToolRegistry.build_default()
print(f'{len(r.list_available())} herramientas: {[t[\"name\"] for t in r.list_available()]}')
"

# Verificar memoria
python -c "
from agentic_pipeline.memory import ConversationalMemory
import tempfile
m = ConversationalMemory(storage_dir=tempfile.mkdtemp())
m.add_history('test', 'ok')
print(f'Memoria OK: {len(m.get_recent(1))} entry')
"

# Verificar WorldModel
python -c "
from agentic_pipeline.world_model import WorldModel
w = WorldModel()
w.apply_action({'type': 'create', 'path': 'test.txt'})
print(f'WorldModel OK: {w.query(\"existe test.txt?\")}')
"

# Suite completa
ruff check compiler-bot/agentic_pipeline/
python -m pytest compiler-bot/agentic_pipeline/tests/ -q --tb=short
```

---

## 12. Referencia rapida de API

| Componente | Import | Uso principal |
|-----------|--------|---------------|
| AgentOrchestrator | `from agentic_pipeline.orchestrator import AgentOrchestrator` | `await orchestrator.run("prompt")` |
| AgentLoop | `from agentic_pipeline.agent_loop import AgentLoop` | `await loop.run("prompt")` |
| ToolRegistry | `from agentic_pipeline.tool_registry import ToolRegistry` | `ToolRegistry.build_default()` |
| ConversationalMemory | `from agentic_pipeline.memory import ConversationalMemory` | `mem.add_history(i, r)` |
| WorldModel | `from agentic_pipeline.world_model import WorldModel` | `w.initialize(); w.query("...")` |
| GoalTreePlanner | `from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner` | `planner.decompose(...)` |
| SupervisorAgent | `from agentic_pipeline.agents.supervisor_agent import SupervisorAgent` | `await supervisor.process(task)` |
| build_context | `from agentic_pipeline.orchestrator import build_context` | `build_context(Stage.INTENT, ctx, world)` |
| SpacyProcessor | `from agentic_pipeline.nodes.preprocessor import SpacyProcessor` | `processor.process("texto")` |
| SentenceTransformerClassifier | `from agentic_pipeline.nodes.perception_unit import SentenceTransformerClassifier` | `clf.classify("texto")` |
