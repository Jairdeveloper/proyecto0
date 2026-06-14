from __future__ import annotations

from pathlib import Path

from .base_generator import BaseGenerator, GeneratorFactory


class PrismaGenerator(BaseGenerator):
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

        if type_name in ("IRProject",):
            schema_lines = [
                "generator client {",
                '  provider = "prisma-client-js"',
                "}",
                "",
                "datasource db {",
                '  provider = "postgresql"',
                '  url      = env("DATABASE_URL")',
                "}",
                "",
            ]
            for child in children:
                model_block = self._render_model(child)
                if model_block:
                    schema_lines.append(model_block)
                    schema_lines.append("")

            filepath = output_dir / "schema.prisma"
            filepath.write_text("\n".join(schema_lines))
            created.append(filepath)
            return

        if type_name == "IREntity":
            ename = self._get_name(node)
            filepath = output_dir / f"{ename.lower()}.prisma"
            filepath.write_text(self._render_model(node))
            created.append(filepath)

    @staticmethod
    def _render_model(entity: object) -> str:
        name = getattr(entity, "name", "Unknown")
        attrs = getattr(entity, "attributes", [])

        if not attrs:
            return f"model {name} {{\n  id Int @id @default(autoincrement())\n}}"

        fields = ["  id Int @id @default(autoincrement())"]
        for attr in attrs:
            attr_name = attr.get("name", "field")
            attr_type = PrismaGenerator._map_type(attr.get("type", "String"))
            optional = attr.get("optional", False)
            is_unique = attr.get("unique", False)
            is_id = attr.get("id", False)

            field_def = f"  {attr_name} {attr_type}"
            if optional:
                field_def += "?"
            if is_id:
                field_def += " @id"
            if is_unique:
                field_def += " @unique"
            fields.append(field_def)

        fields.append("  createdAt DateTime @default(now())")
        fields.append("  updatedAt DateTime @updatedAt")

        return f"model {name} {{\n" + "\n".join(fields) + "\n}}"

    @staticmethod
    def _map_type(py_type: str) -> str:
        mapping = {
            "str": "String",
            "int": "Int",
            "float": "Float",
            "bool": "Boolean",
            "datetime": "DateTime",
            "json": "Json",
            "String": "String",
            "Int": "Int",
            "Float": "Float",
            "Boolean": "Boolean",
            "DateTime": "DateTime",
        }
        return mapping.get(py_type, "String")

    @staticmethod
    def _get_name(node: object) -> str:
        return getattr(node, "name", "Unknown")


GeneratorFactory.register("prisma", PrismaGenerator)
