---
id: "P07"
area: "DEV"
type: "PLAN"
module: "PDCA_SDLC"
version: "1.0"
status: "DRAFT"
tags: ["plan", "execution", "iso12207", "fase3", "tester", "doc-writer", "config-mgr", "pdca-engine", "hitl", "mass"]
summary: "Plan de ejecucion para Fase 3 del modulo PDCA-sdlc — agentes Tester, DocWriter, ConfigMgr, PDCA Engine, HITL Gateway, MASS optimization. SDLC completo."
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — plan de ejecucion Fase 3"
---

# Plan de Ejecucion — PDCA-sdlc Fase 3: Robustez

> **Plan base:** `docs/157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md`  
> **Fase anterior:** `docs/159_PLAN_DEV_PDCA_SDLC_F2_EXECUTION_1_0_DRAFT.md` (F2 — Expansion)  
> **Decisiones:** D1=Hibrido, D2=Adaptation->Req->Architect->Coder->..., D3=Adapter, D4=NetworkX->Neo4j (migrar en F3)

---

## Resumen

**Objetivo:** SDLC completo ISO 12207:
```
Adaptation -> Req -> Architect -> Coder -> Tester -> Verification -> Docs -> Config
                                                                         (PDCA + HITL)
```

**Duracion:** 10 dias (Dias 21-30 del proyecto total)
**Archivos nuevos:** 6 (~550 LOC)
**Tests nuevos:** ~38 (acumulado ~124)
**Dependencias externas nuevas:** `neo4j` (opcional, migracion)

---

## Tareas por Dia

### Dia 21: TesterAgent — Pruebas de Integracion

`agents/tester_agent.py`

**Logica:**
1. Recibe `code.committed` (con `module_id`, `component`, `files`)
2. Detecta el framework de testing:
   - Si el modulo fue generado por `synthesis.py` (NestJS/Prisma): busca `*.spec.ts` o `*.test.ts`
   - Si fue generado por LLM directo (Python): busca `test_*.py` o `*_test.py`
3. Ejecuta tests via subprocess:
   - `pytest` para Python
   - `npm test` o `jest` para TypeScript/NestJS
   - `--tb=short` para output conciso
4. Captura resultados: passed, failed, error, skipped
5. Si `pytest-cov` disponible: captura cobertura
6. Escribe al KG:
   - Nodo `test_suite` con resultados
   - Aristas `test.VERIFIES.component`
7. Emite: `test.executed`

**Manejo de errores:**
- Si el directorio del modulo no existe: emite `code.failed` con "module not found"
- Si no se detecta framework de testing: emite `test.executed` con passed=0, warning="no tests detected"
- Si el subprocess timeout (default 60s): emite `risk.identified` con "test_timeout"

**Tests (`test_tester_agent.py` ~5 tests):**
- `test_detect_pytest`: modulo Python con test_*.py -> pytest detectado
- `test_detect_jest`: modulo NestJS con *.spec.ts -> jest detectado
- `test_execute_tests_passing`: subprocess mock -> test.executed con passed>0
- `test_execute_tests_failing`: subprocess mock con exit code 1 -> test.executed con failed>0
- `test_no_tests_detected`: modulo sin archivos de test -> warning emitido

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_tester_agent.py -v -o "addopts="`

---

### Dia 22: TesterAgent — Cobertura y Regression

**Logica adicional:**
1. Si `pytest-cov` esta instalado: ejecuta `pytest --cov=<module> --cov-report=json`
2. Parse el reporte JSON de cobertura
3. Si la cobertura es < threshold (configurable, default 70%): emite `risk.identified` con "low_coverage"
4. **Regression detection:**
   - Compara resultados actuales vs historicos en el KG
   - Si un test que antes pasaba ahora falla: emite `risk.identified` con "regression"
   - Almacena el ultimo resultado en el nodo `test_suite`

**Tests adicionales (`test_tester_coverage.py` ~3 tests):**
- `test_coverage_above_threshold`: 80% cobertura -> no emite riesgo
- `test_coverage_below_threshold`: 50% cobertura -> risk.identified (low_coverage)
- `test_regression_detected`: test pasado->fallido -> risk.identified (regression)

**Criterio de exito:** `ruff check . && ruff format .`

---

### Dia 23: DocWriterAgent — Documentacion Automatica

`agents/doc_writer_agent.py`

**Logica:**
1. Escucha `code.committed` y `architecture.proposed`
2. Prompt Chaining (cap 1):
   - Paso 1: Leer codigo del modulo del KG (atributo `code_preview`)
   - Paso 2: Extraer interfaces, clases, funciones publicas
   - Paso 3: Generar documentacion en Markdown
   - Paso 4: Si existe `architecture.decision` asociada, incluir contexto
3. Para modulos de `synthesis.py`: generar README con instrucciones de instalacion, configuracion, y API
4. Para modulos LLM-directo: generar docstring-based docs
5. Escribe al KG:
   - Nodo `artifact` con type="documentation"
   - Arista `artifact.DOCUMENTS.module`
6. Emite: `artifact.published`

**Prompt de generacion de docs:**
```
System: You are a Technical Writer. Generate documentation for this module.
Include: overview, installation, API reference, and examples.

