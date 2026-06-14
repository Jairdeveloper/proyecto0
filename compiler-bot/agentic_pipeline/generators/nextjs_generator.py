from __future__ import annotations

from pathlib import Path

from .base_generator import BaseGenerator, GeneratorFactory


class NextJSGenerator(BaseGenerator):
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
            page_dir = output_dir / name.lower()
            page_dir.mkdir(parents=True, exist_ok=True)
            filepath = page_dir / "page.tsx"
            code = self._render_page(node)
            filepath.write_text(code)
            created.append(filepath)

        elif type_name == "IRComponent":
            comp_dir = output_dir / "components"
            comp_dir.mkdir(parents=True, exist_ok=True)
            filepath = comp_dir / f"{name.lower()}.tsx"
            code = self._render_component(node)
            filepath.write_text(code)
            created.append(filepath)

    def _render_page(self, page: object) -> str:
        name = getattr(page, "name", "Page")
        children = getattr(page, "children", [])
        comps = "\n      ".join(self._render_import(c) for c in children)
        return (
            f"import {{ {name} }} from '@/components/{name.lower()}';\n\n"
            f"export default function {name}Page() {{\n"
            f"  return (\n"
            f'    <main className="min-h-screen p-8">\n'
            f"      {comps}\n"
            f"    </main>\n"
            f"  );\n"
            f"}}\n"
        )

    @staticmethod
    def _render_import(comp: object) -> str:
        comp_name = getattr(comp, "name", "Component")
        return f"<{comp_name} />"

    def _render_component(self, comp: object) -> str:
        name = getattr(comp, "name", "Component")
        return (
            f"interface {name}Props {{\n"
            f"  children?: React.ReactNode;\n"
            f"}}\n\n"
            f"export default function {name}({{ children }}: {name}Props) {{\n"
            f"  return (\n"
            f'    <div className="my-4">\n'
            f"      {{children}}\n"
            f"    </div>\n"
            f"  );\n"
            f"}}\n"
        )


GeneratorFactory.register("nextjs", NextJSGenerator)
