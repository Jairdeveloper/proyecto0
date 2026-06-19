"""UIComponentBuilder — Builder pattern for constructing UI components in 5 steps."""

from __future__ import annotations

from typing import Any

from agentic_pipeline.generators.design_tokens import DesignTokens


class UIComponentBuilder:
    def __init__(self, component_type: str) -> None:
        self.component: dict[str, Any] = {
            "type": component_type,
            "props": {},
            "children": [],
        }

    def build_structure(
        self,
        name: str,
        props: dict[str, Any] | None = None,
    ) -> UIComponentBuilder:
        self.component["name"] = name
        self.component["props"] = props or {}
        return self

    def apply_styles(
        self,
        styles: dict[str, Any] | None = None,
    ) -> UIComponentBuilder:
        self.component["styles"] = styles or {}
        if "className" not in self.component.get("props", {}):
            self.component.setdefault("props", {})["className"] = ""
        return self

    def add_behavior(
        self,
        events: dict[str, str] | None = None,
    ) -> UIComponentBuilder:
        self.component["events"] = events or {}
        return self

    def add_accessibility(
        self,
        aria: dict[str, str] | None = None,
    ) -> UIComponentBuilder:
        self.component["aria"] = aria or {
            "label": self.component.get("name", ""),
        }
        return self

    def add_animations(
        self,
        animations: dict[str, str] | None = None,
    ) -> UIComponentBuilder:
        self.component["animations"] = animations or {
            "enter": "fadeIn",
            "duration": "0.3s",
        }
        return self

    def build(self) -> dict[str, Any]:
        return self.component


# ============================================================================
# Pre-built component factories
# ============================================================================


class ComponentFactory:
    @staticmethod
    def form(
        name: str = "Form",
        fields: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        fields = fields or [
            {"name": "email", "type": "email", "label": "Email"},
            {"name": "password", "type": "password", "label": "Password"},
        ]
        children: list[dict[str, Any]] = []
        for field in fields:
            input_builder = (
                UIComponentBuilder("input")
                .build_structure(
                    field["name"],
                    {
                        "type": field["type"],
                        "placeholder": f"Enter {field['label'].lower()}",
                    },
                )
                .apply_styles({"width": "100%", "padding": DesignTokens.SPACING["sm"]})
                .add_accessibility({"label": field["label"]})
                .add_animations({"enter": "fadeIn", "duration": "0.2s"})
            )
            children.append(input_builder.build())

        submit = (
            UIComponentBuilder("button")
            .build_structure("submit", {"type": "submit"})
            .apply_styles(
                {
                    "backgroundColor": DesignTokens.COLORS["primary"],
                    "color": "#FFFFFF",
                    "padding": f"{DesignTokens.SPACING['sm']} {DesignTokens.SPACING['md']}",
                    "border": "none",
                    "borderRadius": DesignTokens.BORDER_RADIUS,
                }
            )
            .add_behavior({"onClick": "handleSubmit"})
            .add_accessibility({"label": "Submit form"})
            .add_animations({"enter": "slideUp", "duration": "0.3s"})
            .build()
        )
        children.append(submit)

        form = (
            UIComponentBuilder("form")
            .build_structure(name, {"onSubmit": "handleSubmit"})
            .apply_styles(
                {
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": DesignTokens.SPACING["md"],
                    "padding": DesignTokens.SPACING["lg"],
                    "backgroundColor": DesignTokens.COLORS["surface"],
                    "borderRadius": DesignTokens.BORDER_RADIUS,
                }
            )
            .add_behavior({"onSubmit": "handleSubmit"})
            .add_accessibility({"label": name, "role": "form"})
            .add_animations({"enter": "fadeIn", "duration": "0.4s"})
            .build()
        )
        form["children"] = children
        return form

    @staticmethod
    def table(
        name: str = "DataTable",
        columns: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        columns = columns or [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "status", "label": "Status"},
        ]
        header_cells: list[dict[str, Any]] = []
        for col in columns:
            th = (
                UIComponentBuilder("th")
                .build_structure(col["key"], {"sortable": True})
                .apply_styles(
                    {
                        "padding": DesignTokens.SPACING["sm"],
                        "textAlign": "left",
                        "cursor": "pointer",
                        "color": DesignTokens.COLORS["text"],
                    }
                )
                .add_behavior({"onClick": f"sortBy('{col['key']}')"})
                .add_accessibility(
                    {
                        "label": f"Sort by {col['label']}",
                        "role": "columnheader",
                    }
                )
                .build()
            )
            header_cells.append(th)

        header = (
            UIComponentBuilder("thead")
            .build_structure(f"{name}Header")
            .apply_styles({"backgroundColor": DesignTokens.COLORS["surface"]})
            .build()
        )
        header["children"] = header_cells

        table = (
            UIComponentBuilder("table")
            .build_structure(name)
            .apply_styles(
                {
                    "width": "100%",
                    "borderCollapse": "collapse",
                    "fontFamily": DesignTokens.FONTS["sans"],
                }
            )
            .add_accessibility(
                {
                    "label": name,
                    "role": "table",
                }
            )
            .add_animations({"enter": "fadeIn", "duration": "0.3s"})
            .build()
        )
        table["children"] = [header]
        return table
