"""Generadores — plugins opcionales que traducen IR canonico a codigo especifico por tecnologia."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseGenerator(ABC):
    """Plugin base para generadores de codigo especifico. Registra un nuevo generador en GeneratorFactory."""

    @abstractmethod
    def generate(self, ir_node: object, output_dir: Path) -> list[Path]:
        """Generate files from IR node. Returns list of created paths."""


class GeneratorFactory:
    """Factory de generadores plugin. Cada tecnologia (NestJS, Prisma, React, etc.) es un plugin intercambiable."""

    @staticmethod
    def get_generator(target: str) -> BaseGenerator:
        if target == "react":
            from agentic_pipeline.generators.react_generator import ReactGenerator

            return ReactGenerator()
        if target == "nextjs":
            from agentic_pipeline.generators.nextjs_generator import NextJSGenerator

            return NextJSGenerator()
        if target == "tailwind":
            from agentic_pipeline.generators.tailwind_generator import TailwindGenerator

            return TailwindGenerator()
        if target == "prisma":
            from agentic_pipeline.generators.prisma_generator import PrismaGenerator

            return PrismaGenerator()
        if target == "nestjs":
            from agentic_pipeline.generators.nestjs_generator import NestJSGenerator

            return NestJSGenerator()
        if target == "docker":
            from agentic_pipeline.generators.docker_generator import DockerGenerator

            return DockerGenerator()
        raise ValueError(f"Unknown target: {target}")
