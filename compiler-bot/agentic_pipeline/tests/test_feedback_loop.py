"""Tests for FeedbackLoop, MetricsStore, GlobalFeedbackLoop, and ASTCache."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from agentic_pipeline.feedback_loop import FeedbackLoop, GlobalFeedbackLoop, get_global_feedback
from agentic_pipeline.metrics_store import MetricsStore
from agentic_pipeline.nodes.ast_cache import ASTCache


# ---------------------------------------------------------------------------
# FeedbackLoop (legacy file-based)
# ---------------------------------------------------------------------------

def test_legacy_feedback_record_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        import agentic_pipeline.config as cfg

        original = cfg.config.memory_dir
        cfg.config.memory_dir = tmpdir

        fb = FeedbackLoop()
        fb.record("test_stage", {"tokens": 5})
        fb.record("test_stage", {"tokens": 10})

        recent = fb.get_recent("test_stage")
        assert len(recent) == 2
        assert recent[0]["stage"] == "test_stage"
        assert recent[0]["metrics"]["tokens"] == 5
        assert recent[1]["metrics"]["tokens"] == 10

        cfg.config.memory_dir = original


def test_legacy_feedback_no_file():
    fb = FeedbackLoop(memory_dir="/tmp/nonexistent_feedback_test")
    recent = fb.get_recent("nonexistent_stage")
    assert recent == []


def test_legacy_feedback_custom_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        fb = FeedbackLoop(memory_dir=tmpdir)
        fb.record("custom", {"val": 42})
        recent = fb.get_recent("custom")
        assert len(recent) == 1
        assert recent[0]["metrics"]["val"] == 42
        assert os.path.exists(os.path.join(tmpdir, "custom.json"))


# ---------------------------------------------------------------------------
# MetricsStore (SQLite)
# ---------------------------------------------------------------------------

def test_metrics_store_record_and_recent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    store = MetricsStore(db_path=db_path)
    store.record("lexer", {"tokens": 10, "errors": 0})
    store.record("lexer", {"tokens": 5, "errors": 1})
    recent = store.get_recent("lexer", limit=5)
    assert len(recent) == 2
    assert recent[0]["metrics"]["tokens"] == 10
    assert recent[1]["metrics"]["tokens"] == 5
    db_path.unlink(missing_ok=True)


def test_metrics_store_summary():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    store = MetricsStore(db_path=db_path)
    store.record("lexer", {"tokens": 10, "errors": 0})
    store.record("parser", {"tokens": 5, "errors": 1})
    store.record("lexer", {"tokens": 3, "errors": 0})
    summary = store.summary()
    assert summary["total_records"] == 3
    assert summary["stages"]["lexer"] == 2
    assert summary["stages"]["parser"] == 1
    assert summary["total_errors"] == 1
    db_path.unlink(missing_ok=True)


def test_metrics_store_get_recent_empty():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    store = MetricsStore(db_path=db_path)
    recent = store.get_recent("nonexistent")
    assert recent == []
    db_path.unlink(missing_ok=True)


def test_metrics_store_record_token():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    store = MetricsStore(db_path=db_path)
    store.record_token("ACTION_CREATE", 1.0)
    store.record_token("ACTION_CREATE", 1.0)
    store.record_token("MODULE", 1.0)
    weights = store.get_token_weights()
    assert "ACTION_CREATE" in weights
    assert "MODULE" in weights
    db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# GlobalFeedbackLoop
# ---------------------------------------------------------------------------

def test_global_feedback_record_stage():
    fb = GlobalFeedbackLoop()
    fb.record_stage("parser", {"tokens": 50, "errors": 0, "task_count": 10, "node_count": 20})
    summary = fb.summary()
    assert summary["total_records"] >= 1


def test_global_feedback_lexer_adjustment_high_errors():
    fb = GlobalFeedbackLoop()
    fb.record_stage("lexer", {"tokens": 50, "errors": 7, "task_count": 10, "node_count": 5})
    adj = fb.get_lexer_adjustments()
    assert adj["action"] == "reduce_complexity"


def test_global_feedback_lexer_adjustment_high_nodes():
    fb = GlobalFeedbackLoop()
    fb.record_stage("lexer", {"tokens": 50, "errors": 0, "task_count": 10, "node_count": 100})
    adj = fb.get_lexer_adjustments()
    assert adj["action"] == "increase_threshold"


def test_global_feedback_no_adjustment():
    fb = GlobalFeedbackLoop()
    fb.record_stage("lexer", {"tokens": 50, "errors": 0, "task_count": 10, "node_count": 5})
    adj = fb.get_lexer_adjustments()
    assert adj == {}


def test_global_feedback_get_recent():
    fb = GlobalFeedbackLoop()
    fb.record_stage("test", {"val": 1})
    fb.record_stage("test", {"val": 2})
    recent = fb.get_recent("test", limit=5)
    assert len(recent) >= 2


def test_global_feedback_get_adjustments_non_lexer():
    fb = GlobalFeedbackLoop()
    fb.record_stage("parser", {"errors": 10, "task_count": 10, "node_count": 100})
    adj = fb.get_adjustments("parser")
    assert adj == {}


# ---------------------------------------------------------------------------
# ASTCache (LRU dict)
# ---------------------------------------------------------------------------

def test_ast_cache_get_set():
    cache = ASTCache(maxsize=10)
    cache.set("key1", {"data": 123})
    assert cache.get("key1") == {"data": 123}


def test_ast_cache_miss():
    cache = ASTCache(maxsize=10)
    assert cache.get("nonexistent") is None


def test_ast_cache_get_or_compute():
    cache = ASTCache(maxsize=10)
    computed = []

    def compute():
        computed.append(1)
        return {"result": 42}

    result1 = cache.get_or_compute("test", compute)
    result2 = cache.get_or_compute("test", compute)
    assert result1 == {"result": 42}
    assert result2 == {"result": 42}
    assert len(computed) == 1


def test_ast_cache_clear():
    cache = ASTCache(maxsize=10)
    cache.set("a", 1)
    cache.clear()
    assert cache.size == 0
    assert cache.hits == 0
    assert cache.misses == 0
    assert cache.get("a") is None


def test_ast_cache_hit_rate():
    cache = ASTCache(maxsize=10)
    cache.set("a", 1)
    cache.get("a")
    cache.get("b")
    assert cache.hit_rate == 0.5


def test_ast_cache_lru_eviction():
    cache = ASTCache(maxsize=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_ast_cache_stats():
    cache = ASTCache(maxsize=64)
    cache.set("x", 1)
    cache.get("x")
    stats = cache.stats()
    assert stats["size"] == 1
    assert stats["maxsize"] == 64
    assert stats["hits"] == 1
    assert stats["hit_rate"] == 1.0


# ---------------------------------------------------------------------------
# get_global_feedback singleton
# ---------------------------------------------------------------------------

def test_get_global_feedback_singleton():
    fb1 = get_global_feedback()
    fb2 = get_global_feedback()
    assert fb1 is fb2
