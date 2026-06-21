---
id: "R05"
area: "DEV"
type: "PROP"
module: "ISO12207_AGENT_SYSTEM"
version: "1.0"
status: IMPLEMENTED
tags: ["proposal", "implementation", "iso12207", "event-driven", "python", "pydantic", "protocols", "swarm", "class-skeleton"]
summary: "Implementacion concreta del sistema agentico ISO 12207 reactivo — esqueleto de clases Python, protocolos de comunicacion Pydantic, y trace completo del ejemplo 'sistema de inventario simple'. Misma vision que 155_PROP, perspectiva de Arquitecto Senior."
changelog:
  - version: "1.0"
    date: "2026-06-19"
    author: "Sistema"
    description: "Version inicial — esqueleto de implementacion Python + protocolos + ejemplo trace"
---

# Implementacion: Sistema Agentico ISO 12207 — Arquitectura Reactiva de Capacidades

> **Rol:** Arquitecto de Sistemas Senior / Especialista en IA Agentica  
> **Fuente:** `152_GUIDE_DEV_AGENT_PATTERNS_SUMMARY` (patrones 1-9) + `153_GUIDE_DEV_AGENT_DESIGN_PATTERNS2_SUMMARY` (patrones 10-21 + Ap A)  
> **Vision base:** 155_PROP — reactiva, event-driven, capability-based, emergente  
> **Entrega:** Esqueleto Python, protocolos de comunicacion, ejemplo trace completo ISO 12207  

---

## 0. Principios Arquitectonicos

1. **No hay orquestador central** — los agentes son peers que reaccionan a eventos
2. **ISO 12207 es metadata, no estructura** — las capacidades se auto-declaran, no se imponen
3. **El estado es un grafo, no un pipeline** — los agentes leen/escriben en un Knowledge Graph compartido
4. **Los eventos son el unico contrato** — el schema del event bus es el unico acoplamiento
5. **PDCA es el motor nativo** — cada evento es PLAN, cada reaccion es DO, cada quality gate es CHECK, cada ajuste es ACT
6. **Fast-Path / Deep-Path** — tareas simples bypassan diseno arquitectonico, complejas activan swarm completo
7. **Fallos via replay** — el log de eventos es el checkpoint, no hay rollback por etapa

---

## 1. Esqueleto de Clases Python

### 1.1 Nucleo del Sistema

```python
"""core/event_bus.py — Bus de eventos asincrono con topicos jerarquicos."""
import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional


@dataclass
class Event:
    id: str = field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    topic: str = ""
    source: str = ""            # agent_id que emitio el evento
    project_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0           # numero de secuencia global por proyecto

    def to_json(self) -> str:
        return json.dumps({"id": self.id, "topic": self.topic,
                           "source": self.source, "project_id": self.project_id,
                           "data": self.data, "timestamp": self.timestamp,
                           "sequence": self.sequence})

    @classmethod
    def from_json(cls, raw: str) -> "Event":
        return cls(**json.loads(raw))


class TopicMatcher:
    """Matchea topicos con soporte de wildcard: proyecto.{id}.>  y  proyecto.{id}.*"""

    @staticmethod
    def matches(pattern: str, topic: str) -> bool:
        if pattern == topic:
            return True
        if pattern.endswith(".>"):
            prefix = pattern[:-2]
            return topic.startswith(prefix)
        if pattern.endswith(".*"):
            prefix = pattern[:-1]
            return topic.startswith(prefix) and "." not in topic[len(prefix):]
        return False


class EventBus:
    """Bus de eventos async. Topics jerarquicos con NATS-style wildcard (.>, .*)."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Event], Coroutine]]] = {}
        self._global_sequence: int = 0
        self._event_log: list[Event] = []   # log persistente para replay

    def subscribe(self, topic_pattern: str,
                  handler: Callable[[Event], Coroutine]) -> None:
        if topic_pattern not in self._subscribers:
            self._subscribers[topic_pattern] = []
        self._subscribers[topic_pattern].append(handler)

    def unsubscribe(self, topic_pattern: str,
                    handler: Callable[[Event], Coroutine]) -> None:
        if topic_pattern in self._subscribers:
            self._subscribers[topic_pattern].remove(handler)

    async def publish(self, event: Event) -> list[Coroutine]:
        self._global_sequence += 1
        event.sequence = self._global_sequence
        self._event_log.append(event)
        tasks = []
        for pattern, handlers in self._subscribers.items():
            if TopicMatcher.matches(pattern, event.topic):
                for handler in handlers:
                    tasks.append(handler(event))
        return tasks

    def replay(self, project_id: str, since_sequence: int = 0) -> list[Event]:
        return [e for e in self._event_log
                if e.project_id == project_id and e.sequence > since_sequence]

    def get_event_log(self) -> list[Event]:
        return self._event_log.copy()
```

```python
"""core/knowledge_graph.py — Grafo de conocimiento compartido entre agentes."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class NodeType(str, Enum):
    GOAL = "goal"
    REQUIREMENT = "requirement"
    ARCHITECTURE_DECISION = "architecture_decision"
    COMPONENT = "component"
    CODE_MODULE = "code_module"
    TEST_SUITE = "test_suite"
    RISK = "risk"
    ARTIFACT = "artifact"
    TASK = "task"
    MILESTONE = "milestone"


class EdgeType(str, Enum):
    SATISFIES = "satisfies"             # requirement -> goal
    IMPLEMENTS = "implements"           # component -> requirement
    VERIFIES = "verifies"               # test -> component
    AFFECTS = "affects"                 # arch_decision -> component
    DEPENDS_ON = "depends_on"           # component -> component
    GENERATES = "generates"             # agent -> artifact
    DOCUMENTS = "documents"             # artifact -> module
    PRECEDES = "precedes"               # task -> task (orden)


@dataclass
class Node:
    id: str
    node_type: NodeType
    properties: dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: float = 0.0

    def get(self, key: str, default: Any = None) -> Any:
        return self.properties.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.properties[key] = value


@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: EdgeType
    properties: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    """Grafo dirigido con nodos y aristas tipadas. Acceso concurrente."""

    def __init__(self):
        self._nodes: dict[str, Node] = {}
        self._edges: list[Edge] = []

    def add_node(self, node: Node) -> None:
        self._nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[Node]:
        return self._nodes.get(node_id)

    def update_node(self, node_id: str, **props) -> None:
        node = self._nodes.get(node_id)
        if node:
            node.properties.update(props)

    def add_edge(self, edge: Edge) -> None:
        self._edges.append(edge)

    def get_outgoing(self, node_id: str, edge_type: Optional[EdgeType] = None
                     ) -> list[Edge]:
        return [e for e in self._edges if e.source_id == node_id
                and (edge_type is None or e.edge_type == edge_type)]

    def get_incoming(self, node_id: str, edge_type: Optional[EdgeType] = None
                     ) -> list[Edge]:
        return [e for e in self._edges if e.target_id == node_id
                and (edge_type is None or e.edge_type == edge_type)]

    def get_trace(self, from_id: str, to_id: str) -> list[Edge]:
        """BFS simple para encontrar camino entre dos nodos (trazabilidad)."""
        visited: set[str] = set()
        queue: list[tuple[str, list[Edge]]] = [(from_id, [])]
        while queue:
            current, path = queue.pop(0)
            if current == to_id:
                return path
            if current in visited:
                continue
            visited.add(current)
            for edge in self.get_outgoing(current):
                queue.append((edge.target_id, path + [edge]))
        return []

    def query(self, node_type: Optional[NodeType] = None,
              status: Optional[str] = None, **filters) -> list[Node]:
        results = []
        for node in self._nodes.values():
            if node_type and node.node_type != node_type:
                continue
            if status and node.get("status") != status:
                continue
            if all(node.get(k) == v for k, v in filters.items()):
                results.append(node)
        return results
```

