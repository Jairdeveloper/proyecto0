---
id: 194
area: dev
type: rep
module: pdca-sdlc
version: 1.0
status: DRAFT
tags:
  - report
  - implementation
  - architect-agent
  - iso-12207
  - component-architecture
  - tree-of-thought
  - pdca-sdlc
summary: "Implementacion de ArchitectAgent para diseno de componentes (Dia 11 del plan F2). Agent recibe requirement.created, clasifica complejidad, usa LLM con Tree-of-Thought para proyectos MODERATE/COMPLEX, fallback flat para LLM caido, escribe componentes + ADRs al KG y emite architecture.proposed."
keywords:
  - reporte
  - implementacion
  - architect-agent
  - diseno-componentes
  - architecture-decision-records
  - tree-of-thought
  - iso-12207
  - pdca-sdlc
  - fase-2
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Implementacion de ArchitectAgent — diseno de componentes via LLM con ToT, fallback flat, 8 tests
---

# Reporte de Implementacion: ArchitectAgent — Diseno de Componentes

> **Plan de referencia:** `159_PLAN_DEV_PDCA_SDLC_F2_EXECUTION_1_0_DRAFT.md` (Dia 11, lineas 43-90)
> **Archivo creado:** `compiler-bot/pdca_sdlc/agents/architect_agent.py`
> **Tests:** `compiler-bot/pdca_sdlc/tests/test_architect_agent.py` (8 tests)
> **Guia de estilo:** `070_GUIDE_DEV_PYTHON_STYLE_1_0_DRAFT.md`

---

## Resumen

Se implemento el `ArchitectAgent`, responsable de disenar la arquitectura de
componentes a partir de los requisitos generados por el `RequirementsAnalystAgent`.
El agente sigue el estandar ISO 12207 (proceso 6.2 — Diseno Arquitectonico) y
utiliza un enfoque Tree-of-Thought para explorar variantes arquitectonicas en
proyectos MODERATE y COMPLEX.

## Arquitectura del Agente

### Ciclo de vida

```
requirement.created
    ↓
ArchitectAgent.handle_event()
    ├── Lee complejidad del goal node (KG)
    ├── SIMPLE → fast-path skip (no emite nada)
    └── MODERATE/COMPLEX
        ├── Carga requisitos del KG
        ├── LLM con Tree-of-Thought (2-3 variantes)
        │   ├── MODERATE → flash (temp 0.3)
        │   └── COMPLEX → pro (temp 0.2)
        ├── Fallback: flat (1 componente por requisito)
        ├── Escribe nodos component + architecture_decision al KG
        ├── Crea aristas IMPLEMENTS component → requirement
        └── Emite architecture.proposed
```

### Componentes implementados

| Componente | Archivo | Proposito |
|---|---|---|
| `ArchitectAgent` | `architect_agent.py` | Clase principal del agente |
| `_design_architecture()` | `architect_agent.py` | Orquesta el diseno via LLM con fallback |
| `_llm_for_complexity()` | `architect_agent.py` | Selecciona modelo/temperatura segun complejidad |
| `_validate_components()` | `architect_agent.py` | Valida y deduplica componentes del LLM |
| `_validate_decisions()` | `architect_agent.py` | Valida ADRs (title, context, decision, consequences) |
| `_fallback_flat()` | `architect_agent.py` | Genera 1 componente por requisito deterministicamente |
| `_derive_component_name()` | `architect_agent.py` | Deriva nombre de componente desde texto del requisito |
| `_write_components()` | `architect_agent.py` | Persiste nodos component + aristas IMPLEMENTS al KG |
| `_write_decisions()` | `architect_agent.py` | Persiste nodos architecture_decision al KG |
| `TestArchitectAgent` | `test_architect_agent.py` | Suite de 8 tests |
| `_FakeLLM` | `test_architect_agent.py` | Stub de LLM con respuesta controlada |
| `_FailingLLM` | `test_architect_agent.py` | Stub de LLM que simula fallo |
| `_CountingLLM` | `test_architect_agent.py` | Stub de LLM con N componentes configurables |

### Arbol de archivos

```
compiler-bot/pdca_sdlc/
├── agents/
│   ├── architect_agent.py       ← NUEVO (427 lineas)
│   └── ... (agentes existentes)
└── tests/
    ├── test_architect_agent.py  ← NUEVO (418 lineas, 8 tests)
    └── ... (tests existentes)
```

## Prompt Tree-of-Thought

El prompt de sistema sigue la especificacion del plan:

