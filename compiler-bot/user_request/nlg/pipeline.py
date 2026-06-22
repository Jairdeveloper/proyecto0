"""NLG Pipeline — orquestador del pipeline de generacion de lenguaje natural."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from user_request.contracts.enums import RequestChannel
from user_request.contracts.response import ResponseObject
from user_request.nlg.adapters import resolve_adapter
from user_request.nlg.formatters import resolve_formatter
from user_request.nlg.translator import NLGTranslator

logger = logging.getLogger(__name__)


@dataclass
class NLGPipelineResult:
    """Resultado del pipeline NLG.

    Attributes:
        content: Contenido formateado (pre-adapter).
        translated: Contenido traducido (post-translator).
        output: Salida final adaptada al canal.
        metadata: Metadatos del proceso.
    """

    content: str = ""
    translated: str = ""
    output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class NLGPipeline:
    """Orquestador del pipeline NLG.

    Pipeline completo::

        ResponseObject
            │
            ▼
        Formatter (success / error / ir / metrics)
            │  content string
            ▼
        Translator (template-based es/en)
            │  translated string
            ▼
        ChannelAdapter (CLI / API / WebUI / Editor / Agent)
            │
            ▼
        string (segun canal)
    """

    def __init__(
        self,
        channel: RequestChannel = RequestChannel.CLI,
        lang: str = "es",
    ) -> None:
        self._channel = channel
        self._translator = NLGTranslator(default_lang=lang)

    def process(
        self,
        response: ResponseObject,
        channel: RequestChannel | None = None,
        lang: str | None = None,
    ) -> str:
        """Ejecuta el pipeline NLG completo.

        Args:
            response: ResponseObject a formatear.
            channel: Canal destino (opcional, usa el del pipeline si no se da).
            lang: Idioma destino (opcional).

        Returns:
            String formateado segun el canal.
        """
        channel = channel or self._channel
        lang = lang or self._translator.default_lang
        _meta: dict[str, Any] = {}

        # 1. Seleccionar formatter y formatear
        formatter = resolve_formatter(response)
        content = formatter.format(response)
        _meta["formatter"] = formatter.__class__.__name__
        logger.debug("Formatter: %s -> %d chars", _meta["formatter"], len(content))

        # 2. Traducir
        translated = self._translator.translate(content, target_lang=lang)
        _meta["language"] = lang
        _meta["translated"] = translated != content

        # 3. Adaptar al canal
        adapter = resolve_adapter(channel)
        output = adapter.adapt(translated, response)
        _meta["adapter"] = adapter.__class__.__name__
        _meta["channel"] = channel.value
        logger.debug("Adapter: %s -> %d chars", _meta["adapter"], len(output))

        return output

    def process_with_metadata(
        self,
        response: ResponseObject,
        channel: RequestChannel | None = None,
        lang: str | None = None,
    ) -> NLGPipelineResult:
        """Ejecuta el pipeline NLG completo con metadatos.

        Similar a ``process()`` pero retorna un ``NLGPipelineResult``
        con el resultado de cada etapa.
        """
        channel = channel or self._channel
        lang = lang or self._translator.default_lang

        formatter = resolve_formatter(response)
        content = formatter.format(response)

        translated = self._translator.translate(content, target_lang=lang)

        adapter = resolve_adapter(channel)
        output = adapter.adapt(translated, response)

        return NLGPipelineResult(
            content=content,
            translated=translated,
            output=output,
            metadata={
                "formatter": formatter.__class__.__name__,
                "adapter": adapter.__class__.__name__,
                "channel": channel.value,
                "language": lang,
            },
        )

    def set_channel(self, channel: RequestChannel) -> None:
        """Cambia el canal por defecto del pipeline."""
        self._channel = channel
