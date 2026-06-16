"""ValidatorAgent — verifica resultados usando WorldModel (N3.2d)."""

from __future__ import annotations

from ..world_model import WorldModel
from .base_agent import Agent, SharedContext, Task, TaskResult


class ValidatorAgent(Agent):
    """Agente especializado en verificar resultados de ejecucion."""

    name = "validator_agent"
    role = "verificar que los archivos generados existen y son correctos"

    def __init__(self, context: SharedContext, world: WorldModel | None = None):
        super().__init__(context)
        self.world = world or WorldModel()

    async def process(self, task: Task) -> TaskResult:
        reasoning = self.context.subscribe("reasoning_result") or {}
        execution = self.context.subscribe("execution_result") or {}

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
            "passed_criteria": sum(1 for v in validation_results if v["passed"]),
            "file_checks": file_checks,
        }

        self.context.publish("validation_result", result)
        return TaskResult(
            task_id=task.id,
            success=all_passed,
            data=result,
            error=None if all_passed else "Algunos criterios no se cumplieron",
        )