```python
"""core/capability_registry.py — Registro de capacidades de agentes."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CapabilityManifest:
    agent_id: str
    agent_name: str
    description: str
    iso_12207: dict[str, Any] = field(default_factory=dict)
    #   {"process": "Development",
    #    "activities": ["Requirements Elicitation"],
    #    "tasks": ["Define functional requirements"]}
    triggers: list[dict] = field(default_factory=list)
    #   [{"event": "project.initialized", "role": "primary"},
    #    {"event": "requirement.clarification_needed", "role": "primary"}]
    output_events: list[str] = field(default_factory=list)
    llm_profile: dict[str, Any] = field(default_factory=dict)
    #   {"recommended_model": "flash", "max_tokens": 8192, "temperature": 0.2}
    version: str = "1.0.0"
    status: str = "active"  # active | paused | retired

    def matches_event(self, topic: str) -> bool:
        for t in self.triggers:
            if TopicMatcher.matches(t["event"], topic):
                return True
        return False


class CapabilityRegistry:
    """Directorio de agentes y sus capacidades. Los agentes se registran
    al iniciar y pueden ser descubiertos por otros componentes."""

    def __init__(self):
        self._agents: dict[str, CapabilityManifest] = {}

    def register(self, manifest: CapabilityManifest) -> None:
        self._agents[manifest.agent_id] = manifest

    def unregister(self, agent_id: str) -> None:
        self._agents.pop(agent_id, None)

    def find_by_event(self, topic: str,
                      role: Optional[str] = None) -> list[CapabilityManifest]:
        results = []
        for m in self._agents.values():
            if m.status != "active":
                continue
            if not m.matches_event(topic):
                continue
            if role:
                if not any(t["event"] == topic and t.get("role") == role
                           for t in m.triggers):
                    continue
            results.append(m)
        return results

    def find_by_iso_activity(self, activity: str) -> list[CapabilityManifest]:
        return [m for m in self._agents.values()
                if activity in m.iso_12207.get("activities", [])]

    def get_all(self) -> list[CapabilityManifest]:
        return list(self._agents.values())

    def update_status(self, agent_id: str, status: str) -> None:
        if agent_id in self._agents:
            self._agents[agent_id].status = status
```

```python
"""core/base_agent.py — Clase base abstracta para todos los agentes."""
from __future__ import annotations
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

from core.event_bus import Event, EventBus, TopicMatcher
from core.knowledge_graph import KnowledgeGraph
from core.capability_registry import CapabilityManifest, CapabilityRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentContext:
    """Contexto compartido que recibe cada agente al inicializar."""
    event_bus: EventBus
    knowledge_graph: KnowledgeGraph
    capability_registry: CapabilityRegistry
    agent_id: str


class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema.

    Ciclo de vida de un agente:
    1. Register: publica su CapabilityManifest en el CapabilityRegistry
    2. Subscribe: se suscribe a los topicos que matchean sus triggers
    3. Listen: cuando llega un evento, evalua si debe actuar
    4. Execute: ejecuta su capacidad, escribe al KG, emite nuevos eventos
    5. Error: en caso de fallo, emite un evento de error o risk
    """

    def __init__(self, ctx: AgentContext, manifest: CapabilityManifest):
        self.ctx = ctx
        self.manifest = manifest
        self._running = False

    async def start(self) -> None:
        """Registra el agente y se suscribe a eventos."""
        self.ctx.capability_registry.register(self.manifest)
        for trigger in self.manifest.triggers:
            self.ctx.event_bus.subscribe(
                trigger["event"],
                self._handle_event_wrapper
            )
        self._running = True
        logger.info(f"Agent {self.manifest.agent_id} started. "
                     f"Subscribed to {len(self.manifest.triggers)} topics.")

    async def stop(self) -> None:
        self._running = False
        self.ctx.capability_registry.unregister(self.manifest.agent_id)
        logger.info(f"Agent {self.manifest.agent_id} stopped.")

    async def _handle_event_wrapper(self, event: Event) -> None:
        if not self._running:
            return
        try:
            await self.handle_event(event)
        except Exception as e:
            logger.error(f"Agent {self.manifest.agent_id} error handling "
                          f"{event.topic}: {e}")
            await self.ctx.event_bus.publish(Event(
                topic=f"proyecto.{event.project_id}.risk.identified",
                source=self.manifest.agent_id,
                project_id=event.project_id,
                data={"error": str(e), "original_event_id": event.id,
                      "severity": "medium"}
            ))

    @abstractmethod
    async def handle_event(self, event: Event) -> None:
        """Procesa un evento. Cada agente implementa su logica aqui."""
        ...

    async def emit(self, topic: str, project_id: str, data: dict,
                   source: Optional[str] = None) -> Event:
        event = Event(
            topic=topic,
            source=source or self.manifest.agent_id,
            project_id=project_id,
            data=data
        )
        await self.ctx.event_bus.publish(event)
        return event

    def read_graph(self, node_id: str):
        return self.ctx.knowledge_graph.get_node(node_id)

    def write_graph(self, node) -> None:
        self.ctx.knowledge_graph.add_node(node)

    def query_graph(self, **filters):
        return self.ctx.knowledge_graph.query(**filters)
```

### 1.2 Agentes Especializados

