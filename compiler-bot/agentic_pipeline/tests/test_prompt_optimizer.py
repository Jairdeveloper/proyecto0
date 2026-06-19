"""Tests for PromptOptimizer (F5.2)."""

from __future__ import annotations

from unittest.mock import MagicMock

from agentic_pipeline.optimizer import PromptOptimizer


class TestPromptOptimizer:
    def test_optimize_high_success_no_changes(self):
        store = MagicMock()
        store.get_prompt_success_rate.return_value = 1.0
        store.get_prompt_avg_duration.return_value = 0.5
        store.get_prompt_fallback_rate.return_value = 0.0

        opt = PromptOptimizer(store)
        params = opt.optimize("preprocess")
        assert params == {}

    def test_optimize_low_success_reduces_temperature(self):
        store = MagicMock()
        store.get_prompt_success_rate.return_value = 0.5
        store.get_prompt_avg_duration.return_value = 0.5
        store.get_prompt_fallback_rate.return_value = 0.0

        opt = PromptOptimizer(store)
        params = opt.optimize("plan")
        assert "temperature" in params
        assert params["temperature"] < 0.3

    def test_optimize_high_duration_changes_model(self):
        store = MagicMock()
        store.get_prompt_success_rate.return_value = 1.0
        store.get_prompt_avg_duration.return_value = 6.0
        store.get_prompt_fallback_rate.return_value = 0.0

        opt = PromptOptimizer(store)
        params = opt.optimize("generate")
        assert params["model"] == "gpt-4o-mini"

    def test_optimize_high_fallback_reduces_temperature(self):
        store = MagicMock()
        store.get_prompt_success_rate.return_value = 1.0
        store.get_prompt_avg_duration.return_value = 0.5
        store.get_prompt_fallback_rate.return_value = 0.8

        opt = PromptOptimizer(store)
        params = opt.optimize("intent")
        assert "temperature" in params
        assert params["temperature"] <= 0.2

    def test_optimize_all_conditions(self):
        store = MagicMock()
        store.get_prompt_success_rate.return_value = 0.5
        store.get_prompt_avg_duration.return_value = 6.0
        store.get_prompt_fallback_rate.return_value = 0.8

        opt = PromptOptimizer(store)
        params = opt.optimize("generate")
        assert "temperature" in params
        assert "model" in params
        assert params["model"] == "gpt-4o-mini"
