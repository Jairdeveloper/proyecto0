"""Base Agent, Task, TaskResult, SharedContext (N3.1 + N3.3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Task:
    id: str
    description: str
    agent: str
    params: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"


@dataclass
class TaskResult:
    task_id: str
    success: bool
    data: Any = None
    error: str | None = None


class SharedContext:
    """Bus de contexto compartido entre agentes (N3.3)."""

    def __init__(self):
        self._data: dict[str, Any] = {}
        self._subscribers: dict[str, list[Callable]] = {}

    def publish(self, topic: str, data: Any) -> None:
        self._data[topic] = data
        for cb in self._subscribers.get(topic, []):
            cb(topic, data)

    def subscribe(self, topic: str, callback: Callable | None = None) -> Any:
        if callback:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)
        return self._data.get(topic)

    def get_snapshot(self) -> dict:
        return dict(self._data)


class AsyncSharedContext(SharedContext):
    """Bus de contexto con pub/sub asincrono (N3.3)."""

    def __init__(self):
        super().__init__()
        self._channels: dict[str, list[Callable]] = {}

    async def publish(self, topic: str, data: Any) -> None:
        self._data[topic] = data
        for cb in self._channels.get(topic, []):
            await cb(topic, data)

    def subscribe(self, topic: str, callback: Callable | None = None) -> Any:
        if callback:
            if topic not in self._channels:
                self._channels[topic] = []
            self._channels[topic].append(callback)
        return self._data.get(topic)


class Agent(ABC):
    """Clase base abstracta para todos los agentes (N3.1)."""

    name: str = ""
    role: str = ""

    def __init__(self, context: SharedContext, **kwargs: Any):
        self.context = context
        for k, v in kwargs.items():
            setattr(self, k, v)

    @abstractmethod
    async def process(self, task: Task) -> TaskResult: ...
