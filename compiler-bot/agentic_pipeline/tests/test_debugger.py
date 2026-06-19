"""Tests for PipelineDebugger."""

from __future__ import annotations

import pytest

from agentic_pipeline.debugger import PipelineDebugger


class TestPipelineDebugger:
    @pytest.mark.asyncio
    async def test_trace_mode_runs(self):
        debugger = PipelineDebugger(mode="trace")
        result = await debugger.run("crea un modulo de pagos")
        assert result is not None
        assert "output" in result

    @pytest.mark.asyncio
    async def test_timing_mode_runs(self):
        debugger = PipelineDebugger(mode="timing")
        result = await debugger.run("crea un modulo")
        assert result is not None

    @pytest.mark.asyncio
    async def test_timing_collects_stage_times(self):
        debugger = PipelineDebugger(mode="timing")
        await debugger.run("test prompt")
        assert len(debugger._stage_times) > 0
        total = sum(debugger._stage_times.values())
        assert total >= 0

    @pytest.mark.asyncio
    async def test_inspect_mode_creates_snapshots(self, tmp_path):
        debugger = PipelineDebugger(mode="inspect", debug_output_dir=tmp_path)
        await debugger.run("crea un modulo de pagos")
        snaps = list(tmp_path.glob("**/*.json"))
        names = [s.name for s in snaps]
        assert "intent.json" in names
        assert "preprocessor.json" in names

    @pytest.mark.asyncio
    async def test_step_mode_continues_noninteractive(self):
        debugger = PipelineDebugger(mode="step")
        result = await debugger.run("crea un modulo")
        assert result is not None

    def test_estimate_size_small(self):
        size = PipelineDebugger._estimate_size({"a": 1})
        assert "B" in size

    def test_estimate_size_large(self):
        big = {"data": "x" * 2000}
        size = PipelineDebugger._estimate_size(big)
        assert "KB" in size or "B" in size

    def test_summarize_truncates(self):
        summary = PipelineDebugger._summarize({"data": "a" * 500}, max_len=50)
        assert len(summary) <= 53
        assert summary.endswith("...")

    def test_summarize_short(self):
        summary = PipelineDebugger._summarize({"a": 1})
        assert '"a"' in summary
        assert not summary.endswith("...")

    @pytest.mark.asyncio
    async def test_run_returns_dict(self):
        debugger = PipelineDebugger(mode="trace")
        result = await debugger.run("")
        assert isinstance(result, dict)
        assert "output" in result

    @pytest.mark.asyncio
    async def test_trace_with_show_output_does_not_crash(self):
        debugger = PipelineDebugger(mode="trace", show_output=True)
        result = await debugger.run("crea un modulo")
        assert result is not None

    @pytest.mark.asyncio
    async def test_timing_with_show_output_does_not_crash(self):
        debugger = PipelineDebugger(mode="timing", show_output=True)
        result = await debugger.run("crea un modulo")
        assert result is not None

    @pytest.mark.asyncio
    async def test_inspect_with_show_output_has_full_data(self, tmp_path):
        debugger = PipelineDebugger(mode="inspect", show_output=True, debug_output_dir=tmp_path)
        await debugger.run("crea un modulo")
        snaps = list(tmp_path.glob("**/*.json"))
        assert len(snaps) > 0
        import json

        data = json.loads(snaps[0].read_text())
        assert "output_data" in data
        assert "source_location" in data
