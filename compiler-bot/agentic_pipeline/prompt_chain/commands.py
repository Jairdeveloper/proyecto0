"""Prompt Command wrappers — encapsulan handlers como Command."""

from __future__ import annotations

import logging
import time
from typing import Any

from agentic_pipeline.prompt_chain.chain_context import ChainContext
from agentic_pipeline.prompt_chain.command_base import Command, CommandResult
from agentic_pipeline.prompt_chain.handler_base import PromptRequest
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend

logger = logging.getLogger(__name__)


class PreprocessCommand(Command):
    """Command que ejecuta PREPROCESS handler."""

    name = "preprocess"

    def __init__(
        self,
        raw_text: str,
        llm: LLMBackend | None = None,
    ) -> None:
        self._raw_text = raw_text
        self._llm = llm

    async def execute(self) -> CommandResult:
        from agentic_pipeline.prompt_chain.prompts.preprocess import (
            PreprocessHandler,
        )

        t0 = time.time()
        try:
            handler = PreprocessHandler(llm=self._llm)
            request = PromptRequest(raw_input=self._raw_text)
            ctx = ChainContext()
            response = await handler.handle(request, ctx)
            duration = time.time() - t0
            return CommandResult(
                success=response.success,
                data=response.output,
                error=response.error,
                duration=duration,
                command_name=self.name,
                fallback_used=False,
            )
        except Exception as exc:
            duration = time.time() - t0
            return CommandResult(
                success=False,
                error=str(exc),
                duration=duration,
                command_name=self.name,
            )


class IntentCommand(Command):
    """Command que ejecuta INTENT handler."""

    name = "intent"

    def __init__(
        self,
        normalized_text: str,
        domain: str = "backend",
        llm: LLMBackend | None = None,
    ) -> None:
        self._normalized_text = normalized_text
        self._domain = domain
        self._llm = llm

    async def execute(self) -> CommandResult:
        from agentic_pipeline.prompt_chain.prompts.intent import IntentHandler

        t0 = time.time()
        try:
            handler = IntentHandler(llm=self._llm)
            request = PromptRequest(raw_input=self._normalized_text)
            ctx = ChainContext()
            ctx.set_output(
                "preprocess",
                {
                    "normalized": self._normalized_text,
                    "domain": self._domain,
                },
            )
            response = await handler.handle(request, ctx)
            duration = time.time() - t0
            return CommandResult(
                success=response.success,
                data=response.output,
                error=response.error,
                duration=duration,
                command_name=self.name,
            )
        except Exception as exc:
            duration = time.time() - t0
            return CommandResult(
                success=False,
                error=str(exc),
                duration=duration,
                command_name=self.name,
            )


class PlanCommand(Command):
    """Command que ejecuta PLAN handler."""

    name = "plan"

    def __init__(
        self,
        intent: str,
        module: str | None = None,
        entity: str | None = None,
        tech: list[str] | None = None,
        features: list[str] | None = None,
        llm: LLMBackend | None = None,
    ) -> None:
        self._intent = intent
        self._module = module
        self._entity = entity
        self._tech = tech or []
        self._features = features or []
        self._llm = llm

    async def execute(self) -> CommandResult:
        from agentic_pipeline.prompt_chain.prompts.plan import PlanHandler

        t0 = time.time()
        try:
            handler = PlanHandler(llm=self._llm)
            request = PromptRequest(raw_input=self._intent)
            ctx = ChainContext()
            ctx.set_output("preprocess", {"normalized": "", "domain": "backend"})
            ctx.set_output(
                "intent",
                {
                    "intent": self._intent,
                    "module": self._module,
                    "entity": self._entity,
                    "tech": self._tech,
                    "features": self._features,
                },
            )
            response = await handler.handle(request, ctx)
            duration = time.time() - t0
            return CommandResult(
                success=response.success,
                data=response.output,
                error=response.error,
                duration=duration,
                command_name=self.name,
            )
        except Exception as exc:
            duration = time.time() - t0
            return CommandResult(
                success=False,
                error=str(exc),
                duration=duration,
                command_name=self.name,
            )