Module name: {module_name}
Component: {component_name}
Code: {code_preview[:2000]}
Architecture context: {arch_context}

Return Markdown.
```

**Tests (`test_doc_writer_agent.py` ~5 tests):**
- `test_doc_generated_for_module`: modulo con codigo -> artifact.published emitido
- `test_doc_includes_api_ref`: documentacion contiene seccion de API
- `test_doc_updated_on_recommit`: mismo modulo, nuevo commit -> doc actualizada
- `test_architecture_context_included`: si existe ADR asociado, se incluye en docs
- `test_no_code_no_doc`: modulo sin codigo -> no emite nada

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_doc_writer_agent.py -v -o "addopts="`

---

### Dia 24: ConfigMgmtAgent — Versionado y Lineas Base

`agents/config_mgr_agent.py`

**Logica:**
1. Escucha:
   - `code.committed` -> versiona modulo
   - `artifact.published` -> versiona artifact
   - `quality.gate.passed` -> evalua si crear linea base
2. **Versionado semantico:**
   - Mantiene contadores major.minor.patch por cada `module_id`
   - Patch: cualquier cambio
   - Minor: nuevo requisito implementado
   - Major: cambios arquitectonicos (nuevo ADR)
3. **Linea base (baseline):**
   - Cuando un conjunto de requisitos asociados a un hito tienen status "verified"
   - Crea nodo `milestone` en KG con: version, req_ids, module_ids, timestamp
   - Aristas: `milestone.PRECEDES.milestone` (orden de hitos)
4. Emite: `artifact.versioned`, `baseline.created`

**Tests (`test_config_mgr_agent.py` ~5 tests):**
- `test_version_increment_patch`: code.committed -> version patch incrementado (1.0.0 -> 1.0.1)
- `test_version_increment_minor`: nuevo requisito implementado -> minor incrementado (1.0.0 -> 1.1.0)
- `test_version_increment_major`: nuevo ADR -> major incrementado (1.0.0 -> 2.0.0)
- `test_baseline_created`: todos los reqs de un hito verificados -> baseline.created
- `test_baseline_requires_all_reqs`: falta 1 req -> baseline NO creado aun

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_config_mgr_agent.py -v -o "addopts="`

---

### Dia 25: PDCA Engine — Ciclo de Mejora Continua

`core/pdca_engine.py`

**Logica:**
El PDCA engine no es un agente mas. Es un **bucle interno** que ejecuta MASS periodicamente.

```python
class PDCAEngine:
    """Motor PDCA: recolecta metricas y ejecuta MASS optimization.

    No es un agente del bus. Es un proceso separado que corre
    en background y publica eventos de optimizacion.
    """

    def __init__(self, event_bus, kg, registry, llm):
        self.event_bus = event_bus
        self.kg = kg
        self.registry = registry
        self.llm = llm
        self._metrics = defaultdict(lambda: defaultdict(int))

    async def record_event(self, event: Event):
        """Registra metricas de cada evento del bus."""
        source = event.source
        self._metrics[source]["total"] += 1
        if "failed" in event.topic or "risk" in event.topic:
            self._metrics[source]["failures"] += 1
        if "passed" in event.topic or "complete" in event.topic:
            self._metrics[source]["successes"] += 1
        # Latencia: timestamp actual - event.timestamp
        latency = time.time() - event.timestamp
        self._metrics[source]["total_latency"] += latency

    async def run_mass_optimization(self):
        """Ejecuta MASS (Multi-Agent System Search, cap 17).

        3 etapas:
        1. Block-Level: identificar agentes con alta tasa de fallo
           -> optimizar su prompt via LLM
        2. Workflow Topology: evaluar si la topologia actual es optima
           ->建议 cambios de suscripciones entre agentes
        3. Workflow-Level: optimizar prompts del sistema completo
        """
        report = {"block_optimizations": [], "topology_suggestions": []}

        for agent_id, metrics in self._metrics.items():
            total = metrics["total"]
            if total == 0:
                continue
            fail_rate = metrics["failures"] / total
            if fail_rate > 0.3:  # >30% fallo -> optimizar
                opt = await self._optimize_block(agent_id, fail_rate)
                report["block_optimizations"].append(opt)

        # Publicar reporte
        await self.event_bus.publish(Event(
            topic="system.pdca.optimization.complete",
            source="pdca-engine",
            data=report
        ))

    async def _optimize_block(self, agent_id: str, fail_rate: float) -> dict:
        """Stage 1 MASS: optimizar prompt de un agente."""
        manifest = self.registry._agents.get(agent_id)
        if not manifest:
            return {"agent_id": agent_id, "status": "no_manifest"}
        return {"agent_id": agent_id, "fail_rate": fail_rate,
                "status": "optimized"}
