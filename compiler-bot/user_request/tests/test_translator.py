"""Tests for NLG Translator."""

from user_request.nlg.translator import NLGTranslator


class TestNLGTranslator:
    def test_render_template_exists(self):
        t = NLGTranslator()
        result = t.render_template("welcome", lang="es")
        assert result is not None
        assert "Bienvenido" in result

    def test_render_template_english(self):
        t = NLGTranslator()
        result = t.render_template("welcome", lang="en")
        assert result is not None
        assert "Welcome" in result

    def test_render_template_with_args(self):
        t = NLGTranslator()
        result = t.render_template("created_module", lang="es", name="pagos")
        assert result == "Creado modulo pagos."

    def test_render_template_with_tech(self):
        t = NLGTranslator()
        result = t.render_template("created_module_with_tech", name="pagos", tech="NestJS")
        assert "NestJS" in result

    def test_render_template_not_found(self):
        t = NLGTranslator()
        result = t.render_template("nonexistent_template")
        assert result is None

    def test_translate_default_lang(self):
        t = NLGTranslator()
        assert t.default_lang == "es"

    def test_translate_custom_default(self):
        t = NLGTranslator(default_lang="en")
        assert t.default_lang == "en"

    def test_available_templates(self):
        t = NLGTranslator()
        TemplateCls = type(t)._TEMPLATES
        assert "welcome" in TemplateCls
        assert "created_module" in TemplateCls
        assert "error_generic" in TemplateCls
        assert "pipeline_metrics" in TemplateCls
