"""Tests for NestJSGenerator with IR nodes."""

from pathlib import Path

from agentic_pipeline.generators.base_generator import GeneratorFactory
from agentic_pipeline.generators.nestjs_generator import NestJSGenerator
from agentic_pipeline.nodes.ir_nodes import IRAPI, IREntity, IRProject


class TestNestJSGenerator:
    def test_generate_controller(self, tmp_path: Path):
        gen = NestJSGenerator()
        api = IRAPI("Auth", methods=["GET", "POST"])
        created = gen.generate(api, tmp_path)
        names = {p.name for p in created}
        assert names == {"auth.controller.ts", "auth.service.ts", "auth.module.ts"}

    def test_controller_content(self, tmp_path: Path):
        gen = NestJSGenerator()
        api = IRAPI("User", methods=["GET"])
        created = gen.generate(api, tmp_path)
        controller = [p for p in created if "controller" in p.name][0]
        content = controller.read_text()
        assert "@Controller('user')" in content
        assert "class UserController" in content
        assert "UserService" in content

    def test_service_content(self, tmp_path: Path):
        gen = NestJSGenerator()
        api = IRAPI("Payment", methods=["POST"])
        created = gen.generate(api, tmp_path)
        service = [p for p in created if "service" in p.name][0]
        content = service.read_text()
        assert "@Injectable()" in content
        assert "class PaymentService" in content

    def test_module_content(self, tmp_path: Path):
        gen = NestJSGenerator()
        api = IRAPI("Order", methods=["GET"])
        created = gen.generate(api, tmp_path)
        module = [p for p in created if "module" in p.name][0]
        content = module.read_text()
        assert "@Module({" in content
        assert "OrderController" in content
        assert "OrderService" in content

    def test_generate_entity(self, tmp_path: Path):
        gen = NestJSGenerator()
        entity = IREntity(
            "Product",
            attributes=[
                {"name": "name", "type": "string"},
                {"name": "price", "type": "number"},
            ],
        )
        created = gen.generate(entity, tmp_path)
        assert len(created) == 1
        content = created[0].read_text()
        assert "class Product" in content
        assert "name: string;" in content
        assert "price: number;" in content

    def test_generate_project_with_apis(self, tmp_path: Path):
        gen = NestJSGenerator()
        proj = IRProject("api")
        proj.add(IRAPI("Auth"))
        proj.add(IRAPI("User"))
        created = gen.generate(proj, tmp_path)
        assert len(created) == 6  # 3 files per API

    def test_factory_registered(self):
        gen = GeneratorFactory.get_generator("nestjs")
        assert isinstance(gen, NestJSGenerator)
