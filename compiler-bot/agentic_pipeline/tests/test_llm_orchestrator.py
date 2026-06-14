"""Tests for LLM tools (classifiers, extractors, feature identifier)."""

from agentic_pipeline.tools.llm_tools import (
    ConstraintDetector,
    DomainClassifier,
    EntityExtractor,
    FeatureIdentifier,
    StoryGenerator,
)


# ============================================================================
# DomainClassifier
# ============================================================================


class TestDomainClassifier:
    def test_classify_web_domain(self):
        dc = DomainClassifier()
        result = dc.classify("Quiero una pagina web moderna con frontend")
        assert result == "web"

    def test_classify_api_domain(self):
        dc = DomainClassifier()
        result = dc.classify("Necesito una API REST para gestion de usuarios")
        assert result == "api"

    def test_classify_mobile_domain(self):
        dc = DomainClassifier()
        result = dc.classify("Crea una app movil para Android")
        assert result == "mobile"

    def test_classify_default_fallback(self):
        dc = DomainClassifier()
        result = dc.classify("xyz unknown text without keywords")
        assert result == "web"


# ============================================================================
# EntityExtractor
# ============================================================================


class TestEntityExtractor:
    def test_extract_user_entity(self):
        ee = EntityExtractor()
        result = ee.extract("Crea un modulo de usuarios")
        assert any(e["type"] == "user" for e in result)

    def test_extract_form_entity(self):
        ee = EntityExtractor()
        result = ee.extract("Agrega un formulario de registro")
        assert any(e["type"] == "form" for e in result)

    def test_extract_page_entity(self):
        ee = EntityExtractor()
        result = ee.extract("Pagina de login con formulario")
        assert any(e["type"] == "page" for e in result)

    def test_extract_multiple_entities(self):
        ee = EntityExtractor()
        result = ee.extract("Pagina de login con formulario de usuarios y enlaces")
        assert len(result) >= 2

    def test_extract_empty_text(self):
        ee = EntityExtractor()
        result = ee.extract("")
        assert result == []


# ============================================================================
# FeatureIdentifier
# ============================================================================


class TestFeatureIdentifier:
    def test_identify_auth_features(self):
        fi = FeatureIdentifier()
        result = fi.identify("Sistema con auth y login")
        assert any("JWT" in f for f in result)
        assert any("User model" in f for f in result)

    def test_identify_qr_features(self):
        fi = FeatureIdentifier()
        result = fi.identify("Generar codigos QR")
        assert any("QR" in f for f in result)

    def test_identify_multiple_features(self):
        fi = FeatureIdentifier()
        result = fi.identify("Pagina con auth y analytics")
        assert any("JWT" in f for f in result)
        assert any("Click tracking" in f for f in result)

    def test_identify_no_features(self):
        fi = FeatureIdentifier()
        result = fi.identify("Crea una pagina simple")
        assert result == []


# ============================================================================
# ConstraintDetector
# ============================================================================


class TestConstraintDetector:
    def test_detect_performance(self):
        cd = ConstraintDetector()
        result = cd.detect("Debe ser rapido y responsive")
        assert "performance" in result

    def test_detect_security(self):
        cd = ConstraintDetector()
        result = cd.detect("Sistema seguro con autenticacion")
        assert "security" in result

    def test_detect_multiple_constraints(self):
        cd = ConstraintDetector()
        result = cd.detect("rapido, seguro y escalable")
        assert "performance" in result
        assert "security" in result
        assert "scalability" in result

    def test_detect_no_constraints(self):
        cd = ConstraintDetector()
        result = cd.detect("Crea una pagina")
        assert result == []


# ============================================================================
# StoryGenerator
# ============================================================================


class TestStoryGenerator:
    def test_generate_stories(self):
        sg = StoryGenerator()
        features = ["User model", "JWT", "login/signup"]
        entities = [{"name": "User", "type": "user", "attributes": []}]
        stories = sg.generate(features, entities)
        assert len(stories) == 3
        assert all(s.startswith("Como usuario quiero") for s in stories)

    def test_generate_empty(self):
        sg = StoryGenerator()
        stories = sg.generate([], [])
        assert stories == []
