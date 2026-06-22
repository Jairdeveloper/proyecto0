"""Tests for agents/verification_agent.py."""

from __future__ import annotations

import pytest

from pdca_sdlc.agents.verification_agent import VerificationAgent
from pdca_sdlc.core.base_agent import AgentContext
from pdca_sdlc.core.capability_registry import CapabilityRegistry
from pdca_sdlc.core.event_bus import AsyncEventBus, Event
from pdca_sdlc.core.knowledge_graph import (
    Edge,
    EdgeType,
    KnowledgeGraph,
    Node,
    NodeType,
)
from pdca_sdlc.core.llm_client import LLMClient
from pdca_sdlc.core.quality_gate import QualityGate


class _JudgePassLLM(LLMClient):
    """LLM stub that returns a passing score (>= threshold)."""

    def _mock_complete(self, prompt: str, max_tokens: int, response_format: str | None) -> str:
        return "4"


class _JudgeFailLLM(LLMClient):
    """LLM stub that returns a failing score (< threshold)."""

    def _mock_complete(self, prompt: str, max_tokens: int, response_format: str | None) -> str:
        return "1"


class _JudgeInvalidLLM(LLMClient):
    """LLM stub that returns non-numeric response."""

    def _mock_complete(self, prompt: str, max_tokens: int, response_format: str | None) -> str:
        return "I think the code looks good but I'm not sure about the score."