```

**Integracion:** El PDCAEngine se registra como listener en el EventBus (recibe todos los eventos para metricas). Corre MASS cada N eventos (configurable, default: cada 100 eventos) o cada N horas.

**Tests (`test_pdca_engine.py` ~6 tests):**
- `test_metrics_recorded`: cada evento registrado incrementa contadores
- `test_mass_block_optimization`: agente con 50% fallo -> optimizacion block-level
- `test_mass_no_optimization_needed`: todos los agentes < 30% fallo -> no hay optimizaciones
- `test_mass_topology_suggestion`: patron de eventos suboptimo -> sugerencia de topologia
- `test_optimization_event_emitted`: tras MASS, evento system.pdca.optimization.complete emitido
- `test_metrics_empty`: sin eventos -> metrics vacio

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_pdca_engine.py -v -o "addopts="`

---

### Dia 26: HITL Gateway — Intervencion Humana

`agents/hitl_gateway.py`

**Logica:**
1. Escucha `human.input.needed` (emitido por cualquier agente cuando necesita decision humana)
2. Presenta al usuario via CLI:
```
[HITL] Agente: architect-agent-v1
Proyecto: p-001
Contexto: Se requiere decision arquitectonica sobre el componente auth
Opcion A: Microservicio independiente (recomendado)
Opcion B: Modulo dentro del monolitico
Impacto: A anade ~3d de desarrollo, B es mas rapido pero menos escalable

Su decision (A/B/skip): _
```
3. Recibe la decision del usuario
4. Publica `human.decision.submitted` con la decision
5. El agente que solicito la HITL recibe el evento y continua

**Niveles de autonomia (cap 13):**
- `approval`: el agente propone, humano solo aprueba/rechaza
- `advisory`: el agente da opciones con recomendacion, humano elige
- `full`: el agente presenta el problema, humane define la solucion

**Configuracion en `config.yaml`:**
```yaml
hitl:
  enabled: true
  default_mode: "advisory"
  modes:
    architecture_review: "approval"
    security_audit: "full"
    requirement_clarification: "advisory"
```

**Tests (`test_hitl_gateway.py` ~5 tests):**
- `test_human_input_requested`: agente emite human.input.needed -> gateway lo recibe
- `test_human_decision_approved`: humano responde "A" -> decision.submitted con opcion A
- `test_human_decision_skipped`: humano responde "skip" -> decision.submitted con "skipped"
- `test_hitl_timeout`: humano no responde en N segundos -> timeout y agente continua con default
- `test_hitl_disabled`: hitl.enabled=false -> gateway ignora eventos

**Criterio de exito:** `ruff check . && ruff format . && python -m pytest tests/test_hitl_gateway.py -v -o "addopts="`

---

### Dia 27: Migracion Knowledge Graph a Neo4j

**Objetivo:** Migrar de NetworkX (memoria) a Neo4j (persistente).

**Clase `Neo4jKnowledgeGraph`:**
- Implementa la misma interfaz que `KnowledgeGraph` (duck typing)
- Metodos: `add_node`, `get_node`, `update_node`, `add_edge`, `get_outgoing`, `get_incoming`, `get_trace`, `query`
- Internamente usa `neo4j` driver con queries Cypher

