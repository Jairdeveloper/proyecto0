"""Tests for User Request Layer contracts (Pydantic models + enums)."""

from __future__ import annotations

import json

import pytest

from user_request.contracts.enums import IntentType, Language, RequestChannel, SlotName
from user_request.contracts.request import (
    AmbiguityResult,
    Entities,
    Entity,
    IntentResult,
    RequestContext,
    RequestObject,
    Slots,
)
from user_request.contracts.response import ResponseObject


# ---------------------------------------------------------------------------
# Enum tests
# ---------------------------------------------------------------------------


class TestIntentType:
    def test_values_are_unique(self):
        values = [e.value for e in IntentType]
        assert len(values) == len(set(values))

    def test_from_alias_scaffold_resolves_to_create(self):
        assert IntentType.from_alias("SCAFFOLD") == IntentType.CREATE

    def test_from_alias_generate_resolves_to_create(self):
        assert IntentType.from_alias("GENERATE") == IntentType.CREATE

    def test_from_alias_query_resolves_to_read(self):
        assert IntentType.from_alias("QUERY") == IntentType.READ

    def test_from_alias_explore_resolves_to_read(self):
        assert IntentType.from_alias("EXPLORE") == IntentType.READ

    def test_from_alias_modify_resolves_to_update(self):
        assert IntentType.from_alias("MODIFY") == IntentType.UPDATE

    def test_from_alias_remove_resolves_to_delete(self):
        assert IntentType.from_alias("REMOVE") == IntentType.DELETE

    def test_from_alias_help_resolves_to_explain(self):
        assert IntentType.from_alias("HELP") == IntentType.EXPLAIN

    def test_from_alias_config_resolves_to_configure(self):
        assert IntentType.from_alias("CONFIG") == IntentType.CONFIGURE

    def test_from_alias_unknown_returns_create(self):
        assert IntentType.from_alias("BOGUS") == IntentType.CREATE

    def test_from_alias_case_insensitive(self):
        assert IntentType.from_alias("scaffold") == IntentType.CREATE

    def test_aliases_for_create(self):
        aliases = IntentType.aliases_for(IntentType.CREATE)
        assert "scaffold" in aliases
        assert "generate" in aliases

    def test_known_aliases_includes_all(self):
        known = IntentType.known_aliases()
        assert "scaffold" in known
        assert "query" in known
        assert "help" in known


class TestRequestChannel:
    def test_values_are_unique(self):
        values = [e.value for e in RequestChannel]
        assert len(values) == len(set(values))

    def test_default_is_cli(self):
        assert RequestChannel.CLI.value == "cli"

    def test_all_channels_present(self):
        expected = {"cli", "webui", "api", "editor", "agent"}
        assert {e.value for e in RequestChannel} == expected


class TestLanguage:
    def test_es_and_en(self):
        assert Language.ES.value == "es"
        assert Language.EN.value == "en"


class TestSlotName:
    def test_values_are_unique(self):
        values = [e.value for e in SlotName]
        assert len(values) == len(set(values))


# ---------------------------------------------------------------------------
# Request model tests
# ---------------------------------------------------------------------------


class TestIntentResult:
    def test_minimal_construction(self):
        r = IntentResult(primary=IntentType.CREATE, confidence=0.95)
        assert r.primary == IntentType.CREATE
        assert r.confidence == 0.95
        assert r.secondary is None
        assert r.classifier == "rule"
        assert r.scores == {}
        assert r.domain == "backend"

    def test_full_construction(self):
        r = IntentResult(
            primary=IntentType.UPDATE,
            secondary=IntentType.READ,
            confidence=0.8,
            classifier="semantic",
            scores={"UPDATE": 0.8, "READ": 0.3},
            domain="frontend",
        )
        assert r.primary == IntentType.UPDATE
        assert r.secondary == IntentType.READ
        assert r.classifier == "semantic"

    def test_immutable(self):
        r = IntentResult(primary=IntentType.CREATE, confidence=0.9)
        with pytest.raises((AttributeError, TypeError)):
            r.primary = IntentType.READ  # type: ignore[misc]


class TestEntity:
    def test_minimal(self):
        e = Entity(nombre="pagos", tipo="module")
        assert e.nombre == "pagos"
        assert e.tipo == "module"
        assert e.rol == ""
        assert not e.negado

    def test_negated(self):
        e = Entity(nombre="auth", tipo="tech", rol="oauth", negado=True)
        assert e.negado


class TestEntities:
    def test_empty(self):
        e = Entities()
        assert e.modulos == []
        assert e.techs == []
        assert e.requisitos == []

    def test_with_items(self):
        e = Entities(
            modulos=[Entity(nombre="pagos", tipo="module")],
            techs=[Entity(nombre="nestjs", tipo="tech")],
        )
        assert len(e.modulos) == 1
        assert e.modulos[0].nombre == "pagos"


