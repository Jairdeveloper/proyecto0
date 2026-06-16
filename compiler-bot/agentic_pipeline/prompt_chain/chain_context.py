"""ChainContext — bus de datos entre etapas del prompt chain."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel

from .prompt_template import ChainStep


class ChainContext:
    """Bus de datos entre etapas con validacion de contratos.

    Cada etapa publica su salida via set_output(), y las etapas
    siguientes toman solo los campos que necesitan via get_fields().
    """

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}
        self._history: list[ChainStep] = []

    def set_output(
        self,
        stage: str,
        data: dict,
        contract: type[BaseModel] | None = None,
    ) -> None:
        """Publica salida de una etapa. Valida contra contrato si existe.

        Args:
            stage: Nombre de la etapa (ej: "preprocess")
            data: Datos de salida
            contract: Pydantic model opcional para validar

        Raises:
            ValidationError: si data no cumple contract
        """
        if contract:
            contract.model_validate(data)
        self._data[stage] = data
        self._history.append(ChainStep(
            stage=stage,
            output=data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True,
        ))

    def get_fields(self, stage: str, fields: list[str]) -> dict:
        """Obtiene campos especificos de una etapa anterior.

        Args:
            stage: Nombre de la etapa origen
            fields: Lista de campos a extraer

        Returns:
            Dict con solo los campos solicitados

        Raises:
            KeyError: si la etapa o algun campo no existe
        """
        if stage not in self._data:
            msg = f"Stage '{stage}' not found in context"
            raise KeyError(msg)
        output = self._data[stage]
        missing = [f for f in fields if f not in output]
        if missing:
            msg = f"Fields {missing} not found in stage '{stage}'"
            raise KeyError(msg)
        return {f: output[f] for f in fields}

    def render_template(self, template: str, stage: str, fields: list[str]) -> str:
        """Rellena un template con campos de una etapa anterior.

        Ejemplo:
            ctx.render_template("Texto: {normalized}", "preprocess",
                                ["normalized"])
            → "Texto: crea un modulo de pagos en nestjs"
        """
        context = self.get_fields(stage, fields)
        return template.format(**context)

    def get_history(self, limit: int | None = None) -> list[ChainStep]:
        """Retorna historial de etapas ejecutadas."""
        if limit is not None:
            return self._history[-limit:]
        return list(self._history)

    def get_all_outputs(self) -> dict[str, dict]:
        """Retorna todas las salidas publicadas (solo lectura)."""
        return dict(self._data)
