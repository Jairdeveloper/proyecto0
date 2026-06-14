from __future__ import annotations

from pathlib import Path

from .base_generator import BaseGenerator, GeneratorFactory


class DockerGenerator(BaseGenerator):
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
        name = getattr(node, "name", "app")
        children = getattr(node, "children", [])

        if type_name == "IRProject":
            for child in children:
                self._generate_node(child, output_dir, created)

        elif type_name == "IRInfra":
            infra_type = getattr(node, "infra_type", "resource")
            resources = getattr(node, "resources", [])

            if infra_type == "database":
                compose = output_dir / "docker-compose.yml"
                compose.write_text(self._render_database_compose(name))
                created.append(compose)
            elif infra_type == "service":
                dockerfile = output_dir / "Dockerfile"
                dockerfile.write_text(self._render_dockerfile(name))
                created.append(dockerfile)

                compose = output_dir / "docker-compose.yml"
                compose.write_text(self._render_service_compose(name))
                created.append(compose)
            else:
                if resources:
                    compose = output_dir / "docker-compose.yml"
                    compose.write_text(self._render_multi_service(resources))
                    created.append(compose)

    @staticmethod
    def _render_database_compose(db_name: str) -> str:
        return (
            f"version: '3.8'\n\n"
            f"services:\n"
            f"  {db_name}:\n"
            f"    image: postgres:15\n"
            f"    container_name: {db_name}\n"
            f"    environment:\n"
            f"      POSTGRES_DB: {db_name}\n"
            f"      POSTGRES_USER: user\n"
            f"      POSTGRES_PASSWORD: password\n"
            f"    ports:\n"
            f"      - '5432:5432'\n"
            f"    volumes:\n"
            f"      - pgdata:/var/lib/postgresql/data\n\n"
            f"volumes:\n"
            f"  pgdata:\n"
        )

    @staticmethod
    def _render_service_compose(service_name: str) -> str:
        return (
            f"version: '3.8'\n\n"
            f"services:\n"
            f"  {service_name}:\n"
            f"    build: .\n"
            f"    container_name: {service_name}\n"
            f"    ports:\n"
            f"      - '3000:3000'\n"
            f"    environment:\n"
            f"      NODE_ENV: production\n"
        )

    @staticmethod
    def _render_dockerfile(service_name: str) -> str:
        return (
            "FROM node:20-alpine\n\n"
            "WORKDIR /app\n\n"
            "COPY package*.json ./\n"
            "RUN npm ci --only=production\n\n"
            "COPY . .\n\n"
            "EXPOSE 3000\n"
            'CMD ["node", "dist/main"]\n'
        )

    @staticmethod
    def _render_multi_service(resources: list[dict]) -> str:
        lines = ["version: '3.8'\n", "services:"]
        for res in resources:
            name = res.get("name", "service")
            image = res.get("image", "node:20-alpine")
            ports = res.get("ports", ["3000:3000"])
            port_lines = "\n".join(f'      - "{p}"' for p in ports)
            lines.append(f"  {name}:\n    image: {image}\n    ports:\n{port_lines}\n")
        return "\n".join(lines) + "\n"


GeneratorFactory.register("docker", DockerGenerator)
