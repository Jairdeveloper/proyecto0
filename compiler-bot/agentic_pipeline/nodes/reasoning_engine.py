"""ReasoningEngine — Task model, TaskGraph, HeuristicPlanner, GoalTreePlanner, stage."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from graphlib import TopologicalSorter
from typing import Any, Literal, Optional

from pydantic import BaseModel

from ..base_stage import PipelineStage
from ..state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)


# ============================================================================
# GoalTreePlanner (N2.2b)
# ============================================================================


@dataclass
class Goal:
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "failed", "blocked"]
    dependencies: list[str] = field(default_factory=list)
    subtasks: list[Goal] = field(default_factory=list)
    verification_criteria: list[str] = field(default_factory=list)
    result: Any = None
    error: str | None = None


class GoalTreePlanner:
    """Planificador estrategico con descomposicion, verificacion y replan."""

    def __init__(self, memory: Optional[object] = None):
        self.memory = memory
        self._plan_templates = {
            "create_module": self._plan_create_module,
            "create_entity": self._plan_create_entity,
            "create_crud": self._plan_create_crud,
            "explain": self._plan_explain,
        }

    def decompose(self, objective: str, intent: str,
                  entities: list[dict], world: object = None) -> Goal:
        template_key = self._match_template(intent, entities)
        builder = self._plan_templates.get(template_key, self._plan_generic)
        return builder(objective, entities, world)

    def verify(self, goal: Goal, world: object) -> bool:
        if not goal.verification_criteria:
            return True
        for criterion in goal.verification_criteria:
            if hasattr(world, "query"):
                result = world.query(criterion)
                if "Si" not in result and "Si," not in result:
                    return False
        return True

    def replan(self, goal: Goal, world: object, error: str) -> Goal:
        goal.status = "failed"
        goal.error = error
        fix = Goal(
            id=f"{goal.id}_fix",
            description=f"corregir: {error}",
            status="pending",
            dependencies=goal.dependencies,
        )
        goal.subtasks.append(fix)
        return goal

    def _match_template(self, intent: str, entities: list[dict]) -> str:
        intent_lower = intent.lower()
        if intent_lower == "explain":
            return "explain"
        types = {e.get("type", "") for e in entities}
        if "module" in types or "modulo" in types:
            return "create_module"
        if "entity" in types or "entidad" in types:
            return "create_entity"
        if "crud" in types:
            return "create_crud"
        return "create_module"

    def _extract_module_name(self, objective: str, entities: list[dict]) -> str:
        for e in entities:
            name = e.get("name", "")
            if name:
                return name
        words = objective.lower().split()
        if "modulo" in words:
            idx = words.index("modulo")
            if idx + 1 < len(words):
                return words[idx + 1]
        if "de" in words:
            idx = words.index("de")
            if idx + 1 < len(words):
                return words[idx + 1]
        return "app"

    def _plan_create_module(self, objective: str, entities: list[dict],
                            world: object = None) -> Goal:
        module_name = self._extract_module_name(objective, entities)
        return Goal(
            id="create_module",
            description=f"Crear modulo {module_name}",
            status="pending",
            verification_criteria=[
                f"existe modules/{module_name}/{module_name}.module.ts?",
                f"existe modules/{module_name}/{module_name}.controller.ts?",
                f"existe modules/{module_name}/{module_name}.service.ts?",
            ],
            subtasks=[
                Goal(id="create_dir", description=f"Crear directorio modules/{module_name}",
                     status="pending",
                     verification_criteria=[f"existe modules/{module_name}?"]),
                Goal(id="create_module_file", description="Crear archivo .module.ts",
                     status="pending", dependencies=["create_dir"]),
                Goal(id="create_controller", description="Crear archivo .controller.ts",
                     status="pending", dependencies=["create_dir"]),
                Goal(id="create_service", description="Crear archivo .service.ts",
                     status="pending", dependencies=["create_dir"]),
            ],
        )

    def _plan_create_entity(self, objective: str, entities: list[dict],
                            world: object = None) -> Goal:
        entity_name = self._extract_module_name(objective, entities)
        return Goal(
            id="create_entity",
            description=f"Crear entidad {entity_name}",
            status="pending",
            verification_criteria=[
                f"existe prisma/schema/{entity_name}.prisma?",
            ],
            subtasks=[
                Goal(id="create_entity_schema", description=f"Crear schema {entity_name}",
                     status="pending",
                     verification_criteria=[f"existe prisma/schema/{entity_name}.prisma?"]),
            ],
        )

    def _plan_create_crud(self, objective: str, entities: list[dict],
                          world: object = None) -> Goal:
        name = self._extract_module_name(objective, entities)
        return Goal(
            id="create_crud",
            description=f"Crear CRUD para {name}",
            status="pending",
            verification_criteria=[
                f"existe modules/{name}/{name}.module.ts?",
                f"existe modules/{name}/{name}.controller.ts?",
                f"existe modules/{name}/{name}.service.ts?",
                f"existe prisma/schema/{name}.prisma?",
            ],
            subtasks=[
                Goal(id="crud_module", description=f"Crear modulo {name}",
                     status="pending"),
                Goal(id="crud_entity", description=f"Crear entidad {name}",
                     status="pending", dependencies=["crud_module"]),
                Goal(id="crud_service", description=f"Crear servicio CRUD {name}",
                     status="pending", dependencies=["crud_entity"]),
            ],
        )

    def _plan_explain(self, objective: str, entities: list[dict],
                      world: object = None) -> Goal:
        return Goal(
            id="explain",
            description=f"Explicar: {objective[:80]}",
            status="pending",
            verification_criteria=[],
            subtasks=[],
        )

    def _plan_generic(self, objective: str, entities: list[dict],
                      world: object = None) -> Goal:
        return Goal(
            id="generic",
            description=objective[:100],
            status="pending",
            verification_criteria=[],
            subtasks=[],
        )


# ============================================================================
# Task model
# ============================================================================


class TaskState(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"


class Task(BaseModel):
    id: str
    description: str
    dependencies: list[str] = []
    generator: str = ""
    target: str = ""
    state: TaskState = TaskState.PENDING
    output_path: str = ""
    validation_rules: list[str] = []

    def can_run(self, done_ids: set[str]) -> bool:
        return all(d in done_ids for d in self.dependencies)


# ============================================================================
# TaskGraph — manages task ordering
# ============================================================================


class TaskGraph:
    """Directed graph of tasks with topological ordering."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._edges: dict[str, set[str]] = {}

    def add_task(self, task: Task) -> None:
        self._tasks[task.id] = task
        if task.id not in self._edges:
            self._edges[task.id] = set()
        for dep_id in task.dependencies:
            self._edges[task.id].add(dep_id)

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def topological_order(self) -> list[str]:
        try:
            sorter = TopologicalSorter(self._edges)
            return list(sorter.static_order())
        except ValueError as e:
            logger.error("Cycle in task graph: %s", e)
            return []

    def has_cycle(self) -> bool:
        try:
            list(TopologicalSorter(self._edges).static_order())
            return False
        except ValueError:
            return True

    def ready_tasks(self, done_ids: set[str]) -> list[Task]:
        return [
            t
            for t in self._tasks.values()
            if t.id not in done_ids
            and t.state == TaskState.PENDING
            and t.can_run(done_ids)
        ]


