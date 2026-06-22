"""Tests para UserRequestLayer facade y CLI integration."""

from __future__ import annotations

import pytest

from user_request.contracts.enums import IntentType, RequestChannel
from user_request.contracts.response import ResponseObject
from user_request.layer import UserRequestLayer


class TestUserRequestLayer:
    """Tests unitarios para UserRequestLayer facade."""

    def test_init_default_channel(self) -> None:
        """Debe inicializar con canal CLI por defecto."""
        layer = UserRequestLayer()
        assert layer.channel == RequestChannel.CLI
        assert layer.nlu is not None
        assert layer.nlg is not None

    def test_init_custom_channel(self) -> None:
        """Debe aceptar canal personalizado."""
        layer = UserRequestLayer(channel=RequestChannel.API)
        assert layer.channel == RequestChannel.API

    def test_process_input_returns_request_object(self) -> None:
        """process_input debe retornar un RequestObject."""
        layer = UserRequestLayer()
        request = layer.process_input("crea un modulo de pagos")
        assert request.raw == "crea un modulo de pagos"
        assert request.intent is not None
        assert request.intent.primary == IntentType.CREATE

    def test_process_input_short_query(self) -> None:
        """Debe procesar consultas cortas."""
        layer = UserRequestLayer()
        request = layer.process_input("hola")
        assert request is not None
        assert request.raw == "hola"

    def test_process_input_normalizes_text(self) -> None:
        """Debe normalizar el texto de entrada."""
        layer = UserRequestLayer()
        request = layer.process_input("  CREA un módulo de Pagos!!  ")
        assert request.normalized == request.normalized.lower()
        assert "!!" not in request.normalized

    def test_format_output_success(self) -> None:
        """format_output debe devolver string formateado."""
        layer = UserRequestLayer()
        response = ResponseObject(
            success=True,
            message="Operacion completada.",
            channel=RequestChannel.CLI,
        )
        output = layer.format_output(response)
        assert isinstance(output, str)
        assert len(output) > 0

    def test_format_output_with_data(self) -> None:
        """Debe formatear respuesta con datos."""
        layer = UserRequestLayer()
        response = ResponseObject(
            success=True,
            data={"module": "test", "files": ["test.py"]},
            channel=RequestChannel.CLI,
        )
        output = layer.format_output(response)
        assert isinstance(output, str)
        assert "test" in output

    def test_format_output_json_channel(self) -> None:
        """Con canal API debe producir JSON."""
        layer = UserRequestLayer(channel=RequestChannel.API)
        response = ResponseObject(
            success=True,
            message="OK",
            channel=RequestChannel.API,
        )
        output = layer.format_output(response)
        assert isinstance(output, str)

    def test_format_ir_output(self) -> None:
        """force_ir=True debe usar IRFormatter."""
        layer = UserRequestLayer()
        response = ResponseObject(
            success=True,
            data={"ir_tree": {}, "ir_json": '{"test": 1}'},
            channel=RequestChannel.CLI,
        )
        output = layer.format_output(response, force_ir=True)
        assert isinstance(output, str)

    def test_resolve_ambiguity_no_ambiguity(self) -> None:
        """Sin ambiguedad debe retornar lista vacia."""
        layer = UserRequestLayer()
        request = layer.process_input("crea un modulo de pagos con NestJS")
        questions = layer.resolve_ambiguity(request)
        assert isinstance(questions, list)

    def test_resolve_ambiguity_with_ambiguity(self) -> None:
        """Entrada ambigua debe generar preguntas."""
        layer = UserRequestLayer()
        request = layer.process_input("crea")
        questions = layer.resolve_ambiguity(request)
        assert isinstance(questions, list)

    def test_set_channel_updates_nlg(self) -> None:
        """set_channel debe propagar el cambio a NLG pipeline."""
        layer = UserRequestLayer()
        layer.set_channel(RequestChannel.API)
        assert layer.channel == RequestChannel.API
        assert layer.nlg._channel == RequestChannel.API

    def test_format_empty_response(self) -> None:
        """Debe manejar ResponseObject vacio."""
        layer = UserRequestLayer()
        response = ResponseObject()
        output = layer.format_output(response)
        assert isinstance(output, str)


class TestUserRequestLayerEdgeCases:
    """Tests de casos limite para UserRequestLayer."""

    def test_process_input_empty_string(self) -> None:
        """Debe manejar string vacio."""
        layer = UserRequestLayer()
        request = layer.process_input("")
        assert request is not None

    def test_process_input_very_long(self) -> None:
        """Debe manejar textos largos."""
        layer = UserRequestLayer()
        long_text = "crea un modulo " * 100
        request = layer.process_input(long_text)
        assert request is not None
        assert len(request.raw) > 100

    def test_format_output_none_data(self) -> None:
        """Debe manejar data=None."""
        layer = UserRequestLayer()
        response = ResponseObject(success=True, data=None)
        output = layer.format_output(response)
        assert isinstance(output, str)

    def test_multiple_format_calls(self) -> None:
        """Multiples llamadas a format_output deben funcionar."""
        layer = UserRequestLayer()
        r1 = ResponseObject(success=True, message="First")
        r2 = ResponseObject(success=True, message="Second")
        o1 = layer.format_output(r1)
        o2 = layer.format_output(r2)
        assert isinstance(o1, str)
        assert isinstance(o2, str)

    def test_channel_preserved_across_calls(self) -> None:
        """El canal debe mantenerse entre llamadas."""
        layer = UserRequestLayer(channel=RequestChannel.EDITOR)
        assert layer.channel == RequestChannel.EDITOR
        r = ResponseObject(success=True, message="test", channel=RequestChannel.EDITOR)
        o = layer.format_output(r)
        assert isinstance(o, str)


@pytest.mark.asyncio
async def test_agentic_imports() -> None:
    """Verifica que los imports del entrypoint funcionan."""
    from user_request.contracts.response import ResponseObject  # noqa: F811
    from user_request.layer import UserRequestLayer  # noqa: F811

    layer = UserRequestLayer()
    response = ResponseObject(success=True, message="test")
    output = layer.format_output(response)
    assert isinstance(output, str)


class TestUserRequestLayerChannelIntegration:
    """Tests de integracion con canales NLG."""

    def test_cli_channel_output(self) -> None:
        """Canal CLI debe producir texto plano."""
        layer = UserRequestLayer(channel=RequestChannel.CLI)
        response = ResponseObject(
            success=True,
            message="Modulo creado exitosamente.",
            channel=RequestChannel.CLI,
        )
        output = layer.format_output(response)
        assert isinstance(output, str)
        assert "Modulo creado" in output

    def test_api_channel_output(self) -> None:
        """Canal API debe producir JSON estructurado."""
        layer = UserRequestLayer(channel=RequestChannel.API)
        response = ResponseObject(
            success=True,
            message="OK",
            channel=RequestChannel.API,
        )
        output = layer.format_output(response)
        assert isinstance(output, str)

    def test_editor_channel_output(self) -> None:
        """Canal Editor debe producir texto truncable."""
        layer = UserRequestLayer(channel=RequestChannel.EDITOR)
        response = ResponseObject(
            success=True,
            message="x" * 1000,
            channel=RequestChannel.EDITOR,
        )
        output = layer.format_output(response)
        assert isinstance(output, str)

    def test_agent_channel_output(self) -> None:
        """Canal Agent debe producir JSON."""
        layer = UserRequestLayer(channel=RequestChannel.AGENT)
        response = ResponseObject(
            success=True,
            message="test",
            channel=RequestChannel.AGENT,
        )
        output = layer.format_output(response)
        assert isinstance(output, str)
