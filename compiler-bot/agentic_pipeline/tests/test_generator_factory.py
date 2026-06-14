"""Tests for GeneratorFactory."""

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

    def test_list_targets(self):
        targets = GeneratorFactory.list_targets()
        assert "react" in targets
        assert "nextjs" in targets
        assert "tailwind" in targets
        assert "prisma" in targets
        assert "nestjs" in targets
        assert "docker" in targets

    def test_custom_registration(self):
        class TestGen(BaseGenerator):
            def generate(self, ir_node, output_dir):
                return []

        GeneratorFactory.register("test_custom", TestGen)
        gen = GeneratorFactory.get_generator("test_custom")
        assert isinstance(gen, TestGen)
