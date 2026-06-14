"""ResponsiveEngine, AccessibilityInjector, AnimationInjector — UI utilities."""

from __future__ import annotations

from typing import Any

from .design_tokens import DesignTokens


# ============================================================================
# ResponsiveEngine
# ============================================================================


class ResponsiveEngine:
    """Mobile-first responsive class generator."""

    BREAKPOINTS = DesignTokens.BREAKPOINTS

    @staticmethod
    def responsive_class(
        base: str,
        sm: str | None = None,
        md: str | None = None,
        lg: str | None = None,
        xl: str | None = None,
    ) -> str:
        classes = [base]
        if sm:
            classes.append(f"sm:{sm}")
        if md:
            classes.append(f"md:{md}")
        if lg:
            classes.append(f"lg:{lg}")
        if xl:
            classes.append(f"xl:{xl}")
        return " ".join(classes)

    @staticmethod
    def grid_columns(cols: dict[str, int]) -> str:
        classes: list[str] = []
        for bp, num in cols.items():
            if bp == "default":
                classes.append(f"grid-cols-{num}")
            else:
                classes.append(f"{bp}:grid-cols-{num}")
        return " ".join(classes)

    @staticmethod
    def hide_at(breakpoint: str) -> str:
        return f"hidden {breakpoint}:block"

    @staticmethod
    def show_at(breakpoint: str) -> str:
        return f"block {breakpoint}:hidden"

    @staticmethod
    def container() -> str:
        return "w-full mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl"

    @staticmethod
    def responsive_font(size: dict[str, str]) -> str:
        classes: list[str] = []
        for bp, val in size.items():
            if bp == "default":
                classes.append(f"text-{val}")
            else:
                classes.append(f"{bp}:text-{val}")
        return " ".join(classes)


# ============================================================================
# AccessibilityInjector
# ============================================================================


class AccessibilityInjector:
    @staticmethod
    def inject(component: dict[str, Any]) -> dict[str, Any]:
        if "aria" not in component:
            component["aria"] = {"label": component.get("name", "")}
        aria = component["aria"]
        if "role" not in aria:
            ctype = component.get("type", "div")
            aria["role"] = AccessibilityInjector._default_role(ctype)
        return component

    @staticmethod
    def _default_role(component_type: str) -> str:
        roles = {
            "button": "button",
            "form": "form",
            "input": "textbox",
            "table": "table",
            "nav": "navigation",
            "header": "banner",
            "footer": "contentinfo",
            "main": "main",
            "aside": "complementary",
            "section": "region",
        }
        return roles.get(component_type, "presentation")

    @staticmethod
    def label(component: dict[str, Any], text: str) -> dict[str, Any]:
        component.setdefault("aria", {})["label"] = text
        return component


# ============================================================================
# AnimationInjector
# ============================================================================


class AnimationInjector:
    DEFAULT_ANIMATIONS: dict[str, str] = {
        "enter": "fadeIn",
        "duration": "0.3s",
        "timing": "ease-in-out",
    }

    @staticmethod
    def inject(
        component: dict[str, Any],
        animations: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        component["animations"] = animations or AnimationInjector.DEFAULT_ANIMATIONS
        return component

    @staticmethod
    def to_css(animations: dict[str, str]) -> str:
        anim_name = animations.get("enter", "fadeIn")
        duration = animations.get("duration", "0.3s")
        timing = animations.get("timing", "ease-in-out")
        return (
            f"animation: {anim_name} {duration} {timing};\n"
            f"@keyframes {anim_name} {{\n"
            f"  from {{ opacity: 0; transform: translateY(10px); }}\n"
            f"  to {{ opacity: 1; transform: translateY(0); }}\n"
            f"}}"
        )

    @staticmethod
    def to_tailwind(animations: dict[str, str]) -> str:
        anim_name = animations.get("enter", "fadeIn")
        duration = animations.get("duration", "0.3s")
        dur_map = {
            "0.2s": "duration-200",
            "0.3s": "duration-300",
            "0.4s": "duration-400",
            "0.5s": "duration-500",
        }
        return f"animate-{anim_name} {dur_map.get(duration, 'duration-300')}"
