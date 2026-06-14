"""Tests for IR nodes — 5 layers, validation, dependencies."""

import pytest

from agentic_pipeline.nodes.ir_nodes import (
    IRAPI,
    IRComponent,
    IRConfig,
    IREntity,
    IRInfra,
    IRNode,
    IRPage,
    IRProject,
)


class TestIRNodeABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            IRNode("abstract")  # type: ignore

    def test_add_child(self):
        p = IRProject("root")
        c = IRPage("child")
        p.add(c)
        assert len(p.children) == 1
        assert p.children[0] is c


class TestIRProject:
    def test_name(self):
        p = IRProject("myapp")
        assert p.name == "myapp"

    def test_validate_empty(self):
        p = IRProject("empty")
        assert p.validate() == []

    def test_dependencies(self):
        p = IRProject("root")
        p.add(IRPage("home"))
        p.add(IREntity("User", [{"name": "id", "type": "int"}]))
        assert len(p.dependencies()) == 0  # project aggregates

    def test_to_code_aggregates_children(self):
        p = IRProject("root")
        c = IRComponent("Test", "test")
        p.add(c)
        code = p.to_code("react")
        assert "<Test />" in code


class TestIRPage:
    def test_validate_no_components(self):
        page = IRPage("empty")
        errors = page.validate()
        assert any("no components" in e for e in errors)

    def test_validate_with_components(self):
        page = IRPage("home")
        page.add(IRComponent("Nav", "navbar"))
        assert page.validate() == []

    def test_to_code_react(self):
        page = IRPage("Login")
        page.add(IRComponent("Form", "formulario"))
        code = page.to_code("react")
        assert "function Login" in code
        assert "<Form />" in code

    def test_dependencies_includes_components(self):
        page = IRPage("login")
        page.add(IRComponent("Form", "form"))
        deps = page.dependencies()
        assert "Form" in deps


class TestIRComponent:
    def test_validate_empty_name(self):
        c = IRComponent("", "button")
        errors = c.validate()
        assert any("empty" in e for e in errors)

    def test_validate_valid(self):
        c = IRComponent("Btn", "button")
        assert c.validate() == []

    def test_to_code_react(self):
        c = IRComponent("MyButton", "button")
        assert c.to_code("react") == "<MyButton />"

    def test_dependencies_empty(self):
        c = IRComponent("X", "y")
        assert c.dependencies() == []


class TestIREntity:
    def test_validate_no_attributes(self):
        e = IREntity("Empty")
        errors = e.validate()
        assert any("no attributes" in er for er in errors)

    def test_validate_empty_name(self):
        e = IREntity("", [{"name": "id", "type": "int"}])
        errors = e.validate()
        assert any("empty" in er for er in errors)

    def test_validate_valid(self):
        e = IREntity("User", [{"name": "email", "type": "string"}])
        assert e.validate() == []

    def test_to_code_prisma(self):
        e = IREntity(
            "User",
            [
                {"name": "id", "type": "Int"},
                {"name": "email", "type": "String"},
            ],
        )
        code = e.to_code("prisma")
        assert "model User" in code
        assert "id Int" in code
        assert "email String" in code

    def test_to_code_nestjs(self):
        e = IREntity("User", [{"name": "email", "type": "string"}])
        code = e.to_code("nestjs")
        assert "entity: User" in code

    def test_dependencies_empty(self):
        e = IREntity("X")
        assert e.dependencies() == []


class TestIRAPI:
    def test_validate_empty_name(self):
        api = IRAPI("")
        errors = api.validate()
        assert any("empty" in er for er in errors)

    def test_validate_valid(self):
        api = IRAPI("Auth", ["POST", "GET"])
        assert api.validate() == []

    def test_to_code_nestjs(self):
        api = IRAPI("Auth", ["POST"])
        code = api.to_code("nestjs")
        assert "@Controller('auth')" in code
        assert "AuthController" in code

    def test_dependencies_empty(self):
        api = IRAPI("X")
        assert api.dependencies() == []


class TestIRConfig:
    def test_settings(self):
        c = IRConfig("app", {"port": 3000, "debug": True})
        assert c.settings["port"] == 3000

    def test_to_code_json(self):
        c = IRConfig("app", {"port": 3000})
        code = c.to_code("json")
        assert '"port"' in code
        assert "3000" in code

    def test_validate(self):
        c = IRConfig("app")
        assert c.validate() == []


class TestIRInfra:
    def test_validate_empty_name(self):
        infra = IRInfra("")
        errors = infra.validate()
        assert any("empty" in er for er in errors)

    def test_validate_empty_type(self):
        infra = IRInfra("db", "")
        errors = infra.validate()
        assert any("empty" in er for er in errors)

    def test_validate_valid(self):
        infra = IRInfra("postgres", "database")
        assert infra.validate() == []

    def test_to_code_docker_database(self):
        infra = IRInfra("postgres", "database")
        code = infra.to_code("docker")
        assert "postgres:" in code
        assert "image: postgres:15" in code

    def test_to_code_docker_service(self):
        infra = IRInfra("api", "service")
        code = infra.to_code("docker")
        assert "api:" in code
        assert "build: ." in code

    def test_dependencies_empty(self):
        infra = IRInfra("r", "t")
        assert infra.dependencies() == []