class TestSlots:
    def test_defaults(self):
        s = Slots()
        assert s.accion is None
        assert s.tipo is None
        assert not s.completado
        assert s.faltantes == []
        assert s.atributos == []

    def test_complete(self):
        s = Slots(
            accion="create",
            tipo="module",
            nombre="pagos",
            tech="nestjs",
            completado=True,
        )
        assert s.accion == "create"
        assert s.completado


class TestAmbiguityResult:
    def test_not_detected(self):
        a = AmbiguityResult()
        assert not a.detected
        assert a.elementos == []

    def test_detected(self):
        a = AmbiguityResult(
            detected=True,
            elementos=[{"tipo": "slot_faltante", "descripcion": "Falta nombre"}],
        )
        assert a.detected
        assert len(a.elementos) == 1


class TestRequestContext:
    def test_defaults(self):
        ctx = RequestContext()
        assert ctx.session_id == ""
        assert ctx.defaults == {"tech": "nestjs"}
        assert ctx.channel == RequestChannel.CLI

    def test_custom(self):
        ctx = RequestContext(
            session_id="ses-001",
            defaults={"tech": "react"},
            channel=RequestChannel.WEBUI,
        )
        assert ctx.session_id == "ses-001"
        assert ctx.channel == RequestChannel.WEBUI


class TestRequestObject:
    def test_minimal(self):
        obj = RequestObject(
            raw="crea modulo pagos",
            normalized="crea modulo pagos",
            intent=IntentResult(primary=IntentType.CREATE, confidence=0.95),
            entities=Entities(),
            slots=Slots(),
        )
        assert obj.raw == "crea modulo pagos"
        assert obj.intent.primary == IntentType.CREATE
        assert obj.channel == RequestChannel.CLI
        assert obj.metadata == {}

    def test_full(self):
        obj = RequestObject(
            raw="crea modulo pagos con NestJS",
            normalized="crea modulo pagos con nestjs",
            intent=IntentResult(primary=IntentType.CREATE, confidence=0.95),
            entities=Entities(
                modulos=[Entity(nombre="pagos", tipo="module")],
                techs=[Entity(nombre="nestjs", tipo="tech")],
            ),
            slots=Slots(accion="create", tipo="module", nombre="pagos", completado=True),
            channel=RequestChannel.CLI,
            context=RequestContext(session_id="ses-001"),
            metadata={"version": "2.9.0"},
        )
        assert obj.entities.modulos[0].nombre == "pagos"
        assert obj.slots.completado

    def test_serialization(self):
        obj = RequestObject(
            raw="test",
            normalized="test",
            intent=IntentResult(primary=IntentType.CREATE, confidence=0.9),
            entities=Entities(),
            slots=Slots(),
        )
        data = obj.model_dump()
        assert data["raw"] == "test"
        assert data["channel"] == "cli"
        assert data["intent"]["primary"] == "create"

    def test_deserialization(self):
        data = {
            "raw": "test",
            "normalized": "test",
            "intent": {"primary": "create", "confidence": 0.9},
            "entities": {},
            "slots": {},
        }
        obj = RequestObject.model_validate(data)
        assert obj.intent.primary == IntentType.CREATE
        assert obj.slots.accion is None


# ---------------------------------------------------------------------------
# Response model tests
# ---------------------------------------------------------------------------


class TestResponseObject:
    def test_success_defaults(self):
        r = ResponseObject()
        assert r.success
        assert r.message is None
        assert r.error is None
        assert r.suggestions == []
        assert r.channel == RequestChannel.CLI

    def test_error_response(self):
        r = ResponseObject(
            success=False,
            error="Module already exists",
            message=None,
        )
        assert not r.success
        assert r.error == "Module already exists"

    def test_with_data(self):
        r = ResponseObject(
            success=True,
            message="Creado modulo pagos en NestJS",
            data={"module": "pagos", "tech": "nestjs"},
        )
        assert r.data is not None
        assert r.data["module"] == "pagos"

    def test_serialization_roundtrip(self):
        r = ResponseObject(
            success=True,
            message="OK",
            channel=RequestChannel.API,
            metadata={"duration_ms": 150},
        )
        raw = r.model_dump_json()
        restored = ResponseObject.model_validate(json.loads(raw))
        assert restored.message == "OK"
        assert restored.channel == RequestChannel.API
        assert restored.metadata["duration_ms"] == 150

    def test_suggestions(self):
        r = ResponseObject(
            success=True,
            message="Done",
            suggestions=["Crear entidad Usuario", "Anadir autenticacion"],
        )
        assert len(r.suggestions) == 2
