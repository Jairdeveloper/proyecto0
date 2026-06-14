"""Tests for ResponsiveEngine."""

from agentic_pipeline.generators.responsive_engine import ResponsiveEngine


class TestResponsiveEngine:
    def test_responsive_class_with_all_breakpoints(self):
        result = ResponsiveEngine.responsive_class(
            "text-base",
            sm="text-sm",
            md="text-md",
            lg="text-lg",
            xl="text-xl",
        )
        assert "text-base" in result
        assert "sm:text-sm" in result
        assert "md:text-md" in result
        assert "lg:text-lg" in result
        assert "xl:text-xl" in result

    def test_responsive_class_base_only(self):
        result = ResponsiveEngine.responsive_class("p-4")
        assert result == "p-4"

    def test_grid_columns_default(self):
        result = ResponsiveEngine.grid_columns({"default": 1})
        assert "grid-cols-1" in result

    def test_grid_columns_responsive(self):
        result = ResponsiveEngine.grid_columns(
            {
                "default": 1,
                "md": 2,
                "lg": 3,
            }
        )
        assert "grid-cols-1" in result
        assert "md:grid-cols-2" in result
        assert "lg:grid-cols-3" in result

    def test_hide_at(self):
        result = ResponsiveEngine.hide_at("md")
        assert "hidden" in result
        assert "md:block" in result

    def test_show_at(self):
        result = ResponsiveEngine.show_at("md")
        assert "block" in result
        assert "md:hidden" in result

    def test_container(self):
        result = ResponsiveEngine.container()
        assert "w-full" in result
        assert "mx-auto" in result
        assert "max-w-7xl" in result

    def test_responsive_font(self):
        result = ResponsiveEngine.responsive_font(
            {
                "default": "base",
                "lg": "lg",
            }
        )
        assert "text-base" in result
        assert "lg:text-lg" in result
