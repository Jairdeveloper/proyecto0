"""Lexer stage — DFA-based tokenization with multi-word support."""

from __future__ import annotations

import logging
from typing import Any

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.nodes.sub_dfa import (
    UIDFA,
    ActionDFA,
    BaseDFA,
    DomainDFA,
    EntityDFA,
    QualityDFA,
    TechDFA,
)
from agentic_pipeline.state_models import (
    ActionPlan,
    AnalysisResult,
    StageContext,
    StageOutput,
    Token,
)

logger = logging.getLogger(__name__)


# ============================================================================
# TOKEN FLYWEIGHT REGISTRY
# ============================================================================


class TokenFlyweightRegistry:
    """Cache for Token objects to reduce memory allocation."""

    _cache: dict[tuple[str, str, str], Token] = {}

    @classmethod
    def get(cls, value: str, token_type: str, category: str, pos: int) -> Token:
        key = (value, token_type, category)
        if key not in cls._cache:
            cls._cache[key] = Token(
                value=value,
                type=token_type,
                category=category,
                position=pos,
            )
        return cls._cache[key].model_copy(update={"position": pos})

    @classmethod
    def clear(cls) -> None:
        cls._cache.clear()

    @classmethod
    def size(cls) -> int:
        return len(cls._cache)


# ============================================================================
# MULTI-WORD TRIE
# ============================================================================


class MultiWordTrie:
    """Trie for multi-word phrase recognition."""

    def __init__(self):
        self.root: dict[str, Any] = {}

    def insert(self, phrase: str, token_type: str) -> None:
        node = self.root
        for word in phrase.lower().split():
            node = node.setdefault(word, {})
        node["__type__"] = token_type

    def lookup(self, words: list[str], start: int) -> tuple[int, str] | None:
        node = self.root
        i = start
        last_match: tuple[int, str] | None = None
        while i < len(words) and words[i] in node:
            node = node[words[i]]
            i += 1
            if "__type__" in node:
                last_match = (i, node["__type__"])
        return last_match


# ============================================================================
# TRIE PHRASES
# ============================================================================

TRIE_PHRASES: list[tuple[str, str]] = [
    ("panel de control", "DASHBOARD"),
    ("codigo qr", "QR_CODE"),
    ("codigos qr", "QR_CODE"),
    ("acortamiento de enlaces", "URL_SHORTENER"),
    ("acortador de enlaces", "URL_SHORTENER"),
    ("inicio de sesion", "LOGIN"),
    ("base de datos", "DATABASE"),
    ("tiempo real", "REALTIME"),
    ("dos factores", "MFA"),
    ("correo electronico", "EMAIL"),
    ("inteligencia artificial", "AI"),
    ("aprendizaje automatico", "ML"),
    ("ciudad inteligente", "SMART_CITY"),
    ("registro de usuarios", "SIGNUP"),
]

DEFAULT_TRIE = MultiWordTrie()
for phrase, ttype in TRIE_PHRASES:
    DEFAULT_TRIE.insert(phrase, ttype)


# ============================================================================
# LEXER STAGE
# ============================================================================


class Lexer(PipelineStage):
    """Stage 3: tokenizes normalized text using sub-DFAs and multi-word trie."""

    name = "lexer"

    def __init__(self, context: StageContext):
        super().__init__(context)
        self.dfas: dict[str, BaseDFA] = {
            "domain": DomainDFA(),
            "action": ActionDFA(),
            "tech": TechDFA(),
            "ui": UIDFA(),
            "quality": QualityDFA(),
            "entity": EntityDFA(),
        }
        self.trie = DEFAULT_TRIE
        self._text = ""
        self._enriched: dict = {}

    def receive_mission(self, input_data: object) -> None:
        if isinstance(input_data, dict):
            self._text = input_data.get("normalized_text", "") or ""
            self._enriched = input_data.get("enriched", {}) or {}
        else:
            self._text = str(input_data)
            self._enriched = {}
        logger.debug("Lexer received: %.100s", self._text)

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(
            observations=[f"Text length: {len(self._text)}"],
            detected_patterns=[],
            risks=[],
            complexity_score=0.2,
        )

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        all_tokens: list[Token] = []
        for dfa in self.dfas.values():
            all_tokens.extend(dfa.tokenize(self._text))
        trie_tokens = self._tokenize_trie(self._text)
        all_tokens.extend(trie_tokens)
        all_tokens.sort(key=lambda t: t.position)
        logger.info("Lexer produced %d tokens", len(all_tokens))
        return StageOutput(
            stage=self.context.stage,
            output_data={
                "tokens": [t.model_dump() for t in all_tokens],
                "enriched": self._enriched or None,
            },
            metrics={"tokens_count": len(all_tokens)},
        )

    def _tokenize_trie(self, text: str) -> list[Token]:
        words = text.lower().split()
        tokens: list[Token] = []
        char_pos = 0
        for i in range(len(words)):
            result = self.trie.lookup(words, i)
            if result is not None:
                end_idx, token_type = result
                phrase_words = words[i:end_idx]
                phrase = " ".join(phrase_words)
                start_pos = self._find_char_pos(self._text, phrase, char_pos)
                tokens.append(
                    TokenFlyweightRegistry.get(
                        value=phrase,
                        token_type=token_type,
                        category="phrase",
                        pos=start_pos,
                    )
                )
                char_pos = start_pos + len(phrase)
                i = end_idx - 1
            else:
                char_pos += len(words[i]) + 1
        return tokens

    @staticmethod
    def _find_char_pos(text: str, phrase: str, start: int) -> int:
        idx = text.lower().find(phrase.lower(), start)
        return idx if idx != -1 else start

    def learn_and_improve(self, feedback: object) -> None:
        pass
