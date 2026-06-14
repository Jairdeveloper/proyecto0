"""Tests for DockerGenerator with IR nodes."""

from pathlib import Path

from agentic_pipeline.generators.base_generator import GeneratorFactory
from agentic_pipeline.generators.docker_generator import DockerGenerator
from agentic_pipeline.nodes.ir_nodes import IRInfra, IRProject


class TestDockerGenerator:
    def test_generate_database(self, tmp_path: Path):
        gen = DockerGenerator()
        infra = IRInfra("postgres", infra_type="database")
        created = gen.generate(infra, tmp_path)
        assert len(created) >= 1
        content = created[0].read_text()
        assert "postgres:15" in content
        assert "POSTGRES_DB: postgres" in content
        assert "pgdata" in content

    def test_generate_service(self, tmp_path: Path):
        gen = DockerGenerator()
        infra = IRInfra("webapp", infra_type="service")
        created = gen.generate(infra, tmp_path)
        assert len(created) == 2  # Dockerfile + docker-compose.yml
        names = {p.name for p in created}
        assert names == {"Dockerfile", "docker-compose.yml"}

    def test_dockerfile_content(self, tmp_path: Path):
        gen = DockerGenerator()
        infra = IRInfra("api", infra_type="service")
        created = gen.generate(infra, tmp_path)
        df = [p for p in created if p.name == "Dockerfile"][0]
        content = df.read_text()
        assert "FROM node:20-alpine" in content
        assert "WORKDIR /app" in content
        assert 'CMD ["node", "dist/main"]' in content

    def test_generate_project(self, tmp_path: Path):
        gen = DockerGenerator()
        proj = IRProject("infra")
        proj.add(IRInfra("postgres", infra_type="database"))
        proj.add(IRInfra("redis", infra_type="database"))
        created = gen.generate(proj, tmp_path)
        assert len(created) >= 2

    def test_factory_registered(self):
        gen = GeneratorFactory.get_generator("docker")
        assert isinstance(gen, DockerGenerator)