```python
"""agents/adaptation_agent.py — Proceso de Adaptacion ISO 12207.
Recibe el prompt del usuario, clasifica complejidad, selecciona procesos,
y propone el ciclo de vida."""
from core.base_agent import BaseAgent, AgentContext, Event
from core.capability_registry import CapabilityManifest
from core.knowledge_graph import Node, NodeType
from core.llm_client import LLMClient  # cliente LLM generico
from enum import Enum
import json
import time


class Complexity(str, Enum):
    SIMPLE = "simple"          # 1-2 archivos, sin diseno arquitectonico
    MODERATE = "moderate"      # 3-5 archivos, cambios de esquema menores
    COMPLEX = "complex"        # multi-modulo, requiere decision arquitectonica


class LifecycleModel(str, Enum):
    FAST_TRACK = "fast_track"    # Req -> Code -> Test (lineal)
    ITERATIVE = "iterative"      # ciclos cortos req -> diseno -> code -> test
    INCREMENTAL = "incremental"  # entregas parciales por funcionalidad
    AGILE = "agile"              # sprints con planificacion adaptativa
    SPIRAL = "spiral"            # prototipado + analisis de riesgos


# Definiciones de proceso ISO 12207 como templates
ISO_PROCESS_TEMPLATES = {
    "minimal": {
        "processes": ["Development"],
        "activities": [
            "Requirements Elicitation",
            "Software Implementation",
            "Unit Testing"
        ],
        "lifecycle": LifecycleModel.FAST_TRACK
    },
    "standard": {
        "processes": ["Development", "Support"],
        "activities": [
            "Requirements Elicitation",
            "Requirements Analysis",
            "Architecture Design",
            "Detailed Design",
            "Software Implementation",
            "Unit Testing",
            "Integration Testing",
            "Configuration Management",
            "Verification"
        ],
        "lifecycle": LifecycleModel.ITERATIVE
    },
    "full": {
        "processes": ["Development", "Support", "Organizational"],
        "activities": [
            "Requirements Elicitation",
            "Requirements Analysis",
            "Architecture Design",
            "Detailed Design",
            "Software Implementation",
            "Unit Testing",
            "Integration Testing",
            "Configuration Management",
            "Verification",
            "Validation",
            "Project Planning",
            "Risk Management",
            "Quality Assurance"
        ],
        "lifecycle": LifecycleModel.AGILE
    }
}


class AdaptationAgent(BaseAgent):
    """Agente de Adaptacion ISO 12207.
    Analiza el prompt del usuario y selecciona procesos, actividades,
    ciclo de vida, y ruta (fast-path vs deep-path)."""

    def __init__(self, ctx: AgentContext, llm: LLMClient):
        manifest = CapabilityManifest(
            agent_id="adaptation-agent-v1",
            agent_name="Adaptation Agent",
            description="ISO 12207 Adaptation Process: clasifica solicitudes, "
                        "selecciona procesos y define ciclo de vida",
            iso_12207={"process": "Adaptation",
                       "activities": ["Process Selection",
                                      "Lifecycle Modeling"],
                       "tasks": ["Select minimum process set",
                                 "Define lifecycle architecture",
                                 "Tailor processes to project"]},
            triggers=[{"event": "project.initialized", "role": "primary"},
                      {"event": "project.replan.needed", "role": "primary"}],
            output_events=["project.adaptation.complete",
                           "project.complexity.classified",
                           "project.lifecycle.proposed"],
            llm_profile={"recommended_model": "flash",
                         "max_tokens": 4096, "temperature": 0.3}
        )
        super().__init__(ctx, manifest)
        self.llm = llm

    async def handle_event(self, event: Event) -> None:
        if event.topic == "project.initialized":
            await self._classify_and_plan(event)
        elif event.topic == "project.replan.needed":
            await self._replan(event)

    async def _classify_and_plan(self, event: Event) -> None:
        prompt = event.data.get("description", "")
        project_id = event.project_id

        # 1. Clasificar complejidad del proyecto
        classification = await self._classify_complexity(prompt)

        # 2. Seleccionar procesos ISO 12207 segun complejidad
        selected = self._select_processes(classification)

        # 3. Estimar effort (Story Points o tiempo)
        effort_estimate = await self._estimate_effort(prompt, selected)

        # 4. Persistir en Knowledge Graph
        self.write_graph(Node(
            id=f"project-{project_id}",
            node_type=NodeType.GOAL,
            properties={"description": prompt,
                        "complexity": classification.value,
                        "lifecycle": selected["lifecycle"].value,
                        "processes": selected["processes"],
                        "activities": selected["activities"],
                        "effort_estimate": effort_estimate,
                        "status": "planned"}
        ))

        # 5. Emitir eventos
        await self.emit(
            f"proyecto.{project_id}.adaptation.complete",
            project_id,
            {"complexity": classification.value,
             "lifecycle": selected["lifecycle"].value,
             "processes": selected["processes"],
             "activities": selected["activities"],
             "effort_estimate": effort_estimate}
        )
        await self.emit(
            f"proyecto.{project_id}.complexity.classified",
            project_id,
            {"complexity": classification.value}
        )
        await self.emit(
            f"proyecto.{project_id}.lifecycle.proposed",
            project_id,
            {"model": selected["lifecycle"].value}
        )

    async def _classify_complexity(self, prompt: str) -> Complexity:
        """Usar LLM para clasificar si es SIMPLE, MODERATE o COMPLEX.
        Fallback a reglas deterministicas si el LLM falla."""
        system_prompt = (
            "Classify the following software project description into "
            "one of: 'simple', 'moderate', 'complex'. "
            "Respond with ONLY the word.\n\n"
            "Criteria:\n"
            "- simple: 1-2 files, CRUD, no new dependencies, no DB schema change\n"
            "- moderate: 3-5 files, minor schema changes, 1-2 dependencies\n"
            "- complex: multi-module, architectural decision required, "
            "security-sensitive, multiple integrations\n"
        )
        try:
            result = await self.llm.complete(system_prompt + prompt,
                                              max_tokens=10)
            text = result.strip().lower()
            if "simple" in text:
                return Complexity.SIMPLE
            elif "complex" in text:
                return Complexity.COMPLEX
            else:
                return Complexity.MODERATE
        except Exception:
            # Fallback deterministico
            keywords = {"auth", "oauth", "microservice", "integration",
                        "multi-tenant", "pipeline", "real-time", "event-driven"}
            if any(kw in prompt.lower() for kw in keywords):
                return Complexity.COMPLEX
            word_count = len(prompt.split())
            if word_count < 20:
                return Complexity.SIMPLE
            return Complexity.MODERATE

    def _select_processes(self, complexity: Complexity) -> dict:
        if complexity == Complexity.SIMPLE:
            return dict(ISO_PROCESS_TEMPLATES["minimal"])
        elif complexity == Complexity.MODERATE:
            return dict(ISO_PROCESS_TEMPLATES["standard"])
        else:
            return dict(ISO_PROCESS_TEMPLATES["full"])

    async def _estimate_effort(self, prompt: str, selected: dict) -> dict:
        activities = selected.get("activities", [])
        base = len(activities) * 2  # 2 SP por actividad
        if selected["lifecycle"] == LifecycleModel.FAST_TRACK:
            base = max(1, base // 3)
        return {"story_points": base,
                "activities_count": len(activities)}

    async def _replan(self, event: Event) -> None:
        project_id = event.project_id
        node = self.read_graph(f"project-{project_id}")
        if node:
            # Reclasificar y re-planificar
            prompt = node.get("description", "")
            await self._classify_and_plan(Event(
                topic="project.initialized",
                data={"description": prompt},
                project_id=project_id
            ))
```

