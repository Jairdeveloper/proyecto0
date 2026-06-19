"""Tests for sub-DFAs, TokenFlyweightRegistry, MultiWordTrie, and Lexer stage."""

import pytest

from agentic_pipeline.nodes.lexer import (
    DEFAULT_TRIE,
    Lexer,
    MultiWordTrie,
    TokenFlyweightRegistry,
)
from agentic_pipeline.nodes.sub_dfa import (
    UIDFA,
    ActionDFA,
    DomainDFA,
    QualityDFA,
    TechDFA,
    build_dfa_from_words,
)
from agentic_pipeline.state_models import Stage, StageContext

# ============================================================================
# build_dfa_from_words
# ============================================================================


class TestBuildDFA:
    def test_build_single_word(self):
        trans, accept = build_dfa_from_words([("hola", "GREETING")])
        assert len(accept) == 1
        state = 0
        for ch in "hola":
            assert ch in trans[state]
            state = trans[state][ch]
        assert state in accept
        assert accept[state] == "GREETING"

    def test_build_multiple_words(self):
        words = [("si", "YES"), ("no", "NO"), ("yes", "YES")]
        trans, accept = build_dfa_from_words(words)
        assert len(accept) >= 2


# ============================================================================
# DomainDFA
# ============================================================================


class TestDomainDFA:
    def test_web_app_token(self):
        dfa = DomainDFA()
        tokens = dfa.tokenize("web_app")
        assert len(tokens) == 1
        assert tokens[0].type == "WEB_APP"

    def test_api_token(self):
        dfa = DomainDFA()
        tokens = dfa.tokenize("api")
        assert any(t.type == "API" for t in tokens)

    def test_multiple_tokens(self):
        dfa = DomainDFA()
        tokens = dfa.tokenize("web_app api mobile")
        types = [t.type for t in tokens]
        assert "WEB_APP" in types
        assert "API" in types
        assert "MOBILE" in types

    def test_no_match(self):
        dfa = DomainDFA()
        tokens = dfa.tokenize("xyzxyz")
        assert len(tokens) == 0

    def test_partial_match_not_accepted(self):
        dfa = DomainDFA()
        tokens = dfa.tokenize("domino")
        assert len(tokens) == 0  # "domino" has no complete token match


# ============================================================================
# ActionDFA
# ============================================================================


class TestActionDFA:
    def test_create_token(self):
        dfa = ActionDFA()
        tokens = dfa.tokenize("crear")
        assert any(t.type == "CREATE" for t in tokens)

    def test_delete_token(self):
        dfa = ActionDFA()
        tokens = dfa.tokenize("eliminar usuario")
        assert any(t.type == "DELETE" for t in tokens)

    def test_read_token(self):
        dfa = ActionDFA()
        tokens = dfa.tokenize("listar todos")
        assert any(t.type == "READ" for t in tokens)

    def test_multiple_actions(self):
        dfa = ActionDFA()
        tokens = dfa.tokenize("crear editar eliminar")
        types = [t.type for t in tokens]
        assert "CREATE" in types
        assert "UPDATE" in types
        assert "DELETE" in types


# ============================================================================
# TechDFA
# ============================================================================


class TestTechDFA:
    def test_nestjs(self):
        dfa = TechDFA()
        tokens = dfa.tokenize("nestjs")
        assert any(t.type == "NESTJS" for t in tokens)

    def test_prisma(self):
        dfa = TechDFA()
        tokens = dfa.tokenize("prisma")
        assert any(t.type == "PRISMA" for t in tokens)

    def test_multiple_techs(self):
        dfa = TechDFA()
        tokens = dfa.tokenize("nestjs prisma postgres redis")
        types = [t.type for t in tokens]
        assert "NESTJS" in types
        assert "PRISMA" in types
        assert "POSTGRES" in types
        assert "REDIS" in types


# ============================================================================
# UIDFA
# ============================================================================


class TestUIDFA:
    def test_form(self):
        dfa = UIDFA()
        tokens = dfa.tokenize("formulario")
        assert any(t.type == "FORM" for t in tokens)

    def test_table(self):
        dfa = UIDFA()
        tokens = dfa.tokenize("tabla")
        assert any(t.type == "TABLE" for t in tokens)

    def test_card(self):
        dfa = UIDFA()
        tokens = dfa.tokenize("card")
        assert any(t.type == "CARD" for t in tokens)


