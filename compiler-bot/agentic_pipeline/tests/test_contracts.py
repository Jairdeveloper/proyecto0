"""Tests for stage output contracts (Pydantic validation)."""

import pytest

from agentic_pipeline.contracts import (
    IRContract,
    LexerContract,
    NLPContract,
    ParserContract,
    PlannerContract,
    PreprocessorContract,
    SemanticContract,
    SynthesisContract,
    UIContract,
    ValidatorContract,
)


class TestNLPContract:
    def test_valid_data(self):
        data = {
            "raw": "crea un modulo",
            "intent": {"primary": "SCAFFOLD"},
            "entities": {"modulos": []},
            "slots": {"accion": "create"},
            "ambiguity": {"detected": False},
        }
        NLPContract.model_validate(data)

    def test_invalid_missing_fields(self):
        with pytest.raises(Exception):
            NLPContract.model_validate({})


class TestPreprocessorContract:
    def test_valid(self):
        PreprocessorContract.model_validate({"normalized_text": "crea modulo", "domain": "web"})


class TestLexerContract:
    def test_valid(self):
        LexerContract.model_validate(
            {"tokens": [{"value": "crea", "type": "ACTION", "category": "action"}]}
        )

    def test_valid_with_enriched(self):
        LexerContract.model_validate(
            {
                "tokens": [],
                "enriched": {"domain": "web"},
            }
        )


class TestParserContract:
    def test_valid(self):
        ParserContract.model_validate(
            {"ast": {"type": "project", "nodes": []}, "grammar": "project"}
        )


class TestSemanticContract:
    def test_valid(self):
        SemanticContract.model_validate({"ast": {}, "semantic_errors": [], "warnings": []})


class TestIRContract:
    def test_valid(self):
        IRContract.model_validate({"ir_json": "{}"})


class TestPlannerContract:
    def test_valid(self):
        PlannerContract.model_validate({"tasks": [], "commands": [], "complexity": "low"})


class TestSynthesisContract:
    def test_valid(self):
        SynthesisContract.model_validate({"generated_files": [], "errors": []})


class TestUIContract:
    def test_valid(self):
        UIContract.model_validate({"generated_files": []})


class TestValidatorContract:
    def test_valid(self):
        ValidatorContract.model_validate({"results": [], "should_retry": False})
