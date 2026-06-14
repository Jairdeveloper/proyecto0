"""Tests for PrismaGenerator with IR nodes."""

from pathlib import Path

from agentic_pipeline.generators.base_generator import GeneratorFactory
from agentic_pipeline.generators.prisma_generator import PrismaGenerator
from agentic_pipeline.nodes.ir_nodes import IREntity, IRProject


class TestPrismaGenerator:
    def test_generate_entity(self, tmp_path: Path):
        gen = PrismaGenerator()
        entity = IREntity(
            "User",
            attributes=[
                {"name": "email", "type": "String"},
                {"name": "age", "type": "Int"},
            ],
        )
        created = gen.generate(entity, tmp_path)
        assert len(created) >= 1
        content = created[0].read_text()
        assert "model User" in content
        assert "email String" in content
        assert "age Int" in content

    def test_generate_project_with_entities(self, tmp_path: Path):
        gen = PrismaGenerator()
        proj = IRProject("db")
        proj.add(IREntity("User", attributes=[{"name": "email", "type": "String"}]))
        proj.add(IREntity("Post", attributes=[{"name": "title", "type": "String"}]))
        created = gen.generate(proj, tmp_path)
        assert len(created) == 1  # single schema.prisma
        content = created[0].read_text()
        assert "generator client" in content
        assert "datasource db" in content
        assert "model User" in content
        assert "model Post" in content

    def test_entity_no_attributes(self, tmp_path: Path):
        gen = PrismaGenerator()
        entity = IREntity("Empty")
        created = gen.generate(entity, tmp_path)
        content = created[0].read_text()
        assert "model Empty" in content
        assert "id Int @id" in content

    def test_entity_unique_field(self, tmp_path: Path):
        gen = PrismaGenerator()
        entity = IREntity(
            "User",
            attributes=[
                {"name": "email", "type": "String", "unique": True},
            ],
        )
        created = gen.generate(entity, tmp_path)
        content = created[0].read_text()
        assert "@unique" in content

    def test_factory_registered(self):
        gen = GeneratorFactory.get_generator("prisma")
        assert isinstance(gen, PrismaGenerator)

    def test_type_mapping(self):
        assert PrismaGenerator._map_type("str") == "String"
        assert PrismaGenerator._map_type("int") == "Int"
        assert PrismaGenerator._map_type("bool") == "Boolean"
        assert PrismaGenerator._map_type("datetime") == "DateTime"
        assert PrismaGenerator._map_type("json") == "Json"
