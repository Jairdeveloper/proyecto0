"""StageExecutor — per-stage execution isolation with error boundary."""

from __future__ import annotations

import logging

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.state_models import StageOutput

logger = logging.getLogger(__name__)


class StageExecutor:
    """Wraps PipelineStage.execute() with a try/except error boundary.

    Any exception raised by the stage is caught and returned as a
    StageOutput with success=False, preventing the error from propagating
    up the StateGraph and crashing the entire pipeline.
    """

    async def execute(self, stage: PipelineStage, input_data: object) -> StageOutput:
        """Execute stage with isolation.

        Args:
            stage: PipelineStage instance to execute.
            input_data: Data to pass to stage.execute().

        Returns:
            StageOutput — either the stage's output, or a fallback with
            success=False and the exception details.
        """
        try:
            return stage.execute(input_data)
        except Exception as exc:
            logger.exception("Stage %s failed: %s", stage.name, exc)
            return StageOutput(
                stage=stage.context.stage,
                output_data={},
                success=False,
                error=str(exc),
                metrics={"exception": type(exc).__name__},
            )
