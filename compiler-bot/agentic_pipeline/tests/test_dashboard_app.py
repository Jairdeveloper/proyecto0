from __future__ import annotations

import json
import tempfile
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from agentic_pipeline.dashboard.app import create_server
from agentic_pipeline.dashboard.service import DashboardService
from agentic_pipeline.metrics_store import MetricsStore


def _find_free_port() -> int:
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestDashboardApp:
    def setup_method(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.store = MetricsStore(db_path=self.tmpdir / "test.db")
        self.service = DashboardService(self.store)
        self.port = _find_free_port()
        self.server = create_server("127.0.0.1", self.port, self.service)
        self._t = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._t.start()

    def teardown_method(self) -> None:
        self.server.shutdown()
        self._t.join(timeout=2)

    def _get(self, path: str) -> tuple[int, dict | str]:
        try:
            with urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=3) as resp:
                body = resp.read().decode("utf-8")
                if "application/json" in resp.headers.get("Content-Type", ""):
                    return resp.status, json.loads(body)
                return resp.status, body
        except HTTPError as exc:
            body = exc.read().decode("utf-8")
            try:
                return exc.code, json.loads(body)
            except (json.JSONDecodeError, ValueError):
                return exc.code, body

    def test_health_endpoint(self) -> None:
        status, data = self._get("/api/health")
        assert status == 200
        assert isinstance(data, dict)
        assert "backend" in data
        assert "timestamp" in data

    def test_summary_endpoint(self) -> None:
        self.store.record("test", {"errors": 0, "success": True})
        status, data = self._get("/api/summary")
        assert status == 200
        assert isinstance(data, dict)
        assert "total_records" in data
        assert "total_errors" in data
        assert "success_rate" in data
        assert data["total_records"] >= 1

    def test_stages_endpoint(self) -> None:
        self.store.record("intent", {"errors": 0, "success": True})
        self.store.record("lexer", {"errors": 1, "success": False})
        status, data = self._get("/api/stages")
        assert status == 200
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_recent_endpoint(self) -> None:
        for i in range(5):
            self.store.record("parser", {"errors": 0, "success": True})
        status, data = self._get("/api/stages/parser/recent?limit=3")
        assert status == 200
        assert isinstance(data, list)
        assert len(data) == 3

    def test_not_found(self) -> None:
        status, data = self._get("/api/nonexistent")
        assert status == 404
        assert isinstance(data, dict)
        assert "error" in data