# ============================================================================
# HeuristicPlanner — simple task planning
# ============================================================================


class HeuristicPlanner:
    """Planner for simple cases (<= 5 dependencies). Groups tasks by layer."""

    LAYER_ORDER = ["config", "domain", "data", "api", "ui", "infra"]

    def plan(self, task_graph: TaskGraph) -> list[Task]:
        order = task_graph.topological_order()
        planned: list[Task] = []
        for task_id in order:
            task = task_graph.get_task(task_id)
            if task is not None:
                planned.append(task)
        return planned

    def group_by_layer(self, tasks: list[Task]) -> dict[str, list[Task]]:
        groups: dict[str, list[Task]] = {}
        for layer in self.LAYER_ORDER:
            groups[layer] = []
        for t in tasks:
            layer = self._detect_layer(t)
            if layer not in groups:
                groups[layer] = []
            groups[layer].append(t)
        return groups

    @staticmethod
    def _detect_layer(task: Task) -> str:
        tid = task.id.lower()
        if any(kw in tid for kw in ("config", "setting", "env")):
            return "config"
        if any(kw in tid for kw in ("entidad", "entity", "model", "prisma")):
            return "data"
        if any(kw in tid for kw in ("api", "control", "route", "endpoint")):
            return "api"
        if any(kw in tid for kw in ("pagina", "page", "component", "ui", "view")):
            return "ui"
        if any(kw in tid for kw in ("db", "database", "infra", "deploy", "docker")):
            return "infra"
        return "domain"

    def estimate_complexity(self, task_graph: TaskGraph) -> str:
        task_count = len(task_graph.all_tasks())
        if task_count <= 3:
            return "simple"
        if task_count <= 5:
            return "moderate"
        return "complex"


# ============================================================================
# ReasoningEngine — PipelineStage
# ============================================================================