```python
class Neo4jKnowledgeGraph:
    """Adapter sobre Neo4j. Misma interfaz que KnowledgeGraph."""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="..."):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def add_node(self, node: Node) -> None:
        with self._driver.session() as session:
            session.run(
                "MERGE (n:Node {id: $id}) "
                "SET n.type = $type, n.properties = $props, "
                "n.created_by = $created_by, n.created_at = $created_at",
                id=node.id, type=node.node_type.value,
                props=json.dumps(node.properties),
                created_by=node.created_by, created_at=node.created_at
            )
    # ... (mismos metodos que KnowledgeGraph)
```

**Configuracion en `config.yaml`:**
```yaml
knowledge_graph:
  backend: "neo4j"  # networkx | neo4j
  neo4j:
    uri: "bolt://localhost:7687"
    user: "neo4j"
    # password via env: NEO4J_PASSWORD
```

**Tests (`test_neo4j_kg.py` ~4 tests):**
- `test_add_and_get_node`: crear nodo, recuperarlo
- `test_add_edge_and_trace`: crear aristas, get_trace encuentra camino
- `test_query_by_type`: query filtrado por node_type
- `test_update_node_properties`: actualizar propiedades persiste

**Nota:** Si Neo4j no esta disponible, el sistema usa NetworkX como fallback automatico.

**Criterio de exito:** `ruff check . && ruff format .`

---

### Dia 28: Integracion F3 — Full SDLC

Integracion de todos los componentes en `main.py`.

**main.py actualizado (todos los agentes):**
```python
async def main():
    bus = AsyncEventBus()
    kg = Neo4jKnowledgeGraph() if config.kg_backend == "neo4j" else KnowledgeGraph()
    registry = CapabilityRegistry()
    llm = LLMClient(config)
    qg = QualityGate(bus, kg)
    swarm = SwarmDetector(bus, kg)

    # Registrar gates
    qg.register_gate("requisitos_tienen_aceptacion", ...)
    qg.register_gate("componentes_tienen_trazabilidad", ...)
    qg.register_gate("modulos_tienen_trazabilidad", ...)

    # PDCA engine (background)
    pdca = PDCAEngine(bus, kg, registry, llm)
    bus.subscribe("proyecto.{id}.>", pdca.record_event)

    # 8 agentes
    agents = [
        AdaptationAgent(ctx, llm),
        RequirementsAnalystAgent(ctx, llm),
        ArchitectAgent(ctx, llm),
        CoderAgent(ctx, llm),
        TesterAgent(ctx),
        VerificationAgent(ctx, llm, qg),
        DocWriterAgent(ctx, llm),
        ConfigMgmtAgent(ctx),
        ProjectTracker(ctx),
        HITLGateway(ctx),
    ]
    for a in agents:
        await a.start()

    # Swarm
    bus.subscribe("proyecto.{id}.>", swarm.on_event)

    # PDCA schedule (cada 100 eventos)
    event_count = 0
    while True:
        await asyncio.sleep(5)
        event_count += 1
        if event_count % 100 == 0:
            await pdca.run_mass_optimization()
        await swarm.check_timeouts()
```

**Tests de integracion (`test_integration_f3.py` ~8 tests):**
- `test_full_sdlc_simple`: proyecto SIMPLE -> fast-path: 3 agentes, quality gates pasan, docs generados, versionado
- `test_full_sdlc_complex`: proyecto COMPLEX -> deep-path: 8+ agentes, swarm, quality gates, baseline creado
- `test_pdca_optimization_trigger`: tras N eventos, MASS se ejecuta y emite reporte
- `test_hitl_intervention_during_flow`: agente solicita input humano, gateway responde, flujo continua
- `test_artifact_versioning`: cada code.committed incrementa version del artifacto
- `test_baseline_created_on_milestone`: todos los reqs verificados -> baseline.created
- `test_regression_detected`: test que falla -> risk.identified -> verification lo captura
- `test_full_traceability_chain`: goal -> requirement -> component -> module -> test -> artifact

---

### Dia 29: Pruebas de Carga y Casos Borde

**Pruebas de carga (~4 tests):**
- `test_concurrent_projects`: 3 proyectos simultaneos, cada uno con 10 requisitos
- `test_high_event_throughput`: 1000 eventos en 10s, el bus no pierde ninguno
- `test_swarm_50_concurrent_expectations`: 50 requisitos en swarm simultaneo
- `test_pdca_metrics_under_load`: metricas correctas bajo carga

