"""Tests for core/capability_registry.py."""

from pdca_sdlc.core.capability_registry import (
    CapabilityManifest,
    CapabilityRegistry,
)


class TestCapabilityRegistry:
    def test_register_and_get(self) -> None:
        reg = CapabilityRegistry()
        manifest = CapabilityManifest(
            agent_id="adaptation-agent",
            agent_name="AdaptationAgent",
            description="Clasifica proyectos y selecciona ciclo de vida",
            iso_12207={"process": "6.1", "activities": ["6.1.1"]},
            triggers=["project.initialized"],
            output_events=["adaptation.complete"],
        )
        reg.register(manifest)
        retrieved = reg.get("adaptation-agent")
        assert retrieved is not None
        assert retrieved.agent_name == "AdaptationAgent"
        assert retrieved.status == "active"

    def test_unregister(self) -> None:
        reg = CapabilityRegistry()
        manifest = CapabilityManifest(
            agent_id="test",
            agent_name="Test",
            description="",
            iso_12207={},
            triggers=[],
            output_events=[],
        )
        reg.register(manifest)
        assert reg.unregister("test")
        assert reg.get("test") is None

    def test_unregister_nonexistent(self) -> None:
        reg = CapabilityRegistry()
        assert not reg.unregister("ghost")

    def test_find_by_event(self) -> None:
        reg = CapabilityRegistry()
        reg.register(
            CapabilityManifest(
                agent_id="adaptation",
                agent_name="Adaptation",
                description="",
                iso_12207={},
                triggers=["project.initialized"],
                output_events=["adaptation.complete"],
            )
        )
        reg.register(
            CapabilityManifest(
                agent_id="reqs",
                agent_name="RequirementsAnalyst",
                description="",
                iso_12207={},
                triggers=["adaptation.complete"],
                output_events=["requirement.created"],
            )
        )
        found = reg.find_by_event("project.initialized")
        assert len(found) == 1
        assert found[0].agent_id == "adaptation"

    def test_find_by_event_exact_topic(self) -> None:
        reg = CapabilityRegistry()
        reg.register(
            CapabilityManifest(
                agent_id="coder",
                agent_name="CoderAgent",
                description="",
                iso_12207={},
                triggers=["requirement.created"],
                output_events=["code.committed"],
            )
        )
        found = reg.find_by_event("requirement.created")
        assert len(found) == 1
        assert found[0].agent_id == "coder"

    def test_find_by_iso_activity(self) -> None:
        reg = CapabilityRegistry()
        reg.register(
            CapabilityManifest(
                agent_id="architect",
                agent_name="ArchitectAgent",
                description="",
                iso_12207={"process": "6.2", "activities": ["6.2.3 Architecture Design"]},
                triggers=[],
                output_events=[],
            )
        )
        reg.register(
            CapabilityManifest(
                agent_id="coder",
                agent_name="CoderAgent",
                description="",
                iso_12207={"process": "6.3", "activities": ["6.3.1 Software Implementation"]},
                triggers=[],
                output_events=[],
            )
        )
        found = reg.find_by_iso_activity("Architecture")
        assert len(found) == 1
        assert found[0].agent_id == "architect"

    def test_get_all(self) -> None:
        reg = CapabilityRegistry()
        assert reg.get_all() == []
        reg.register(
            CapabilityManifest(
                agent_id="a",
                agent_name="A",
                description="",
                iso_12207={},
                triggers=[],
                output_events=[],
            )
        )
        reg.register(
            CapabilityManifest(
                agent_id="b",
                agent_name="B",
                description="",
                iso_12207={},
                triggers=[],
                output_events=[],
            )
        )
        assert len(reg.get_all()) == 2

    def test_update_status(self) -> None:
        reg = CapabilityRegistry()
        reg.register(
            CapabilityManifest(
                agent_id="test",
                agent_name="Test",
                description="",
                iso_12207={},
                triggers=[],
                output_events=[],
            )
        )
        assert reg.update_status("test", "disabled")
        assert reg.get("test") is not None
        assert reg.get("test").status == "disabled"

    def test_update_status_nonexistent(self) -> None:
        reg = CapabilityRegistry()
        assert not reg.update_status("ghost", "disabled")

    def test_count(self) -> None:
        reg = CapabilityRegistry()
        assert reg.count() == 0
        reg.register(
            CapabilityManifest(
                agent_id="a",
                agent_name="A",
                description="",
                iso_12207={},
                triggers=[],
                output_events=[],
            )
        )
        assert reg.count() == 1
