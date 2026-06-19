"""Tests for ChainOrchestrator and CLI integration (Fase 3)."""

from __future__ import annotations

import argparse
import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agentic_pipeline.prompt_chain.llm_backend import LLMResult
from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry

# ── Helper: mock LLM result for a stage ──


def _make_result(data: dict) -> LLMResult:
    return LLMResult(
        content=str(data),
        structured=data,
        success=True,
        provider="test",
        model="test",
        duration=0.01,
    )


_FAIL_RESULT = LLMResult(success=False, error="mock failure")

_PREPROCESS_DATA = {
    "normalized": "crea modulo pagos en nestjs",
    "domain": "backend",
    "language": "es",
    "segments": ["crea modulo pagos en nestjs"],
    "has_ambiguity": False,
    "confidence": 0.95,
}

_INTENT_DATA = {
    "intent": "CREATE",
    "confidence": 0.95,
    "module": "pagos",
    "entity": None,
    "tech": ["nestjs"],
    "features": [],
    "is_ambiguous": False,
    "missing_info": [],
}

_PLAN_DATA = {
    "tasks": [
        {
            "id": "t1",
            "type": "scaffold_module",
            "target": "pagos",
            "params": {},
            "dependencies": [],
        },
    ],
    "execution_order": ["t1"],
    "complexity": "low",
    "estimated_files": 1,
}

_GENERATE_DATA = {
    "files": [
        {
            "path": "modules/pagos/pagos.module.ts",
            "content": "// modulo pagos",
        },
    ],
    "errors": [],
}

_VERIFY_VALID = {
    "valid": True,
    "checks": [],
    "should_retry": False,
    "suggestions": [],
}

_VERIFY_RETRY = {
    "valid": False,
    "checks": [],
    "should_retry": True,
    "suggestions": ["revisar imports"],
}

_FORMAT_DATA = {
    "summary": "Modulo pagos creado exitosamente.",
    "files_created": ["modules/pagos/pagos.module.ts"],
    "warnings": [],
    "next_steps": ["Revisa los archivos generados en el directorio de salida"],
    "success": True,
}