# ============================================================================
# QualityDFA
# ============================================================================


class TestQualityDFA:
    def test_fast(self):
        dfa = QualityDFA()
        tokens = dfa.tokenize("rapido")
        assert any(t.type == "FAST" for t in tokens)

    def test_scalable(self):
        dfa = QualityDFA()
        tokens = dfa.tokenize("escalable")
        assert any(t.type == "SCALABLE" for t in tokens)

    def test_secure(self):
        dfa = QualityDFA()
        tokens = dfa.tokenize("seguro")
        assert any(t.type == "SECURE" for t in tokens)


# ============================================================================
# MultiWordTrie
# ============================================================================


class TestMultiWordTrie:
    def test_insert_and_lookup(self):
        trie = MultiWordTrie()
        trie.insert("panel de control", "DASHBOARD")
        result = trie.lookup(["panel", "de", "control", "con", "tabla"], 0)
        assert result == (3, "DASHBOARD")

    def test_no_match(self):
        trie = MultiWordTrie()
        trie.insert("codigo qr", "QR_CODE")
        result = trie.lookup(["panel", "de", "control"], 0)
        assert result is None

    def test_prefix_not_accepted(self):
        trie = MultiWordTrie()
        trie.insert("panel de control", "DASHBOARD")
        result = trie.lookup(["panel", "de"], 0)
        assert result is None

    def test_default_trie_has_phrases(self):
        assert DEFAULT_TRIE is not None
        result = DEFAULT_TRIE.lookup(["panel", "de", "control", "con", "tabla"], 0)
        assert result == (3, "DASHBOARD")

    def test_default_trie_url_shortener(self):
        result = DEFAULT_TRIE.lookup(["acortador", "de", "enlaces", "con", "auth"], 0)
        assert result == (3, "URL_SHORTENER")

    def test_default_trie_qr(self):
        result = DEFAULT_TRIE.lookup(["codigo", "qr", "para", "compartir"], 0)
        assert result == (2, "QR_CODE")


# ============================================================================
# TokenFlyweightRegistry
# ============================================================================


class TestTokenFlyweightRegistry:
    def setup_method(self):
        TokenFlyweightRegistry.clear()

    def test_get_returns_token(self):
        t = TokenFlyweightRegistry.get("api", "API", "domain", 0)
        assert t.value == "api"
        assert t.type == "API"
        assert t.category == "domain"
        assert t.position == 0

    def test_cache_reuses_same_object(self):
        t1 = TokenFlyweightRegistry.get("api", "API", "domain", 0)
        t2 = TokenFlyweightRegistry.get("api", "API", "domain", 10)
        assert t1.value == t2.value
        assert t1.type == t2.type
        assert t1.category == t2.category
        # position should differ (model_copy)
        assert t1.position == 0
        assert t2.position == 10

    def test_cache_respects_size(self):
        TokenFlyweightRegistry.clear()
        assert TokenFlyweightRegistry.size() == 0
        TokenFlyweightRegistry.get("api", "API", "domain", 0)
        assert TokenFlyweightRegistry.size() == 1
        TokenFlyweightRegistry.get("api", "API", "domain", 5)
        assert TokenFlyweightRegistry.size() == 1  # same key
        TokenFlyweightRegistry.get("jwt", "JWT", "tech", 0)
        assert TokenFlyweightRegistry.size() == 2

    def test_clear(self):
        TokenFlyweightRegistry.get("api", "API", "domain", 0)
        assert TokenFlyweightRegistry.size() > 0
        TokenFlyweightRegistry.clear()
        assert TokenFlyweightRegistry.size() == 0


# ============================================================================
# Lexer Stage
# ============================================================================


@pytest.fixture
def lexer():
    ctx = StageContext(stage=Stage.LEXER, input_data="")
    return Lexer(ctx)


