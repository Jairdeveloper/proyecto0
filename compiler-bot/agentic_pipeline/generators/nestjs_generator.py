from __future__ import annotations

from pathlib import Path

from .base_generator import BaseGenerator, GeneratorFactory


class NestJSGenerator(BaseGenerator):
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

        elif type_name == "IRAPI":
            mod_dir = output_dir / name.lower()
            mod_dir.mkdir(parents=True, exist_ok=True)

            controller = mod_dir / f"{name.lower()}.controller.ts"
            controller.write_text(self._render_controller(node))
            created.append(controller)

            service = mod_dir / f"{name.lower()}.service.ts"
            service.write_text(self._render_service(node))
            created.append(service)

            module = mod_dir / f"{name.lower()}.module.ts"
            module.write_text(self._render_module(node))
            created.append(module)

        elif type_name == "IREntity":
            entity_dir = output_dir / "entities"
            entity_dir.mkdir(parents=True, exist_ok=True)
            filepath = entity_dir / f"{name.lower()}.entity.ts"
            filepath.write_text(self._render_entity(node))
            created.append(filepath)

    def _render_controller(self, api: object) -> str:
        name = getattr(api, "name", "Api")
        methods = getattr(api, "methods", ["GET"])
        route = name.lower()

        method_decorators = []
        for m in methods:
            http_method = m.lower()
            method_decorators.append(
                f"  @{http_method}()\n"
                f"  {http_method}{name}(): string {{\n"
                f'    return "{name} {m} endpoint";\n'
                f"  }}\n"
            )

        return (
            f"import {{ Controller, Get, Post, Put, Delete }} from '@nestjs/common';\n"
            f"import {{ {name}Service }} from './{route}.service';\n\n"
            f"@Controller('{route}')\n"
            f"export class {name}Controller {{\n"
            f"  constructor(private readonly {route}Service: {name}Service) {{}}\n\n"
            f"{''.join(method_decorators)}"
            f"}}\n"
        )

    def _render_service(self, api: object) -> str:
        name = getattr(api, "name", "Api")
        route = name.lower()
        return (
            f"import {{ Injectable }} from '@nestjs/common';\n\n"
            f"@Injectable()\n"
            f"export class {name}Service {{\n"
            f"  findAll(): string {{\n"
            f'    return "all {route}";\n'
            f"  }}\n"
            f"}}\n"
        )

    def _render_module(self, api: object) -> str:
        name = getattr(api, "name", "Api")
        route = name.lower()
        return (
            f"import {{ Module }} from '@nestjs/common';\n"
            f"import {{ {name}Controller }} from './{route}.controller';\n"
            f"import {{ {name}Service }} from './{route}.service';\n\n"
            f"@Module({{\n"
            f"  controllers: [{name}Controller],\n"
            f"  providers: [{name}Service],\n"
            f"}})\n"
            f"export class {name}Module {{}}\n"
        )

    def _render_entity(self, entity: object) -> str:
        name = getattr(entity, "name", "Entity")
        attrs = getattr(entity, "attributes", [])

        fields = "\n".join(
            f"  {a.get('name', 'field')}: {a.get('type', 'string')};" for a in attrs
        )
        return f"export class {name} {{\n{fields}\n}}\n"


GeneratorFactory.register("nestjs", NestJSGenerator)
