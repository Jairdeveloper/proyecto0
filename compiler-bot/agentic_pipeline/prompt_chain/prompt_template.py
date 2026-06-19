"""PromptTemplate, PromptRegistry, and ChainStep for prompt chaining."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel


@dataclass
class PromptTemplate:
    """Una plantilla de prompt con schema de entrada/salida."""

    name: str
    system_prompt: str
    template: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    fallback_name: str | None = None
    temperature: float = 0.3
    model: str = "gpt-4o-mini"
    provider: str = "openai"
    version: str = "1.0"

    def render(self, **kwargs: Any) -> str:
        """Rellena el template con kwargs y valida contra input_schema."""
        validated = self.input_schema(**kwargs)
        return self.template.format(**validated.model_dump())


class PromptRegistry:
    """Registro central de plantillas de prompt."""

    _templates: dict[str, PromptTemplate] = {}

    @classmethod
    def register(cls, template: PromptTemplate) -> None:
        """Registra un template. Lanza si ya existe con mismo nombre."""
        if template.name in cls._templates:
            msg = f"PromptTemplate '{template.name}' already registered"
            raise KeyError(msg)
        cls._templates[template.name] = template

    @classmethod
    def get(cls, name: str) -> PromptTemplate:
        """Obtiene un template por nombre. Lanza KeyError si no existe."""
        if name not in cls._templates:
            msg = f"PromptTemplate '{name}' not found"
            raise KeyError(msg)
        return cls._templates[name]

    @classmethod
    def list(cls) -> list[dict]:
        """Lista todos los templates registrados."""
        return [
            {
                "name": t.name,
                "version": t.version,
                "provider": t.provider,
                "model": t.model,
                "temperature": t.temperature,
                "input_schema": t.input_schema.__name__,
                "output_schema": t.output_schema.__name__,
                "has_fallback": t.fallback_name is not None,
            }
            for t in cls._templates.values()
        ]

    @classmethod
    def validate_output(cls, name: str, data: dict) -> BaseModel:
        """Valida un dict contra el output_schema del template."""
        template = cls.get(name)
        return template.output_schema(**data)

    @classmethod
    def clear(cls) -> None:
        """Limpia el registro (util en tests)."""
        cls._templates.clear()


def register_prompt(template: PromptTemplate) -> PromptTemplate:
    """Helper para registrar y retornar un template."""
    PromptRegistry.register(template)
    return template


@dataclass
class ChainStep:
    """Una etapa ejecutada en la cadena, con su output y metadatos."""

    stage: str
    output: dict
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )
    duration: float = 0.0
    success: bool = True
    error: str | None = None
