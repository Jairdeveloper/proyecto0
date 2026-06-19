"""Sub-DFAs for lexical analysis — one per token category."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_pipeline.state_models import Token

# ============================================================================
# DFA BUILDER UTILITY
# ============================================================================


def build_dfa_from_words(
    words: list[tuple[str, str]],
) -> tuple[dict[int, dict[str, int]], dict[int, str]]:
    """Build DFA transitions and accepting states from a list of (word, token_type)."""
    transitions: dict[int, dict[str, int]] = {0: {}}
    accepting: dict[int, str] = {}
    next_state = 1

    for word, token_type in words:
        state = 0
        for ch in word:
            if ch not in transitions[state]:
                transitions[state][ch] = next_state
                transitions[next_state] = {}
                next_state += 1
            state = transitions[state][ch]
        accepting[state] = token_type

    return transitions, accepting


# ============================================================================
# BASE DFA
# ============================================================================


class BaseDFA(ABC):
    """Abstract DFA with maximal munch tokenization."""

    category: str
    _words: list[tuple[str, str]] = []

    def __init__(self):
        self.transitions: dict[int, dict[str, int]] = {}
        self.accepting_states: dict[int, str] = {}
        self._build()

    @abstractmethod
    def _build(self) -> None: ...

    def tokenize(self, text: str, start_pos: int = 0) -> list[Token]:
        tokens: list[Token] = []
        pos = start_pos
        text_lower = text.lower()
        while pos < len(text):
            state = 0
            token_start = pos
            last_accept: tuple[int, str] | None = None
            while pos < len(text_lower) and state in self.transitions:
                ch = text_lower[pos]
                if ch in self.transitions[state]:
                    state = self.transitions[state][ch]
                    pos += 1
                    if state in self.accepting_states:
                        last_accept = (pos, self.accepting_states[state])
                else:
                    break
            if last_accept is not None:
                end, token_type = last_accept
                tokens.append(
                    Token(
                        value=text[token_start:end],
                        type=token_type,
                        category=self.category,
                        position=token_start,
                    )
                )
                pos = end
            else:
                pos += 1
        return tokens


# ============================================================================
# DOMAIN DFA  (~25 tokens)
# ============================================================================


class DomainDFA(BaseDFA):
    category = "domain"

    def _build(self):
        words = [
            ("web_app", "WEB_APP"),
            ("api", "API"),
            ("rest", "API"),
            ("saas", "SAAS"),
            ("mobile", "MOBILE"),
            ("landing", "LANDING"),
            ("portal", "PORTAL"),
            ("dashboard", "DASHBOARD"),
            ("admin", "ADMIN"),
            ("blog", "BLOG"),
            ("ecommerce", "ECOMMERCE"),
            ("cms", "CMS"),
            ("microservice", "MICROSERVICE"),
            ("spa", "SPA"),
            ("pwa", "PWA"),
            ("desktop", "DESKTOP"),
            ("cli", "CLI"),
            ("sdk", "SDK"),
            ("plugin", "PLUGIN"),
            ("theme", "THEME"),
            ("widget", "WIDGET"),
            ("landing_page", "LANDING"),
            ("web", "WEB_APP"),
            ("pagina", "WEB_APP"),
            ("app", "MOBILE"),
            ("movil", "MOBILE"),
        ]
        self.transitions, self.accepting_states = build_dfa_from_words(words)


# ============================================================================
# ACTION DFA (~30 tokens)
# ============================================================================


class ActionDFA(BaseDFA):
    category = "action"

    def _build(self):
        words = [
            ("crear", "CREATE"),
            ("crea", "CREATE"),
            ("nuevo", "CREATE"),
            ("nueva", "CREATE"),
            ("agregar", "CREATE"),
            ("registrar", "CREATE"),
            ("listar", "READ"),
            ("ver", "READ"),
            ("mostrar", "READ"),
            ("consultar", "READ"),
            ("obtener", "READ"),
            ("buscar", "READ"),
            ("editar", "UPDATE"),
            ("actualizar", "UPDATE"),
            ("modificar", "UPDATE"),
            ("cambiar", "UPDATE"),
            ("eliminar", "DELETE"),
            ("borrar", "DELETE"),
            ("remover", "DELETE"),
            ("generar", "GENERATE"),
            ("exportar", "EXPORT"),
            ("importar", "IMPORT"),
            ("enviar", "SEND"),
            ("recibir", "RECEIVE"),
            ("procesar", "PROCESS"),
            ("validar", "VALIDATE"),
            ("calcular", "CALCULATE"),
            ("transformar", "TRANSFORM"),
            ("notificar", "NOTIFY"),
            ("autenticar", "AUTH"),
            ("auth", "AUTH"),
            ("login", "AUTH"),
            ("logout", "AUTH"),
        ]
        self.transitions, self.accepting_states = build_dfa_from_words(words)


# ============================================================================
# TECH DFA (~25 tokens)
# ============================================================================


class TechDFA(BaseDFA):
    category = "tech"

    def _build(self):
        words = [
            ("nestjs", "NESTJS"),
            ("nest", "NESTJS"),
            ("prisma", "PRISMA"),
            ("postgres", "POSTGRES"),
            ("postgresql", "POSTGRES"),
            ("redis", "REDIS"),
            ("docker", "DOCKER"),
            ("jwt", "JWT"),
            ("graphql", "GRAPHQL"),
            ("rest", "REST"),
            ("grpc", "GRPC"),
            ("rabbitmq", "RABBITMQ"),
            ("react", "REACT"),
            ("vue", "VUE"),
            ("angular", "ANGULAR"),
            ("tailwind", "TAILWIND"),
            ("bootstrap", "BOOTSTRAP"),
            ("typescript", "TYPESCRIPT"),
            ("python", "PYTHON"),
            ("node", "NODEJS"),
            ("nodejs", "NODEJS"),
            ("express", "EXPRESS"),
            ("fastify", "FASTIFY"),
            ("nextjs", "NEXTJS"),
            ("nuxt", "NUXT"),
        ]
        self.transitions, self.accepting_states = build_dfa_from_words(words)


# ============================================================================
# UI DFA (~25 tokens)
# ============================================================================


class UIDFA(BaseDFA):
    category = "ui"

    def _build(self):
        words = [
            ("boton", "BUTTON"),
            ("button", "BUTTON"),
            ("formulario", "FORM"),
            ("form", "FORM"),
            ("tabla", "TABLE"),
            ("table", "TABLE"),
            ("card", "CARD"),
            ("tarjeta", "CARD"),
            ("modal", "MODAL"),
            ("navbar", "NAVBAR"),
            ("sidebar", "SIDEBAR"),
            ("footer", "FOOTER"),
            ("header", "HEADER"),
            ("input", "INPUT"),
            ("select", "SELECT"),
            ("checkbox", "CHECKBOX"),
            ("radio", "RADIO"),
            ("slider", "SLIDER"),
            ("toast", "TOAST"),
            ("badge", "BADGE"),
            ("avatar", "AVATAR"),
            ("breadcrumb", "BREADCRUMB"),
            ("paginacion", "PAGINATION"),
            ("pagination", "PAGINATION"),
            ("dropdown", "DROPDOWN"),
            ("menu", "MENU"),
        ]
        self.transitions, self.accepting_states = build_dfa_from_words(words)


# ============================================================================
# QUALITY DFA (~20 tokens)
# ============================================================================


class QualityDFA(BaseDFA):
    category = "quality"

    def _build(self):
        words = [
            ("rapido", "FAST"),
            ("veloz", "FAST"),
            ("responsive", "RESPONSIVE"),
            ("adaptable", "RESPONSIVE"),
            ("escalable", "SCALABLE"),
            ("seguro", "SECURE"),
            ("confiable", "RELIABLE"),
            ("robusto", "ROBUST"),
            ("eficiente", "EFFICIENT"),
            ("flexible", "FLEXIBLE"),
            ("modular", "MODULAR"),
            ("testeable", "TESTABLE"),
            ("mantenible", "MAINTAINABLE"),
            ("portable", "PORTABLE"),
            ("accesible", "ACCESSIBLE"),
            ("usable", "USABLE"),
            ("intuitivo", "USABLE"),
            ("observable", "OBSERVABLE"),
            ("trazable", "TRACEABLE"),
            ("auditable", "AUDITABLE"),
        ]
        self.transitions, self.accepting_states = build_dfa_from_words(words)


# ============================================================================
# ENTITY DFA (~15 tokens)
# ============================================================================


class EntityDFA(BaseDFA):
    category = "entity"

    def _build(self):
        words = [
            ("modulo", "MODULE"),
            ("module", "MODULE"),
            ("entidad", "ENTITY"),
            ("entity", "ENTITY"),
            ("modelo", "MODEL"),
            ("model", "MODEL"),
            ("pagos", "PAYMENT"),
            ("auth", "AUTH"),
            ("autenticacion", "AUTH"),
            ("usuario", "USER"),
            ("user", "USER"),
            ("producto", "PRODUCT"),
            ("orden", "ORDER"),
            ("factura", "INVOICE"),
            ("catalogo", "CATALOG"),
        ]
        self.transitions, self.accepting_states = build_dfa_from_words(words)
