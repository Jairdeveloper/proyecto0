"""Adapter registry — resolve_adapter() factory."""

from __future__ import annotations

from user_request.contracts.enums import RequestChannel
from user_request.nlg.adapters.agent import AgentAdapter
from user_request.nlg.adapters.api import APIAdapter
from user_request.nlg.adapters.base import ChannelAdapter
from user_request.nlg.adapters.cli import CLIAdapter
from user_request.nlg.adapters.editor import EditorAdapter
from user_request.nlg.adapters.webui import WebUIAdapter

_ADAPTER_REGISTRY: dict[RequestChannel, ChannelAdapter] = {
    RequestChannel.CLI: CLIAdapter(),
    RequestChannel.API: APIAdapter(),
    RequestChannel.WEBUI: WebUIAdapter(),
    RequestChannel.EDITOR: EditorAdapter(),
    RequestChannel.AGENT: AgentAdapter(),
}

__all__ = [
    "AgentAdapter",
    "APIAdapter",
    "ChannelAdapter",
    "CLIAdapter",
    "EditorAdapter",
    "resolve_adapter",
    "WebUIAdapter",
]


def resolve_adapter(channel: RequestChannel) -> ChannelAdapter:
    """Resuelve el adaptador adecuado para un canal."""
    adapter = _ADAPTER_REGISTRY.get(channel)
    if adapter is None:
        return _ADAPTER_REGISTRY[RequestChannel.CLI]
    return adapter