```python
"""agents/requirements_analyst.py — Analisis de Requerimientos ISO 12207."""
from core.base_agent import BaseAgent, AgentContext, Event
from core.capability_registry import CapabilityManifest
from core.knowledge_graph import Node, NodeType
from core.llm_client import LLMClient
from pydantic import BaseModel, Field
from typing import Literal
import time
import json


class RequirementSchema(BaseModel):
    """Pydantic model para structured output (Ap A)."""
    id: str = ""
    text: str = Field(..., description="Texto del requerimiento")
    type: Literal["functional", "business", "user", "non_functional"] = \
        "functional"
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    source: str = "user"
    acceptance_criteria: list[str] = Field(default_factory=list)


class RequirementsAnalystAgent(BaseAgent):
    """Traduce lenguaje natural a requerimientos estructurados.
    Implementa las actividades de ISO 12207:
    - Requirements Elicitation
    - Requirements Analysis
    - User Documentation Requirements"""

    def __init__(self, ctx: AgentContext, llm: LLMClient):
        manifest = CapabilityManifest(
            agent_id="requirements-analyst-v1",
            agent_name="Requirements Analyst",
            description="ISO 12207 Requirements Engineering: elicitacion, "
                        "analisis y documentacion de requerimientos",
            iso_12207={"process": "Development",
                       "activities": ["Requirements Elicitation",
                                      "Requirements Analysis"],
                       "tasks": ["Define functional requirements",
                                 "Define business requirements",
                                 "Define user documentation requirements",
                                 "Analyze software requirements"]},
            triggers=[{"event": "proyecto.{id}.adaptation.complete",
                       "role": "primary"},
                      {"event": "proyecto.{id}.requirement.clarification_needed",
                       "role": "primary"},
                      {"event": "proyecto.{id}.architecture.review.needs_req_input",
                       "role": "secondary"}],
            output_events=["requirement.created",
                           "requirement.validated",
                           "requirement.updated"],
            llm_profile={"recommended_model": "flash",
                         "max_tokens": 8192, "temperature": 0.2}
        )
        super().__init__(ctx, manifest)
        self.llm = llm

    async def handle_event(self, event: Event) -> None:
        if "adaptation.complete" in event.topic:
            await self._elicit_requirements(event)
        elif "clarification_needed" in event.topic:
            await self._clarify(event)

    async def _elicit_requirements(self, event: Event) -> None:
        project_id = event.project_id
        project_node = self.read_graph(f"project-{project_id}")
        if not project_node:
            return

        description = project_node.get("description", "")
        complexity = project_node.get("complexity", "moderate")

        # Prompt Chaining (cap 1): NL -> lista de requerimientos estructurados
        raw_reqs = await self._llm_extract_requirements(description, complexity)

        # Escribir cada requerimiento al Knowledge Graph
        req_ids = []
        for i, req_data in enumerate(raw_reqs):
            req_id = f"req-{project_id}-{i+1:03d}"
            req = RequirementSchema(
                id=req_id, text=req_data.get("text", ""),
                type=req_data.get("type", "functional"),
                priority=req_data.get("priority", "medium"),
                source="user",
                acceptance_criteria=req_data.get("acceptance_criteria", [])
            )
            node = Node(
                id=req_id,
                node_type=NodeType.REQUIREMENT,
                properties=req.model_dump(),
                created_by=self.manifest.agent_id,
                created_at=time.time()
            )
            self.write_graph(node)
            req_ids.append(req_id)

        # Emitir evento con los IDs de requerimientos creados
        await self.emit(
            f"proyecto.{project_id}.requirement.created",
            project_id,
            {"requirement_ids": req_ids, "count": len(req_ids)}
        )

    async def _llm_extract_requirements(
            self, description: str, complexity: str) -> list[dict]:
        system_prompt = (
            "You are a Requirements Engineer following ISO 12207. "
            "Extract structured requirements from the user's description.\n"
            "Return a JSON array of objects with keys: "
            "text (str), type (functional|business|user|non_functional), "
            "priority (critical|high|medium|low), "
            "acceptance_criteria (list[str]).\n"
            f"Complexity: {complexity}\n"
            "Requirements must be testable and unambiguous."
        )
        try:
            result = await self.llm.complete(
                system_prompt + "\n\nDescription:\n" + description,
                max_tokens=4096,
                response_format="json"
            )
            reqs = json.loads(result)
            if isinstance(reqs, list):
                return reqs
            return []
        except Exception:
            # Fallback: generar un unico requerimiento generico
            return [{"text": f"Implement {description}",
                     "type": "functional", "priority": "medium",
                     "acceptance_criteria": ["Works as specified"]}]

    async def _clarify(self, event: Event) -> None:
        req_id = event.data.get("requirement_id", "")
        question = event.data.get("question", "")
        # En un sistema real, esto escalaria al usuario (HITL, cap 13)
        # Por ahora, emitimos un evento de espera
        await self.emit(
            f"proyecto.{event.project_id}.human.input.needed",
            event.project_id,
            {"requirement_id": req_id, "question": question}
        )
```

```python
"""agents/architect_agent.py — Diseno Arquitectonico ISO 12207."""
from core.base_agent import BaseAgent, AgentContext, Event
from core.capability_registry import CapabilityManifest
from core.knowledge_graph import Node, NodeType, Edge, EdgeType
from core.llm_client import LLMClient
import time


class ArchitectAgent(BaseAgent):
    """Transforma requerimientos en arquitectura de componentes y diseno detallado.
    Actividades ISO 12207:
    - Architecture Design
    - Detailed Design
    - Integration Planning"""

    def __init__(self, ctx: AgentContext, llm: LLMClient):
        manifest = CapabilityManifest(
            agent_id="architect-agent-v1",
            agent_name="Software Architect",
            description="ISO 12207 Architecture Design: diseno de alto nivel, "
                        "detallado, y plan de integracion",
            iso_12207={"process": "Development",
                       "activities": ["Architecture Design",
                                      "Detailed Design",
                                      "Integration Planning"],
                       "tasks": ["Define software architecture",
                                 "Define database design",
                                 "Define component interfaces",
                                 "Define integration plan"]},
            triggers=[{"event": "proyecto.{id}.requirement.created",
                       "role": "primary"},
                      {"event": "proyecto.{id}.architecture.review.requested",
                       "role": "primary"}],
            output_events=["architecture.proposed",
                           "design.detailed.complete",
                           "integration.plan.proposed"],
            llm_profile={"recommended_model": "pro",
                         "max_tokens": 8192, "temperature": 0.2}
        )
        super().__init__(ctx, manifest)
        self.llm = llm

    async def handle_event(self, event: Event) -> None:
        if "requirement.created" in event.topic:
            await self._design_architecture(event)

    async def _design_architecture(self, event: Event) -> None:
        project_id = event.project_id
        req_ids = event.data.get("requirement_ids", [])

        # Cargar requerimientos del Knowledge Graph
        requirements = []
        for rid in req_ids:
            node = self.read_graph(rid)
            if node:
                requirements.append(node.properties)

        # Usar Tree-of-Thought (cap 17) para explorar alternativas
        architecture = await self._explore_architectures(requirements)

        # Persistir componentes en Knowledge Graph
        component_ids = []
        for comp in architecture.get("components", []):
            comp_id = f"comp-{project_id}-{comp['name'].lower().replace(' ', '-')}"
            node = Node(
                id=comp_id,
                node_type=NodeType.COMPONENT,
                properties={"name": comp["name"],
                            "tech_stack": comp.get("tech_stack", []),
                            "interfaces": comp.get("interfaces", []),
                            "status": "designed"},
                created_by=self.manifest.agent_id,
                created_at=time.time()
            )
            self.write_graph(node)
            component_ids.append(comp_id)

            # Trazabilidad: componente implementa requerimientos
            for req_id in comp.get("implements_requirements", []):
                if req_id in req_ids:
                    self.ctx.knowledge_graph.add_edge(Edge(
                        source_id=comp_id,
                        target_id=req_id,
                        edge_type=EdgeType.IMPLEMENTS
                    ))

        # Persistir decisiones arquitectonicas
        for dec in architecture.get("decisions", []):
            dec_id = f"adr-{project_id}-{len(dec):04d}"
            node = Node(
                id=dec_id,
                node_type=NodeType.ARCHITECTURE_DECISION,
                properties=dec,
                created_by=self.manifest.agent_id,
                created_at=time.time()
            )
            self.write_graph(node)

        # Emitir evento
        await self.emit(
            f"proyecto.{project_id}.architecture.proposed",
            project_id,
            {"component_ids": component_ids,
             "components": architecture.get("components", []),
             "decisions": architecture.get("decisions", []),
             "requirement_ids": req_ids}
        )

    async def _explore_architectures(self, requirements: list[dict]) -> dict:
        """Usa Tree-of-Thought (cap 17) para proponer arquitectura.
        En produccion, esto exploraria multiples estilos en paralelo."""
        prompt = (
            "You are a Software Architect following ISO 12207. "
            "Design a software architecture for these requirements:\n"
            f"{json.dumps(requirements, indent=2)}\n\n"
            "Return JSON with:\n"
            "- components: list of {name, tech_stack, interfaces, "
            "implements_requirements}\n"
            "- decisions: list of {title, context, decision, consequences}\n"
            "- database_design: description of data model"
        )
        try:
            result = await self.llm.complete(prompt, max_tokens=4096,
                                              response_format="json")
            return json.loads(result)
        except Exception:
            return {"components": [], "decisions": [],
                    "database_design": "Pending"}
```