class ReasoningEngine(PipelineStage):
    """Stage 7: plans task execution order using heuristic or LLM."""

    name = "planner"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_data: dict[str, Any] | None = None
        self._heuristic = HeuristicPlanner()
        self._task_graph = TaskGraph()
        self._enriched: dict = {}
        self._goal_planner = GoalTreePlanner()

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            self._input_data = input_data
            self._enriched = input_data.get("enriched", {}) or {}
        else:
            self._input_data = {}
            self._enriched = {}

    def analyze(self) -> AnalysisResult:
        dep_order = (
            self._input_data.get("dependency_order", []) if self._input_data else []
        )
        return AnalysisResult(
            observations=[f"Dependency order: {dep_order}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.3,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        complexity = self._heuristic.estimate_complexity(self._task_graph)
        strategy = "heuristic" if complexity in ("simple", "moderate") else "llm"
        return ActionPlan(
            steps=[
                {"action": "build_task_graph"},
                {"action": "decompose_goal"},  # N2.2b
                {"action": "plan_execution_order"},
                {"action": "assign_commands"},
            ],
            strategy=strategy,
            estimated_cost=0.1 if strategy == "heuristic" else 1.0,
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        self._task_graph = TaskGraph()
        ir_tree = self._input_data.get("ir_tree") if self._input_data else None
        self._build_tasks_from_ir()

        # Goal decomposition (N2.2b)
        goal_result = None
        if self._input_data:
            objective = str(self._input_data.get("intent", {}).get("raw", ""))
            intent_name = str(self._input_data.get("intent", {}).get("primary", ""))
            entities_raw = self._input_data.get("entities", {})
            entities_list = []
            if isinstance(entities_raw, dict):
                for key in ("modulos", "techs", "entities"):
                    for item in entities_raw.get(key, []):
                        if isinstance(item, dict):
                            entities_list.append(item)
                        elif isinstance(item, str):
                            entities_list.append({"name": item, "type": key})
            goal = self._goal_planner.decompose(objective, intent_name, entities_list)
            goal_result = {
                "goal_id": goal.id,
                "goal_description": goal.description,
                "subtasks": [
                    {"id": s.id, "description": s.description, "status": s.status}
                    for s in goal.subtasks
                ],
                "verification_criteria": goal.verification_criteria,
            }

        complexity = self._heuristic.estimate_complexity(self._task_graph)
        ordered = self._heuristic.plan(self._task_graph)
        layers = self._heuristic.group_by_layer(ordered)
        commands = self._build_commands(ordered)
        return StageOutput(
            stage=self.context.stage,
            output_data={
                "tasks": [t.model_dump() for t in ordered],
                "task_graph": ordered,
                "layers": {k: [t.model_dump() for t in v] for k, v in layers.items()},
                "complexity": complexity,
                "execution_order": [t.id for t in ordered],
                "commands": commands,
                "is_acyclic": not self._task_graph.has_cycle(),
                "ir_tree": ir_tree,
                "enriched": self._enriched or None,
                "goal_tree": goal_result,
            },
            metrics={
                "task_count": len(ordered),
                "complexity": complexity,
                "goal_decomposed": goal_result is not None,
            },
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass

    def _build_tasks_from_ir(self) -> None:
        ir_tree = self._input_data.get("ir_tree") if self._input_data else None
        if ir_tree is None:
            return
        for child in getattr(ir_tree, "children", []):
            task_id = getattr(child, "name", "unnamed")
            task = Task(
                id=task_id,
                description=f"Generate {task_id}",
                generator=type(child).__name__,
                target=self._detect_target(child),
            )
            self._task_graph.add_task(task)
            for sub in getattr(child, "children", []):
                sub_id = getattr(sub, "name", "unnamed")
                sub_task = Task(
                    id=sub_id,
                    description=f"Generate {sub_id}",
                    generator=type(sub).__name__,
                    target=self._detect_target(sub),
                    dependencies=[task_id],
                )
                self._task_graph.add_task(sub_task)

    @staticmethod
    def _detect_target(node: Any) -> str:
        type_name = type(node).__name__
        if type_name in ("IREntity",):
            return "prisma"
        if type_name in ("IRAPI",):
            return "nestjs"
        if type_name in ("IRPage", "IRComponent"):
            return "react"
        if type_name in ("IRInfra",):
            return "docker"
        return "generic"

    def _build_commands(self, tasks: list[Task]) -> list[dict[str, Any]]:
        commands: list[dict[str, Any]] = []
        for task in tasks:
            commands.append(
                {
                    "task_id": task.id,
                    "type": "scaffold",
                    "path": f"modules/{task.id.lower()}",
                }
            )
        return commands
