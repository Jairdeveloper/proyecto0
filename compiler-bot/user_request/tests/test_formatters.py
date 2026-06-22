"""Tests for NLG formatters."""

from user_request.contracts.enums import RequestChannel
from user_request.contracts.response import ResponseObject
from user_request.nlg.formatters import resolve_formatter
from user_request.nlg.formatters.error import ErrorFormatter
from user_request.nlg.formatters.ir_display import IRFormatter
from user_request.nlg.formatters.metrics import MetricFormatter
from user_request.nlg.formatters.success import SuccessFormatter


class TestSuccessFormatter:
    def test_format_with_message(self):
        fmt = SuccessFormatter()
        resp = ResponseObject(success=True, message="Creado modulo pagos.")
        result = fmt.format(resp)
        assert "Creado modulo pagos" in result

    def test_format_with_data(self):
        fmt = SuccessFormatter()
        resp = ResponseObject(
            success=True,
            data={"module": "pagos", "tech": "nestjs"},
        )
        result = fmt.format(resp)
        assert "pagos" in result
        assert "nestjs" in result

    def test_format_without_message_or_data(self):
        fmt = SuccessFormatter()
        resp = ResponseObject(success=True)
        result = fmt.format(resp)
        assert "Operacion completada" in result

    def test_format_with_suggestions(self):
        fmt = SuccessFormatter()
        resp = ResponseObject(
            success=True,
            message="Modulo creado.",
            suggestions=["Crear entidad", "Anadir auth"],
        )
        result = fmt.format(resp)
        assert "Sugerencias" in result
        assert "Crear entidad" in result

    def test_format_with_files_in_data(self):
        fmt = SuccessFormatter()
        resp = ResponseObject(
            success=True,
            data={"module": "pagos", "files": ["controller.ts", "service.ts"]},
        )
        result = fmt.format(resp)
        assert "controller.ts" in result
        assert "service.ts" in result


class TestErrorFormatter:
    def test_format_with_error(self):
        fmt = ErrorFormatter()
        resp = ResponseObject(success=False, error="El modulo ya existe.")
        result = fmt.format(resp)
        assert "Error:" in result
        assert "ya existe" in result

    def test_format_with_suggestions(self):
        fmt = ErrorFormatter()
        resp = ResponseObject(
            success=False,
            error="Modulo duplicado",
            suggestions=["Usar otro nombre", "Eliminar el existente"],
        )
        result = fmt.format(resp)
        assert "Sugerencias" in result
        assert "otro nombre" in result


class TestIRFormatter:
    def test_format_with_ir_data(self):
        fmt = IRFormatter()
        resp = ResponseObject(
            success=True,
            data={
                "ir": {
                    "accion": "create",
                    "modulo": "pagos",
                    "entidades": [{"nombre": "Pago", "tipo": "entity"}],
                    "tecnologias": ["NestJS", "Prisma"],
                    "plan": [{"descripcion": "Crear modulo"}],
                }
            },
        )
        result = fmt.format(resp)
        assert "Intermediate Representation" in result
        assert "create" in result
        assert "Pago" in result
        assert "NestJS" in result

    def test_format_without_ir_data(self):
        fmt = IRFormatter()
        resp = ResponseObject(success=True, data={"key": "value"})
        result = fmt.format(resp)
        assert result  # should not crash


class TestMetricFormatter:
    def test_format_with_metrics(self):
        fmt = MetricFormatter()
        resp = ResponseObject(
            success=True,
            data={"metrics": {"stages": 8, "errors": 0, "duration_ms": 255}},
        )
        result = fmt.format(resp)
        assert "Pipeline" in result
        assert "8" in result

    def test_format_without_metrics(self):
        fmt = MetricFormatter()
        resp = ResponseObject(success=True, data={})
        result = fmt.format(resp)
        assert "(sin metricas)" in result or not result


class TestResolveFormatter:
    def test_error_response_uses_error_formatter(self):
        resp = ResponseObject(success=False, error="algo fallo")
        fmt = resolve_formatter(resp)
        assert isinstance(fmt, ErrorFormatter)

    def test_ir_data_uses_ir_formatter(self):
        resp = ResponseObject(success=True, data={"ir": {}})
        fmt = resolve_formatter(resp)
        assert isinstance(fmt, IRFormatter)

    def test_metrics_data_uses_metric_formatter(self):
        resp = ResponseObject(success=True, data={"metrics": {}})
        fmt = resolve_formatter(resp)
        assert isinstance(fmt, MetricFormatter)

    def test_success_uses_success_formatter(self):
        resp = ResponseObject(success=True, message="ok")
        fmt = resolve_formatter(resp)
        assert isinstance(fmt, SuccessFormatter)
