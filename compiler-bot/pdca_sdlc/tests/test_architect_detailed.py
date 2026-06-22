"""Tests for agents/architect_agent.py — Detailed Design (Dia 12)."""

from __future__ import annotations

import pytest

from pdca_sdlc.agents.architect_agent import ArchitectAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus
from pdca_sdlc.core.knowledge_graph import EdgeType, KnowledgeGraph, Node, NodeType


class TestDetailedDesign:
    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="architect",
        )

    @pytest.fixture
    def agent(self, context: AgentContext) -> ArchitectAgent:
        return ArchitectAgent(context)

    def _seed_component(
        self,
        agent: ArchitectAgent,
        comp_id: str,
        name: str,
        tech_stack: list[str] | None = None,
        interfaces: list[str] | None = None,
        implements_requirements: list[str] | None = None,
    ) -> None:
        """Create a component node in the KG."""
        agent.write_graph(
            Node(
                id=comp_id,
                node_type=NodeType.component,
                properties={
                    "name": name,
                    "tech_stack": tech_stack or ["generic"],
                    "interfaces": interfaces or ["handle"],
                    "implements_requirements": implements_requirements or [],
                },
            ),
        )

    # ── _has_data_schema ──────────────────────────────────────────────

    def test_schema_detection_prisma(self, agent: ArchitectAgent) -> None:
        """Component with 'prisma' tech_stack has data schema."""
        comp = {"name": "UserModule", "tech_stack": ["nestjs", "prisma"]}
        assert agent._has_data_schema(comp)

    def test_schema_detection_database(self, agent: ArchitectAgent) -> None:
        """Component with 'database' tech_stack has data schema."""
        comp = {"name": "Metrics", "tech_stack": ["database"]}
        assert agent._has_data_schema(comp)

    def test_schema_detection_entity_name(self, agent: ArchitectAgent) -> None:
        """Component named with entity/model keyword has data schema."""
        comp = {"name": "PaymentEntity", "tech_stack": ["generic"]}
        assert agent._has_data_schema(comp)

    def test_schema_detection_generic(self, agent: ArchitectAgent) -> None:
        """Generic component without DB keywords has no schema."""
        comp = {"name": "AuthComponent", "tech_stack": ["react", "api"]}
        assert not agent._has_data_schema(comp)

    # ── _generate_schema ──────────────────────────────────────────────

    def test_generate_schema_structure(self, agent: ArchitectAgent) -> None:
        """Generated schema has entity, fields, and relations."""
        comp = {"name": "UserModule"}
        schema = agent._generate_schema(comp)
        assert "entity" in schema
        assert "fields" in schema
        assert "relations" in schema
        assert schema["entity"] == "UserModule"
        assert len(schema["fields"]) >= 3
        assert any(f["name"] == "id" and f["primary"] for f in schema["fields"])

    # ── _generate_interfaces ──────────────────────────────────────────

    def test_generate_interfaces_default(self, agent: ArchitectAgent) -> None:
        """Component with 'handle' interface gets expanded to CRUD methods."""
        result = agent._generate_interfaces(
            "comp-auth-p01",
            {"name": "AuthComponent", "interfaces": ["handle"]},
        )
        assert len(result["interfaces"]) == 1
        iface = result["interfaces"][0]
        assert iface["name"] == "handle"
        method_names = {m["name"] for m in iface["methods"]}
        assert method_names == {"create", "read", "update", "delete"}

    def test_generate_interfaces_custom(self, agent: ArchitectAgent) -> None:
        """Component with custom interface names keeps them with CRUD."""
        result = agent._generate_interfaces(
            "comp-api-p01",
            {"name": "ApiComponent", "interfaces": ["rest", "admin"]},
        )
        assert len(result["interfaces"]) == 2
        for iface in result["interfaces"]:
            assert "methods" in iface
            assert len(iface["methods"]) > 0

    def test_generate_interfaces_method_structure(self, agent: ArchitectAgent) -> None:
        """Each interface method has name, params, and returns."""
        result = agent._generate_interfaces(
            "comp-test-p01",
            {"name": "TestComponent", "interfaces": ["api"]},
        )
        for iface in result["interfaces"]:
            for method in iface["methods"]:
                assert "name" in method
                assert "params" in method
                assert "returns" in method

    # ── _generate_dependencies ────────────────────────────────────────

    async def test_dependency_graph_shared_requirement(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """Components sharing a requirement get a DEPENDS_ON edge."""
        self._seed_component(
            agent,
            "comp-auth-p01",
            "AuthComponent",
            implements_requirements=["r-001"],
        )
        self._seed_component(
            agent,
            "comp-dash-p01",
            "DashboardComponent",
            implements_requirements=["r-001", "r-002"],
        )
        component_ids = ["comp-auth-p01", "comp-dash-p01"]
        components = [
            {
                "name": "AuthComponent",
                "interfaces": ["handle"],
                "implements_requirements": ["r-001"],
            },
            {
                "name": "DashboardComponent",
                "interfaces": ["handle"],
                "implements_requirements": ["r-001", "r-002"],
            },
        ]
        agent._generate_dependencies("p01", component_ids, components)
        edges = agent._ctx.knowledge_graph.get_outgoing("comp-dash-p01")
        depends = [e for e in edges if e.edge_type == EdgeType.depends_on]
        assert len(depends) >= 1
        assert depends[0].target_id == "comp-auth-p01"

    async def test_dependency_graph_no_shared(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """Components without shared requirements have no DEPENDS_ON edge."""
        self._seed_component(
            agent,
            "comp-auth-p01",
            "AuthComponent",
            implements_requirements=["r-001"],
        )
        self._seed_component(
            agent,
            "comp-pay-p01",
            "PaymentComponent",
            implements_requirements=["r-002"],
        )
        component_ids = ["comp-auth-p01", "comp-pay-p01"]
        components = [
            {
                "name": "AuthComponent",
                "interfaces": ["handle"],
                "implements_requirements": ["r-001"],
            },
            {
                "name": "PaymentComponent",
                "interfaces": ["handle"],
                "implements_requirements": ["r-002"],
            },
        ]
        agent._generate_dependencies("p01", component_ids, components)
        edges = agent._ctx.knowledge_graph.get_outgoing("comp-pay-p01")
        depends = [e for e in edges if e.edge_type == EdgeType.depends_on]
        assert len(depends) == 0

    # ── _detailed_design end-to-end ────────────────────────────────────

    async def test_detailed_design_updates_interfaces(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """_detailed_design updates component nodes with expanded interfaces."""
        self._seed_component(agent, "comp-auth-p01", "AuthComponent")
        await agent._detailed_design(
            "p01",
            ["comp-auth-p01"],
            [
                {
                    "name": "AuthComponent",
                    "tech_stack": ["generic"],
                    "interfaces": ["handle"],
                    "implements_requirements": [],
                },
            ],
        )
        node = agent.read_graph("comp-auth-p01")
        assert node is not None
        interfaces = node.properties.get("interfaces", [])
        assert len(interfaces) > 0
        if isinstance(interfaces[0], dict):
            assert "methods" in interfaces[0]
            methods = interfaces[0]["methods"]
            assert any(m["name"] == "create" for m in methods)

    async def test_detailed_design_emits_event(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """_detailed_design emits design.detailed.complete."""
        self._seed_component(agent, "comp-auth-p01", "AuthComponent")
        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            from pdca_sdlc.core.event_bus import Event as BusEvent

            if isinstance(data, BusEvent):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("design.detailed.complete", collector)
        await agent._detailed_design(
            "p01",
            ["comp-auth-p01"],
            [
                {
                    "name": "AuthComponent",
                    "tech_stack": ["generic"],
                    "interfaces": ["handle"],
                    "implements_requirements": [],
                },
            ],
        )
        assert len(received) == 1
        payload = received[0]
        assert "component_ids" in payload
        assert "components" in payload

    async def test_detailed_design_schema_when_applicable(
        self,
        agent: ArchitectAgent,
    ) -> None:
        """Components with DB tech get schema written to KG."""
        self._seed_component(
            agent,
            "comp-user-p01",
            "UserEntity",
            tech_stack=["nestjs", "prisma"],
        )
        await agent._detailed_design(
            "p01",
            ["comp-user-p01"],
            [
                {
                    "name": "UserEntity",
                    "tech_stack": ["nestjs", "prisma"],
                    "interfaces": ["handle"],
                    "implements_requirements": [],
                },
            ],
        )
        node = agent.read_graph("comp-user-p01")
        assert node is not None
        schema = node.properties.get("schema")
        assert schema is not None
        assert "entity" in schema
        assert "fields" in schema