class TestLexer:
    def test_receive_mission(self, lexer):
        lexer.receive_mission("crear modulo nestjs")
        assert lexer._text == "crear modulo nestjs"

    def test_analyze(self, lexer):
        lexer.receive_mission("test")
        result = lexer.analyze()
        assert result.complexity_score == 0.2

    def test_act_returns_tokens(self, lexer):
        lexer.receive_mission("crear api web_app nestjs")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        assert "tokens" in output.output_data
        assert output.metrics["tokens_count"] >= 3

    def test_act_domain_tokens(self, lexer):
        lexer.receive_mission("web_app api mobile")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        types = [t["type"] for t in output.output_data["tokens"]]
        assert "WEB_APP" in types
        assert "API" in types
        assert "MOBILE" in types

    def test_act_action_tokens(self, lexer):
        lexer.receive_mission("crear editar eliminar")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        types = [t["type"] for t in output.output_data["tokens"]]
        assert "CREATE" in types
        assert "UPDATE" in types
        assert "DELETE" in types

    def test_act_tech_tokens(self, lexer):
        lexer.receive_mission("nestjs prisma postgres")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        types = [t["type"] for t in output.output_data["tokens"]]
        assert "NESTJS" in types
        assert "PRISMA" in types
        assert "POSTGRES" in types

    def test_act_ui_tokens(self, lexer):
        lexer.receive_mission("formulario tabla card modal")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        types = [t["type"] for t in output.output_data["tokens"]]
        assert "FORM" in types
        assert "TABLE" in types
        assert "CARD" in types
        assert "MODAL" in types

    def test_trie_tokenization(self, lexer):
        lexer.receive_mission("panel de control con tabla")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        types = [t["type"] for t in output.output_data["tokens"]]
        assert "DASHBOARD" in types
        assert "TABLE" in types

    def test_realistic_prompt(self, lexer):
        lexer.receive_mission("crear modulo pagos en nestjs con auth")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        assert output.metrics["tokens_count"] >= 3

    def test_execute_full_flow(self, lexer):
        result = lexer.execute("crear web_app api nestjs escalable")
        assert result.success is True
        assert result.stage == Stage.LEXER
        assert result.metrics["tokens_count"] >= 4

    def test_positions_are_sorted(self, lexer):
        lexer.receive_mission("crear web_app api nestjs")
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        tokens = output.output_data["tokens"]
        positions = [t["position"] for t in tokens]
        assert positions == sorted(positions)

    def test_learn_and_improve(self, lexer):
        lexer.receive_mission("test")
        output = lexer.act(lexer.reflect_and_plan(lexer.analyze()))
        lexer.learn_and_improve(output.feedback)
        assert True  # no exception


class TestLexerEdgeCases:
    def test_empty_input(self):
        ctx = StageContext(stage=Stage.LEXER, input_data="")
        lexer = Lexer(ctx)
        result = lexer.execute("")
        assert result.success is True
        assert result.metrics["tokens_count"] == 0

    def test_no_matching_keywords(self):
        ctx = StageContext(stage=Stage.LEXER, input_data="")
        lexer = Lexer(ctx)
        result = lexer.execute("xyz foo bar baz")
        assert result.success is True
        assert result.metrics["tokens_count"] == 0

    def test_very_long_input(self):
        ctx = StageContext(stage=Stage.LEXER, input_data="")
        lexer = Lexer(ctx)
        long_text = "crear web_app api nestjs " * 100
        result = lexer.execute(long_text)
        assert result.success is True
        assert result.metrics["tokens_count"] >= 100


class TestLexerIntegration:
    def test_prompt_acortador(self, lexer):
        prompt = "crear web_app para acortar enlaces con auth y qr"
        lexer.receive_mission(prompt)
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        types = [t["type"] for t in output.output_data["tokens"]]
        assert "WEB_APP" in types
        assert "CREATE" in types

    def test_all_categories_represented(self, lexer):
        prompt = "crear web_app nestjs rapido con formulario de auth"
        lexer.receive_mission(prompt)
        plan = lexer.reflect_and_plan(lexer.analyze())
        output = lexer.act(plan)
        types = [t["type"] for t in output.output_data["tokens"]]
        assert "CREATE" in types  # action
        assert "WEB_APP" in types  # domain
        assert "NESTJS" in types  # tech
        assert "FAST" in types  # quality
        assert "FORM" in types  # ui
