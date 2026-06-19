"""Tests for MetricsStore prompt chain extensions (F5.1)."""

from __future__ import annotations

import tempfile
from pathlib import Path

from agentic_pipeline.metrics_store import MetricsStore


class TestMetricsStorePrompt:
    def setup_method(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp())
        self.store = MetricsStore(db_path=self.tmpdir / "test.db")

    def test_record_prompt_and_queries(self):
        self.store.record_prompt(
            "preprocess",
            {
                "success": True,
                "duration": 0.5,
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.1,
                "fallback_used": False,
                "output_size": 256,
                "tokens_used": 150,
            },
        )
        self.store.record_prompt(
            "preprocess",
            {
                "success": True,
                "duration": 0.6,
                "llm_provider": "openai",
                "llm_model": "gpt-4o-mini",
                "temperature": 0.1,
                "fallback_used": False,
                "output_size": 300,
                "tokens_used": 180,
            },
        )
        rate = self.store.get_prompt_success_rate("preprocess", n=20)
        assert rate == 1.0
        avg = self.store.get_prompt_avg_duration("preprocess", n=20)
        assert avg == 0.55

    def test_record_prompt_fallback(self):
        self.store.record_prompt(
            "intent",
            {
                "success": False,
                "duration": 0.0,
                "llm_provider": "",
                "llm_model": "",
                "temperature": 0.2,
                "fallback_used": True,
                "output_size": 0,
                "tokens_used": 0,
            },
        )
        fb_rate = self.store.get_prompt_fallback_rate("intent")
        assert fb_rate == 1.0
        success_rate = self.store.get_prompt_success_rate("intent")
        assert success_rate == 0.0

    def test_get_prompt_chain_summary(self):
        stages = ["preprocess", "intent", "plan", "generate", "verify", "format"]
        for i, stage in enumerate(stages):
            self.store.record_prompt(
                stage,
                {
                    "success": i != 3,  # generate fails once
                    "duration": 0.5 + i * 0.1,
                    "llm_provider": "openai",
                    "llm_model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "fallback_used": i == 3,
                    "output_size": 100,
                    "tokens_used": 50,
                },
            )
        summary = self.store.get_prompt_chain_summary()
        assert summary["total_records"] == 6
        assert summary["total_errors"] == 1
        assert summary["per_stage"]["generate"]["errors"] == 1
        assert summary["per_stage"]["preprocess"]["calls"] == 1
        assert summary["per_stage"]["preprocess"]["success_rate"] == 100.0

    def test_get_prompt_chain_summary_empty(self):
        summary = self.store.get_prompt_chain_summary()
        assert summary["total_records"] == 0
        assert summary["per_stage"] == {}

    def test_get_prompt_success_rate_no_data(self):
        rate = self.store.get_prompt_success_rate("nonexistent")
        assert rate == 1.0

    def test_get_prompt_avg_duration_no_data(self):
        avg = self.store.get_prompt_avg_duration("nonexistent")
        assert avg == 0.0