class TestVerificationAgent:
    @pytest.fixture
    def context(self) -> AgentContext:
        return AgentContext(
            event_bus=AsyncEventBus(),
            knowledge_graph=KnowledgeGraph(),
            capability_registry=CapabilityRegistry(),
            agent_id="verification",
        )

    @pytest.fixture
    def agent(self, context: AgentContext) -> VerificationAgent:
        return VerificationAgent(context, llm_client=_JudgePassLLM())

    def _seed_full_trace(self, agent: VerificationAgent) -> None:
        """Set up module -> component -> requirement chain in KG."""
        agent.write_graph(
            Node(
                id="mod-auth-p01",
                node_type=NodeType.code_module,
                properties={"name": "auth.module"},
            ),
        )
        agent.write_graph(
            Node(
                id="comp-auth-p01",
                node_type=NodeType.component,
                properties={"name": "AuthComponent"},
            ),
        )
        agent.write_graph(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "text": "Login con autenticacion OAuth2",
                    "acceptance_criteria": ["Usuario puede loguearse con Google"],
                },
            ),
        )
        agent._ctx.knowledge_graph.add_edge(
            Edge(
                source_id="mod-auth-p01",
                target_id="comp-auth-p01",
                edge_type=EdgeType.implements,
            ),
        )
        agent._ctx.knowledge_graph.add_edge(
            Edge(
                source_id="comp-auth-p01",
                target_id="r-001",
                edge_type=EdgeType.implements,
            ),
        )

    def _seed_module_only(self, agent: VerificationAgent) -> None:
        """Set up module node without any edges."""
        agent.write_graph(
            Node(
                id="mod-orphan-p01",
                node_type=NodeType.code_module,
                properties={"name": "orphan.module"},
            ),
        )

    # ── _verify_trace ───────────────────────────────────────────────

    def test_verification_trace_complete(self, agent: VerificationAgent) -> None:
        """module -> component -> requirement -> PASSED."""
        self._seed_full_trace(agent)
        passed, detail = agent._verify_trace("mod-auth-p01")
        assert passed is True
        assert "complete" in detail

    def test_verification_trace_broken(self, agent: VerificationAgent) -> None:
        """Module sin componente -> FAILED."""
        self._seed_module_only(agent)
        passed, detail = agent._verify_trace("mod-orphan-p01")
        assert passed is False
        assert "IMPLEMENTS" in detail

    def test_verification_no_code_module(self, agent: VerificationAgent) -> None:
        """Module ID que no existe en KG -> FAILED graceful."""
        passed, detail = agent._verify_trace("mod-no-existe")
        assert passed is False
        assert "not found" in detail

    def test_verification_component_no_requirement(
        self,
        agent: VerificationAgent,
    ) -> None:
        """Componente sin requirement -> FAILED."""
        agent.write_graph(
            Node(
                id="mod-test-p01",
                node_type=NodeType.code_module,
                properties={"name": "test.module"},
            ),
        )
        agent.write_graph(
            Node(
                id="comp-test-p01",
                node_type=NodeType.component,
                properties={"name": "TestComponent"},
            ),
        )
        agent._ctx.knowledge_graph.add_edge(
            Edge(
                source_id="mod-test-p01",
                target_id="comp-test-p01",
                edge_type=EdgeType.implements,
            ),
        )
        passed, detail = agent._verify_trace("mod-test-p01")
        assert passed is False
        assert "requirement" in detail.lower()

    # ── LLM Judge ───────────────────────────────────────────────────

    async def test_validation_llm_judge_passes(
        self,
        context: AgentContext,
    ) -> None:
        """LLM retorna >= threshold -> validation PASSED."""
        agent = VerificationAgent(context, llm_client=_JudgePassLLM())
        results = await agent._validate_code(
            "p-01",
            [],
        )
        # With no requirements in KG, results should be empty
        # So seed a requirement
        context.knowledge_graph.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "text": "Login",
                    "acceptance_criteria": ["Usuario puede loguearse"],
                },
            ),
        )
        results = await agent._validate_code("p-01", [])
        assert len(results) == 1
        assert results[0]["passed"] is True
        assert results[0]["score"] >= results[0]["threshold"]

    async def test_validation_llm_judge_fails(
        self,
        context: AgentContext,
    ) -> None:
        """LLM retorna < threshold -> validation FAILED."""
        agent = VerificationAgent(context, llm_client=_JudgeFailLLM())
        context.knowledge_graph.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "text": "Login",
                    "acceptance_criteria": ["Usuario puede loguearse"],
                },
            ),
        )
        results = await agent._validate_code("p-01", [])
        assert len(results) == 1
        assert results[0]["passed"] is False
        assert results[0]["score"] < results[0]["threshold"]

    async def test_validation_llm_invalid_response(
        self,
        context: AgentContext,
    ) -> None:
        """LLM retorna texto no numerico -> fallback a score=1."""
        agent = VerificationAgent(context, llm_client=_JudgeInvalidLLM())
        context.knowledge_graph.add_node(
            Node(
                id="r-001",
                node_type=NodeType.requirement,
                properties={
                    "text": "Login",
                    "acceptance_criteria": ["Usuario puede loguearse"],
                },
            ),
        )
        results = await agent._validate_code("p-01", [])
        assert len(results) == 1
        assert results[0]["score"] == 1
        assert results[0]["passed"] is False

    # ── Quality Gates ───────────────────────────────────────────────

    async def test_quality_gate_invoked(
        self,
        context: AgentContext,
    ) -> None:
        """Verification dispara quality gates."""
        qg = QualityGate(context.event_bus, context.knowledge_graph)
        agent = VerificationAgent(context, llm_client=_JudgePassLLM(), quality_gate=qg)

        # Seed incomplete data so gates fail
        self._seed_module_only(agent)

        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await context.event_bus.subscribe(
            "proyecto.p-01.quality.gate.failed",
            collector,
        )

        await agent._fire_quality_gates("p-01")

        # At least one gate should fire (module without edges fails traceability)
        assert len(received) >= 1
        assert "gate" in received[0]
        assert "reason" in received[0]

    # ── handle_event end-to-end ─────────────────────────────────────

    async def test_handle_event_emits_verification_complete(
        self,
        agent: VerificationAgent,
    ) -> None:
        """handle_event emite verification.complete."""
        self._seed_full_trace(agent)

        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("verification.complete", collector)
        await agent.start()

        event = Event(
            topic="code.committed",
            source="coder-agent",
            project_id="p-01",
            data={
                "module_id": "mod-auth-p01",
                "component": "auth",
                "files": [],
                "tests_passed": False,
            },
        )
        await agent._handle_event_wrapper("code.committed", event)

        assert len(received) == 1
        payload = received[0]
        assert payload["module_id"] == "mod-auth-p01"
        assert payload["trace_ok"] is True
        await agent.stop()

    async def test_handle_event_trace_broken_emits_failed(
        self,
        agent: VerificationAgent,
    ) -> None:
        """Trace roto -> verification.complete con trace_ok=False."""
        self._seed_module_only(agent)

        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("verification.complete", collector)
        await agent.start()

        event = Event(
            topic="code.committed",
            source="coder-agent",
            project_id="p-01",
            data={
                "module_id": "mod-orphan-p01",
                "component": "auth",
                "files": [],
                "tests_passed": False,
            },
        )
        await agent._handle_event_wrapper("code.committed", event)

        assert len(received) == 1
        payload = received[0]
        assert payload["trace_ok"] is False
        await agent.stop()

    # ── Dia 18: Casos borde ─────────────────────────────────────────

    async def test_verification_missing_trace(
        self,
        agent: VerificationAgent,
    ) -> None:
        """Modulo sin componente en KG -> FAILED con mensaje claro."""
        # Seed module-only (no component, no edges)
        agent.write_graph(
            Node(
                id="mod-missing-comp",
                node_type=NodeType.code_module,
                properties={"name": "missing.trace.module"},
            ),
        )

        received: list[dict[str, object]] = []

        async def collector(topic: str, data: object) -> None:
            if isinstance(data, Event):
                received.append(data.data)

        await agent._ctx.event_bus.subscribe("verification.complete", collector)
        await agent.start()

        event = Event(
            topic="code.committed",
            source="coder-agent",
            project_id="p-01",
            data={
                "module_id": "mod-missing-comp",
                "component": "orphan",
                "files": [],
                "tests_passed": True,
            },
        )
        await agent._handle_event_wrapper("code.committed", event)

        assert len(received) == 1
        payload = received[0]
        assert payload["trace_ok"] is False
        # The detail must contain a clear message referencing the missing trace
        detail = payload.get("detail", "")
        assert isinstance(detail, str) and len(detail) > 0, (
            "Missing trace must include a descriptive detail message"
        )
        assert (
            "IMPLEMENTS" in detail or "not found" in detail.lower() or "trace" in detail.lower()
        ), f"Detail must mention the missing trace: {detail}"
        await agent.stop()
