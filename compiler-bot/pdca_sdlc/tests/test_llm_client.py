"""Tests for core/llm_client.py."""

import json

import pytest

from pdca_sdlc.core.llm_client import LLMClient, LLMError


class TestLLMClient:
    def test_mock_backend_returns_response(self) -> None:
        client = LLMClient({"model": "mock"})
        response = client.complete("Hello")
        assert "Mock response to:" in response
        assert "Hello" in response

    def test_json_response_format(self) -> None:
        client = LLMClient({"model": "mock"})
        response = client.complete("test prompt", response_format="json")
        parsed = json.loads(response)
        assert "response" in parsed

    def test_mock_respects_max_tokens(self) -> None:
        client = LLMClient({"model": "mock"})
        response = client.complete("Hello world", max_tokens=5)
        assert len(response) <= 50

    def test_unknown_model_raises_error(self) -> None:
        client = LLMClient({"model": "nonexistent", "max_retries": 0})
        with pytest.raises(LLMError, match="Unknown model backend"):
            client.complete("test")

    def test_retry_on_failure(self) -> None:
        client = LLMClient({"model": "error", "max_retries": 2})
        with pytest.raises(LLMError):
            client.complete("test")

    def test_default_config(self) -> None:
        client = LLMClient()
        assert client.model == "mock"
        assert client.temperature == 0.3
        assert client.config["max_tokens"] == 4096

    def test_custom_config(self) -> None:
        client = LLMClient(
            {
                "model": "pro",
                "temperature": 0.1,
                "max_tokens": 8192,
                "timeout": 60,
            }
        )
        assert client.model == "pro"
        assert client.temperature == 0.1
        assert client.config["max_tokens"] == 8192
