"""PipelineDebugger — trace, step, timing, and inspect modes for RECPL v2.0."""

from __future__ import annotations

import inspect
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from agentic_pipeline.orchestrator import NODE_MAP, PipelineOrchestrator
from agentic_pipeline.state_models import Stage, StageOutput

logger = logging.getLogger(__name__)

DEBUG_OUTPUT_DIR = Path("debug_output")


def _resolve_stage_locations() -> dict[str, str]:
    """Build map: stage_name → 'relative/path.py:line'."""
    locations: dict[str, str] = {}
    for stage, cls in NODE_MAP.items():
        try:
            module = inspect.getmodule(cls)
            rel = (
                os.path.relpath(module.__file__, start=os.getcwd())
                if module and module.__file__
                else "?"
            )
            _, line = inspect.getsourcelines(cls)
            locations[stage.value] = f"{rel}:{line}"
        except (OSError, TypeError):
            locations[stage.value] = "?:?"
    return locations


class PipelineDebugger:
    """Wraps PipelineOrchestrator with debug hooks.

    Modes:
        trace      — print full JSON output_data of each stage
        step       — like trace, but pauses between stages
        timing     — print JSON + elapsed time per stage + summary bar chart
        inspect    — save full StageOutput snapshots to debug_output/

    When ``show_output=True`` inspect mode saves the full output_data
    (instead of a summary) to the snapshot file.
    """

    def __init__(
        self,
        mode: str = "trace",
        output_dir: str = "modules",
        show_output: bool = False,
        debug_output_dir: Path | None = None,
    ) -> None:
        self.mode = mode
        self._output_dir = output_dir
        self.show_output = show_output
        self._debug_output_dir = debug_output_dir or DEBUG_OUTPUT_DIR
        self._stage_times: dict[str, float] = {}
        self._orchestrator: PipelineOrchestrator | None = None
        self._locations = _resolve_stage_locations()

    _CHAIN_STAGE_MAP: dict[str, Stage] = {
        "preprocess": Stage.PREPROCESSOR,
        "intent": Stage.INTENT,
        "plan": Stage.PLANNER,
        "generate": Stage.SYNTHESIS,
        "verify": Stage.VALIDATOR,
    }

    @staticmethod
    def _to_stage(stage_name: str) -> Stage:
        try:
            return Stage(stage_name)
        except ValueError:
            return PipelineDebugger._CHAIN_STAGE_MAP.get(stage_name, Stage.VALIDATOR)

    @staticmethod
    def _normalize(stage_name: str, output: StageOutput | dict) -> StageOutput:
        """Convert dict to StageOutput when callback receives raw dict (chain path)."""
        if isinstance(output, dict):
            return StageOutput(
                stage=PipelineDebugger._to_stage(stage_name),
                output_data=output,
                success=bool(output),
                error=None,
                metrics={},
            )
        return output

    async def run(self, prompt: str) -> dict[str, Any]:
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.mode == "inspect":
            snap_dir = self._debug_output_dir / session_id
            snap_dir.mkdir(parents=True, exist_ok=True)
            self._snap_dir = snap_dir

        self._orchestrator = PipelineOrchestrator(
            stream_callback=self._make_stream_callback(),
            output_dir=self._output_dir,
        )
        result = await self._orchestrator.run(prompt)

        if self.mode == "timing":
            self._print_timing_summary()

        return result

    def _make_stream_callback(self):
        mode = self.mode

        def callback(stage: str, output: StageOutput) -> None:
            if mode == "trace":
                self._trace_stage(stage, output)
            elif mode == "step":
                self._step_stage(stage, output)
            elif mode == "timing":
                self._timing_stage(stage, output)
            elif mode == "inspect":
                self._inspect_stage(stage, output)

        return callback

    def _loc(self, stage: str) -> str:
        return self._locations.get(stage, "?:?")

    def _output_preview(self, data: object) -> str:
        try:
            pretty = json.dumps(data, indent=2, default=str)
            indented = "\n      ".join(pretty.splitlines())
            return f"    ── output:\n      {indented}"
        except Exception:
            return f"    ── output: {data!r}"

    def _trace_stage(self, stage: str, output: StageOutput) -> None:
        output = self._normalize(stage, output)
        status = "OK" if output.success else "FAIL"
        data_size = self._estimate_size(output.output_data)
        print(
            f"  [{stage}] {status}  ({data_size})  ← {self._loc(stage)}",
            file=sys.stderr,
        )
        if not output.success:
            print(
                f"    error: {output.error}",
                file=sys.stderr,
            )
        if output.metrics:
            metrics_str = " ".join(f"{k}={v}" for k, v in output.metrics.items())
            print(
                f"    metrics: {metrics_str}",
                file=sys.stderr,
            )
        print(self._output_preview(output.output_data), file=sys.stderr)

    def _step_stage(self, stage: str, output: StageOutput) -> None:
        output = self._normalize(stage, output)
        status = "OK" if output.success else "FAIL"
        data_size = self._estimate_size(output.output_data)
        print(
            f"  [{stage}] {status}  ({data_size})  ← {self._loc(stage)}",
            file=sys.stderr,
        )
        if not output.success:
            print(
                f"    error: {output.error}",
                file=sys.stderr,
            )
        if output.metrics:
            metrics_str = " ".join(f"{k}={v}" for k, v in output.metrics.items())
            print(
                f"    metrics: {metrics_str}",
                file=sys.stderr,
            )
        print(self._output_preview(output.output_data), file=sys.stderr)
        if sys.stdin.isatty():
            try:
                input("  Press Enter to continue... ")
            except (EOFError, KeyboardInterrupt):
                print("", file=sys.stderr)
        else:
            print("  (non-interactive, continuing)", file=sys.stderr)

    def _timing_stage(self, stage: str, output: StageOutput) -> None:
        output = self._normalize(stage, output)
        elapsed = output.metrics.get("duration_seconds", 0)
        self._stage_times[stage] = elapsed
        status = "OK" if output.success else "FAIL"
        print(
            f"  [{stage}] {status}  {elapsed:.3f}s  ← {self._loc(stage)}",
            file=sys.stderr,
        )
        if output.metrics:
            metrics_str = " ".join(f"{k}={v}" for k, v in output.metrics.items())
            print(
                f"    metrics: {metrics_str}",
                file=sys.stderr,
            )
        print(self._output_preview(output.output_data), file=sys.stderr)

    def _inspect_stage(self, stage: str, output: StageOutput) -> None:
        output = self._normalize(stage, output)
        loc = self._loc(stage)
        snap_output = (
            output.output_data if self.show_output else self._summarize(output.output_data)
        )
        snap = {
            "stage": stage,
            "success": output.success,
            "error": output.error,
            "metrics": output.metrics,
            "output_data": snap_output,
            "source_location": loc,
        }
        snap_path = self._snap_dir / f"{stage}.json"
        snap_path.write_text(json.dumps(snap, indent=2, default=str))
        status = "OK" if output.success else "FAIL"
        print(
            f"  [{stage}] {status}  ← {loc}",
            file=sys.stderr,
        )
        if output.metrics:
            metrics_str = " ".join(f"{k}={v}" for k, v in output.metrics.items())
            print(
                f"    metrics: {metrics_str}",
                file=sys.stderr,
            )
        print(self._output_preview(output.output_data), file=sys.stderr)
        print(
            f"    snapshot → {snap_path}",
            file=sys.stderr,
        )

    def _print_timing_summary(self) -> None:
        total = sum(self._stage_times.values())
        print("", file=sys.stderr)
        print("=== Timing Summary ===", file=sys.stderr)
        for stage, elapsed in self._stage_times.items():
            pct = (elapsed / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(
                f"  {stage:30s} {elapsed:6.3f}s {bar} {pct:5.1f}%",
                file=sys.stderr,
            )
        print(
            f"  {'TOTAL':30s} {total:6.3f}s",
            file=sys.stderr,
        )

    @staticmethod
    def _estimate_size(data: object) -> str:
        try:
            size = len(json.dumps(data, default=str))
            if size < 1024:
                return f"{size}B"
            return f"{size / 1024:.1f}KB"
        except Exception:
            return "?"

    @staticmethod
    def _summarize(data: object, max_len: int = 200) -> str:
        try:
            text = json.dumps(data, default=str)
            if len(text) > max_len:
                return text[:max_len] + "..."
            return text
        except Exception:
            return str(data)[:max_len]