class TestChainOrchestrator:
    """Tests for ChainOrchestrator (Tarea 3.1)."""

    def setup_method(self) -> None:
        import agentic_pipeline.prompt_chain.prompts as _pkg

        _ = _pkg
        PromptRegistry.clear()
        for mod_name in [
            "preprocess",
            "intent",
            "plan",
            "generate",
            "verify",
            "format",
        ]:
            mod = importlib.import_module(
                f"agentic_pipeline.prompt_chain.prompts.{mod_name}",
            )
            importlib.reload(mod)
        import agentic_pipeline.prompt_chain.orchestrator as orch_mod

        orch_mod._PROMOTES_REGISTERED = False

    @pytest.mark.asyncio
    async def test_orchestrator_full_flow(self):
        """Cadena completa con LLM mockeado retorna output valido."""
        from agentic_pipeline.prompt_chain.orchestrator import (
            ChainOrchestrator,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.side_effect = [
            _make_result(_PREPROCESS_DATA),
            _make_result(_INTENT_DATA),
            _make_result(_PLAN_DATA),
            _make_result(_GENERATE_DATA),
            _make_result(_VERIFY_VALID),
            _make_result(_FORMAT_DATA),
        ]

        orchestrator = ChainOrchestrator(llm=mock_llm, max_retries=3)
        result = await orchestrator.run("crea modulo pagos en NestJS")

        assert result is not None
        assert result["summary"] == "Modulo pagos creado exitosamente."
        assert result["success"] is True
        assert "modules/pagos/pagos.module.ts" in result["files_created"]
        assert mock_llm.generate_structured.call_count == 6

    @pytest.mark.asyncio
    async def test_orchestrator_verify_retry(self):
        """VERIFY retorna should_retry → GENERATE se re-ejecuta."""
        from agentic_pipeline.prompt_chain.orchestrator import (
            ChainOrchestrator,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.side_effect = [
            _make_result(_PREPROCESS_DATA),
            _make_result(_INTENT_DATA),
            _make_result(_PLAN_DATA),
            _make_result(_GENERATE_DATA),
            _make_result(_VERIFY_RETRY),  # 1st verify → retry
            _make_result(_GENERATE_DATA),  # retry generate
            _make_result(_VERIFY_VALID),  # 2nd verify → format
            _make_result(_FORMAT_DATA),
        ]

        orchestrator = ChainOrchestrator(llm=mock_llm, max_retries=3)
        result = await orchestrator.run("crea modulo pagos")

        assert result is not None
        assert result["success"] is True
        assert mock_llm.generate_structured.call_count == 8

    @pytest.mark.asyncio
    async def test_orchestrator_max_retries(self):
        """Despues de N retrys, continua a FORMAT."""
        from agentic_pipeline.prompt_chain.orchestrator import (
            ChainOrchestrator,
        )

        mock_llm = AsyncMock()
        verify_retry = _VERIFY_RETRY.copy()
        # max_retries=2 → retry on attempt 1 only, attempt 2 → format
        # total calls: pre(1) + intent(2) + plan(3) + gen(4) + ver(5)
        #   + gen(6) + ver(7) + fmt(8) = 8
        mock_llm.generate_structured.side_effect = [
            _make_result(_PREPROCESS_DATA),
            _make_result(_INTENT_DATA),
            _make_result(_PLAN_DATA),
            _make_result(_GENERATE_DATA),  # attempt 1 → attempt_count=1
            _make_result(verify_retry),  # verify → 1 < 2 → retry
            _make_result(_GENERATE_DATA),  # attempt 2 → attempt_count=2
            _make_result(verify_retry),  # verify → 2 >= 2 → format
            _make_result(_FORMAT_DATA),
        ]

        orchestrator = ChainOrchestrator(llm=mock_llm, max_retries=2)
        result = await orchestrator.run("crea modulo pagos")

        assert result is not None
        assert "summary" in result
        assert mock_llm.generate_structured.call_count == 8

    @pytest.mark.asyncio
    async def test_orchestrator_fallback_only(self):
        """Sin LLM (todos fallan), toda la cadena usa fallbacks."""
        from agentic_pipeline.prompt_chain.orchestrator import (
            ChainOrchestrator,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = _FAIL_RESULT

        orchestrator = ChainOrchestrator(llm=mock_llm)
        result = await orchestrator.run("crea modulo pagos")

        # All LLM calls fail → fallbacks are invoked.
        # Con los 5 bugs fixeados, los 6 fallbacks rule-based completan
        # el pipeline entero sin errores.
        assert isinstance(result, dict)
        assert result.get("success", False) is True
        assert mock_llm.generate_structured.call_count == 6

    @pytest.mark.asyncio
    async def test_orchestrator_debug_callback(self):
        """Callback recibe output de cada etapa."""
        from agentic_pipeline.prompt_chain.orchestrator import (
            ChainOrchestrator,
        )

        mock_llm = AsyncMock()
        mock_llm.generate_structured.side_effect = [
            _make_result(_PREPROCESS_DATA),
            _make_result(_INTENT_DATA),
            _make_result(_PLAN_DATA),
            _make_result(_GENERATE_DATA),
            _make_result(_VERIFY_VALID),
            _make_result(_FORMAT_DATA),
        ]

        callback = MagicMock()

        orchestrator = ChainOrchestrator(llm=mock_llm, debug_callback=callback)
        result = await orchestrator.run("crea modulo pagos")

        assert result is not None
        assert callback.call_count == 6
        called_stages = [call.args[0] for call in callback.call_args_list]
        assert called_stages == [
            "preprocess",
            "intent",
            "plan",
            "generate",
            "verify",
            "format",
        ]

    @pytest.mark.asyncio
    async def test_orchestrator_invalid_input(self):
        """Input vacio → manejo graceful (no crash)."""
        from agentic_pipeline.prompt_chain.orchestrator import (
            ChainOrchestrator,
        )

        mock_llm = AsyncMock()
        empty_preprocess = {
            "normalized": "",
            "domain": "general",
            "language": "es",
            "segments": [],
            "has_ambiguity": True,
            "confidence": 0.1,
        }
        empty_intent = {
            "intent": "EXPLAIN",
            "confidence": 0.1,
            "module": None,
            "entity": None,
            "tech": [],
            "features": [],
            "is_ambiguous": True,
            "missing_info": ["input insuficiente"],
        }
        mock_llm.generate_structured.side_effect = [
            _make_result(empty_preprocess),
            _make_result(empty_intent),
            _make_result(_PLAN_DATA),
            _make_result(_GENERATE_DATA),
            _make_result(_VERIFY_VALID),
            _make_result(_FORMAT_DATA),
        ]

        orchestrator = ChainOrchestrator(llm=mock_llm)
        result = await orchestrator.run("")

        assert result is not None
        assert isinstance(result, dict)


class TestChainOrchestratorCLI:
    """Tests para CLI integration (Tarea 3.2 + 3.3)."""

    def test_add_chain_args_adds_flag(self):
        """add_chain_args anade el flag --chain al parser."""
        from agentic_pipeline.prompt_chain.cli import add_chain_args

        parser = argparse.ArgumentParser()
        add_chain_args(parser)

        args = parser.parse_args([])
        assert args.chain is False

        args = parser.parse_args(["--chain"])
        assert args.chain is True

    @pytest.mark.asyncio
    async def test_cli_chain_flag(self):
        """run_chain invoca ChainOrchestrator y retorna output."""
        from agentic_pipeline.prompt_chain.cli import run_chain

        mock_result = {"summary": "test", "files_created": [], "success": True}

        with patch(
            "agentic_pipeline.prompt_chain.orchestrator.ChainOrchestrator",
        ) as MockOrch:
            instance = AsyncMock()
            instance.run.return_value = mock_result
            MockOrch.return_value = instance

            result = await run_chain("crea modulo pagos")

            MockOrch.assert_called_once()
            instance.run.assert_awaited_once_with("crea modulo pagos")
            assert result["success"] is True
            assert result["output"]["summary"] == "test"
