"""CLI handler para el flag --chain."""

from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def add_chain_args(parser: argparse.ArgumentParser) -> None:
    """Anade argumentos de prompt chain al parser."""
    parser.add_argument(
        "--chain",
        action="store_true",
        help="Usar pipeline Prompt Chaining (en vez del clasico)",
    )


async def run_chain(
    prompt: str,
    output_dir: str = "modules",
    debug_mode: str | None = None,
    show_output: bool = False,
) -> dict:
    """Ejecuta el pipeline Prompt Chaining completo.

    Args:
        prompt: Texto del usuario.
        output_dir: Directorio de salida para archivos generados.
        debug_mode: "trace" | "step" | "timing" | "inspect" | None.
        show_output: Mostrar output_data completo.

    Returns:
        Dict con resultado final.
    """
    from agentic_pipeline.prompt_chain.orchestrator import ChainOrchestrator

    debug_callback = None
    if debug_mode:
        from agentic_pipeline.debugger import PipelineDebugger

        debugger = PipelineDebugger(
            mode=debug_mode,
            output_dir=output_dir,
            show_output=show_output,
        )
        debug_callback = debugger._make_stream_callback()

    orchestrator = ChainOrchestrator(
        debug_callback=debug_callback,
    )
    result = await orchestrator.run(prompt)
    success = result.get("success", True) if isinstance(result, dict) else True
    return {"output": result, "success": success}
