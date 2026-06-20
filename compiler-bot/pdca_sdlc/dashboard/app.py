"""HTTP server for PDCA-sdlc dashboard.

Zero external dependencies. Uses stdlib http.server.
Pattern consistent with agentic_pipeline/dashboard/app.py.
"""

from __future__ import annotations

import json
import logging
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from pdca_sdlc.core.event_bus import AsyncEventBus, Event
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
    bus: AsyncEventBus | None = None

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
            # Health / Metrics
            if path == "/api/health":
                self._send_json(self.service.get_health())

            elif path == "/api/health/metrics":
                self._send_json(self.service.get_metrics())

            # Projects
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

            # Agents
            elif path == "/api/agents":
                self._send_json(self.service.get_agents())

            # Events — orden: exactos primero, luego dinámicos
            elif path == "/api/events/distribution":
                pid = params.get("project", [""])[0]
                if not pid:
                    self._send_json({"error": "Missing project parameter"}, 400)
                    return
                self._send_json(self.service.get_event_distribution(pid))

            elif path == "/api/events/timeline":
                pid = params.get("project", [""])[0]
                if not pid:
                    self._send_json({"error": "Missing project parameter"}, 400)
                    return
                granularity = params.get("granularity", ["1m"])[0]
                self._send_json(
                    self.service.get_event_timeline(pid, granularity)
                )

            elif path == "/api/events/live":
                self._handle_sse(params)

            elif path.startswith("/api/events/"):
                event_id = path.replace("/api/events/", "")
                result = self.service.get_event_detail(event_id)
                if result is None:
                    self._send_json(
                        {"error": f"Event not found: {event_id}"}, 404
                    )
                else:
                    self._send_json(result)

            elif path == "/api/events":
                pid = params.get("project", [""])[0]
                topic = params.get("topic", [None])[0]
                source = params.get("source", [None])[0]
                search = params.get("search", [None])[0]
                offset_str = params.get("offset", [None])[0]
                since_time = params.get("since_time", [None])[0]
                until_time = params.get("until_time", [None])[0]
                limit_str = params.get("limit", ["20"])[0]
                try:
                    limit_val = max(1, min(500, int(limit_str)))
                except ValueError:
                    limit_val = 20
                try:
                    offset_val = max(0, int(offset_str)) if offset_str else 0
                except (ValueError, TypeError):
                    offset_val = 0
                since_f: float | None = (
                    float(since_time) if since_time else None
                )
                until_f: float | None = (
                    float(until_time) if until_time else None
                )
                self._send_json(
                    self.service.query_events(
                        project_id=pid if pid and pid != "_all" else None,
                        topic=topic or None,
                        source=source or None,
                        since_time=since_f,
                        until_time=until_f,
                        search=search or None,
                        limit=limit_val,
                        offset=offset_val,
                    )
                )

            # Topics / Sources / Subscriptions
            elif path == "/api/topics":
                self._send_json(self.service.get_topics())

            elif path == "/api/sources":
                self._send_json(self.service.get_sources())

            elif path == "/api/subscriptions":
                self._send_json(self.service.get_subscriptions())

            # Static
            elif path == "/" or path == "":
                self._send_static("index.html")

            elif path.startswith("/static/"):
                self._send_static(path)

            else:
                self._send_json({"error": "Not found"}, 404)

        except Exception as exc:
            logger.exception("Error handling %s", path)
            self._send_json({"error": str(exc)}, 500)

    def _handle_sse(
        self,
        params: dict[str, list[str]],
    ) -> None:
        """Handle Server-Sent Events connection for live event streaming."""
        if self.bus is None:
            self._send_json(
                {"error": "EventBus not available for SSE"}, 500
            )
            return
        pid = params.get("project", [""])[0]
        if not pid:
            self._send_json({"error": "Missing project parameter"}, 400)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        def on_event(event: Event) -> None:
            try:
                data = json.dumps(
                    {
                        "sequence": event.sequence,
                        "topic": event.topic,
                        "source": event.source,
                        "timestamp": event.timestamp,
                        "data": event.data,
                    },
                    ensure_ascii=False,
                    default=str,
                )
                self.wfile.write(f"data: {data}\n\n".encode())
                self.wfile.flush()
            except OSError:
                pass

        target = pid if pid != "_all" else "_all"
        self.bus.register_sse_callback(target, on_event)
        try:
            while not self.server._shutdown_request:
                self.wfile.write(b": heartbeat\n\n")
                time.sleep(15)
        except (BrokenPipeError, OSError):
            pass
        finally:
            self.bus.unregister_sse_callback(target, on_event)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug("HTTP: %s", format % args)


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    service: SdlcDashboardService | None = None,
    bus: AsyncEventBus | None = None,
) -> HTTPServer:
    """Create an HTTPServer with the dashboard handler.

    Args:
        host: Bind address (default 127.0.0.1).
        port: Bind port (default 8764).
        service: Injected SdlcDashboardService. If None, creates one.
        bus: Injected AsyncEventBus (required for SSE endpoint).
    """
    if service is not None:
        DashboardHTTPHandler.service = service
    if bus is not None:
        DashboardHTTPHandler.bus = bus
    server = HTTPServer((host, port), DashboardHTTPHandler)
    server.timeout = 0.5
    return server


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    service: SdlcDashboardService | None = None,
    bus: AsyncEventBus | None = None,
) -> None:
    """Run the dashboard server (blocking, Ctrl+C to stop)."""
    server = create_server(host, port, service, bus)
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
