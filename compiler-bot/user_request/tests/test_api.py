"""Tests para la API HTTP de la capa User Request."""

from __future__ import annotations

import json
from http.server import HTTPServer
from threading import Thread
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from user_request.api.server import create_server
from user_request.contracts.enums import RequestChannel
from user_request.layer import UserRequestLayer


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def api_server() -> HTTPServer:
    """Arranca un servidor de pruebas en un thread."""
    server = create_server(host="127.0.0.1", port=0)  # puerto aleatorio
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()


@pytest.fixture
def server_url(api_server: HTTPServer) -> str:
    """URL base del servidor de pruebas."""
    host, port = api_server.server_address
    return f"http://{host}:{port}"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _post(url: str, data: dict[str, Any]) -> dict[str, Any]:
    """Envía una peticion POST y retorna el JSON de respuesta."""
    body = json.dumps(data).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _post_expect_error(
    url: str,
    data: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    """Envía una peticion POST y retorna (status, json_error)."""
    body = json.dumps(data).encode("utf-8")
    req = Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req) as resp:
            return (resp.status, json.loads(resp.read().decode("utf-8")))
    except HTTPError as exc:
        return (exc.code, json.loads(exc.read().decode("utf-8")))


def _get(url: str) -> dict[str, Any]:
    """Envía una peticion GET y retorna el JSON de respuesta."""
    with urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ------------------------------------------------------------------
# Tests Health
# ------------------------------------------------------------------


class TestHealthEndpoint:
    """Tests para GET /api/health."""

    def test_health_returns_ok(self, server_url: str) -> None:
        result = _get(f"{server_url}/api/health")
        assert result["status"] == "ok"
        assert result["service"] == "user-request-api"

    def test_health_via_post(self, server_url: str) -> None:
        result = _post(f"{server_url}/api/health", {})
        assert result["status"] == "ok"

    def test_unknown_route_returns_404(self, server_url: str) -> None:
        status, result = _post_expect_error(f"{server_url}/api/unknown", {})
        assert status == 404
        assert "error" in result


# ------------------------------------------------------------------
# Tests /api/nlu
# ------------------------------------------------------------------


