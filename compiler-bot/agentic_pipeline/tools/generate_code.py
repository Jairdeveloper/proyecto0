"""Tool: generate_code — Envuelve los 6 generadores existentes."""

from __future__ import annotations

from pathlib import Path

from agentic_pipeline.generators.base_generator import GeneratorFactory
from agentic_pipeline.nodes.ir_nodes import IRAPI, IRConfig, IREntity, IRInfra, IRPage, IRProject
from agentic_pipeline.tool_registry import Parameter, Tool, ToolResult


class GenerateCodeTool(Tool):
    name = "generate_code"
    description = (
        "Genera codigo scaffolding usando los generadores disponibles "
        "(nestjs, prisma, react, nextjs, tailwind, docker)"
    )
    parameters = [
        Parameter(
            "target", "string", "Target de generacion (nestjs|prisma|react|nextjs|tailwind|docker)"
        ),
        Parameter("name", "string", "Nombre del modulo/entidad/componente"),
        Parameter("output_dir", "string", "Directorio de salida", required=False),
    ]

    async def execute(self, params: dict) -> ToolResult:
        target = params["target"]
        name = params["name"]
        output_dir = Path(params.get("output_dir", "modules"))
        try:
            gen = GeneratorFactory.get_generator(target)
        except ValueError:
            return ToolResult(
                success=False,
                error=f"Generador no encontrado: {target}. "
                f"Disponibles: nestjs, prisma, react, nextjs, tailwind, docker",
            )
        target_dir = output_dir / name.lower()
        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            ir_node = self._build_ir_node(target, name)
            created = gen.generate(ir_node, target_dir)
            return ToolResult(
                success=True,
                data={
                    "generated_files": [str(p) for p in created],
                    "target": target,
                    "name": name,
                    "output_dir": str(target_dir),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Error en generacion: {e}")

    @staticmethod
    def _build_ir_node(target: str, name: str) -> object:
        if target == "prisma":
            return IREntity(name=name, attributes=[{"name": "id", "type": "int"}])
        if target == "nestjs":
            return IRAPI(name=name, module=name)
        if target == "react":
            return IRPage(name=name, components=[])
        if target == "nextjs":
            return IRPage(name=name, components=[])
        if target == "infra" or target == "docker":
            return IRInfra(name=name, type="service")
        if target == "tailwind":
            return IRConfig(name=name, settings={})
        project = IRProject(name=name)
        project.add_child(GenerateCodeTool._build_ir_node("nestjs", name))
        return project
