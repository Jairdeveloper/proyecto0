from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from agentic_pipeline.dashboard.service import DashboardService

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

_STATIC_DIR = Path(__file__).resolve().parent / "static"

_MIME_MAP: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
}


class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler that routes requests to DashboardService."""

    service: DashboardService = DashboardService()

    def _json_response(
        self,
        data: Any,
        status: int = 200,
    ) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _static_response(self, filename: str) -> None:
        filepath = _STATIC_DIR / filename
        if not filepath.exists() or not filepath.is_file():
            self._json_response({"error": "Not found"}, 404)
            return
        ext = filepath.suffix
        content_type = _MIME_MAP.get(ext, "application/octet-stream")
        body = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        try:
            if path == "" or path == "/":
                self._static_response("index.html")
                return
            if path == "/static/dashboard.css":
                self._static_response("dashboard.css")
                return
            if path == "/static/dashboard.js":
                self._static_response("dashboard.js")
                return
            if path == "/api/health":
                self._json_response(self.service.get_health())
                return
            if path == "/api/summary":
                self._json_response(self.service.get_summary())
                return
            if path == "/api/stages":
                self._json_response(self.service.get_stages())
                return
            if path == "/api/prompt-chain":
                self._json_response(self.service.get_prompt_chain_summary())
                return
            if path.startswith("/api/stages/") and path.endswith("/recent"):
                stage = path.split("/")[3]
                qs = parse_qs(parsed.query)
                limit_str = qs.get("limit", ["20"])[0]
                try:
                    limit = int(limit_str)
                except (ValueError, TypeError):
                    limit = 20
                self._json_response(self.service.get_recent(stage, limit))
                return
            self._json_response({"error": "Not found"}, 404)
        except Exception as exc:
            self._json_response({"error": str(exc)}, 500)

    def log_message(self, fmt: str, *args: Any) -> None:
        pass


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    service: DashboardService | None = None,
) -> HTTPServer:
    if service is not None:
        DashboardHTTPHandler.service = service
    return HTTPServer((host, port), DashboardHTTPHandler)


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    server = create_server(host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