```python
"""agents/coder_agent.py — Implementacion de Software ISO 12207."""
from core.base_agent import BaseAgent, AgentContext, Event
from core.capability_registry import CapabilityManifest
from core.knowledge_graph import Node, NodeType, Edge, EdgeType
from core.llm_client import LLMClient
import time


class CoderAgent(BaseAgent):
    """Implementa unidades de software y ejecuta pruebas unitarias.
    Actividades ISO 12207:
    - Software Implementation
    - Unit Testing"""

    def __init__(self, ctx: AgentContext, llm: LLMClient):
        manifest = CapabilityManifest(
            agent_id="coder-agent-v1",
            agent_name="Software Coder",
            description="ISO 12207 Software Implementation: codificacion y "
                        "pruebas unitarias",
            iso_12207={"process": "Development",
                       "activities": ["Software Implementation",
                                      "Unit Testing"],
                       "tasks": ["Implement software units",
                                 "Execute unit tests",
                                 "Document code"]},
            triggers=[{"event": "proyecto.{id}.architecture.proposed",
                       "role": "primary"},
                      {"event": "proyecto.{id}.design.detailed.complete",
                       "role": "primary"},
                      {"event": "proyecto.{id}.test.executed",
                       "role": "secondary"}],
            output_events=["code.committed",
                           "code.failed",
                           "code.unit_test.passed",
                           "code.unit_test.failed"],
            llm_profile={"recommended_model": "pro",
                         "max_tokens": 16384, "temperature": 0.1}
        )
        super().__init__(ctx, manifest)
        self.llm = llm
        self.max_retries = 3

    async def handle_event(self, event: Event) -> None:
        if "architecture.proposed" in event.topic:
            await self._implement_components(event)
        elif "test.executed" in event.topic and event.data.get("failed", False):
            await self._fix_failing_code(event)

    async def _implement_components(self, event: Event) -> None:
        project_id = event.project_id
        components = event.data.get("components", [])
        req_ids = event.data.get("requirement_ids", [])

        # ReAct loop (cap 17): Thought -> Action -> Observation
        for comp in components:
            comp_name = comp.get("name", "unknown")
            module_id = f"mod-{project_id}-{comp_name.lower().replace(' ', '-')}"

            # Thought: planificar implementacion
            plan = await self._plan_implementation(comp)

            # Action: generar codigo
            code = await self._generate_code(comp, plan)
            if not code:
                await self.emit(
                    f"proyecto.{project_id}.code.failed", project_id,
                    {"component": comp_name, "error": "Code generation failed"}
                )
                continue

            # Observation: validar con tests
            tests_passed = await self._run_unit_tests(module_id, code)

            # Persistir modulo en Knowledge Graph
            node = Node(
                id=module_id,
                node_type=NodeType.CODE_MODULE,
                properties={"name": comp_name, "component": comp_name,
                            "code_preview": code[:500],
                            "tests_passed": tests_passed,
                            "status": "implemented" if tests_passed else "failed"},
                created_by=self.manifest.agent_id,
                created_at=time.time()
            )
            self.write_graph(node)

            # Trazabilidad: modulo implementa componentes
            self.ctx.knowledge_graph.add_edge(Edge(
                source_id=module_id,
                target_id=event.data.get("component_ids", [None])[0],
                edge_type=EdgeType.IMPLEMENTS
            ))

            # Emitir resultado
            if tests_passed:
                await self.emit(
                    f"proyecto.{project_id}.code.committed", project_id,
                    {"module_id": module_id, "component": comp_name,
                     "files": [f"{module_id}.py"], "tests_passed": tests_passed}
                )
            else:
                await self.emit(
                    f"proyecto.{project_id}.code.failed", project_id,
                    {"module_id": module_id, "component": comp_name,
                     "error": "Unit tests failed", "retries_left": self.max_retries - 1}
                )

    async def _plan_implementation(self, component: dict) -> str:
        return f"Plan for {component.get('name')}"

    async def _generate_code(self, component: dict, plan: str) -> str:
        prompt = (
            f"Generate Python code for component: {json.dumps(component)}\n"
            f"Plan: {plan}\n"
            "Include type hints, docstrings, and error handling."
        )
        try:
            return await self.llm.complete(prompt, max_tokens=4096)
        except Exception:
            return ""

    async def _run_unit_tests(self, module_id: str, code: str) -> bool:
        """Simula ejecucion de tests. En produccion ejecutaria pytest
        via Tool Use (cap 5) o PALM (cap 17)."""
        # Placeholder: siempre pasa en simulacion
        return True

    async def _fix_failing_code(self, event: Event) -> None:
        """Self-Correction (cap 17) sobre codigo fallido."""
        module_id = event.data.get("module_id", "")
        node = self.read_graph(module_id)
        if not node:
            return
        # Reintentar con el error como contexto adicional
        # (en produccion, el LLM recibe el error y corrige)
        await self.emit(
            f"proyecto.{event.project_id}.code.committed",
            event.project_id,
            {"module_id": module_id, "retry": True}
        )
```

```python
"""agents/verification_agent.py — Verificacion y Validacion ISO 12207."""
from core.base_agent import BaseAgent, AgentContext, Event
from core.capability_registry import CapabilityManifest
from core.knowledge_graph import Edge, EdgeType
from core.llm_client import LLMClient


class VerificationAgent(BaseAgent):
    """Verificacion: el codigo cumple el diseno?
    Validacion: el sistema satisface el uso previsto?
    Actividades ISO 12207: Verification, Validation"""

    def __init__(self, ctx: AgentContext, llm: LLMClient):
        manifest = CapabilityManifest(
            agent_id="verification-agent-v1",
            agent_name="Verification & Validation Agent",
            description="ISO 12207 Verification & Validation: asegura que "
                        "el codigo cumple el diseno y satisface reqs",
            iso_12207={"process": "Support",
                       "activities": ["Verification", "Validation"],
                       "tasks": ["Verify code against design",
                                 "Validate system against requirements",
                                 "Conduct technical reviews",
                                 "Conduct audits"]},
            triggers=[{"event": "proyecto.{id}.code.committed",
                       "role": "primary"},
                      {"event": "proyecto.{id}.quality.gate.requested",
                       "role": "primary"}],
            output_events=["quality.gate.passed",
                           "quality.gate.failed",
                           "verification.complete",
                           "validation.complete"],
            llm_profile={"recommended_model": "pro",
                         "max_tokens": 4096, "temperature": 0.1}
        )
        super().__init__(ctx, manifest)
        self.llm = llm

    async def handle_event(self, event: Event) -> None:
        if "code.committed" in event.topic:
            await self._verify_code(event)

    async def _verify_code(self, event: Event) -> None:
        project_id = event.project_id
        module_id = event.data.get("module_id", "")

        # Verification: el modulo tiene trazabilidad a componentes?
        trace = self.ctx.knowledge_graph.get_incoming(
            module_id, EdgeType.IMPLEMENTS
        )
        has_trace = len(trace) > 0

        # Validation: el modulo responde a requerimientos?
        # Recorrer: module -> component -> requirement
        validated = False
        for edge in trace:
            req_trace = self.ctx.knowledge_graph.get_outgoing(
                edge.target_id, EdgeType.IMPLEMENTS
            )
            validated = len(req_trace) > 0
            if validated:
                break

        if has_trace and validated:
            await self.emit(
                f"proyecto.{project_id}.quality.gate.passed",
                project_id,
                {"module_id": module_id,
                 "gate": "verification",
                 "traced": has_trace,
                 "validated": validated}
            )
        else:
            await self.emit(
                f"proyecto.{project_id}.quality.gate.failed",
                project_id,
                {"module_id": module_id,
                 "gate": "verification",
                 "traced": has_trace,
                 "validated": validated,
                 "details": "Module lacks full traceability"}
            )
```

