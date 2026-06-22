"""Enumerations for the User Request Layer."""

from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    """Taxonomia unificada de intenciones del sistema.

    Cada intencion representa una accion que el usuario puede solicitar.
    Los alias (SCAFFOLD, QUERY, etc.) se resuelven al tipo canonico
    mediante ``from_alias()``.
    """

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPLAIN = "explain"
    CONFIGURE = "configure"

    @classmethod
    def from_alias(cls, alias: str) -> IntentType:
        """Resuelve un alias legacy al tipo canonico.

        Args:
            alias: String con el nombre del alias (case-insensitive).

        Returns:
            IntentType canonico, o ``cls.CREATE`` si no se reconoce.

        Example:
            >>> IntentType.from_alias("SCAFFOLD")
            <IntentType.CREATE: 'create'>
        """
        return _ALIAS_MAP.get(alias.lower(), cls.CREATE)

    @classmethod
    def known_aliases(cls) -> list[str]:
        """Todos los alias conocidos (incluyendo los nombres canonicos)."""
        return list(_ALIAS_MAP.keys())

    @classmethod
    def aliases_for(cls, intent: IntentType) -> list[str]:
        """Alias que resuelven a un tipo canonico dado."""
        return [k for k, v in _ALIAS_MAP.items() if v == intent]


# Mapeo de alias definido fuera de la clase para evitar colisiones
# con el mecanismo de miembros del Enum (Python 3.11).
_ALIAS_MAP: dict[str, IntentType] = {
    # Canonico a si mismo
    "create": IntentType.CREATE,
    "read": IntentType.READ,
    "update": IntentType.UPDATE,
    "delete": IntentType.DELETE,
    "explain": IntentType.EXPLAIN,
    "configure": IntentType.CONFIGURE,
    # Alias legacy
    "scaffold": IntentType.CREATE,
    "generate": IntentType.CREATE,
    "new": IntentType.CREATE,
    "query": IntentType.READ,
    "explore": IntentType.READ,
    "get": IntentType.READ,
    "modify": IntentType.UPDATE,
    "edit": IntentType.UPDATE,
    "change": IntentType.UPDATE,
    "remove": IntentType.DELETE,
    "help": IntentType.EXPLAIN,
    "clarify": IntentType.READ,
    "set": IntentType.CONFIGURE,
    "config": IntentType.CONFIGURE,
}


class RequestChannel(str, Enum):
    """Canal por el que llega la solicitud del usuario.

    Determina el formato de salida del pipeline NLG.
    """

    CLI = "cli"
    WEBUI = "webui"
    API = "api"
    EDITOR = "editor"
    AGENT = "agent"


class Language(str, Enum):
    """Idiomas soportados para traduccion NLG."""

    ES = "es"
    EN = "en"


class SlotName(str, Enum):
    """Nombres de slots normalizados para la taxonomia unificada."""

    ACCION = "accion"
    TIPO = "tipo"
    NOMBRE = "nombre"
    TECH = "tech"
    ATRIBUTOS = "atributos"
    DOMINIO = "dominio"
    OBJETIVO = "objetivo"
    FILTRO = "filtro"
    LIMITE = "limite"
    CAMBIO = "cambio"
    VALOR = "valor"
    TOPICO = "topico"
    PROFUNDIDAD = "profundidad"
    PARAMETRO = "parametro"
