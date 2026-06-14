"""Tests for Preprocessor filters and pipeline stage."""

import pytest

from agentic_pipeline.nodes.preprocessor import (
    DomainEnrichmentFilter,
    ImplicitRequirementFilter,
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
        assert "!" in result  # keep basic punctuation

    def test_preserve_spanish_accents(self):
        f = NormalizationFilter()
        result = f.process("canción única")
        assert "canción" == result.split()[0]
        assert "única" == result.split()[1]


# ============================================================================
# DomainEnrichmentFilter
# ============================================================================


class TestDomainEnrichmentFilter:
    def test_web_domain_enrichment(self):
        f = DomainEnrichmentFilter()
        result = f.process("crea una pagina", {"domain": "web"})
        assert "domain:web" in result
        assert "stack:" in result

    def test_default_domain_enrichment(self):
        f = DomainEnrichmentFilter()
        result = f.process("crea algo")
        assert "domain:web" in result

    def test_mobile_domain_enrichment(self):
        f = DomainEnrichmentFilter()
        result = f.process("crea una app", {"domain": "mobile"})
        assert "domain:mobile" in result
        assert "mobile_app" in result


# ============================================================================
# ImplicitRequirementFilter
# ============================================================================


class TestImplicitRequirementFilter:
    def test_auth_implicit(self):
        f = ImplicitRequirementFilter()
        result = f.process("sistema con auth")
        assert "User model" in result
        assert "JWT" in result
        assert "login/signup" in result

    def test_qr_implicit(self):
        f = ImplicitRequirementFilter()
        result = f.process("generar qr")
        assert "QR code library" in result
        assert "QR generation" in result

    def test_multiple_implicit(self):
        f = ImplicitRequirementFilter()
        result = f.process("auth y qr")
        assert "User model" in result
        assert "QR code library" in result

    def test_no_implicit(self):
        f = ImplicitRequirementFilter()
        result = f.process("crea una pagina simple")
        assert "[implicit:" not in result


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
    def test_web_chain_includes_domain_enrichment(self):
        chain = build_filter_chain("web")
        names = [c.__class__.__name__ for c in chain]
        assert "NormalizationFilter" in names
        assert "DomainEnrichmentFilter" in names
        assert "ImplicitRequirementFilter" in names
        assert "SegmentationFilter" in names
        assert len(chain) == 4

    def test_api_chain_without_domain_enrichment(self):
        chain = build_filter_chain("api")
        names = [c.__class__.__name__ for c in chain]
        assert "NormalizationFilter" in names
        assert "DomainEnrichmentFilter" not in names
        assert len(chain) == 3


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

    def test_act_detects_implicit(self, preprocessor):
        preprocessor.receive_mission("Crea sistema con auth y qr")
        plan = preprocessor.reflect_and_plan(preprocessor.analyze())
        output = preprocessor.act(plan)
        assert "User model" in output.output_data["normalized_text"]
        assert "QR" in output.output_data["normalized_text"]

    def test_act_metrics(self, preprocessor):
        preprocessor.receive_mission("Crea una pagina")
        plan = preprocessor.reflect_and_plan(preprocessor.analyze())
        output = preprocessor.act(plan)
        assert output.metrics["filters_applied"] == 4
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
        assert len(p.filters) == 4

    def test_api_domain_filters(self):
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data="")
        p = Preprocessor(ctx, domain="api")
        assert len(p.filters) == 3