**Casos borde (~4 tests):**
- `test_all_agents_crash_and_recover`: todos los agentes se detienen y reinician via replay
- `test_empty_project`: " " (espacio) como input -> manejado sin crash
- `test_llm_all_failbacks_exhausted`: todos los LLM caidos -> sistema opera en modo degraded
- `test_quality_gate_all_fail`: todos los gates fallan -> flujo se detiene correctamente

---

### Dia 30: Documentacion Final y Cierre

**Documentacion:**
- Docstrings completos en 100% de clases y metodos publicos
- README del modulo `PDCA-sdlc/README.md` con:
  - Vis general de la arquitectura
  - Como anadir un nuevo agente
  - Como configurar modelos LLM
  - Ejemplos de uso (fast-path + deep-path)
- Actualizar `CHANGELOG.md` con entrada para PDCA-sdlc v1.0.0

**Validacion final:**
```bash
ruff check .          # 0 errors
ruff format .         # sin cambios
python -m pytest tests/ -v -o "addopts="  # ~124 tests PASS

# Smoke tests
python -m compiler-bot.PDCA-sdlc.main "CRUD de productos" --fast
python -m compiler-bot.PDCA-sdlc.main "Sistema multi-tenant con OAuth2" --deep
python -m compiler-bot.PDCA-sdlc.main "API REST para inventario" --interactive
```

**Commit final:**
```
feat(PDCA-sdlc): Fase 3 robustez — SDLC ISO 12207 completo

- TesterAgent: ejecucion de tests, cobertura, deteccion de regression
- DocWriterAgent: documentacion automatica sincronizada con codigo
- ConfigMgmtAgent: versionado semantico, lineas base
- PDCAEngine: ciclo de mejora continua con MASS optimization
- HITLGateway: intervencion humana en puntos de decision
- Migracion Knowledge Graph: NetworkX -> Neo4j (con fallback)
- 124 tests, 0 ruff errors
```

---

## Resumen de Archivos F3

| Archivo | LOC estimado | Tests |
|---------|-------------|-------|
| `agents/tester_agent.py` | 130 | 8 |
| `agents/doc_writer_agent.py` | 100 | 5 |
| `agents/config_mgr_agent.py` | 90 | 5 |
| `core/pdca_engine.py` | 100 | 6 |
| `agents/hitl_gateway.py` | 80 | 5 |
| `core/neo4j_kg.py` | 60 | 4 |
| `tests/test_integration_f3.py` | 120 | 12 |
| `PDCA-sdlc/README.md` | 80 | — |
| Actualizaciones `main.py`, `config.yaml` | 40 | — |
| **Total** | **~800** | **~38** |

---

## Resumen Acumulado Total

| Fase | Dias | LOC | Tests | Hito |
|------|------|-----|-------|------|
| F1 — Fundacion | 10 | ~930 | 44 | Fast-Path funcional |
| F2 — Expansion | 10 | ~640 | 42 | Deep-Path con Quality Gates |
| F3 — Robustez | 10 | ~800 | 38 | SDLC completo + PDCA + HITL |
| **Total** | **30** | **~2370** | **~124** | **Sistema ISO 12207 completo** |

---

## Riesgos Especificos F3

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **Neo4j no disponible** en entorno de desarrollo | Alta | Medio | Fallback automatico a NetworkX. Solo se pierde persistencia entre reinicios. |
| **Subprocess de tests lento** (pytest/npm) | Alta | Medio | Timeout configurable (default 60s). Si expira, test.executed con error. |
| **HITL bloquea el flujo** si el humano no responde | Media | Alto | Timeout por decision (configurable). Si expira, agente continua con default. |
| **PDCA MASS costoso** (muchas llamadas LLM) | Media | Bajo | MASS se ejecuta cada 100 eventos (no cada evento). Modelo "flash" para optimizacion. |
| **DocWriter duplica docs** si hay muchos commits | Baja | Bajo | DocWriter solo regenera si el codigo cambio. Cache por hash del modulo. |

---

*Plan de ejecucion Fase 3 basado en `docs/157_PLAN_DEV_PDCA_SDLC_IMPLEMENTATION_1_0_DRAFT.md`. Fecha: 2026-06-19.*
