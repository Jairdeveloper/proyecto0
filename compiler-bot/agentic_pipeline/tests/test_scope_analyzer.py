"""Tests for SymbolTable with scopes and Memento pattern."""

from agentic_pipeline.nodes.symbol_table import SymbolTable


class TestSymbolTable:
    def test_define_and_lookup(self):
        st = SymbolTable()
        st.define("user", {"type": "entity"})
        result = st.lookup("user")
        assert result == {"type": "entity"}

    def test_lookup_missing(self):
        st = SymbolTable()
        assert st.lookup("nonexistent") is None

    def test_scope_isolation(self):
        st = SymbolTable()
        st.define("a", {"val": 1})
        st.enter_scope()
        st.define("a", {"val": 2})
        assert st.lookup("a") == {"val": 2}  # inner scope
        st.exit_scope()
        assert st.lookup("a") == {"val": 1}  # restored outer

    def test_scope_depth(self):
        st = SymbolTable()
        assert st.scope_depth() == 1
        st.enter_scope()
        assert st.scope_depth() == 2
        st.enter_scope()
        assert st.scope_depth() == 3
        st.exit_scope()
        assert st.scope_depth() == 2

    def test_lookup_local(self):
        st = SymbolTable()
        st.define("global_var", {"val": "global"})
        st.enter_scope()
        assert st.lookup_local("global_var") is None  # not in local scope
        st.define("local_var", {"val": "local"})
        assert st.lookup_local("local_var") == {"val": "local"}

    def test_current_scope(self):
        st = SymbolTable()
        st.define("x", {"val": 1})
        assert st.current_scope() == {"x": {"val": 1}}

    def test_has_symbol(self):
        st = SymbolTable()
        assert st.has_symbol("foo") is False
        st.define("foo", {"type": "bar"})
        assert st.has_symbol("foo") is True


class TestMemento:
    def test_save_and_restore(self):
        st = SymbolTable()
        st.define("pre", {"val": "before"})
        st.memento_save()
        st.define("post", {"val": "after"})
        assert st.has_symbol("post")
        st.memento_restore()
        assert st.has_symbol("pre")
        assert not st.has_symbol("post")  # rolled back

    def test_restore_empty(self):
        st = SymbolTable()
        assert st.memento_restore() is False

    def test_multiple_snapshots(self):
        st = SymbolTable()
        st.define("a", {"v": 1})
        st.memento_save()
        st.define("b", {"v": 2})
        st.memento_save()
        st.define("c", {"v": 3})
        st.memento_restore()
        assert not st.has_symbol("c")
        assert st.has_symbol("b")
        st.memento_restore()
        assert not st.has_symbol("b")

    def test_save_returns_snapshot(self):
        st = SymbolTable()
        st.define("keep", {"val": 1})
        snapshot = st.memento_save()
        assert isinstance(snapshot, list)
        assert len(snapshot) >= 1

    def test_restore_scope_isolation(self):
        st = SymbolTable()
        st.enter_scope()
        st.define("inner", {"v": "i"})
        st.memento_save()
        st.exit_scope()
        st.enter_scope()
        st.define("inner2", {"v": "i2"})
        st.memento_restore()
        assert st.has_symbol("inner")
        assert not st.has_symbol("inner2")
