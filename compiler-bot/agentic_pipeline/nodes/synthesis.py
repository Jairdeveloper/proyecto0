"""Synthesis stage — generates code files from planner output using generators."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..base_stage import PipelineStage
from ..generators.base_generator import GeneratorFactory
from ..generators.code_formatter import CodeFormatter
from ..state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)


class SynthesisOrchestrator(PipelineStage):
    """Stage 8: generates target code files from planned tasks and IR tree."""

    name = "synthesis"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_data: dict[str, Any] | None = None
        self._output_dir: Path = Path("modules")
        self._formatter = CodeFormatter()

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            self._input_data = input_data
        else:
            self._input_data = {}

    def analyze(self) -> AnalysisResult:
        task_count = len(self._input_data.get("tasks", [])) if self._input_data else 0
        return AnalysisResult(
            observations=[f"Tasks to synthesize: {task_count}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.4,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(
            steps=[
                {"action": "resolve_generators"},
                {"action": "generate_code"},
                {"action": "format_output"},
            ],
            strategy="deterministic",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        ir_tree = self._input_data.get("ir_tree") if self._input_data else None
        commands = self._input_data.get("commands", []) if self._input_data else []
        tasks = self._input_data.get("tasks", []) if self._input_data else []

        generated_files: list[str] = []
        errors: list[str] = []
        warnings: list[str] = []

        for cmd in commands:
            cmd_type = cmd.get("type", "")
            if cmd_type == "scaffold":
                warnings.append(
                    "Command type 'scaffold' is deprecated. "
                    "Use AST-based generators instead. "
                    "See agentic_pipeline/generators/"
                )

        if ir_tree is not None:
            file_paths = self._generate_from_tree(ir_tree)
            generated_files.extend(str(p) for p in file_paths)

        for cmd in commands:
            task_id = cmd.get("task_id", "unknown")
            target = self._find_target(tasks, task_id)
            if target is None:
                errors.append(f"No target found for task '{task_id}'")
                continue
            path_str = cmd.get("path", f"modules/{task_id}")
            task_dir = Path(path_str)
            task_dir.mkdir(parents=True, exist_ok=True)
            ir_node = self._find_ir_node(ir_tree, task_id)
            if ir_node is None:
                errors.append(f"No IR node found for task '{task_id}'")
                continue
            gen = self._get_generator(target)
            if gen is None:
                errors.append(f"No generator for target '{target}'")
                continue
            try:
                created = gen.generate(ir_node, task_dir)
                generated_files.extend(str(p) for p in created)
            except Exception as e:
                errors.append(f"Generation failed for '{task_id}': {e}")

        for fp_str in generated_files:
            self._formatter.format_file(Path(fp_str))

        return StageOutput(
            stage=self.context.stage,
            output_data={
                "generated_files": generated_files,
                "errors": errors,
                "warnings": warnings,
                "task_count": len(tasks),
            },
            metrics={
                "files_generated": len(generated_files),
                "errors": len(errors),
            },
            success=len(errors) == 0,
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass

    def _generate_from_tree(self, ir_tree: object) -> list[Path]:
        created: list[Path] = []
        ir_type = type(ir_tree).__name__
        if ir_type == "IRProject":
            for child in getattr(ir_tree, "children", []):
                target = self._detect_target(child)
                gen = self._get_generator(target)
                if gen is None:
                    continue
                child_dir = self._output_dir / getattr(child, "name", "unknown").lower()
                created.extend(gen.generate(child, child_dir))
        return created

    @staticmethod
    def _detect_target(node: object) -> str:
        type_name = type(node).__name__
        if type_name in ("IREntity",):
            return "prisma"
        if type_name in ("IRAPI",):
            return "nestjs"
        if type_name in ("IRPage", "IRComponent"):
            return "react"
        if type_name in ("IRInfra",):
            return "docker"
        if type_name in ("IRConfig",):
            return "tailwind"
        return "generic"

    @staticmethod
    def _get_generator(target: str) -> object | None:
        try:
            return GeneratorFactory.get_generator(target)
        except ValueError:
            return None

    @staticmethod
    def _find_target(tasks: list[dict], task_id: str) -> str | None:
        for t in tasks:
            if t.get("id") == task_id:
                return t.get("target")
        return None

    @staticmethod
    def _find_ir_node(ir_tree: object, node_id: str) -> object | None:
        if ir_tree is None:
            return None
        name = getattr(ir_tree, "name", "")
        if name and name.lower() == node_id.lower():
            return ir_tree
        for child in getattr(ir_tree, "children", []):
            result = SynthesisOrchestrator._find_ir_node(child, node_id)
            if result is not None:
                return result
        return None
