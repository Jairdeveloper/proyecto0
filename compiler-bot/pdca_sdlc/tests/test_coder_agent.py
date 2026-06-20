"""Tests for agents/coder_agent.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pdca_sdlc.agents.coder_agent import CoderAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import KnowledgeGraph, Node, NodeType


class TestCoderAgent:
    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="coder-agent",
        )

    @pytest.fixture
    def agent(self, context: AgentContext) -> CoderAgent:
        return CoderAgent(context)

    def _seed_requirement(
        self,
        agent: CoderAgent,
        req_id: str,
        text: str,
        req_type: str = "functional",
        priority: str = "medium",
    ) -> None:
        agent.write_graph(
            Node(
                id=req_id,
                node_type=NodeType.requirement,
                properties={
                    "id": req_id,
                    "text": text,
                    "type": req_type,
                    "priority": priority,
                    "acceptance_criteria": [f"{text} — verificado"],
                },
            ),
        )

    def test_manifest(self, agent: CoderAgent) -> None:
        m = agent.manifest
        assert m.agent_id == "coder-agent"
        assert "requirement.created" in m.triggers
        assert "code.committed" in m.output_events
        assert "6.3" in m.iso_12207["process"]

    def test_read_requirements_found(self, agent: CoderAgent) -> None:
        self._seed_requirement(agent, "r-001", "Crear API de usuarios")
        self._seed_requirement(agent, "r-002", "Modelo de base de datos")
        reqs = agent._read_requirements(["r-001", "r-002"])
        assert len(reqs) == 2
        assert reqs[0]["text"] == "Crear API de usuarios"
        assert reqs[1]["text"] == "Modelo de base de datos"

    def test_read_requirements_missing(self, agent: CoderAgent) -> None:
        assert agent._read_requirements(["ghost"]) == []

    def test_plan_targets_nestjs(self, agent: CoderAgent) -> None:
        reqs = [{"text": "Crear API REST de productos"}]
        targets = agent._plan_targets(reqs)
        assert "nestjs" in targets
        assert len(targets["nestjs"]) == 1

    def test_plan_targets_prisma(self, agent: CoderAgent) -> None:
        reqs = [{"text": "Entidad de Usuario con campos"}]
        targets = agent._plan_targets(reqs)
        assert "prisma" in targets
        assert len(targets["prisma"]) == 1

    def test_plan_targets_multiple(self, agent: CoderAgent) -> None:
        reqs = [
            {"text": "API REST de productos"},
            {"text": "Entidad de Usuario"},
            {"text": "Docker compose para desarrollo"},
        ]
        targets = agent._plan_targets(reqs)
        assert "nestjs" in targets
        assert "prisma" in targets
        assert "docker" in targets

    def test_plan_targets_default_nestjs(self, agent: CoderAgent) -> None:
        reqs = [{"text": "Algo sin palabras clave"}]
        targets = agent._plan_targets(reqs)
        assert "nestjs" in targets
        assert len(targets["nestjs"]) == 1

    def test_extract_entities(self, agent: CoderAgent) -> None:
        reqs = [{"text": "Entidad Product con campos"}]
        entities = agent._extract_entities(reqs)
        assert len(entities) > 0
        names = [e[0] for e in entities]
        assert "Product" in names

    def test_extract_entities_no_duplicates(self, agent: CoderAgent) -> None:
        reqs = [{"text": "Product y Product otra vez"}]
        entities = agent._extract_entities(reqs)
        count = sum(1 for e in entities if e[0] == "Product")
        assert count == 1

    def test_extract_apis(self, agent: CoderAgent) -> None:
        reqs = [{"text": "User module API"}]
        apis = agent._extract_apis(reqs)
        assert len(apis) > 0
        names = [a[0] for a in apis]
        assert "User" in names

    def test_build_ir_nestjs(self, agent: CoderAgent) -> None:
        reqs = [{"text": "Crear API de Productos"}]
        ir_node = agent._build_ir("p-01", "nestjs", reqs)
        assert type(ir_node).__name__ == "IRProject"
        assert ir_node.name == "p-01"
        assert len(ir_node.children) > 0

    def test_build_ir_prisma(self, agent: CoderAgent) -> None:
        reqs = [{"text": "Entidad Product y Category"}]
        ir_node = agent._build_ir("p-01", "prisma", reqs)
        assert type(ir_node).__name__ == "IRProject"
        assert len(ir_node.children) > 0

    def test_output_dir(self, agent: CoderAgent) -> None:
        p = agent._output_dir("p-01", "nestjs")
        assert p == Path("output") / "p-01" / "nestjs"

    def test_output_dir_custom_base(self, context: AgentContext) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agent = CoderAgent(context, output_base=Path(tmp))
            p = agent._output_dir("p-01", "nestjs")
            assert str(p).startswith(tmp)

    async def test_handle_event_nestjs_generates_code(
        self,
        agent: CoderAgent,
    ) -> None:
        self._seed_requirement(agent, "r-001", "API de Productos")
        req_event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-01",
            data={
                "requirement_ids": ["r-001"],
                "count": 1,
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent._output_base = Path(tmp)
            await agent.start()
            await agent._handle_event_wrapper(
                "requirement.created",
                req_event,
            )
            artifacts = agent.query_graph(node_type=NodeType.artifact)
            assert len(artifacts) >= 1
            art = [a for a in artifacts if a.properties.get("target") == "nestjs"]
            assert len(art) == 1
            assert art[0].properties["status"] == "committed"
            assert len(art[0].properties["paths"]) >= 1
            await agent.stop()

    async def test_handle_event_prisma_generates_code(
        self,
        agent: CoderAgent,
    ) -> None:
        self._seed_requirement(agent, "r-001", "Entidad Product")
        req_event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-01",
            data={
                "requirement_ids": ["r-001"],
                "count": 1,
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent._output_base = Path(tmp)
            await agent.start()
            await agent._handle_event_wrapper(
                "requirement.created",
                req_event,
            )
            artifacts = agent.query_graph(node_type=NodeType.artifact)
            prisma_arts = [a for a in artifacts if a.properties.get("target") == "prisma"]
            assert len(prisma_arts) >= 1
            assert prisma_arts[0].properties["status"] == "committed"
            await agent.stop()

    async def test_handle_event_emits_code_committed(
        self,
        agent: CoderAgent,
    ) -> None:
        self._seed_requirement(agent, "r-001", "API de Productos")
        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("code.committed", collector)
        req_event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-01",
            data={
                "requirement_ids": ["r-001"],
                "count": 1,
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent._output_base = Path(tmp)
            await agent.start()
            await agent._handle_event_wrapper(
                "requirement.created",
                req_event,
            )
            assert len(received) == 1
            assert received[0]["module_id"] == "p-01"
            assert len(received[0]["files"]) >= 1
            await agent.stop()

    async def test_empty_requirement_ids_does_nothing(
        self,
        agent: CoderAgent,
    ) -> None:
        req_event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-01",
            data={"requirement_ids": [], "count": 0},
        )
        await agent.start()
        await agent._handle_event_wrapper(
            "requirement.created",
            req_event,
        )
        artifacts = agent.query_graph(node_type=NodeType.artifact)
        assert len(artifacts) == 0
        await agent.stop()

    async def test_missing_requirements_does_nothing(
        self,
        agent: CoderAgent,
    ) -> None:
        req_event = Event(
            topic="requirement.created",
            source="requirements-analyst",
            project_id="p-01",
            data={"requirement_ids": ["ghost-001"], "count": 1},
        )
        await agent.start()
        await agent._handle_event_wrapper(
            "requirement.created",
            req_event,
        )
        artifacts = agent.query_graph(node_type=NodeType.artifact)
        assert len(artifacts) == 0
        await agent.stop()
