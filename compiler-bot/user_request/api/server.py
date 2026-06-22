"""RECPL API Server — endpoints HTTP para la capa User Request.

Endpoints:
    POST /api/nlu    — Clasifica intencion y extrae entidades del texto.
    POST /api/chat   — Ciclo completo: NLU → Pipeline → NLG.
    GET  /api/health — Health check.

Uso:
    from user_request.api import run_server
    run_server(host="127.0.0.1", port=8766)
"""

from __future__ import annotations

import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from user_request.contracts.enums import RequestChannel
from user_request.contracts.response import ResponseObject
from user_request.layer import UserRequestLayer

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8766


class UserRequestAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler para los endpoints de la capa User Request."""

    # Compartido entre instancias (thread-safe para HTTPServer single-threaded)
    layer: UserRequestLayer = UserRequestLayer()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _json_response(
        self,
        data: Any,
        status: int = 200,
    ) -> None:
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any] | None:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return None
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            logger.warning("Invalid JSON body: %s", exc)
            return None

    def log_message(self, fmt: str, *args: Any) -> None:
        logger.debug(fmt, *args)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def do_GET(self) -> None:
        parsed_path = self.path.rstrip("/")
        try:
            if parsed_path == "/api/health":
                self._handle_health()
            else:
                self._json_response({"error": "Not found"}, 404)
        except Exception as exc:
            logger.error("GET %s failed: %s", self.path, exc)
            self._json_response({"error": str(exc)}, 500)

    def do_POST(self) -> None:
        parsed_path = self.path.rstrip("/")
        try:
            if parsed_path == "/api/nlu":
                self._handle_nlu()
            elif parsed_path == "/api/chat":
                self._handle_chat()
            elif parsed_path == "/api/health":
                self._handle_health()
            else:
                self._json_response({"error": "Not found"}, 404)
        except Exception as exc:
            logger.error("POST %s failed: %s", self.path, exc)
            self._json_response({"error": str(exc)}, 500)

    def do_OPTIONS(self) -> None:
        """CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_health(self) -> None:
        self._json_response({"status": "ok", "service": "user-request-api"})

    def _handle_nlu(self) -> None:
        """POST /api/nlu — Clasifica intencion y extrae entidades.

        Request body:
            {"text": "crea un modulo de pagos"}

        Response:
            RequestObject serializado (intent, entities, slots, ...)
        """
        body = self._read_json_body()
        if body is None or "text" not in body:
            self._json_response(
                {"error": "Missing required field: 'text'"},
                400,
            )
            return

        text: str = body["text"]
        if not text.strip():
            self._json_response({"error": "'text' must not be empty"}, 400)
            return

        channel_str = body.get("channel", "cli")
        try:
            channel = RequestChannel(channel_str)
        except ValueError:
            channel = RequestChannel.CLI

        request = self.layer.process_input(text)

        response_data = request.model_dump(mode="json")
        response_data["channel"] = channel.value
        self._json_response(response_data)

    def _handle_chat(self) -> None:
        """POST /api/chat — Ciclo completo: NLU → Pipeline → NLG.

        Request body:
            {"text": "crea un modulo de pagos", "channel": "cli"}

        Response:
            {"success": true, "message": "...", "data": {...}}
        """
        body = self._read_json_body()
        if body is None or "text" not in body:
            self._json_response(
                {"error": "Missing required field: 'text'"},
                400,
            )
            return

        text: str = body["text"]
        if not text.strip():
            self._json_response({"error": "'text' must not be empty"}, 400)
            return

        channel_str = body.get("channel", "cli")
        try:
            channel = RequestChannel(channel_str)
        except ValueError:
            channel = RequestChannel.CLI

        # 1. NLU: clasificar intencion y detectar ambiguedad
        try:
            self.layer.process_input(text)
        except Exception as exc:
            logger.error("NLU failed: %s", exc)
            self._json_response(
                {
                    "success": False,
                    "error": f"NLU processing failed: {exc}",
                    "data": None,
                },
                500,
            )
            return

        # 2. Pipeline principal (orquestador)
        try:
            result = asyncio.run(self._run_pipeline(text))
        except Exception as exc:
            logger.error("Pipeline failed: %s", exc)
            self._json_response(
                {
                    "success": False,
                    "error": f"Pipeline execution failed: {exc}",
                    "data": None,
                },
                500,
            )
            return

        # 3. Construir ResponseObject y formatear con NLG
        response_obj = ResponseObject(
            success=result.get("success", True),
            data=result.get("output", {}),
            channel=channel,
        )

        try:
            output = self.layer.format_output(response_obj, channel=channel)
        except Exception as exc:
            logger.error("NLG failed: %s", exc)
            output = str(result.get("output", {}))

        self._json_response(
            {
                "success": result.get("success", True),
                "message": output,
                "data": result.get("output", {}),
                "channel": channel.value,
            },
        )

    @staticmethod
    async def _run_pipeline(text: str) -> dict[str, Any]:
        """Ejecuta el pipeline RECPL completo.

        Args:
            text: Prompt del usuario.

        Returns:
            Dict con resultado del orquestador.
        """
        from agentic_pipeline.orchestrator import PipelineOrchestrator

        orchestrator = PipelineOrchestrator()
        return await orchestrator.run(text)


# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------


def create_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    layer: UserRequestLayer | None = None,
) -> HTTPServer:
    """Crea una instancia del servidor HTTP.

    Args:
        host: Host al que bindearse.
        port: Puerto.
        layer: Instancia de UserRequestLayer (opcional, crea una por defecto).

    Returns:
        HTTPServer configurado.
    """
    if layer is not None:
        UserRequestAPIHandler.layer = layer
    return HTTPServer((host, port), UserRequestAPIHandler)


def run_server(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Arranca el servidor HTTP (bloqueante).

    Args:
        host: Host al que bindearse.
        port: Puerto.
    """
    server = create_server(host, port)
    logger.info(
        "UserRequest API server listening on http://%s:%d",
        host,
        port,
    )
    print(f"UserRequest API server listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutting down")
        server.shutdown()
