"""UI Generator stage — produces specialized UI components from IR nodes."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.generators.design_tokens import DesignTokens
from agentic_pipeline.generators.responsive_engine import (
    AccessibilityInjector,
    AnimationInjector,
)
from agentic_pipeline.generators.ui_component_builder import ComponentFactory
from agentic_pipeline.state_models import ActionPlan, AnalysisResult, StageContext, StageOutput

logger = logging.getLogger(__name__)


class UIGenerator(PipelineStage):
    """Stage 10: generates specialized UI components (Form, Table, etc.)."""

    name = "ui_generator"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_data: dict[str, Any] | None = None
        self._output_dir: Path = Path(
            context.config_overrides.get("output_dir", "modules"),
        )
        self._enriched: dict = {}

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            self._input_data = input_data
            self._enriched = input_data.get("enriched", {}) or {}
        else:
            self._input_data = {}
            self._enriched = {}

    def analyze(self) -> AnalysisResult:
        tasks = self._input_data.get("tasks", []) if self._input_data else []
        return AnalysisResult(
            observations=[f"UI tasks to process: {len(tasks)}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.35,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(
            steps=[
                {"action": "inject_design_tokens"},
                {"action": "build_ui_components"},
                {"action": "apply_responsive"},
                {"action": "inject_accessibility"},
                {"action": "inject_animations"},
            ],
            strategy="deterministic",
        )

    def act(self, plan: ActionPlan) -> StageOutput:
        ir_tree = self._input_data.get("ir_tree") if self._input_data else None
        tasks = self._input_data.get("tasks", []) if self._input_data else []
        enriched = (self._input_data.get("enriched", {}) or {}) if self._input_data else {}
        generated_files: list[str] = []
        errors: list[str] = []

        previous_files = self._input_data.get("generated_files", []) if self._input_data else []

        # --- Domain gate ---
        domain = enriched.get("intent", {}).get("domain", "backend")
        if domain != "ui":
            ui_components = self._detect_ui_components(ir_tree, tasks)
            if not ui_components:
                return StageOutput(
                    stage=self.context.stage,
                    output_data={
                        "generated_files": previous_files,
                        "errors": [],
                        "task_count": len(tasks),
                        "enriched": enriched or None,
                    },
                    metrics={
                        "files_generated": len(previous_files),
                        "errors": 0,
                        "components": 0,
                        "domain": domain,
                        "ui_components_detected": 0,
                        "domain_gate_triggered": True,
                    },
                    success=True,
                )

        output_dir = self._output_dir / "ui"
        output_dir.mkdir(parents=True, exist_ok=True)

        design_css = output_dir / "design-tokens.css"
        design_css.write_text(DesignTokens.css())
        generated_files.append(str(design_css))

        responsive_css = output_dir / "responsive.css"
        responsive_css.write_text(self._generate_responsive_css())
        generated_files.append(str(responsive_css))

        animation_css = output_dir / "animations.css"
        animation_css.write_text(self._generate_animation_css())
        generated_files.append(str(animation_css))

        ui_components = self._detect_ui_components(ir_tree, tasks)
        for comp in ui_components:
            try:
                filepath = self._render_component(comp, output_dir)
                generated_files.append(str(filepath))
            except Exception as e:
                errors.append(f"Failed to render {comp.get('name', 'unknown')}: {e}")

        tokens_json = output_dir / "design-tokens.json"
        tokens_json.write_text(json.dumps(DesignTokens.tailwind_config(), indent=2))
        generated_files.append(str(tokens_json))

        all_files = list(previous_files) + generated_files
        seen = set()
        deduped = []
        for f in all_files:
            if f not in seen:
                seen.add(f)
                deduped.append(f)

        return StageOutput(
            stage=self.context.stage,
            output_data={
                "generated_files": deduped,
                "errors": errors,
                "task_count": len(tasks),
                "ir_tree": ir_tree,
                "tasks": tasks,
                "enriched": enriched or None,
            },
            metrics={
                "files_generated": len(generated_files),
                "errors": len(errors),
                "components": len(ui_components),
                "domain": domain,
                "ui_components_detected": len(ui_components),
                "domain_gate_triggered": domain != "ui",
            },
            success=len(errors) == 0,
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_ui_components(
        ir_tree: object,
        tasks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        components: list[dict[str, Any]] = []
        seen: set[str] = set()

        if ir_tree is not None:
            for child in getattr(ir_tree, "children", []):
                name = getattr(child, "name", "").lower()
                if "form" in name and name not in seen:
                    components.append(ComponentFactory.form(name.capitalize()))
                    seen.add(name)
                if "table" in name or "list" in name:
                    if name not in seen:
                        components.append(ComponentFactory.table(name.capitalize()))
                        seen.add(name)

        for task in tasks:
            task_name = task.get("id", "").lower()
            if "form" in task_name and task_name not in seen:
                components.append(ComponentFactory.form(task.get("id", "Form").capitalize()))
                seen.add(task_name)
            if ("table" in task_name or "list" in task_name) and task_name not in seen:
                components.append(ComponentFactory.table(task.get("id", "Table").capitalize()))
                seen.add(task_name)

        return components

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_component(
        self,
        component: dict[str, Any],
        output_dir: Path,
    ) -> Path:
        comp = AccessibilityInjector.inject(component)
        comp = AnimationInjector.inject(comp)
        name = comp.get("name", "Component")
        filepath = output_dir / f"{name.lower()}.tsx"
        code = self._component_to_tsx(comp)
        filepath.write_text(code)
        return filepath

    @staticmethod
    def _component_to_tsx(component: dict[str, Any]) -> str:
        name = component.get("name", "Component")
        ctype = component.get("type", "div")
        props = component.get("props", {})
        styles = component.get("styles", {})
        events = component.get("events", {})
        aria = component.get("aria", {})
        animations = component.get("animations", {})
        children = component.get("children", [])

        imports = [
            "import React from 'react';",
            "import '../ui/design-tokens.css';",
            "import '../ui/animations.css';",
            "",
        ]

        props_type = f"{name}Props"
        props_lines = []
        for key, val in props.items():
            if isinstance(val, str):
                props_lines.append(f"  {key}?: string;")
            elif isinstance(val, bool):
                props_lines.append(f"  {key}?: boolean;")
            else:
                props_lines.append(f"  {key}?: any;")
        if not props_lines:
            props_lines.append("  children?: React.ReactNode;")

        style_str = json.dumps(styles, indent=4) if styles else "{}"
        event_attrs = " ".join(f"{k}={{{v}}}" for k, v in events.items())
        aria_attrs = " ".join(f'aria-{k.replace("_", "-")}="{v}"' for k, v in aria.items())
        anim_class = AnimationInjector.to_tailwind(animations)

        if children:
            child_code = "\n".join(UIGenerator._child_to_tsx(c) for c in children)
            return (
                f"{''.join(imports)}"
                f"interface {props_type} {{\n"
                f"{''.join(props_lines)}\n"
                f"}}\n\n"
                f"const {name}: React.FC<{props_type}> = ({{ ...props }}) => {{\n"
                f"  return (\n"
                f"    <{ctype}\n"
                f"      style={{...{style_str}}}\n"
                f'      className="{anim_class}"\n'
                f"      {event_attrs}\n"
                f"      {aria_attrs}\n"
                f"    >\n"
                f"      {child_code}\n"
                f"    </{ctype}>\n"
                f"  );\n"
                f"}};\n\n"
                f"export default {name};\n"
            )
        return (
            f"{''.join(imports)}"
            f"interface {props_type} {{\n"
            f"{''.join(props_lines)}\n"
            f"}}\n\n"
            f"const {name}: React.FC<{props_type}> = ({{ ...props }}) => {{\n"
            f"  return (\n"
            f"    <{ctype}\n"
            f"      style={{...{style_str}}}\n"
            f'      className="{anim_class}"\n'
            f"      {event_attrs}\n"
            f"      {aria_attrs}\n"
            f"    >\n"
            f"      {{/* {name.lower()} content */}}\n"
            f"    </{ctype}>\n"
            f"  );\n"
            f"}};\n\n"
            f"export default {name};\n"
        )

    @staticmethod
    def _child_to_tsx(child: dict[str, Any]) -> str:
        ctype = child.get("type", "div")
        events = child.get("events", {})
        aria = child.get("aria", {})
        styles = child.get("styles", {})
        animations = child.get("animations", {})

        style_str = json.dumps(styles, indent=4) if styles else "{}"
        event_attrs = " ".join(f"{k}={{{v}}}" for k, v in events.items())
        aria_attrs = " ".join(f'aria-{k.replace("_", "-")}="{v}"' for k, v in aria.items())
        anim_class = AnimationInjector.to_tailwind(animations)
        return (
            f"      <{ctype}\n"
            f"        style={{...{style_str}}}\n"
            f'        className="{anim_class}"\n'
            f"        {event_attrs}\n"
            f"        {aria_attrs}\n"
            f"      />\n"
        )

    @staticmethod
    def _generate_responsive_css() -> str:
        return (
            "/* Responsive containers */\n"
            ".container { width: 100%; margin-left: auto; margin-right: auto; }\n"
            "@media (min-width: 640px) { .container { max-width: 640px; } }\n"
            "@media (min-width: 768px) { .container { max-width: 768px; } }\n"
            "@media (min-width: 1024px) { .container { max-width: 1024px; } }\n"
            "@media (min-width: 1280px) { .container { max-width: 1280px; } }\n"
            "\n"
            "/* Responsive grid */\n"
            ".grid { display: grid; gap: 16px; }\n"
            ".grid-cols-1 { grid-template-columns: repeat(1, 1fr); }\n"
            ".grid-cols-2 { grid-template-columns: repeat(2, 1fr); }\n"
            ".grid-cols-3 { grid-template-columns: repeat(3, 1fr); }\n"
            ".grid-cols-4 { grid-template-columns: repeat(4, 1fr); }\n"
            "@media (min-width: 640px) { .sm\\:grid-cols-2 { grid-template-columns: repeat(2, 1fr); } }\n"
            "@media (min-width: 768px) { .md\\:grid-cols-3 { grid-template-columns: repeat(3, 1fr); } }\n"
            "@media (min-width: 1024px) { .lg\\:grid-cols-4 { grid-template-columns: repeat(4, 1fr); } }\n"
        )

    @staticmethod
    def _generate_animation_css() -> str:
        return (
            "/* UI Animations */\n"
            "@keyframes fadeIn {\n"
            "  from { opacity: 0; transform: translateY(10px); }\n"
            "  to { opacity: 1; transform: translateY(0); }\n"
            "}\n\n"
            "@keyframes slideUp {\n"
            "  from { opacity: 0; transform: translateY(20px); }\n"
            "  to { opacity: 1; transform: translateY(0); }\n"
            "}\n\n"
            "@keyframes slideIn {\n"
            "  from { opacity: 0; transform: translateX(-20px); }\n"
            "  to { opacity: 1; transform: translateX(0); }\n"
            "}\n\n"
            ".animate-fadeIn { animation: fadeIn 0.3s ease-in-out; }\n"
            ".animate-slideUp { animation: slideUp 0.3s ease-in-out; }\n"
            ".animate-slideIn { animation: slideIn 0.3s ease-in-out; }\n"
        )
