"""HTTP server for PDCA-sdlc dashboard.

Zero external dependencies. Uses stdlib http.server.
Pattern consistent with agentic_pipeline/dashboard/app.py.
"""

from __future__ import annotations

import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from pdca_sdlc.dashboard.service import SdlcDashboardService

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8764

_MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


class DashboardHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for dashboard API and static files."""

    service: SdlcDashboardService | None = None

    def _send_json(
        self,
        data: dict[str, Any],
        status: int = 200,
    ) -> None:
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, path: str) -> None:
        from pathlib import Path

        static_dir = Path(__file__).resolve().parent / "static"
        ext = Path(path).suffix
        mime = _MIME_TYPES.get(ext, "application/octet-stream")

        # Security: prevent directory traversal
        requested = (static_dir / path.lstrip("/")).resolve()
        if not str(requested).startswith(str(static_dir.resolve())):
            self._send_json({"error": "Forbidden"}, 403)
            return

        if not requested.is_file():
            self._send_json({"error": "Not found"}, 404)
            return

        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(requested.stat().st_size))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(requested.read_bytes())

    def _parse_path(self) -> tuple[str, dict[str, list[str]]]:
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self) -> None:  # noqa: N802
        path, params = self._parse_path()

        if self.service is None:
            self._send_json({"error": "Service not initialized"}, 500)
            return

        try:
            if path == "/api/health":
                self._send_json(self.service.get_health())

            elif path == "/api/projects":
                self._send_json(self.service.get_projects())

            elif path.startswith("/api/projects/") and path.endswith("/trace"):
                pid = path.replace("/api/projects/", "").replace("/trace", "")
                result = self.service.get_trace(pid)
                if result is None:
                    self._send_json({"error": f"Project not found: {pid}"}, 404)
                else:
                    self._send_json(result)

            elif path.startswith("/api/projects/"):
                pid = path.replace("/api/projects/", "")
                result = self.service.get_project(pid)
                if result is None:
                    self._send_json({"error": f"Project not found: {pid}"}, 404)
                else:
                    self._send_json(result)

            elif path == "/api/agents":
                self._send_json(self.service.get_agents())

            elif path == "/api/events":
                pid = params.get("project", [""])[0]
                if not pid:
                    self._send_json({"error": "Missing project parameter"}, 400)
                    return
                limit_str = params.get("limit", ["20"])[0]
                try:
                    limit = max(1, min(100, int(limit_str)))
                except ValueError:
                    limit = 20
                self._send_json(self.service.get_events(pid, limit))

            elif path == "/" or path == "":
                self._send_static("index.html")

            elif path.startswith("/static/"):
                self._send_static(path)

            else:
                self._send_json({"error": "Not found"}, 404)

        except Exception as exc:
            logger.exception("Error handling %s", path)
            self._send_json({"error": str(exc)}, 500)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug("HTTP: %s", format % args)


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    service: SdlcDashboardService | None = None,
) -> HTTPServer:
    """Create an HTTPServer with the dashboard handler.

    Args:
        host: Bind address (default 127.0.0.1).
        port: Bind port (default 8764).
        service: Injected SdlcDashboardService. If None, creates one.
    """
    if service is not None:
        DashboardHTTPHandler.service = service
    server = HTTPServer((host, port), DashboardHTTPHandler)
    server.timeout = 0.5
    return server


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    service: SdlcDashboardService | None = None,
) -> None:
    """Run the dashboard server (blocking, Ctrl+C to stop)."""
    server = create_server(host, port, service)
    addr = server.server_address
    logger.info(
        "Dashboard server started at http://%s:%d",
        addr[0],
        addr[1],
    )
    print(f"Dashboard: http://{addr[0]}:{addr[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        logger.info("Dashboard server stopped")