```
System: You are a Software Architect following ISO 12207.
Given these requirements, design a component architecture.
Explore 2-3 architectural variants and select the best one.

Return JSON:
{components: [{name, tech_stack, interfaces, implements_requirements}],
 decisions: [{title, context, decision, consequences}]}

Requirements: {reqs_json}
```

### Cobertura de modelos

| Escenario | Modelo | Temp | Max Tokens |
|---|---|---|---|
| Proyecto MODERATE | flash | 0.3 | 4096 |
| Proyecto COMPLEX | pro | 0.2 | 8192 |
| Fallback (LLM caido) | Flat: 1 componente por requisito | — | — |

## Estructura del Knowledge Graph

### Nodos creados

```yaml
- node_type: component
  id: "comp-{name}-{project_id}"
  properties:
    name: str
    tech_stack: list[str]
    interfaces: list[str]
    implements_requirements: list[str]

- node_type: architecture_decision
  id: "adr-{project_id}-{nnn}"
  properties:
    title: str
    context: str
    decision: str
    consequences: str
```

### Aristas creadas

```yaml
- source_type: component
  target_type: requirement
  edge_type: implements
```

### Evento emitido

```yaml
topic: "architecture.proposed"
data:
  component_ids: list[str]
  decision_ids: list[str]
  components: list[dict]
  requirement_ids: list[str]
```

## Decisiones de Diseno

1.  **Custom LLM injection**: Se agrego el flag `_custom_llm` para respetar
    el LLM inyectado en tests. Cuando no hay inyeccion, `_design_architecture`
    crea el LLM apropiado segun la complejidad del proyecto.

2.  **Deduplicacion de componentes**: `_validate_components()` y
    `_fallback_flat()` aseguran que no se generen dos componentes con el
    mismo nombre ignorando mayusculas/minusculas.

3.  **Validacion de ADRs**: Solo se persisten ADRs que tengan todos los
    campos obligatorios no vacios (title, context, decision, consequences).

4.  **Fast-path SIMPLE**: Cuando la complejidad del proyecto es "simple",
    el agente retorna inmediatamente sin emitir `architecture.proposed`,
    permitiendo que el `CoderAgent` reciba `requirement.created` directamente.

## Tests

| Test | Que verifica | Estado |
|---|---|---|
| `test_fast_path_skip` | Proyecto SIMPLE → no emite `architecture.proposed` | PASS |
| `test_fallback_flat` | LLM caido → arquitectura flat (1 componente/requisito) | PASS |
| `test_component_generation` | 4 requisitos → 2-3 componentes con nombres validos | PASS |
| `test_traceability_edges` | Cada componente tiene arista IMPLEMENTS >= 1 requisito | PASS |
| `test_adr_creation` | Cada ADR tiene title, context, decision, consequences | PASS |
| `test_complex_project_architecture` | COMPLEX produce mas componentes que MODERATE | PASS |
| `test_no_duplicate_components` | Mismo requisito no genera 2 componentes iguales | PASS |
| `test_architecture_proposed_event` | Evento contiene component_ids y decision_ids | PASS |

### Resultado de verificacion

```text
$ ruff check .
All checks passed!

$ ruff format . --check
34 files already formatted

$ python -m pytest tests/test_architect_agent.py -v -o "addopts="
8 passed in 0.12s
```

## Riesgos y Limitaciones

1.  **LLM mock en Fase 1**: El LLMClient actualmente solo tiene backend
    mock. La integracion con modelos reales (deepseek-chat, deepseek-reasoner)
    requiere configurar el backend en config.yaml y habilitar el agente en
    produccion.

2.  **Tree-of-Thought supervisado**: El ToT se implementa via prompt, no
    como un proceso multi-paso autonomo. La exploracion de variantes depende
    enteramente de la capacidad del LLM para auto-evaluarse.

3.  **Sin validacion cruzada**: No hay un agente revisor que valide la
    arquitectura propuesta contra los requisitos originales (previsto para
    Fase 3 con VerificationAgent).

4.  **Flat fallback sin contexto**: La arquitectura flat no considera
    dependencias entre requisitos ni patrones de diseno. Es un mecanismo
    de supervivencia, no una arquitectura real.

## Proximos Pasos

1.  Habilitar `architect_agent.enabled: true` en `config.yaml` cuando el
    LLM este configurado con backends reales.
2.  Implementar VerificationAgent (Dia 12 del plan F2) para validacion
    cruzada de arquitectura.
3.  Integrar con ProjectTracker para trazabilidad de decisiones
    arquitectonicas a lo largo del ciclo de vida.
4.  Evaluar si el ToT necesita un loop multi-paso con evaluacion explicita
    de variantes (en lugar de confiar en el prompt unico).

---

*Reporte generado el 2026-06-22 por Sisyphus.*
