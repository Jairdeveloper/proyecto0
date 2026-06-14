from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, ir_node: object, output_dir: Path) -> list[Path]: ...


class GeneratorFactory:
    _registry: dict[str, type[BaseGenerator]] = {}

    @classmethod
    def register(cls, target: str, generator_cls: type[BaseGenerator]) -> None:
        cls._registry[target] = generator_cls

    @classmethod
    def get_generator(cls, target: str) -> BaseGenerator:
        if target in cls._registry:
            return cls._registry[target]()
        raise ValueError(f"Unknown target: {target}")

    @classmethod
    def list_targets(cls) -> list[str]:
        return list(cls._registry.keys())
