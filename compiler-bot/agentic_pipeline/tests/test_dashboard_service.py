from __future__ import annotations

import tempfile
from pathlib import Path

from agentic_pipeline.dashboard.service import DashboardService
from agentic_pipeline.metrics_store import HAS_SQLITE, MetricsStore


class TestDashboardService:
    def setup_method(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.store = MetricsStore(db_path=self.tmpdir / "test.db")
        self.service = DashboardService(self.store)

    def test_health_reports_backend(self) -> None:
        health = self.service.get_health()
        assert "backend" in health
        assert health["backend"] in ("sqlite", "json_fallback")
        assert health["backend"] == ("sqlite" if HAS_SQLITE else "json_fallback")
        assert "timestamp" in health

    def test_summary_empty_store(self) -> None:
        summary = self.service.get_summary()
        assert summary["total_records"] == 0
        assert summary["total_errors"] == 0
        assert summary["success_rate"] == 0.0

    def test_summary_with_errors(self) -> None:
        self.store.record("preprocess", {"errors": 0, "success": True, "duration_seconds": 0.1})
        self.store.record("preprocess", {"errors": 0, "success": True, "duration_seconds": 0.2})
        self.store.record("preprocess", {"errors": 1, "success": False, "duration_seconds": 0.3})
        summary = self.service.get_summary()
        assert summary["total_records"] == 3
        assert summary["total_errors"] == 1
        assert summary["success_rate"] == 66.7

    def test_stages_shape(self) -> None:
        self.store.record("intent", {"errors": 0, "success": True})
        self.store.record("intent", {"errors": 1, "success": False})
        self.store.record("lexer", {"errors": 0, "success": True})
        stages = self.service.get_stages()
        assert len(stages) >= 2
        intent = [s for s in stages if s["name"] == "intent"][0]
        assert intent["runs"] == 2
        assert intent["errors"] == 1
        assert intent["success_rate"] == 50.0
        for s in stages:
            assert "name" in s
            assert "runs" in s
            assert "errors" in s
            assert "success_rate" in s

    def test_recent_limit(self) -> None:
        for i in range(10):
            self.store.record("test", {"errors": 0, "success": True})
        recent = self.service.get_recent("test", limit=3)
        assert len(recent) == 3
        clamped = self.service.get_recent("test", limit=999)
        assert len(clamped) <= 100
