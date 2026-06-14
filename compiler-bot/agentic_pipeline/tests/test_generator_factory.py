"""Tests for GeneratorFactory."""

from pathlib import Path

from agentic_pipeline.generators.base_generator import BaseGenerator, GeneratorFactory
from agentic_pipeline.generators.docker_generator import DockerGenerator
from agentic_pipeline.generators.nestjs_generator import NestJSGenerator
from agentic_pipeline.generators.nextjs_generator import NextJSGenerator
from agentic_pipeline.generators.prisma_generator import PrismaGenerator
from agentic_pipeline.generators.react_generator import ReactGenerator
from agentic_pipeline.generators.tailwind_generator import TailwindGenerator


class TestGeneratorFactory:
    def test_get_react(self):
        gen = GeneratorFactory.get_generator("react")
        assert isinstance(gen, ReactGenerator)

    def test_get_nextjs(self):
        gen = GeneratorFactory.get_generator("nextjs")
        assert isinstance(gen, NextJSGenerator)

    def test_get_tailwind(self):
        gen = GeneratorFactory.get_generator("tailwind")
        assert isinstance(gen, TailwindGenerator)

    def test_get_prisma(self):
        gen = GeneratorFactory.get_generator("prisma")
        assert isinstance(gen, PrismaGenerator)

    def test_get_nestjs(self):
        gen = GeneratorFactory.get_generator("nestjs")
        assert isinstance(gen, NestJSGenerator)

    def test_get_docker(self):
        gen = GeneratorFactory.get_generator("docker")
        assert isinstance(gen, DockerGenerator)

    def test_get_unknown_raises(self):
        try:
            GeneratorFactory.get_generator("nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_all_generators_produce_files(self, tmp_path: Path):
        for target in ("react", "nextjs", "tailwind", "prisma", "nestjs", "docker"):
            gen = GeneratorFactory.get_generator(target)
            assert isinstance(gen, BaseGenerator)
            out = tmp_path / target
            out.mkdir(exist_ok=True)
            result = gen.generate(None, out)
            assert isinstance(result, list)
