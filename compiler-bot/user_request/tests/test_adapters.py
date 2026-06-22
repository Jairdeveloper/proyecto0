"""Tests for NLG channel adapters."""

import json

from user_request.contracts.enums import RequestChannel
from user_request.contracts.response import ResponseObject
from user_request.nlg.adapters import resolve_adapter
from user_request.nlg.adapters.agent import AgentAdapter
from user_request.nlg.adapters.api import APIAdapter
from user_request.nlg.adapters.cli import CLIAdapter
from user_request.nlg.adapters.editor import EditorAdapter
from user_request.nlg.adapters.webui import WebUIAdapter


class TestCLIAdapter:
    def test_adapt_content(self):
        adapter = CLIAdapter()
        resp = ResponseObject(success=True)
        result = adapter.adapt("Creado modulo pagos.", resp)
        assert "Creado modulo pagos" in result

    def test_adapt_empty(self):
        adapter = CLIAdapter()
        resp = ResponseObject(success=True)
        result = adapter.adapt("", resp)
        assert result == ""


class TestAPIAdapter:
    def test_adapt_returns_json(self):
        adapter = APIAdapter()
        resp = ResponseObject(success=True, message="Creado")
        result = adapter.adapt("Creado modulo pagos.", resp)
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["message"] == "Creado modulo pagos."

    def test_adapt_error(self):
        adapter = APIAdapter()
        resp = ResponseObject(success=False, error="Falló")
        result = adapter.adapt("", resp)
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["error"] == "Falló"


class TestWebUIAdapter:
    def test_adapt_returns_html(self):
        adapter = WebUIAdapter()
        resp = ResponseObject(success=True, message="Creado")
        result = adapter.adapt("Creado modulo pagos.", resp)
        assert "<div" in result
        assert "Creado modulo pagos" in result

    def test_adapt_error_html(self):
        adapter = WebUIAdapter()
        resp = ResponseObject(success=False, error="Error")
        result = adapter.adapt("Error: algo fallo", resp)
        assert "error" in result or "Error" in result


class TestEditorAdapter:
    def test_adapt_success(self):
        adapter = EditorAdapter()
        resp = ResponseObject(success=True)
        result = adapter.adapt("Modulo creado", resp)
        assert result.startswith("✓")

    def test_adapt_error(self):
        adapter = EditorAdapter()
        resp = ResponseObject(success=False)
        result = adapter.adapt("Algo fallo", resp)
        assert result.startswith("✗")

    def test_adapt_truncates_long_content(self):
        adapter = EditorAdapter()
        resp = ResponseObject(success=True)
        long_content = "x" * 300
        result = adapter.adapt(long_content, resp)
        assert len(result) <= 205  # 200 max + "✓ " prefix

    def test_adapt_empty(self):
        adapter = EditorAdapter()
        resp = ResponseObject(success=True)
        result = adapter.adapt("", resp)
        assert result == ""


class TestAgentAdapter:
    def test_adapt_returns_json(self):
        adapter = AgentAdapter()
        resp = ResponseObject(success=True, message="OK")
        result = adapter.adapt("Modulo creado.", resp)
        parsed = json.loads(result)
        assert parsed["_type"] == "agent_response"
        assert parsed["status"] == "ok"
        assert parsed["summary"] == "Modulo creado."

    def test_adapt_error(self):
        adapter = AgentAdapter()
        resp = ResponseObject(success=False, error="Error")
        result = adapter.adapt("", resp)
        parsed = json.loads(result)
        assert parsed["status"] == "error"


class TestResolveAdapter:
    def test_cli(self):
        adapter = resolve_adapter(RequestChannel.CLI)
        assert isinstance(adapter, CLIAdapter)

    def test_api(self):
        adapter = resolve_adapter(RequestChannel.API)
        assert isinstance(adapter, APIAdapter)

    def test_webui(self):
        adapter = resolve_adapter(RequestChannel.WEBUI)
        assert isinstance(adapter, WebUIAdapter)

    def test_editor(self):
        adapter = resolve_adapter(RequestChannel.EDITOR)
        assert isinstance(adapter, EditorAdapter)

    def test_agent(self):
        adapter = resolve_adapter(RequestChannel.AGENT)
        assert isinstance(adapter, AgentAdapter)

    def test_unknown_falls_back_to_cli(self):
        adapter = resolve_adapter("unknown")  # type: ignore[arg-type]
        assert isinstance(adapter, CLIAdapter)
