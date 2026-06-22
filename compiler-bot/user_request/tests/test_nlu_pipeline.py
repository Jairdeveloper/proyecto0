"""Integration tests for NLU Pipeline."""

from user_request.contracts.enums import IntentType, RequestChannel
from user_request.contracts.request import RequestContext
from user_request.nlu.pipeline import NLUPipeline


class TestNLUPipeline:
    def test_process_create_module(self):
        pipeline = NLUPipeline()
        request = pipeline.process("crea un modulo de pagos")
        assert request.raw == "crea un modulo de pagos"
        assert request.intent.primary == IntentType.CREATE
        assert len(request.entities.modulos) >= 1
        assert request.slots.accion == "create"
        assert request.metadata["pipeline"] == "nlu"

    def test_process_with_tech(self):
        pipeline = NLUPipeline()
        request = pipeline.process("crea modulo con NestJS y Prisma")
        assert len(request.entities.techs) >= 2
        tech_names = [t.nombre for t in request.entities.techs]
        assert "nestjs" in tech_names

    def test_process_channel_propagation(self):
        pipeline = NLUPipeline()
        request = pipeline.process(
            "crea modulo",
            channel=RequestChannel.API,
        )
        assert request.channel == RequestChannel.API

    def test_process_with_context(self):
        pipeline = NLUPipeline()
        ctx = RequestContext(session_id="test-001", defaults={"tech": "react"})
        request = pipeline.process("crea modulo", context=ctx)
        assert request.context is not None
        assert request.context.session_id == "test-001"

    def test_process_metadata(self):
        pipeline = NLUPipeline()
        request = pipeline.process(
            "crea modulo",
            metadata={"source": "test"},
        )
        assert request.metadata["source"] == "test"
        assert "timestamp" in request.metadata

    def test_process_query_resolves_to_read(self):
        pipeline = NLUPipeline()
        request = pipeline.process("como se configura nestjs")
        assert request.intent.primary == IntentType.READ

    def test_process_delete(self):
        pipeline = NLUPipeline()
        request = pipeline.process("borra modulo payments")
        assert request.intent.primary == IntentType.DELETE
        assert request.slots.accion == "delete"

    def test_process_ambiguity_detection(self):
        pipeline = NLUPipeline()
        request = pipeline.process("xyz")
        assert request.ambiguity is not None

    def test_process_normalizes_input(self):
        pipeline = NLUPipeline()
        request = pipeline.process("  CREA MODULO DE PAGOS!!  ")
        assert request.normalized == "crea modulo de pagos"

    def test_process_empty_string(self):
        pipeline = NLUPipeline()
        request = pipeline.process("")
        assert request is not None
        assert request.intent is not None
