"""Tests for Preprocessor filters and pipeline stage."""

import pytest

from agentic_pipeline.nodes.preprocessor import (
    NormalizationFilter,
    Preprocessor,
    SegmentationFilter,
    build_filter_chain,
)
from agentic_pipeline.state_models import Stage, StageContext


# ============================================================================
# NormalizationFilter
# ============================================================================


class TestNormalizationFilter:
    def test_trim_and_lowercase(self):
        f = NormalizationFilter()
        result = f.process("  HELLO WORLD  ")
        assert result == "hello world"

    def test_collapse_whitespace(self):
        f = NormalizationFilter()
        result = f.process("hello    world\ntest")
        assert result == "hello world test"

    def test_remove_special_chars(self):
        f = NormalizationFilter()
        result = f.process("hello @#$% world!!!")
        assert "@" not in result
        assert "#" not in result
        assert "!" in result

    def test_preserve_spanish_accents(self):
        f = NormalizationFilter()
        result = f.process("canción única")
        assert "canción" == result.split()[0]
        assert "única" == result.split()[1]


# ============================================================================
# SegmentationFilter
# ============================================================================


class TestSegmentationFilter:
    def test_split_sentences(self):
        f = SegmentationFilter()
        result = f.process("Hola mundo. Como estas? Bien!")
        assert "[SEG]" in result
        assert "Hola mundo" in result
        assert "Como estas" in result
        assert "Bien" in result

    def test_single_sentence(self):
        f = SegmentationFilter()
        result = f.process("Solo una oracion")
        assert result == "Solo una oracion"


# ============================================================================
# build_filter_chain
# ============================================================================


class TestBuildFilterChain:
    def test_chain_has_two_filters(self):
        chain = build_filter_chain("web")
        names = [c.__class__.__name__ for c in chain]
        assert "NormalizationFilter" in names
        assert "SegmentationFilter" in names
        assert len(chain) == 2


# ============================================================================
# Preprocessor Stage
# ============================================================================


class TestPreprocessor:
    @pytest.fixture
    def preprocessor(self):
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
        return Preprocessor(ctx, domain="web")

    def test_receive_mission(self, preprocessor):
        preprocessor.receive_mission("Crea una pagina web")
        assert preprocessor._input_text == "Crea una pagina web"

    def test_analyze(self, preprocessor):
        preprocessor.receive_mission("test")
        result = preprocessor.analyze()
        assert result.complexity_score == 0.1
        assert result.observations[0] == "Input length: 4"

    def test_act_normalizes_text(self, preprocessor):
        preprocessor.receive_mission("  CREA UNA PAGINA CON AUTH  ")
        plan = preprocessor.reflect_and_plan(preprocessor.analyze())
        output = preprocessor.act(plan)
        data = output.output_data
        assert "normalized_text" in data
        assert "crea una pagina con auth" in data["normalized_text"].lower()

    def test_act_metrics(self, preprocessor):
        preprocessor.receive_mission("Crea una pagina")
        plan = preprocessor.reflect_and_plan(preprocessor.analyze())
        output = preprocessor.act(plan)
        assert output.metrics["filters_applied"] == 2
        assert output.metrics["input_len"] == 15

    def test_execute_full_flow(self, preprocessor):
        result = preprocessor.execute("  CREA UNA PAGINA CON AUTH  ")
        assert result.success is True
        assert result.stage == Stage.PREPROCESSOR


class TestPreprocessorEdgeCases:
    def test_empty_input(self):
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
        p = Preprocessor(ctx)
        result = p.execute("")
        assert result.success is True

    def test_very_long_input(self):
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
        p = Preprocessor(ctx)
        long_text = "palabra " * 1000
        result = p.execute(long_text)
        assert result.success is True

    def test_special_characters(self):
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
        p = Preprocessor(ctx)
        result = p.execute("Hello @#$ %^& World!!!")
        assert result.success is True
        assert "@" not in result.output_data["normalized_text"]


class TestPreprocessorDifferentDomains:
    def test_web_domain_filters(self):
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
        p = Preprocessor(ctx, domain="web")
        assert len(p.filters) == 2

    def test_api_domain_filters(self):
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
        p = Preprocessor(ctx, domain="api")
        assert len(p.filters) == 2
