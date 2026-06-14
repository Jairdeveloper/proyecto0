from __future__ import annotations

from pathlib import Path

from .base_generator import BaseGenerator, GeneratorFactory


class TailwindGenerator(BaseGenerator):
    def generate(self, ir_node: object, output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []
        self._generate_node(ir_node, output_dir, created)
        return created

    def _generate_node(
        self,
        node: object,
        output_dir: Path,
        created: list[Path],
    ) -> None:
        type_name = type(node).__name__
        children = getattr(node, "children", [])

        if type_name in ("IRProject", "IRConfig"):
            config_path = output_dir / "tailwind.config.js"
            config_path.write_text(self._render_config(node))
            created.append(config_path)

            css_path = output_dir / "globals.css"
            css_path.write_text(self._render_css())
            created.append(css_path)

            for child in children:
                self._generate_node(child, output_dir, created)

    @staticmethod
    def _render_config(config_node: object) -> str:
        settings = getattr(config_node, "settings", {})
        primary = settings.get("primary_color", "#6366F1")
        secondary = settings.get("secondary_color", "#10B981")
        font = settings.get("font_family", "'Inter', sans-serif")

        return (
            "/** @type {import('tailwindcss').Config} */\n"
            "module.exports = {\n"
            "  content: [\n"
            '    "./pages/**/*.{js,ts,jsx,tsx}",\n'
            '    "./components/**/*.{js,ts,jsx,tsx}",\n'
            "  ],\n"
            "  theme: {\n"
            "    extend: {\n"
            f"      colors: {{\n"
            f"        primary: '{primary}',\n"
            f"        secondary: '{secondary}',\n"
            f"      }},\n"
            f"      fontFamily: {{\n"
            f"        sans: [{font}],\n"
            f"      }},\n"
            "    },\n"
            "  },\n"
            "  plugins: [],\n"
            "};\n"
        )

    @staticmethod
    def _render_css() -> str:
        return "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"


GeneratorFactory.register("tailwind", TailwindGenerator)
