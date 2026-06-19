"""Tests for WorldModel (N2.2a)."""

from __future__ import annotations


class TestWorldModel:
    def test_initialize_scans_directory(self, tmp_path):
        from agentic_pipeline.world_model import WorldModel

        (tmp_path / "test.txt").write_text("hello")
        (tmp_path / "subdir").mkdir()
        w = WorldModel()
        w.initialize(str(tmp_path))
        assert any("test.txt" in k for k in w.files)

    def test_apply_action_create(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        delta = w.apply_action({"type": "create", "path": "modules/auth/auth.module.ts"})
        assert len(delta.added) == 1
        assert delta.added[0].path == "modules/auth/auth.module.ts"

    def test_apply_action_delete(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        w.apply_action({"type": "create", "path": "test.txt"})
        delta = w.apply_action({"type": "delete", "path": "test.txt"})
        assert "test.txt" not in w.files
        assert "test.txt" in delta.removed

    def test_apply_action_mkdir(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        delta = w.apply_action({"type": "mkdir", "path": "modules/auth"})
        assert len(delta.added) == 1
        assert delta.added[0].file_type == "directory"

    def test_query_exists(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        w.apply_action({"type": "create", "path": "modules/auth/auth.module.ts"})
        result = w.query("existe modules/auth/auth.module.ts?")
        assert "Si" in result

    def test_query_not_exists(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        result = w.query("existe archivo_inexistente.txt?")
        assert "No" in result or "no encontrado" in result.lower()

    def test_query_count(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        w.apply_action({"type": "create", "path": "a.txt"})
        w.apply_action({"type": "create", "path": "b.txt"})
        result = w.query("cuantos archivos")
        assert "2" in result

    def test_snapshot_returns_dict(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        snap = w.snapshot()
        assert "files" in snap
        assert "decisions" in snap
        assert "goals" in snap

    def test_decisions_recorded(self):
        from agentic_pipeline.world_model import WorldModel

        w = WorldModel()
        w.apply_action({"type": "create", "path": "test.txt", "goal_id": "g1", "rationale": "test"})
        assert len(w.decisions) == 1
        assert w.decisions[0].goal_id == "g1"
        assert w.decisions[0].action == "create"
