from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, ir_node: object, output_dir: Path) -> list[Path]:
        """Generate files from IR node. Returns list of created paths."""


class GeneratorFactory:
    @staticmethod
    def get_generator(target: str) -> BaseGenerator:
        if target == "react":
            from .react_generator import ReactGenerator

            return ReactGenerator()
        if target == "nextjs":
            from .nextjs_generator import NextJSGenerator

            return NextJSGenerator()
        if target == "tailwind":
            from .tailwind_generator import TailwindGenerator

            return TailwindGenerator()
        if target == "prisma":
            from .prisma_generator import PrismaGenerator

            return PrismaGenerator()
        if target == "nestjs":
            from .nestjs_generator import NestJSGenerator

            return NestJSGenerator()
        if target == "docker":
            from .docker_generator import DockerGenerator

            return DockerGenerator()
        raise ValueError(f"Unknown target: {target}")
