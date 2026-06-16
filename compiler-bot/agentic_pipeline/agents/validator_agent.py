"""ValidatorAgent — verifica resultados con verify_handler (F4) + fallback WorldModel (N3.2d)."""

from __future__ import annotations

from agentic_pipeline.prompt_chain.llm_backend import LLMBackend

from ..world_model import WorldModel
from .base_agent import Agent, SharedContext, Task, TaskResult


class ValidatorAgent(Agent):
    """Agente especializado en verificar resultados de ejecucion.

    Si se provee ``llm``, usa ``verify_handler`` del prompt chain.
    Si no, usa ``WorldModel.query()`` (rule-based).
    """

    name = "validator_agent"
    role = "verificar que los archivos generados existen y son correctos"

    def __init__(
        self,
        context: SharedContext,
        world: WorldModel | None = None,
        llm: LLMBackend | None = None,
    ):
        super().__init__(context)
        self.world = world or WorldModel()
        self._llm = llm

    async def process(self, task: Task) -> TaskResult:
        reasoning = self.context.subscribe("reasoning_result") or {}
        execution = self.context.subscribe("execution_result") or {}

        if self._llm is not None:
            result_data = await self._process_with_prompt(
                reasoning, execution,
            )
            if result_data is not None:
                self.context.publish("validation_result", result_data)
                return TaskResult(
                    task.id, result_data.get("all_passed", False),
                    data=result_data,
                )

        return await self._process_rule_based(
            task, reasoning, execution,
        )

    async def _process_with_prompt(
        self, reasoning: dict, execution: dict,
    ) -> dict | None:
        try:
            from agentic_pipeline.prompt_chain.orchestrator import (
                _ensure_prompts_registered,
            )
            _ensure_prompts_registered()

            from agentic_pipeline.prompt_chain.prompts.verify import (
                verify_handler,
            )
            files = []
            if isinstance(execution, dict):
                files_data = execution.get("files", execution.get("data", {}))
                if isinstance(files_data, dict):
                    for key, val in files_data.items():
                        files.append({"path": key, "content": str(val)})
                elif isinstance(files_data, list):
                    files = files_data

            output = await verify_handler(
                requirements=reasoning,
                files=files,
                llm=self._llm,
            )
            return {
                "all_passed": output.get("valid", False),
                "criteria_checks": output.get("checks", []),
                "total_criteria": len(output.get("checks", [])),
                "passed_criteria": sum(
                    1 for c in output.get("checks", [])
                    if c.get("passed", False)
                ),
                "file_checks": files,
            }
        except Exception:
            return None

    async def _process_rule_based(
        self, task: Task, reasoning: dict, execution: dict,
    ) -> TaskResult:
        criteria = reasoning.get("verification_criteria", [])
        if not criteria:
            criteria = task.params.get("verification_criteria", [])

        validation_results = []
        all_passed = True

        for criterion in criteria:
            answer = self.world.query(criterion)
            passed = "Si" in answer
            validation_results.append({
                "criterion": criterion,
                "result": answer,
                "passed": passed,
            })
            if not passed:
                all_passed = False

        file_checks = []
        if execution:
            if isinstance(execution, dict):
                for key in execution:
                    file_checks.append({"key": key, "present": True})

        result = {
            "all_passed": all_passed,
            "criteria_checks": validation_results,
            "total_criteria": len(criteria),
            "passed_criteria": sum(
                1 for v in validation_results if v["passed"]
            ),
            "file_checks": file_checks,
        }

        self.context.publish("validation_result", result)
        return TaskResult(
            task.id,
            success=all_passed,
            data=result,
            error=None if all_passed else "Algunos criterios no se cumplieron",
        )
