"""PromptOptimizer — ajusta temperatura/model segun metricas historicas (F5)."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.metrics_store import MetricsStore

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """Ajusta temperatura/model segun metricas historicas (F5).

    Reglas:
        - Si success_rate < 0.8 en ultimas 20 ejecuciones:
          → reducir temperatura en 0.1 (min 0.0)
        - Si avg_duration > 5s:
          → cambiar a modelo mas rapido
        - Si fallback_used > 50%:
          → reducir temperatura, simplificar prompt
    """

    def __init__(self, metrics_store: MetricsStore) -> None:
        self._store = metrics_store

    def optimize(self, prompt_name: str) -> dict[str, Any]:
        """Retorna parametros optimizados para el prompt.

        Args:
            prompt_name: Nombre del prompt a optimizar.

        Returns:
            Dict con parametros ajustados (temperature, model, etc.).
        """
        rate = self._store.get_prompt_success_rate(prompt_name)
        duration = self._store.get_prompt_avg_duration(prompt_name)
        fallback_rate = self._store.get_prompt_fallback_rate(prompt_name)

        params: dict[str, Any] = {}

        if rate < 0.8:
            params["temperature"] = max(0.0, 0.3 - 0.1)

        if duration > 5.0:
            params["model"] = "gpt-4o-mini"

        if fallback_rate > 0.5:
            params["temperature"] = min(
                params.get("temperature", 0.3),
                0.2,
            )

        if params:
            logger.info(
                "PromptOptimizer[%s]: rate=%.2f dur=%.2fs fallback=%.2f → %s",
                prompt_name,
                rate,
                duration,
                fallback_rate,
                params,
            )

        return params