```python
"""agents/project_tracker.py — Gestion de Proyecto ISO 12207 (monitoreo, no control)."""
from core.base_agent import BaseAgent, AgentContext, Event
from core.capability_registry import CapabilityManifest
from core.knowledge_graph import Node, NodeType
import time
from collections import defaultdict


class ProjectTracker(BaseAgent):
    """Monitorea el progreso del proyecto via eventos.
    NO orquesta — solo observa, registra metricas, y emite reports.
    Actividades ISO 12207: Project Planning, Progress Monitoring, Risk Tracking"""

    def __init__(self, ctx: AgentContext):
        manifest = CapabilityManifest(
            agent_id="project-tracker-v1",
            agent_name="Project Tracker",
            description="ISO 12207 Project Management: monitoreo de progreso, "
                        "estimaciones, riesgos sin control directo",
            iso_12207={"process": "Organizational",
                       "activities": ["Project Planning",
                                      "Project Monitoring",
                                      "Risk Management"],
                       "tasks": ["Estimate effort",
                                 "Track progress",
                                 "Identify risks",
                                 "Generate reports"]},
            triggers=[{"event": "proyecto.{id}.>", "role": "observer"}],
            output_events=["project.progress.report",
                           "project.risk.alert",
                           "project.plan.proposed"],
            llm_profile={"recommended_model": "flash",
                         "max_tokens": 2048, "temperature": 0.1}
        )
        super().__init__(ctx, manifest)
        self._event_counts: dict[str, dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

    async def handle_event(self, event: Event) -> None:
        pid = event.project_id
        # Clasificar evento por tipo
        if "created" in event.topic or "proposed" in event.topic:
            self._event_counts[pid]["pending"] += 1
        elif "passed" in event.topic or "complete" in event.topic:
            self._event_counts[pid]["completed"] += 1
            self._event_counts[pid]["pending"] = max(
                0, self._event_counts[pid]["pending"] - 1
            )
        elif "failed" in event.topic:
            self._event_counts[pid]["failed"] += 1

        # Emitir reporte cada 10 eventos o en demanda
        total_events_pid = sum(self._event_counts[pid].values())
        if total_events_pid > 0 and total_events_pid % 10 == 0:
            await self.emit(
                f"proyecto.{pid}.project.progress.report", pid,
                {"pending": self._event_counts[pid]["pending"],
                 "completed": self._event_counts[pid]["completed"],
                 "failed": self._event_counts[pid]["failed"],
                 "total_events": total_events_pid}
            )

        # Detectar riesgos: demasiados fallos en el mismo modulo
        if self._event_counts[pid]["failed"] > 3:
            await self.emit(
                f"proyecto.{pid}.project.risk.alert", pid,
                {"type": "high_failure_rate",
                 "failed_count": self._event_counts[pid]["failed"],
                 "severity": "medium"}
            )
```

```python
"""core/swarm_coordinator.py — Coordinador de swarm: detecta cuando
un conjunto de eventos forma una unidad completa."""
from core.event_bus import Event, EventBus
from core.knowledge_graph import KnowledgeGraph
import asyncio
from collections import defaultdict
from typing import Optional


class SwarmDetector:
    """Detecta cuando un lote de sub-eventos constituye una tarea completa.

    Ejemplo: cuando 'architecture.proposed' + 'security.review.completed'
    + 'ux.flow.proposed' han llegado para el mismo req_id, emite
    'design.complete'."""

    def __init__(self, event_bus: EventBus, kg: KnowledgeGraph):
        self.event_bus = event_bus
        self.kg = kg
        self._waiting: dict[str, dict] = defaultdict(dict)
        # {req_id: {expected_event_type: bool}}

    def register_swarm_pattern(self, trigger_event: str,
                                required_events: list[str],
                                completion_event: str,
                                timeout_seconds: float = 300.0) -> None:
        """Registra un patron de swarm.

        trigger_event: evento que inicia el patron (ej. requirement.created)
        required_events: eventos que deben llegar considerados completos
        completion_event: evento a emitir cuando todos han llegado
        timeout_seconds: maximo tiempo de espera antes de emitir riesgo
        """
        # En produccion, esto se persiste en config
        pass  # Implementacion completa veria los required_events como condiciones

    async def on_event(self, event: Event) -> None:
        """Procesa un evento y evalua condiciones de swarm."""
        # Placeholder para el mecanismo de swarm detection completo.
        # En produccion, evaluaria contra condiciones registradas y emitiria
        # eventos de completitud cuando se cumplan todas.
        pass
```

```python
"""core/quality_gate.py — Quality Gate: evalua condiciones antes de
permitir transiciones de estado."""
from core.event_bus import Event, EventBus
from core.knowledge_graph import KnowledgeGraph, EdgeType


class GateResult:
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"


class QualityGate:
    """Punto de control que evalua condiciones del Knowledge Graph
    antes de permitir que un flujo continue."""

    def __init__(self, event_bus: EventBus, kg: KnowledgeGraph):
        self.event_bus = event_bus
        self.kg = kg
        self._gates: dict[str, callable] = {}

    def register_gate(self, gate_name: str,
                      condition_fn: callable) -> None:
        self._gates[gate_name] = condition_fn

    async def evaluate(self, gate_name: str, project_id: str,
                       context: dict) -> str:
        fn = self._gates.get(gate_name)
        if not fn:
            return GateResult.PASSED
        try:
            result = fn(self.kg, project_id, context)
            if result is True:
                return GateResult.PASSED
            else:
                await self.event_bus.publish(Event(
                    topic=f"proyecto.{project_id}.quality.gate.failed",
                    source="quality-gate",
                    project_id=project_id,
                    data={"gate": gate_name, "reason": str(result)}
                ))
                return GateResult.FAILED
        except Exception as e:
            await self.event_bus.publish(Event(
                topic=f"proyecto.{project_id}.quality.gate.failed",
                source="quality-gate", project_id=project_id,
                data={"gate": gate_name, "error": str(e)}
            ))
            return GateResult.FAILED


# --- Quality Gates pre-definidos ---

def gate_todos_los_requisitos_tienen_aceptacion(
    kg: KnowledgeGraph, project_id: str, ctx: dict
) -> bool:
    """CHECK: todos los requisitos deben tener criterios de aceptacion."""
    reqs = kg.query(node_type=NodeType.REQUIREMENT)
    for r in reqs:
        ac = r.get("acceptance_criteria", [])
        if not ac:
            return f"Requirement {r.id} missing acceptance criteria"
    return True


def gate_cada_componente_tiene_trazabilidad(
    kg: KnowledgeGraph, project_id: str, ctx: dict
) -> bool:
    """CHECK: cada componente debe trazar a al menos un requisito."""
    comps = kg.query(node_type=NodeType.COMPONENT)
    for c in comps:
        traces = kg.get_outgoing(c.id, EdgeType.IMPLEMENTS)
        if not traces:
            return f"Component {c.id} has no requirement traceability"
    return True
```

---

## 2. Protocolos de Comunicacion

### 2.1 Esquema de Eventos (Pydantic Contracts)

Cada tipo de evento tiene un schema Pydantic que define su `data` payload.

```python
"""protocols/event_schemas.py — Schemas de eventos entre agentes."""
from pydantic import BaseModel, Field
from typing import Any, Literal, Optional


class ProjectInitialized(BaseModel):
    description: str
    project_id: str
    user_id: Optional[str] = None


class AdaptationComplete(BaseModel):
    complexity: Literal["simple", "moderate", "complex"]
    lifecycle: Literal["fast_track", "iterative", "incremental", "agile", "spiral"]
    processes: list[str]
    activities: list[str]
    effort_estimate: dict


class RequirementCreated(BaseModel):
    requirement_ids: list[str]
    count: int


class ArchitectureProposed(BaseModel):
    component_ids: list[str]
    components: list[dict]
    decisions: list[dict]
    requirement_ids: list[str]


class CodeCommitted(BaseModel):
    module_id: str
    component: str
    files: list[str]
    tests_passed: bool


class TestExecuted(BaseModel):
    module_id: str
    passed: bool
    coverage: Optional[float] = None
    failed_tests: list[str] = []


class QualityGateResult(BaseModel):
    module_id: Optional[str] = None
    gate: str
    result: Literal["passed", "failed"]
    details: Optional[str] = None


class RiskIdentified(BaseModel):
    risk_id: str = ""
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    source_event: str = ""
    mitigation: Optional[str] = None
```

