"""Integration tests for NLG Pipeline."""

from user_request.contracts.enums import RequestChannel
from user_request.contracts.response import ResponseObject
from user_request.nlg.pipeline import NLGPipeline


class TestNLGPipeline:
    def test_process_success_response(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(success=True, message="Creado modulo pagos.")
        result = pipeline.process(resp)
        assert "Creado modulo pagos" in result

    def test_process_error_response(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(success=False, error="El modulo ya existe.")
        result = pipeline.process(resp)
        assert "Error" in result

    def test_process_with_channel_override(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(success=True, message="OK")
        result = pipeline.process(resp, channel=RequestChannel.API)
        assert '"success": true' in result or "success" in result

    def test_process_empty_response(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(success=True)
        result = pipeline.process(resp)
        assert result

    def test_process_with_suggestions(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(
            success=True,
            message="Modulo creado.",
            suggestions=["Crear entidad Usuario"],
        )
        result = pipeline.process(resp)
        assert "Crear entidad" in result

    def test_process_with_data(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(
            success=True,
            data={"module": "pagos", "tech": "nestjs"},
        )
        result = pipeline.process(resp)
        assert "pagos" in result

    def test_process_with_ir_data(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(
            success=True,
            data={"ir": {"accion": "create", "modulo": "pagos"}},
        )
        result = pipeline.process(resp)
        assert "Intermediate Representation" in result

    def test_process_with_metrics_data(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(
            success=True,
            data={"metrics": {"stages": 8, "errors": 0}},
        )
        result = pipeline.process(resp)
        assert "Pipeline" in result

    def test_set_channel(self):
        pipeline = NLGPipeline(channel=RequestChannel.CLI)
        assert pipeline._channel == RequestChannel.CLI
        pipeline.set_channel(RequestChannel.API)
        assert pipeline._channel == RequestChannel.API

    def test_process_with_metadata(self):
        pipeline = NLGPipeline()
        resp = ResponseObject(success=True, message="OK")
        result = pipeline.process_with_metadata(resp)
        assert result.content == "OK"
        assert result.output
        assert result.metadata["formatter"]
        assert result.metadata["adapter"]
        assert result.metadata["channel"] == "cli"
