import tempfile

from agentic_pipeline.feedback_loop import FeedbackLoop


def test_feedback_record_and_read():
    with tempfile.TemporaryDirectory() as tmpdir:
        import agentic_pipeline.config as cfg

        original = cfg.config.memory_dir
        cfg.config.memory_dir = tmpdir

        fb = FeedbackLoop()
        fb.record("test_stage", {"tokens": 5})
        fb.record("test_stage", {"tokens": 10})

        recent = fb.get_recent("test_stage")
        assert len(recent) == 2
        assert recent[0]["stage"] == "test_stage"
        assert recent[0]["metrics"]["tokens"] == 5
        assert recent[1]["metrics"]["tokens"] == 10

        cfg.config.memory_dir = original


def test_feedback_no_file():
    fb = FeedbackLoop()
    recent = fb.get_recent("nonexistent_stage")
    assert recent == []
