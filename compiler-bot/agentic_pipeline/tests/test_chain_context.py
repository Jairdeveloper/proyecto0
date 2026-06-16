"""Tests for ChainContext."""

from __future__ import annotations

from pydantic import BaseModel


class _TestContract(BaseModel):
    name: str
    value: int


class TestChainContext:
    def test_set_output_and_get_fields(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("stage1", {"name": "test", "value": 42})
        fields = ctx.get_fields("stage1", ["name"])
        assert fields == {"name": "test"}

    def test_get_fields_multiple(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("stage1", {"a": 1, "b": 2, "c": 3})
        fields = ctx.get_fields("stage1", ["a", "c"])
        assert fields == {"a": 1, "c": 3}

    def test_get_fields_missing_stage_raises(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        try:
            ctx.get_fields("nonexistent", ["x"])
            assert False, "should have raised"
        except KeyError:
            pass

    def test_get_fields_missing_field_raises(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("s1", {"a": 1})
        try:
            ctx.get_fields("s1", ["b"])
            assert False, "should have raised"
        except KeyError:
            pass

    def test_set_output_validates_contract(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("ok", {"name": "x", "value": 1}, contract=_TestContract)
        # Should not raise

    def test_set_output_contract_failure_raises(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        try:
            ctx.set_output("bad", {"wrong": "data"}, contract=_TestContract)
            assert False, "should have raised ValidationError"
        except Exception:
            pass

    def test_render_template(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("pre", {"normalized": "crea modulo", "domain": "backend"})
        result = ctx.render_template(
            "Texto: {normalized} | Dom: {domain}",
            "pre",
            ["normalized", "domain"],
        )
        assert result == "Texto: crea modulo | Dom: backend"

    def test_render_template_missing_field_raises(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("pre", {"normalized": "hello"})
        try:
            ctx.render_template("{missing}", "pre", ["missing"])
            assert False, "should have raised"
        except KeyError:
            pass

    def test_get_history_order(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("a", {"v": 1})
        ctx.set_output("b", {"v": 2})
        ctx.set_output("c", {"v": 3})
        history = ctx.get_history()
        assert len(history) == 3
        assert history[0].stage == "a"
        assert history[1].stage == "b"
        assert history[2].stage == "c"

    def test_get_history_limit(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("a", {"v": 1})
        ctx.set_output("b", {"v": 2})
        ctx.set_output("c", {"v": 3})
        recent = ctx.get_history(limit=2)
        assert len(recent) == 2
        assert recent[0].stage == "b"
        assert recent[1].stage == "c"

    def test_get_all_outputs(self):
        from agentic_pipeline.prompt_chain.chain_context import ChainContext

        ctx = ChainContext()
        ctx.set_output("x", {"val": 10})
        ctx.set_output("y", {"val": 20})
        outputs = ctx.get_all_outputs()
        assert outputs["x"]["val"] == 10
        assert outputs["y"]["val"] == 20
