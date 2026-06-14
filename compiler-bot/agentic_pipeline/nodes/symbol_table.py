"""Symbol table with scoped lookup and Memento pattern."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class SymbolTable:
    """Hierarchical symbol table with nested scopes and Memento snapshots."""

    def __init__(self) -> None:
        self._scopes: list[dict[str, dict[str, Any]]] = [{}]
        self._snapshots: list[list[dict[str, dict[str, Any]]]] = []

    def enter_scope(self) -> None:
        self._scopes.append({})

    def exit_scope(self) -> dict[str, dict[str, Any]]:
        return self._scopes.pop()

    def define(self, name: str, symbol: dict[str, Any]) -> None:
        self._scopes[-1][name] = symbol

    def lookup(self, name: str) -> dict[str, Any] | None:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_local(self, name: str) -> dict[str, Any] | None:
        return self._scopes[-1].get(name)

    def current_scope(self) -> dict[str, dict[str, Any]]:
        return self._scopes[-1]

    def scope_depth(self) -> int:
        return len(self._scopes)

    def memento_save(self) -> list[dict[str, dict[str, Any]]]:
        snapshot = deepcopy(self._scopes)
        self._snapshots.append(snapshot)
        return snapshot

    def memento_restore(self) -> bool:
        if not self._snapshots:
            return False
        self._scopes = self._snapshots.pop()
        return True

    def has_symbol(self, name: str) -> bool:
        return self.lookup(name) is not None