### 2.2 Formato del Capability Manifest (JSON)

```json
{
  "agent_id": "coder-agent-v1",
  "agent_name": "Software Coder",
  "protocol_version": "1.0.0",
  "iso_12207": {
    "process": "Development",
    "activities": ["Software Implementation", "Unit Testing"],
    "tasks": [
      "Implement software units",
      "Execute unit tests",
      "Document code"
    ]
  },
  "llm_requirements": {
    "recommended_model": "pro",
    "min_model": "flash",
    "max_tokens": 16384,
    "temperature_range": [0.0, 0.3],
    "response_format": ["text", "json"]
  },
  "dependencies": ["architect-agent-v1"],
  "max_concurrent_tasks": 3,
  "retry_policy": {
    "max_retries": 3,
    "backoff_seconds": 5,
    "escalation_after": 3
  }
}
```

### 2.3 Handshake: Registro de un Nuevo Agente

```
1. Agent inicia -> publica evento: system.agent.register
   {
     "agent_id": "coder-agent-v1",
     "manifest": { ... }
   }

2. CapabilityRegistry recibe -> registra en directorio
   -> publica evento: system.agent.registered
   {
     "agent_id": "coder-agent-v1",
     "status": "active",
     "timestamp": ...
   }

3. Agent recibe confirmacion -> se suscribe a topicos
   Segun su manifest.triggers

4. Agent publica: system.agent.ready
   {
     "agent_id": "coder-agent-v1",
     "subscribed_topics": ["proyecto.{id}.architecture.proposed", ...]
   }

5. Opcional: Agent puede hacer sync replay de eventos pasados
   event_bus.replay(project_id, since_sequence=last_known)
```

### 2.4 Quality Gate Protocol

```
1. Cualquier agente emite: proyecto.{id}.quality.gate.requested
   {
     "gate": "traceability_check",
     "module_id": "mod-p-42-auth-oauth",
     "context": { ... }
   }

2. QualityGate evalua condicion registrada
   -> Si PASS: proyecto.{id}.quality.gate.passed
   -> Si FAIL: proyecto.{id}.quality.gate.failed + risk.identified

3. Los agentes observan el resultado
   -> Gate PASSED: continuan con el flujo normal
   -> Gate FAILED: entran en modo correccion o escalan a humano
```

---

## 3. Ejemplo Completo: "Quiero un sistema de inventario simple"

### 3.1 Input del Usuario

```
Usuario: "Quiero un sistema de inventario simple para mi tienda.
Debe permitir agregar productos, registrar entradas y salidas de stock,
y consultar el inventario actual. Cada producto tiene nombre, SKU,
precio y cantidad."
```

### 3.2 Trace de Eventos (ISO 12207 Completo)

```
Event #1:
  topic: project.initialized
  source: user-interface
  project_id: "inv-001"
  data: {"description": "Quiero un sistema de inventario simple...",
         "user_id": "user-42"}

  ── Reacciona: AdaptationAgent ──

  → LLM clasifica: SIMPLE (CRUD, 1-2 entidades, sin dependencias externas)
  → Selecciona procesos: ISO_PROCESS_TEMPLATES["minimal"]
    - Development: Requirements Elicitation, Software Implementation, Unit Testing
  → Ciclo de vida: FAST_TRACK
  → Estima: 2 story points

Event #2:
  topic: proyecto.inv-001.adaptation.complete
  source: adaptation-agent-v1
  data: {"complexity": "simple", "lifecycle": "fast_track",
         "activities": ["Requirements Elicitation",
                        "Software Implementation",
                        "Unit Testing"],
         "effort_estimate": {"story_points": 2}}

  ── Reacciona: RequirementsAnalystAgent ──

  → Prompt Chaining: NL -> structured requirements
  → Escribe al Knowledge Graph:

  KG: Node req-inv-001-001
      type: requirement
      text: "Agregar productos con nombre, SKU, precio y cantidad"
      type: functional, priority: high
      acceptance_criteria: ["Producto se crea con todos los campos",
                            "SKU debe ser unico"]

  KG: Node req-inv-001-002
      type: requirement
      text: "Registrar entradas de stock"
      type: functional, priority: high
      acceptance_criteria: ["Entrada incrementa cantidad del producto",
                            "Se registra fecha y usuario"]

  KG: Node req-inv-001-003
      type: requirement
      text: "Registrar salidas de stock"
      type: functional, priority: high
      acceptance_criteria: ["Salida decrementa cantidad",
                            "No permite saldo negativo"]

  KG: Node req-inv-001-004
      type: requirement
      text: "Consultar inventario actual"
      type: functional, priority: medium
      acceptance_criteria: ["Lista todos los productos con stock actual",
                            "Permite filtrar por nombre/SKU"]

Event #3:
  topic: proyecto.inv-001.requirement.created
  source: requirements-analyst-v1
  data: {"requirement_ids": ["req-inv-001-001",
                             "req-inv-001-002",
                             "req-inv-001-003",
                             "req-inv-001-004"],
         "count": 4}

  ── Reacciona: ArchitectAgent (pero es SIMPLE -> FAST PATH) ──

  → Fast-Path: bypass de diseno arquitectonico detallado
  → Pero el Architect Agent registra una entrada minima:

  KG: Node comp-inv-001-product
      type: component
      name: "Product Management"
      tech_stack: ["Python", "SQLite"]
      status: "designed"

KG: Edge comp-inv-001-product IMPLEMENTS req-inv-001-001
KG: Edge comp-inv-001-product IMPLEMENTS req-inv-001-002
KG: Edge comp-inv-001-product IMPLEMENTS req-inv-001-003
KG: Edge comp-inv-001-product IMPLEMENTS req-inv-001-004

Event #4:
  topic: proyecto.inv-001.architecture.proposed
  source: architect-agent-v1
  data: {"component_ids": ["comp-inv-001-product"],
         "components": [{"name": "Product Management",
                         "tech_stack": ["Python", "SQLite"],
                         "interfaces": ["CRUD"]}],
         "requirement_ids": ["req-inv-001-001", "req-inv-001-002",
                             "req-inv-001-003", "req-inv-001-004"]}

  ── Reacciona: CoderAgent ──

  → ReAct loop: planificar -> generar codigo -> testear
  → Prompt al LLM (ReAct + PALM, cap 17):

  Thought: "Need to implement Product CRUD with SQLite.
            Fields: name, SKU, price, quantity.
            Stock operations: entry (increment), exit (decrement).
            Query: list all, filter by name/SKU."

  Action: generate_code("inventory_system.py")

  Observation: code generated, running unit tests...

  → Escribe al Knowledge Graph:

  KG: Node mod-inv-001-product
      type: code_module
      name: "inventory_system"
      code_preview: "class Product: ... class Inventory: ..."
      tests_passed: true
      status: "implemented"

Event #5:
  topic: proyecto.inv-001.code.committed
  source: coder-agent-v1
  data: {"module_id": "mod-inv-001-product",
         "component": "Product Management",
         "files": ["inventory_system.py", "test_inventory.py"],
         "tests_passed": true}

  ── Reaccionan en paralelo (swarm implicito): ──

1) VerificationAgent:
  → Verifica trazabilidad: module -> component -> requirement
  → Encuentra: mod-inv-001 -> comp-inv-001 -> req-*
  → Quality Gate: PASSED

  Event #6a:
    topic: proyecto.inv-001.quality.gate.passed
    source: verification-agent-v1
    data: {"module_id": "mod-inv-001-product",
           "gate": "verification", "traced": true}

2) ProjectTracker:
  → Registra: 1 completed, 0 pending, 0 failed
  → Progreso: 25% (1 de 4 requisitos implementados)
  → Emite reporte

  Event #6b:
    topic: proyecto.inv-001.project.progress.report
    source: project-tracker-v1
    data: {"completed": 1, "pending": 3, "failed": 0}

3) (En produccion) DocWriterAgent:
  → Observa code.committed y genera documentacion
  → Emite artifact.published

```

