"""Tests for ReactGenerator with IR nodes."""

from pathlib import Path

from agentic_pipeline.generators.base_generator import GeneratorFactory
from agentic_pipeline.generators.react_generator import ReactGenerator
from agentic_pipeline.nodes.ir_nodes import IRComponent, IRPage, IRProject


class TestReactGenerator:
    def test_generate_page(self, tmp_path: Path):
        gen = ReactGenerator()
        page = IRPage("Login")
        created = gen.generate(page, tmp_path)
        assert len(created) == 1
        filepath = created[0]
        assert filepath.name == "login.tsx"
        content = filepath.read_text()
        assert "const Login" in content
        assert "React.FC" in content
        assert "export default Login" in content

    def test_generate_component(self, tmp_path: Path):
        gen = ReactGenerator()
        comp = IRComponent("Button")
        created = gen.generate(comp, tmp_path)
        assert len(created) == 1
        content = created[0].read_text()
        assert "interface ButtonProps" in content
        assert "export default Button" in content

    def test_generate_page_with_children(self, tmp_path: Path):
        gen = ReactGenerator()
        page = IRPage("Dashboard")
        page.add(IRComponent("Header"))
        page.add(IRComponent("Sidebar"))
        created = gen.generate(page, tmp_path)
        assert len(created) == 1
        content = created[0].read_text()
        assert "<Header />" in content
        assert "<Sidebar />" in content

    def test_generate_project_with_pages(self, tmp_path: Path):
        gen = ReactGenerator()
        proj = IRProject("app")
        proj.add(IRPage("Home"))
        proj.add(IRPage("About"))
        created = gen.generate(proj, tmp_path)
        assert len(created) == 2
        names = {p.name for p in created}
        assert names == {"home.tsx", "about.tsx"}

    def test_factory_registered(self):
        gen = GeneratorFactory.get_generator("react")
        assert isinstance(gen, ReactGenerator)

    def test_factory_returns_new_instance(self):
        g1 = GeneratorFactory.get_generator("react")
        g2 = GeneratorFactory.get_generator("react")
        assert g1 is not g2
