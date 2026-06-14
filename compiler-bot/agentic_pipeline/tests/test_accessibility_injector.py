"""Tests for AccessibilityInjector and AnimationInjector."""

from agentic_pipeline.generators.responsive_engine import (
    AccessibilityInjector,
    AnimationInjector,
)


class TestAccessibilityInjector:
    def test_inject_adds_aria(self):
        comp = {"type": "button", "name": "Submit"}
        result = AccessibilityInjector.inject(comp)
        assert "aria" in result
        assert result["aria"]["label"] == "Submit"
        assert result["aria"]["role"] == "button"

    def test_inject_preserves_existing_aria(self):
        comp = {"type": "form", "name": "Login", "aria": {"label": "Login form"}}
        result = AccessibilityInjector.inject(comp)
        assert result["aria"]["label"] == "Login form"

    def test_default_role_mapping(self):
        assert AccessibilityInjector._default_role("button") == "button"
        assert AccessibilityInjector._default_role("form") == "form"
        assert AccessibilityInjector._default_role("input") == "textbox"
        assert AccessibilityInjector._default_role("table") == "table"
        assert AccessibilityInjector._default_role("unknown") == "presentation"

    def test_label_updates(self):
        comp = {"type": "div"}
        result = AccessibilityInjector.label(comp, "Main content")
        assert result["aria"]["label"] == "Main content"


class TestAnimationInjector:
    def test_inject_adds_default_animations(self):
        comp = {"type": "div", "name": "Card"}
        result = AnimationInjector.inject(comp)
        assert result["animations"]["enter"] == "fadeIn"
        assert result["animations"]["duration"] == "0.3s"

    def test_inject_custom_animations(self):
        comp = {"type": "div"}
        result = AnimationInjector.inject(
            comp,
            {
                "enter": "slideUp",
                "duration": "0.5s",
            },
        )
        assert result["animations"]["enter"] == "slideUp"
        assert result["animations"]["duration"] == "0.5s"

    def test_to_css(self):
        css = AnimationInjector.to_css(
            {
                "enter": "fadeIn",
                "duration": "0.3s",
                "timing": "ease-in-out",
            }
        )
        assert "animation" in css
        assert "fadeIn" in css
        assert "@keyframes" in css

    def test_to_tailwind(self):
        tw = AnimationInjector.to_tailwind({"enter": "slideUp", "duration": "0.3s"})
        assert "animate-slideUp" in tw
        assert "duration-300" in tw

    def test_to_tailwind_duration_mapping(self):
        assert "duration-200" in AnimationInjector.to_tailwind(
            {
                "enter": "fadeIn",
                "duration": "0.2s",
            }
        )
        assert "duration-400" in AnimationInjector.to_tailwind(
            {
                "enter": "fadeIn",
                "duration": "0.4s",
            }
        )
        assert "duration-500" in AnimationInjector.to_tailwind(
            {
                "enter": "fadeIn",
                "duration": "0.5s",
            }
        )
