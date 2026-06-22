"""Template-based translator for NLG pipeline."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class NLGTranslator:
    """Traductor template-based para mensajes del sistema.

    Estrategia:
    1. Template-based para mensajes conocidos (alta frecuencia, bajo costo)
    2. LLM-based para mensajes generativos (solo si hay LLM disponible)

    Templates disponibles inicialmente: espanol (default), ingles.
    """

    _TEMPLATES: dict[str, dict[str, str]] = {
        "created_module": {
            "es": "Creado modulo {name}.",
            "en": "Module {name} created.",
        },
        "created_module_with_tech": {
            "es": "Creado modulo {name} en {tech}.",
            "en": "Module {name} created with {tech}.",
        },
        "created_entity": {
            "es": "Creada entidad {name}.",
            "en": "Entity {name} created.",
        },
        "deleted_module": {
            "es": "Eliminado modulo {name}.",
            "en": "Module {name} deleted.",
        },
        "error_generic": {
            "es": "Error: {detail}",
            "en": "Error: {detail}",
        },
        "operation_complete": {
            "es": "Operacion completada.",
            "en": "Operation completed.",
        },
        "pipeline_metrics": {
            "es": "Pipeline: {stages} stages, {errors} errores, {time}ms total.",
            "en": "Pipeline: {stages} stages, {errors} errors, {time}ms total.",
        },
        "suggestions_header": {
            "es": "Sugerencias:",
            "en": "Suggestions:",
        },
        "welcome": {
            "es": "Bienvenido a RECPL. En que puedo ayudarte?",
            "en": "Welcome to RECPL. How can I help you?",
        },
    }

    def __init__(self, default_lang: str = "es") -> None:
        self._default_lang = default_lang

    def translate(self, text: str, target_lang: str | None = None) -> str:
        """Traduce un texto al idioma destino.

        Actualmente es un placeholder que registra la intencion.
        La implementacion completa con templates y LLM fallback
        se anadira cuando se integre el modulo de i18n.

        Args:
            text: Texto a traducir.
            target_lang: Idioma destino (default: es).

        Returns:
            Texto traducido (actualmente sin cambios).
        """
        _ = target_lang
        return text

    def render_template(
        self,
        template_key: str,
        lang: str | None = None,
        **kwargs: str,
    ) -> str | None:
        """Renderiza un template con los argumentos dados.

        Args:
            template_key: Clave del template en ``_TEMPLATES``.
            lang: Idioma (default: es).
            **kwargs: Variables para formatear el template.

        Returns:
            String renderizado, o None si el template no existe.
        """
        lang = lang or self._default_lang
        template = self._TEMPLATES.get(template_key)
        if template is None:
            logger.debug("Template not found: %s", template_key)
            return None
        tpl = template.get(lang)
        if tpl is None:
            tpl = template.get("es")
        if tpl is None:
            return None
        return tpl.format(**kwargs)

    @property
    def default_lang(self) -> str:
        return self._default_lang
