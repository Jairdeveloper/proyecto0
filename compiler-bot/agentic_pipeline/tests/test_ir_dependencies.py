"""Tests for IR Serializer (Bridge pattern) and IRGenerator stage."""

import pytest

from agentic_pipeline.nodes.ir_generator import IRGenerator
from agentic_pipeline.nodes.ir_nodes import (
    IRComponent,
    IREntity,
    IRPage,
    IRProject,
)
from agentic_pipeline.nodes.ir_serializer import (
    DOTSerializer,
    JSONSerializer,
    YAMLSerializer,
    get_serializer,
)
from agentic_pipeline.state_models import Stage, StageContext


class TestJSONSerializer:
    def test_serialize_project(self):
        ser = JSONSerializer()
        p = IRProject("test")
        p.add(IRPage("home"))
        output = ser.serialize(p)
        assert '"name": "test"' in output
        assert '"children"' in output

    def test_serialize_with_component(self):
        ser = JSONSerializer()
        page = IRPage("login")
        page.add(IRComponent("Form", "formulario"))
        output = ser.serialize(page)
        assert '"name": "login"' in output
        assert '"component_type": "formulario"' in output

    def test_serialize_entity(self):
        ser = JSONSerializer()
        e = IREntity("User", [{"name": "id", "type": "int"}])
        output = ser.serialize(e)
        assert '"attributes"' in output

    def test_mime_type(self):
        assert JSONSerializer().mime_type() == "application/json"


class TestYAMLSerializer:
    def test_serialize(self):
        ser = YAMLSerializer()
        p = IRProject("test")
        p.add(IRPage("home"))
        output = ser.serialize(p)
        assert "test" in output

    def test_mime_type(self):
        assert YAMLSerializer().mime_type() == "text/yaml"


class TestDOTSerializer:
    def test_serialize(self):
        ser = DOTSerializer()
        p = IRProject("root")
        page = IRPage("home")
        p.add(page)
        output = ser.serialize(p)
        assert "digraph IR" in output
        assert "root" in output

    def test_mime_type(self):
        assert DOTSerializer().mime_type() == "text/vnd.graphviz"


class TestGetSerializer:
    def test_default_json(self):
        assert isinstance(get_serializer(), JSONSerializer)

    def test_json(self):
        assert isinstance(get_serializer("json"), JSONSerializer)

    def test_yaml(self):
        assert isinstance(get_serializer("yaml"), YAMLSerializer)

    def test_dot(self):
        assert isinstance(get_serializer("dot"), DOTSerializer)


class TestIRGenerator:
    @pytest.fixture
    def generator(self):
        ctx = StageContext(stage=Stage.IR_GENERATOR, input_data="")
        return IRGenerator(ctx)

    def test_receive_mission_from_ast(self, generator):
        generator.receive_mission({"ast": {"node_type": "project", "children": []}})
        assert generator._input_ir is not None

    def test_receive_mission_fallback(self, generator):
        generator.receive_mission("invalid")
        assert generator._input_ir == {"node_type": "project", "children": []}

    def test_analyze(self, generator):
        generator.receive_mission({"node_type": "project", "children": []})
        result = generator.analyze()
        assert result.complexity_score == 0.35

    def test_act_returns_ir(self, generator):
        generator.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {
                            "node_type": "page",
                            "name": "login",
                            "children": [
                                {
                                    "node_type": "component",
                                    "name": "form",
                                    "component_type": "formulario",
                                },
                            ],
                        },
                    ],
                }
            }
        )
        plan = generator.reflect_and_plan(generator.analyze())
        output = generator.act(plan)
        assert output.success is True
        assert "ir_json" in output.output_data
        assert "ir_yaml" in output.output_data
        assert "ir_dot" in output.output_data
        assert "validation_errors" in output.output_data
        assert "dependency_order" in output.output_data

    def test_act_returns_validation_errors(self, generator):
        generator.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {"node_type": "page", "name": "empty", "children": []},
                    ],
                }
            }
        )
        plan = generator.reflect_and_plan(generator.analyze())
        output = generator.act(plan)
        assert output.success is False
        assert len(output.output_data["validation_errors"]) > 0

    def test_execute_full_flow(self, generator):
        result = generator.execute(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {
                            "node_type": "page",
                            "name": "home",
                            "children": [
                                {
                                    "node_type": "component",
                                    "name": "nav",
                                    "component_type": "navbar",
                                },
                            ],
                        },
                        {
                            "node_type": "entity",
                            "name": "User",
                            "attributes": [{"name": "email", "type": "string"}],
                        },
                    ],
                }
            }
        )
        assert result.stage == Stage.IR_GENERATOR
        assert result.success is True

    def test_learn_and_improve(self, generator):
        generator.receive_mission({"node_type": "project", "children": []})
        generator.learn_and_improve({})
        assert True

    def test_ir_json_content(self, generator):
        generator.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {
                            "node_type": "page",
                            "name": "login",
                            "children": [
                                {
                                    "node_type": "component",
                                    "name": "form",
                                    "component_type": "formulario",
                                },
                            ],
                        },
                    ],
                }
            }
        )
        plan = generator.reflect_and_plan(generator.analyze())
        output = generator.act(plan)
        json_out = output.output_data["ir_json"]
        assert '"name": "login"' in json_out
        assert '"component_type": "formulario"' in json_out

    def test_metrics(self, generator):
        generator.receive_mission(
            {
                "ast": {
                    "node_type": "project",
                    "children": [
                        {"node_type": "page", "name": "a", "children": []},
                        {"node_type": "page", "name": "b", "children": []},
                    ],
                }
            }
        )
        plan = generator.reflect_and_plan(generator.analyze())
        output = generator.act(plan)
        assert output.metrics["node_count"] == 2
