"""UserRequestLayer — facade que orquesta NLU → Pipeline → NLG."""

from __future__ import annotations

import logging

from user_request.contracts.enums import RequestChannel
from user_request.contracts.request import RequestObject
from user_request.contracts.response import ResponseObject
from user_request.nlg.pipeline import NLGPipeline
from user_request.nlu.pipeline import NLUPipeline

logger = logging.getLogger(__name__)


class UserRequestLayer:
    """Facade que unifica NLU + Pipeline + NLG.

    Orquesta el flujo completo: procesamiento de lenguaje natural (NLU),
    compilacion RECPL (PipelineOrchestrator) y generacion de respuesta (NLG).

    Uso:
        >>> layer = UserRequestLayer()
        >>> request = layer.process_input("crea un modulo de pagos")
        >>> questions = layer.resolve_ambiguity(request)
        >>> response = ResponseObject(success=True, data={...})
        >>> output = layer.format_output(response)
    """

    def __init__(
        self,
        channel: RequestChannel = RequestChannel.CLI,
    ) -> None:
        """Inicializa la capa UserRequest.

        Args:
            channel: Canal de salida por defecto.
        """
        self.channel = channel
        self.nlu = NLUPipeline()
        self.nlg = NLGPipeline(channel)

    def process_input(self, raw: str) -> RequestObject:
        """Procesa la entrada del usuario a traves del pipeline NLU.

        Args:
            raw: Texto original del usuario.

        Returns:
            RequestObject con intent, entidades, slots y ambiguedad.
        """
        return self.nlu.process(raw)

    def format_output(
        self,
        response: ResponseObject,
        channel: RequestChannel | None = None,
        force_ir: bool = False,
    ) -> str:
        """Formatea un ResponseObject a traves del pipeline NLG.

        Args:
            response: ResponseObject a formatear.
            channel: Canal destino (opcional, usa el del layer si no se da).
            force_ir: Si True, fuerza el uso de IRFormatter.

        Returns:
            String formateado segun el canal.
        """
        channel = channel or self.channel

        if force_ir and response.data is not None and "ir" not in response.data:
            wrapped = ResponseObject(
                success=response.success,
                data={"ir": response.data},
                error=response.error,
                suggestions=response.suggestions,
                channel=response.channel,
                metadata=response.metadata,
            )
            return self.nlg.process(wrapped, channel=channel)

        return self.nlg.process(response, channel=channel)

    def resolve_ambiguity(self, request: RequestObject) -> list[str]:
        """Genera preguntas para resolver ambiguedades detectadas.

        Args:
            request: RequestObject con ambiguedades detectadas.

        Returns:
            Lista de preguntas en lenguaje natural para el usuario.
        """
        return self.nlu.ambiguity.generate_questions(request)

    def set_channel(self, channel: RequestChannel) -> None:
        """Cambia el canal de salida por defecto.

        Args:
            channel: Nuevo canal de salida.
        """
        self.channel = channel
        self.nlg.set_channel(channel)
