"""Metrics formatter — muestra metricas del pipeline."""

from __future__ import annotations

import json

from user_request.contracts.response import ResponseObject
from user_request.nlg.formatters.base import NLGFormatter


class MetricFormatter(NLGFormatter):
    """Formatea metricas de ejecucion del pipeline.

    Produce mensajes como:
        "Pipeline: 8 stages, 0 errores, 0.255s total."
    """

    def format(self, response: ResponseObject) -> str:
        """Formatea metricas como texto legible.

        Args:
            response: ResponseObject con data conteniendo metrics.

        Returns:
            Metricas formateadas.
        """
        metrics = response.data.get("metrics") if response.data else None
        if metrics is None:
            return json.dumps(response.data, default=str) if response.data else "(sin metricas)"

        parts: list[str] = ["Pipeline:"]

        stages = metrics.get("stages") or metrics.get("total_stages")
        if stages is not None:
            parts.append(f"{stages} stages")

        errors = metrics.get("errors") or metrics.get("errores", 0)
        if errors is not None:
            parts.append(f"{errors} errores")

        duration = metrics.get("duration_ms") or metrics.get("total_time")
        if duration is not None:
            if isinstance(duration, (int, float)) and duration < 1000:
                parts.append(f"{duration}ms total")
            elif isinstance(duration, (int, float)):
                parts.append(f"{duration / 1000:.3f}s total")

        for key, value in metrics.items():
            if key not in ("stages", "total_stages", "errors", "errores", "duration_ms", "total_time"):
                parts.append(f"{key}: {value}")

        return ", ".join(parts)
