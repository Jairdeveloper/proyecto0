"""Tests for UIComponentBuilder and ComponentFactory."""

from agentic_pipeline.generators.design_tokens import DesignTokens
from agentic_pipeline.generators.ui_component_builder import (
    ComponentFactory,
    UIComponentBuilder,
)


class TestUIComponentBuilder:
    def test_build_structure(self):
        builder = UIComponentBuilder("div")
        comp = builder.build_structure("Container", {"id": "main"}).build()
        assert comp["type"] == "div"
        assert comp["name"] == "Container"
        assert comp["props"]["id"] == "main"

    def test_apply_styles(self):
        builder = UIComponentBuilder("button")
        comp = builder.build_structure("Submit").apply_styles({"color": "red"}).build()
        assert comp["styles"]["color"] == "red"

    def test_add_behavior(self):
        builder = UIComponentBuilder("form")
        comp = builder.build_structure("Login").add_behavior({"onSubmit": "handleLogin"}).build()
        assert comp["events"]["onSubmit"] == "handleLogin"

    def test_add_accessibility(self):
        builder = UIComponentBuilder("input")
        comp = (
            builder.build_structure("email").add_accessibility({"label": "Email address"}).build()
        )
        assert comp["aria"]["label"] == "Email address"

    def test_add_animations(self):
        builder = UIComponentBuilder("div")
        comp = (
            builder.build_structure("Card")
            .add_animations({"enter": "slideUp", "duration": "0.5s"})
            .build()
        )
        assert comp["animations"]["enter"] == "slideUp"

    def test_build_returns_dict(self):
        builder = UIComponentBuilder("section")
        comp = builder.build_structure("Hero").build()
        assert isinstance(comp, dict)
        assert comp["type"] == "section"

    def test_fluent_interface(self):
        builder = UIComponentBuilder("form")
        comp = (
            builder.build_structure("Signup", {"method": "POST"})
            .apply_styles({"padding": "16px"})
            .add_behavior({"onSubmit": "handleSignup"})
            .add_accessibility({"label": "Signup form", "role": "form"})
            .add_animations({"enter": "fadeIn", "duration": "0.3s"})
            .build()
        )
        assert comp["name"] == "Signup"
        assert comp["type"] == "form"
        assert comp["props"]["method"] == "POST"
        assert comp["styles"]["padding"] == "16px"
        assert comp["events"]["onSubmit"] == "handleSignup"
        assert comp["aria"]["label"] == "Signup form"
        assert comp["animations"]["enter"] == "fadeIn"


class TestComponentFactory:
    def test_form_structure(self):
        form = ComponentFactory.form("ContactForm")
        assert form["type"] == "form"
        assert form["name"] == "ContactForm"
        assert len(form["children"]) >= 2

    def test_form_has_inputs(self):
        form = ComponentFactory.form()
        inputs = [c for c in form["children"] if c["type"] == "input"]
        assert len(inputs) >= 1

    def test_form_has_submit_button(self):
        form = ComponentFactory.form()
        buttons = [c for c in form["children"] if c["type"] == "button"]
        assert len(buttons) == 1

    def test_form_applies_tokens(self):
        form = ComponentFactory.form()
        assert form["styles"]["backgroundColor"] == DesignTokens.COLORS["surface"]
        assert form["styles"]["borderRadius"] == DesignTokens.BORDER_RADIUS

    def test_form_inputs_have_accessibility(self):
        form = ComponentFactory.form()
        for child in form["children"]:
            if child["type"] == "input":
                assert "aria" in child
                assert "label" in child["aria"]

    def test_form_has_animations(self):
        form = ComponentFactory.form()
        assert "animations" in form

    def test_table_structure(self):
        table = ComponentFactory.table("UsersTable")
        assert table["type"] == "table"
        assert table["name"] == "UsersTable"

    def test_table_has_header(self):
        table = ComponentFactory.table()
        headers = [c for c in table.get("children", []) if c["type"] == "thead"]
        assert len(headers) >= 1

    def test_table_header_has_cells(self):
        table = ComponentFactory.table()
        for child in table.get("children", []):
            if child["type"] == "thead":
                cells = [c for c in child.get("children", []) if c["type"] == "th"]
                assert len(cells) >= 1

    def test_table_cells_have_sort_behavior(self):
        table = ComponentFactory.table()
        for child in table.get("children", []):
            if child["type"] == "thead":
                for cell in child.get("children", []):
                    if cell["type"] == "th":
                        assert "events" in cell
                        assert "onClick" in cell["events"]

    def test_table_responsive(self):
        table = ComponentFactory.table()
        assert table["styles"]["width"] == "100%"
        assert table["styles"]["borderCollapse"] == "collapse"

    def test_custom_fields(self):
        fields = [
            {"name": "username", "type": "text", "label": "Username"},
            {"name": "age", "type": "number", "label": "Age"},
        ]
        form = ComponentFactory.form("CustomForm", fields)
        inputs = [c for c in form["children"] if c["type"] == "input"]
        assert len(inputs) == 2
        assert inputs[0]["name"] == "username"
        assert inputs[1]["name"] == "age"