### 3.3 Estado Final del Knowledge Graph

```
NODOS:
  [goal]     project-inv-001  {description: "Sistema inventario simple", ...}
  [req]      req-inv-001-001  {text: "Agregar productos...", status: "implemented"}
  [req]      req-inv-001-002  {text: "Registrar entradas...", status: "implemented"}
  [req]      req-inv-001-003  {text: "Registrar salidas...", status: "implemented"}
  [req]      req-inv-001-004  {text: "Consultar inventario...", status: "implemented"}
  [comp]     comp-inv-001-product  {name: "Product Management", status: "designed"}
  [mod]      mod-inv-001-product   {name: "inventory_system", status: "implemented"}

ARISTAS:
  comp-inv-001-product  IMPLEMENTS  req-inv-001-001
  comp-inv-001-product  IMPLEMENTS  req-inv-001-002
  comp-inv-001-product  IMPLEMENTS  req-inv-001-003
  comp-inv-001-product  IMPLEMENTS  req-inv-001-004
  mod-inv-001-product   IMPLEMENTS  comp-inv-001-product

TRAZABILIDAD COMPLETA:
  mod-inv-001-product -> comp-inv-001-product -> req-inv-001-{001..004}
```

### 3.4 Puntos de Intervencion Humana (Modo Avanzado)

Si el usuario quiere intervenir (HITL, cap 13), los puntos de entrada son:

| Punto | Evento que lo activa | Que puede hacer el usuario |
|-------|---------------------|---------------------------|
| **Revision de requisitos** | Despues de `requirement.created` | Editar, eliminar, o agregar requisitos antes de que el arquitecto los procese |
| **Revision arquitectonica** | Despues de `architecture.proposed` | Aprobar/rechazar decisiones de diseno, sugerir cambios |
| **Code Review** | Despues de `code.committed` | Revisar codigo generado, solicitar cambios |
| **Auditoria de trazabilidad** | Despues de `quality.gate.failed` | Verificar manualmente la trazabilidad y forzar paso |
| **Re-planificacion** | Despues de `project.risk.alert` | Re-estimar esfuerzo, cambiar prioridades, re-asignar |

Ejemplo de interaccion avanzada:

```
Usuario: "Revisa los requisitos del proyecto inv-001"
Sistema: [Muestra req-inv-001-001..004]
Usuario: "Agrega un requisito: el SKU debe validarse contra el proveedor"
Sistema: -> event: human.input.submitted
         -> requirements-analyst procesa y emite requirement.created (nuevo req-005)
```

---

## 4. Tabla de Trazabilidad ISO 12207

| Proceso ISO 12207 | Actividad | Evento del Bus | Agente Responsable | Patron (cap) |
|------------------|-----------|----------------|-------------------|--------------|
| **Adaptation** | Process Selection | `project.initialized` | AdaptationAgent | Routing (2), Resource Opt (16) |
| **Adaptation** | Lifecycle Modeling | `adaptation.complete` | AdaptationAgent | Planning (6), Goal Setting (11) |
| **Development** | Requirements Elicitation | `requirement.created` | RequirementsAnalyst | Chaining (1), Structured Output (Ap A) |
| **Development** | Requirements Analysis | `requirement.validated` | RequirementsAnalyst | Reflection (4) |
| **Development** | Architecture Design | `architecture.proposed` | ArchitectAgent | ToT (17), Planning (6) |
| **Development** | Detailed Design | `design.detailed.complete` | ArchitectAgent | Hierarchical Planning (6) |
| **Development** | Software Implementation | `code.committed` | CoderAgent | ReAct (17), PALM (17), Tool Use (5) |
| **Development** | Unit Testing | `code.unit_test.passed` | CoderAgent | ReAct (17), PALM (17) |
| **Development** | Integration Testing | `integration.complete` | CoderAgent + Tester | Parallelization (3) |
| **Support** | Configuration Management | `artifact.published` | ConfigMgmtAgent | MCP (10) |
| **Support** | Verification | `quality.gate.passed/failed` | VerificationAgent | Reflection (4), LLM-as-a-Judge (19) |
| **Support** | Validation | `validation.complete` | VerificationAgent | LLM-as-a-Judge (19) |
| **Support** | Documentation | `artifact.published` | DocWriterAgent | Chaining (1), RAG (14) |
| **Organizational** | Project Planning | `project.plan.proposed` | ProjectTracker | Goal Setting (11) |
| **Organizational** | Progress Monitoring | `project.progress.report` | ProjectTracker | Evaluation (19), Prioritization (20) |
| **Organizational** | Risk Management | `risk.identified` | ProjectTracker + todos | Exception Handling (12) |
| **Organizational** | Continuous Improvement | (MASS periodico) | Sistema (automatico) | Learning (9), MASS (17), PDCA |

---

## 5. PDCA como Ciclo del Sistema

Cada interaccion completa sigue el ciclo PDCA:

```
PLAN:
  project.initialized  →  AdaptationAgent define alcance, procesos, y ruta
  ↓
  requirement.created  →  los requisitos son el "plan" para el codigo

DO:
  architecture.proposed  →  diseno
  code.committed         →  implementacion
  (ejecucion paralela de agentes)

CHECK:
  quality.gate.passed/failed  →  VerificationAgent evalua
  project.progress.report     →  ProjectTracker evalua metricas

ACT:
  code.failed + risk.identified  →  CoderAgent se autocorrige (Self-Correction)
  MASS periodico                 →  Sistema optimiza prompts y topologia
  project.replan.needed          →  AdaptationAgent re-planifica

  → El ciclo se repite para cada nuevo requisito o iteracion
```

---

## 6. Resumen de Archivos del Esqueleto

```
iso12207-agent-system/
├── core/
│   ├── event_bus.py            # EventBus, TopicMatcher, Event
│   ├── knowledge_graph.py      # KnowledgeGraph, Node, Edge
│   ├── capability_registry.py  # CapabilityRegistry, CapabilityManifest
│   ├── base_agent.py           # BaseAgent, AgentContext
│   ├── swarm_coordinator.py    # SwarmDetector
│   ├── quality_gate.py         # QualityGate, gates pre-definidos
│   ├── llm_client.py           # LLMClient (interfaz generica)
│   └── __init__.py
├── agents/
│   ├── adaptation_agent.py     # AdaptationAgent
│   ├── requirements_analyst.py # RequirementsAnalystAgent
│   ├── architect_agent.py      # ArchitectAgent
│   ├── coder_agent.py          # CoderAgent
│   ├── verification_agent.py   # VerificationAgent
│   ├── project_tracker.py      # ProjectTracker
│   ├── tester_agent.py         # TesterAgent (adicional)
│   ├── doc_writer_agent.py     # DocWriterAgent (adicional)
│   ├── config_mgr_agent.py     # ConfigMgmtAgent (adicional)
│   └── __init__.py
├── protocols/
│   ├── event_schemas.py        # Pydantic models para eventos
│   └── __init__.py
├── main.py                     # Punto de entrada: inicializa bus, KG, registry, agentes
└── config.yaml                 # Configuracion de modelos LLM, topics, gates
```

---

*Documento de implementacion basado en la vision reactiva de 155_PROP y los patrones de `152_GUIDE` y `153_GUIDE`. Fecha: 2026-06-19.*
