"""Tests for protocols/event_schemas.py."""

import json

from pdca_sdlc.protocols.event_schemas import (
    AdaptationComplete,
    ArchitectureProposed,
    CodeCommitted,
    CodeFailed,
    ProjectInitialized,
    QualityGateResult,
    RequirementCreated,
    RiskIdentified,
)


class TestProjectInitialized:
    def test_create(self) -> None:
        s = ProjectInitialized(description="Crear modulo de pagos", project_id="p-01")
        assert s.description == "Crear modulo de pagos"
        assert s.project_id == "p-01"

    def test_serialize_roundtrip(self) -> None:
        s = ProjectInitialized(description="test", project_id="p-01")
        data = s.model_dump()
        restored = ProjectInitialized.model_validate(data)
        assert restored == s


class TestAdaptationComplete:
    def test_create(self) -> None:
        s = AdaptationComplete(
            complexity="simple",
            lifecycle="fast_track",
            processes=["6.1", "6.3"],
            activities=["Requirements", "Implementation"],
            effort_estimate={"days": 3},
        )
        assert s.complexity == "simple"
        assert s.lifecycle == "fast_track"
        assert s.effort_estimate == {"days": 3}

    def test_serialize_roundtrip(self) -> None:
        s = AdaptationComplete(
            complexity="moderate",
            lifecycle="iterative",
            processes=["6.1", "6.2", "6.3"],
            activities=["Req", "Arch", "Impl"],
            effort_estimate={"days": 10},
        )
        data = s.model_dump()
        restored = AdaptationComplete.model_validate(data)
        assert restored == s

    def test_invalid_complexity(self) -> None:
        try:
            AdaptationComplete(
                complexity="invalid",  # type: ignore
                lifecycle="fast_track",
                processes=[],
                activities=[],
                effort_estimate={},
            )
            assert False, "Should have raised"
        except Exception:
            pass


class TestRequirementCreated:
    def test_create(self) -> None:
        s = RequirementCreated(
            requirement_ids=["r-001", "r-002"],
            count=2,
        )
        assert len(s.requirement_ids) == 2
        assert s.count == 2

    def test_serialize_roundtrip(self) -> None:
        s = RequirementCreated(requirement_ids=["r-01"], count=1)
        data = s.model_dump()
        restored = RequirementCreated.model_validate(data)
        assert restored == s


class TestArchitectureProposed:
    def test_create(self) -> None:
        s = ArchitectureProposed(
            component_ids=["c-01", "c-02"],
            components=[{"name": "Auth"}, {"name": "Payments"}],
            requirement_ids=["r-01"],
        )
        assert len(s.components) == 2
        assert s.component_ids == ["c-01", "c-02"]

    def test_serialize_roundtrip(self) -> None:
        s = ArchitectureProposed(
            component_ids=["c-01"],
            components=[{"name": "Module", "type": "NestJS"}],
            requirement_ids=["r-01", "r-02"],
        )
        data = s.model_dump()
        restored = ArchitectureProposed.model_validate(data)
        assert restored == s


class TestCodeCommitted:
    def test_create(self) -> None:
        s = CodeCommitted(
            module_id="mod-01",
            component="AuthModule",
            files=["auth.controller.ts", "auth.service.ts"],
            tests_passed=True,
        )
        assert s.module_id == "mod-01"
        assert s.tests_passed is True

    def test_serialize_roundtrip(self) -> None:
        s = CodeCommitted(
            module_id="mod-01",
            component="AuthModule",
            files=["auth.ts"],
            tests_passed=False,
        )
        data = s.model_dump()
        restored = CodeCommitted.model_validate(data)
        assert restored == s


class TestCodeFailed:
    def test_create(self) -> None:
        s = CodeFailed(
            module_id="mod-01",
            component="AuthModule",
            error="SyntaxError: unexpected token",
        )
        assert "SyntaxError" in s.error

    def test_serialize_roundtrip(self) -> None:
        s = CodeFailed(module_id="mod-01", component="AuthModule", error="fail")
        data = s.model_dump()
        restored = CodeFailed.model_validate(data)
        assert restored == s


class TestQualityGateResult:
    def test_create(self) -> None:
        s = QualityGateResult(gate="ruff", result="passed")
        assert s.gate == "ruff"
        assert s.module_id is None

    def test_create_with_module(self) -> None:
        s = QualityGateResult(
            module_id="mod-01", gate="pytest", result="failed", details="3 tests failed"
        )
        assert s.module_id == "mod-01"
        assert s.details is not None

    def test_serialize_roundtrip(self) -> None:
        s = QualityGateResult(module_id="mod-01", gate="ruff", result="passed")
        data = s.model_dump()
        restored = QualityGateResult.model_validate(data)
        assert restored == s


class TestRiskIdentified:
    def test_create(self) -> None:
        s = RiskIdentified(
            description="LLM timeout",
            severity="high",
            source_event="code.generation",
        )
        assert s.severity == "high"
        assert s.source_event == "code.generation"

    def test_default_source_event(self) -> None:
        s = RiskIdentified(description="Error", severity="low")
        assert s.source_event == ""

    def test_serialize_roundtrip(self) -> None:
        s = RiskIdentified(description="Error", severity="critical")
        data = s.model_dump()
        restored = RiskIdentified.model_validate(data)
        assert restored == s


class TestJsonSerialization:
    def test_all_schemas_roundtrip_via_json(self) -> None:
        schemas = [
            ProjectInitialized(description="x", project_id="p-01"),
            AdaptationComplete(
                complexity="simple",
                lifecycle="fast_track",
                processes=[],
                activities=[],
                effort_estimate={},
            ),
            RequirementCreated(requirement_ids=[], count=0),
            ArchitectureProposed(
                component_ids=[],
                components=[],
                requirement_ids=[],
            ),
            CodeCommitted(module_id="m", component="c", files=[], tests_passed=True),
            CodeFailed(module_id="m", component="c", error="err"),
            QualityGateResult(gate="g", result="passed"),
            RiskIdentified(description="d", severity="low"),
        ]
        for s in schemas:
            raw = json.dumps(s.model_dump())
            parsed = json.loads(raw)
            restored = s.__class__.model_validate(parsed)
            assert restored == s, f"Failed for {s.__class__.__name__}"
