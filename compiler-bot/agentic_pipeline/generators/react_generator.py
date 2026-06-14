from __future__ import annotations

from pathlib import Path

from .base_generator import BaseGenerator


class ReactGenerator(BaseGenerator):
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
        name = getattr(node, "name", "Unnamed")
        children = getattr(node, "children", [])

        if type_name == "IRProject":
            for child in children:
                self._generate_node(child, output_dir, created)

        elif type_name == "IRPage":
            filepath = output_dir / f"{name.lower()}.tsx"
            code = self._render_page(node)
            filepath.write_text(code)
            created.append(filepath)

        elif type_name == "IRComponent":
            filepath = output_dir / f"{name.lower()}.tsx"
            code = self._render_component(node)
            filepath.write_text(code)
            created.append(filepath)

    def _render_page(self, page: object) -> str:
        name = getattr(page, "name", "Page")
        children = getattr(page, "children", [])
        comps = "\n      ".join(self._render_component_inline(c) for c in children)
        return (
            f"import React from 'react';\n\n"
            f"const {name}: React.FC = () => {{\n"
            f"  return (\n"
            f'    <div className="p-4">\n'
            f"      {comps}\n"
            f"    </div>\n"
            f"  );\n"
            f"}};\n\n"
            f"export default {name};\n"
        )

    def _render_component_inline(self, comp: object) -> str:
        comp_name = getattr(comp, "name", "Component")
        return f"<{comp_name} />"

    def _render_component(self, comp: object) -> str:
        name = getattr(comp, "name", "Component")
        return (
            f"import React from 'react';\n\n"
            f"interface {name}Props {{\n"
            f"  className?: string;\n"
            f"}}\n\n"
            f"const {name}: React.FC<{name}Props> = ({{ className }}) => {{\n"
            f"  return (\n"
            f"    <div className={{className}}>\n"
            f"      {{/* {name.lower()} content */}}\n"
            f"    </div>\n"
            f"  );\n"
            f"}};\n\n"
            f"export default {name};\n"
        )
