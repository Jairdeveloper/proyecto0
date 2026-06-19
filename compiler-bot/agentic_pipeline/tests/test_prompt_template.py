"""Tests for PromptTemplate, PromptRegistry, and ChainStep."""

from __future__ import annotations

from pydantic import BaseModel


class _InputSchema(BaseModel):
    name: str
    count: int


class _OutputSchema(BaseModel):
    result: str


class TestPromptTemplate:
    def test_render_replaces_variables(self):
        from agentic_pipeline.prompt_chain.prompt_template import PromptTemplate

        t = PromptTemplate(
            name="test",
            system_prompt="test",
            template="Hello {name} count={count}",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        result = t.render(name="world", count=42)
        assert result == "Hello world count=42"

    def test_render_validates_input(self):
        from agentic_pipeline.prompt_chain.prompt_template import PromptTemplate

        t = PromptTemplate(
            name="test2",
            system_prompt="test",
            template="{name}",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        try:
            t.render(count=1)  # missing 'name'
            assert False, "should have raised"
        except Exception:
            pass

    def test_render_extra_fields_ignored(self):
        from agentic_pipeline.prompt_chain.prompt_template import PromptTemplate

        t = PromptTemplate(
            name="test3",
            system_prompt="test",
            template="{name}",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        result = t.render(name="x", count=1, extra="ignored")
        assert result == "x"


class TestPromptRegistry:
    def setup_method(self):
        from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry

        PromptRegistry.clear()

    def test_register_and_get(self):
        from agentic_pipeline.prompt_chain.prompt_template import (
            PromptRegistry,
            PromptTemplate,
        )

        t = PromptTemplate(
            name="greet",
            system_prompt="Say hello",
            template="Hello {name}",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        PromptRegistry.register(t)
        retrieved = PromptRegistry.get("greet")
        assert retrieved.name == "greet"
        assert retrieved.system_prompt == "Say hello"

    def test_get_unknown_raises_keyerror(self):
        from agentic_pipeline.prompt_chain.prompt_template import PromptRegistry

        try:
            PromptRegistry.get("nonexistent")
            assert False, "should have raised"
        except KeyError:
            pass

    def test_register_duplicate_raises_keyerror(self):
        from agentic_pipeline.prompt_chain.prompt_template import (
            PromptRegistry,
            PromptTemplate,
        )

        t = PromptTemplate(
            name="dup",
            system_prompt="",
            template="",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        PromptRegistry.register(t)
        try:
            PromptRegistry.register(t)
            assert False, "should have raised"
        except KeyError:
            pass

    def test_list_returns_all(self):
        from agentic_pipeline.prompt_chain.prompt_template import (
            PromptRegistry,
            PromptTemplate,
        )

        t1 = PromptTemplate(
            name="a",
            system_prompt="",
            template="",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        t2 = PromptTemplate(
            name="b",
            system_prompt="",
            template="",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        PromptRegistry.register(t1)
        PromptRegistry.register(t2)
        lst = PromptRegistry.list()
        assert len(lst) == 2
        names = {e["name"] for e in lst}
        assert names == {"a", "b"}

    def test_validate_output_valid(self):
        from agentic_pipeline.prompt_chain.prompt_template import (
            PromptRegistry,
            PromptTemplate,
        )

        t = PromptTemplate(
            name="val",
            system_prompt="",
            template="",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        PromptRegistry.register(t)
        result = PromptRegistry.validate_output("val", {"result": "ok"})
        assert isinstance(result, _OutputSchema)
        assert result.result == "ok"

    def test_validate_output_invalid(self):
        from agentic_pipeline.prompt_chain.prompt_template import (
            PromptRegistry,
            PromptTemplate,
        )

        t = PromptTemplate(
            name="val2",
            system_prompt="",
            template="",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        PromptRegistry.register(t)
        try:
            PromptRegistry.validate_output("val2", {"wrong": "field"})
            assert False, "should have raised"
        except Exception:
            pass

    def test_register_prompt_helper(self):
        from agentic_pipeline.prompt_chain.prompt_template import (
            PromptRegistry,
            PromptTemplate,
            register_prompt,
        )

        t = PromptTemplate(
            name="helper",
            system_prompt="",
            template="",
            input_schema=_InputSchema,
            output_schema=_OutputSchema,
        )
        result = register_prompt(t)
        assert result is t
        assert PromptRegistry.get("helper") is t


class TestChainStep:
    def test_chain_step_creation(self):
        from agentic_pipeline.prompt_chain.prompt_template import ChainStep

        step = ChainStep(
            stage="preprocess",
            output={"normalized": "hello"},
            duration=0.5,
            success=True,
        )
        assert step.stage == "preprocess"
        assert step.output["normalized"] == "hello"
        assert step.duration == 0.5
        assert step.success is True
        assert step.error is None
        assert step.timestamp is not None