class GenerateCommand(Command):
    """Command que ejecuta GENERATE handler."""

    name = "generate"

    def __init__(
        self,
        tasks: list[dict[str, Any]],
        existing_files: list[str] | None = None,
        llm: LLMBackend | None = None,
    ) -> None:
        self._tasks = tasks
        self._existing_files = existing_files or []
        self._llm = llm

    async def execute(self) -> CommandResult:
        from agentic_pipeline.prompt_chain.prompts.generate import (
            GenerateHandler,
        )

        t0 = time.time()
        try:
            handler = GenerateHandler(llm=self._llm)
            request = PromptRequest(raw_input="generate")
            ctx = ChainContext()
            ctx.set_output(
                "plan",
                {
                    "tasks": self._tasks,
                    "execution_order": [t.get("id", "") for t in self._tasks],
                },
            )
            response = await handler.handle(request, ctx)
            duration = time.time() - t0
            return CommandResult(
                success=response.success,
                data=response.output,
                error=response.error,
                duration=duration,
                command_name=self.name,
            )
        except Exception as exc:
            duration = time.time() - t0
            return CommandResult(
                success=False,
                error=str(exc),
                duration=duration,
                command_name=self.name,
            )


class VerifyCommand(Command):
    """Command que ejecuta VERIFY handler."""

    name = "verify"

    def __init__(
        self,
        requirements: dict[str, Any],
        files: list[dict[str, Any]],
        criteria: list[str] | None = None,
        llm: LLMBackend | None = None,
    ) -> None:
        self._requirements = requirements
        self._files = files
        self._criteria = criteria or []
        self._llm = llm

    async def execute(self) -> CommandResult:
        from agentic_pipeline.prompt_chain.prompts.verify import VerifyHandler

        t0 = time.time()
        try:
            handler = VerifyHandler(llm=self._llm)
            request = PromptRequest(raw_input="verify")
            ctx = ChainContext()
            ctx.set_output("intent", self._requirements)
            ctx.set_output("generate", {"files": self._files, "errors": []})
            response = await handler.handle(request, ctx)
            duration = time.time() - t0
            return CommandResult(
                success=response.success,
                data=response.output,
                error=response.error,
                duration=duration,
                command_name=self.name,
            )
        except Exception as exc:
            duration = time.time() - t0
            return CommandResult(
                success=False,
                error=str(exc),
                duration=duration,
                command_name=self.name,
            )


class FormatCommand(Command):
    """Command que ejecuta FORMAT handler."""

    name = "format"

    def __init__(
        self,
        original_request: str,
        plan: dict[str, Any],
        generated_files: list[dict[str, Any]],
        validation: dict[str, Any],
        llm: LLMBackend | None = None,
    ) -> None:
        self._original_request = original_request
        self._plan = plan
        self._generated_files = generated_files
        self._validation = validation
        self._llm = llm

    async def execute(self) -> CommandResult:
        from agentic_pipeline.prompt_chain.prompts.format import FormatHandler

        t0 = time.time()
        try:
            handler = FormatHandler(llm=self._llm)
            request = PromptRequest(raw_input=self._original_request)
            ctx = ChainContext()
            ctx.set_output("plan", self._plan)
            ctx.set_output("generate", {"files": self._generated_files, "errors": []})
            ctx.set_output("verify", self._validation)
            response = await handler.handle(request, ctx)
            duration = time.time() - t0
            return CommandResult(
                success=response.success,
                data=response.output,
                error=response.error,
                duration=duration,
                command_name=self.name,
            )
        except Exception as exc:
            duration = time.time() - t0
            return CommandResult(
                success=False,
                error=str(exc),
                duration=duration,
                command_name=self.name,
            )
