"""Tests for ConversationalMemory."""

from __future__ import annotations

import tempfile

import pytest

from agentic_pipeline.memory import ConversationalMemory


@pytest.fixture
def memory() -> ConversationalMemory:
    tmp = tempfile.mkdtemp()
    return ConversationalMemory(storage_dir=tmp)


class TestConversationalMemory:
    def test_init_creates_empty(self, memory: ConversationalMemory):
        assert memory.current_session == {"historial": [], "contexto": {}, "sesiones": []}

    def test_save_and_get_context(self, memory: ConversationalMemory):
        memory.save_context("key1", "value1")
        assert memory.get_context("key1") == "value1"

    def test_get_context_nonexistent(self, memory: ConversationalMemory):
        assert memory.get_context("nope") is None

    def test_add_history(self, memory: ConversationalMemory):
        memory.add_history("test instruction", "test response")
        recent = memory.get_recent(1)
        assert len(recent) == 1
        assert recent[0]["instruction"] == "test instruction"
        assert recent[0]["response"] == "test response"
        assert "timestamp" in recent[0]

    def test_get_recent_limit(self, memory: ConversationalMemory):
        for i in range(5):
            memory.add_history(f"inst {i}", f"resp {i}")
        recent = memory.get_recent(2)
        assert len(recent) == 2
        assert recent[0]["instruction"] == "inst 3"
        assert recent[1]["instruction"] == "inst 4"

    def test_get_recent_empty(self, memory: ConversationalMemory):
        assert memory.get_recent(5) == []

    def test_persists_between_instances(self, memory: ConversationalMemory):
        memory.save_context("persist", "works")
        storage = memory.storage_dir
        del memory
        memory2 = ConversationalMemory(storage_dir=str(storage))
        assert memory2.get_context("persist") == "works"

    def test_export(self, memory: ConversationalMemory):
        memory.save_context("a", 1)
        exported = memory.export()
        assert "a" in exported
        assert "contexto" in exported

    def test_set_session(self, memory: ConversationalMemory):
        memory.save_context("session_data", "original")
        memory.set_session("test_session")
        assert memory.get_context("session_data") is None
        memory.save_context("session_data", "new")
        assert memory.get_context("session_data") == "new"

    def test_list_sessions(self, memory: ConversationalMemory):
        memory.set_session("sess1")
        memory.save_context("k", "v1")
        memory.set_session("sess2")
        memory.save_context("k", "v2")
        sessions = memory.list_sessions()
        assert len(sessions) >= 2
        assert any("sess1" in s for s in sessions)
        assert any("sess2" in s for s in sessions)