class TestNLUEndpoint:
    """Tests para POST /api/nlu."""

    def test_nlu_classifies_intent(self, server_url: str) -> None:
        result = _post(f"{server_url}/api/nlu", {"text": "crea un modulo de pagos"})
        assert "intent" in result
        assert result["intent"]["primary"] == "create"

    def test_nlu_returns_entities(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/nlu",
            {"text": "crea un modulo de pagos con NestJS"},
        )
        assert "entities" in result

    def test_nlu_missing_text_returns_400(self, server_url: str) -> None:
        status, result = _post_expect_error(f"{server_url}/api/nlu", {})
        assert status == 400
        assert "text" in result.get("error", "")

    def test_nlu_empty_text_returns_400(self, server_url: str) -> None:
        status, result = _post_expect_error(f"{server_url}/api/nlu", {"text": ""})
        assert status == 400
        assert "empty" in result.get("error", "").lower()

    def test_nlu_accepts_channel_param(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/nlu",
            {"text": "consulta modulo", "channel": "api"},
        )
        assert result is not None
        assert "intent" in result

    def test_nlu_returns_normalized_text(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/nlu",
            {"text": "  CREA un módulo!!"},
        )
        assert "normalized" in result
        assert "!!" not in result["normalized"]

    def test_nlu_with_create_query(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/nlu",
            {"text": "crea un modulo de usuarios"},
        )
        assert result["intent"]["primary"] == "create"

    def test_nlu_with_read_query(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/nlu",
            {"text": "consulta el estado del pipeline"},
        )
        assert result["intent"]["primary"] == "read"

    def test_nlu_with_delete_query(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/nlu",
            {"text": "elimina el modulo de pagos"},
        )
        assert result["intent"]["primary"] == "delete"

    def test_nlu_cors_headers(self, server_url: str) -> None:
        body = json.dumps({"text": "test"}).encode("utf-8")
        req = Request(f"{server_url}/api/nlu", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        with urlopen(req) as resp:
            assert resp.headers.get("Access-Control-Allow-Origin") == "*"


# ------------------------------------------------------------------
# Tests /api/chat
# ------------------------------------------------------------------


class TestChatEndpoint:
    """Tests para POST /api/chat."""

    def test_chat_returns_success_structure(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/chat",
            {"text": "crea un modulo de pagos"},
        )
        assert "success" in result
        assert "message" in result
        assert "data" in result
        assert "channel" in result

    def test_chat_missing_text_returns_400(self, server_url: str) -> None:
        status, result = _post_expect_error(f"{server_url}/api/chat", {})
        assert status == 400
        assert "text" in result.get("error", "")

    def test_chat_empty_text_returns_400(self, server_url: str) -> None:
        status, result = _post_expect_error(f"{server_url}/api/chat", {"text": ""})
        assert status == 400

    def test_chat_accepts_channel_param(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/chat",
            {"text": "crea un modulo", "channel": "api"},
        )
        assert result["channel"] == "api"

    def test_chat_invalid_channel_falls_back_to_cli(self, server_url: str) -> None:
        result = _post(
            f"{server_url}/api/chat",
            {"text": "crea un modulo", "channel": "invalid"},
        )
        # Invalid channel defaults to CLI
        assert result["channel"] == "cli"


# ------------------------------------------------------------------
# Tests de servidor
# ------------------------------------------------------------------


class TestServerLifecycle:
    """Tests para creacion y ciclo de vida del servidor."""

    def test_create_server_returns_httpserver(self) -> None:
        """create_server debe retornar un HTTPServer."""
        server = create_server(host="127.0.0.1", port=0)
        assert server is not None
        assert isinstance(server, HTTPServer)
        server.server_close()

    def test_create_server_with_custom_layer(self) -> None:
        """create_server acepta una instancia de UserRequestLayer."""
        layer = UserRequestLayer(channel=RequestChannel.API)
        server = create_server(host="127.0.0.1", port=0, layer=layer)
        assert server is not None
        server.server_close()

    def test_server_routes_are_independent(self, server_url: str) -> None:
        """Multiples rutas deben funcionar independientemente."""
        h = _get(f"{server_url}/api/health")
        assert h["status"] == "ok"

        nlu = _post(f"{server_url}/api/nlu", {"text": "crea modulo"})
        assert "intent" in nlu

        h2 = _get(f"{server_url}/api/health")
        assert h2["status"] == "ok"


# ------------------------------------------------------------------
# Tests de WebUIAdapter (T5.1 verificación)
# ------------------------------------------------------------------


class TestWebUIAdapterVerification:
    """Verifica que WebUIAdapter produce HTML valido (T5.1)."""

    def test_webui_adapter_imports(self) -> None:
        from user_request.nlg.adapters import resolve_adapter
        from user_request.nlg.adapters.webui import WebUIAdapter

        adapter = WebUIAdapter()
        assert adapter is not None
        assert resolve_adapter(RequestChannel.WEBUI) is not None

    def test_webui_adapter_produces_html(self) -> None:
        from user_request.contracts.response import ResponseObject
        from user_request.nlg.adapters.webui import WebUIAdapter

        adapter = WebUIAdapter()
        response = ResponseObject(success=True, message="Modulo creado")
        output = adapter.adapt("Modulo creado exitosamente.", response)
        assert output.startswith("<")
        assert "Modulo creado" in output
        assert "</div>" in output

    def test_webui_adapter_error_html(self) -> None:
        from user_request.contracts.response import ResponseObject
        from user_request.nlg.adapters.webui import WebUIAdapter

        adapter = WebUIAdapter()
        response = ResponseObject(
            success=False,
            error="Algo salio mal",
        )
        output = adapter.adapt("Error: Algo salio mal", response)
        assert "Error" in output or "error" in output

    def test_webui_adapter_with_suggestions(self) -> None:
        from user_request.contracts.response import ResponseObject
        from user_request.nlg.adapters.webui import WebUIAdapter

        adapter = WebUIAdapter()
        response = ResponseObject(
            success=True,
            message="Hecho",
            suggestions=["prueba --help", "crea un modulo"],
        )
        output = adapter.adapt("Hecho", response)
        assert "<ul>" in output
        assert "crea un modulo" in output
