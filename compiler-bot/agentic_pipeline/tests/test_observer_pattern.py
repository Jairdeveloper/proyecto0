from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from agentic_pipeline.base_stage import PipelineStage
from agentic_pipeline.metrics_store import MetricsStore
from agentic_pipeline.observers import (
    DashboardObserver,
    DebugObserver,
    MetricsObserver,
    PromptOptimizerObserver,
)
from agentic_pipeline.prompt_chain.observer_base import (
    StageEvent,
    StageSubject,
)
from agentic_pipeline.state_models import Stage, StageContext


class TestStageSubject:
    """Tests for StageSubject attach/detach/notify."""

    def test_attach_and_notify(self):
        subject = StageSubject()
        observer = MagicMock()
        subject.attach(observer)
        event = StageEvent(stage="test", duration=0.1, success=True)
        subject.notify(event)
        observer.on_event.assert_called_once_with(event)

    def test_detach_stops_notifications(self):
        subject = StageSubject()
        observer = MagicMock()
        subject.attach(observer)
        subject.detach(observer)
        event = StageEvent(stage="test", duration=0.1, success=True)
        subject.notify(event)
        observer.on_event.assert_not_called()

    def test_notifies_all_observers(self):
        subject = StageSubject()
        obs1 = MagicMock()
        obs2 = MagicMock()
        subject.attach(obs1)
        subject.attach(obs2)
        event = StageEvent(stage="test", duration=0.1, success=True)
        subject.notify(event)
        obs1.on_event.assert_called_once()
        obs2.on_event.assert_called_once()

    def test_observer_count(self):
        subject = StageSubject()
        assert subject.observer_count == 0
        subject.attach(MagicMock())
        assert subject.observer_count == 1

    def test_no_observers_no_error(self):
        subject = StageSubject()
        event = StageEvent(stage="test", duration=0.1, success=True)
        subject.notify(event)


class TestStageEvent:
    """Tests for StageEvent dataclass."""

    def test_defaults(self):
        event = StageEvent(stage="preprocess", duration=0.5, success=True)
        assert event.output == {}
        assert event.error is None
        assert event.metadata == {}
        assert event.timestamp is not None

    def test_full_event(self):
        event = StageEvent(
            stage="lexer",
            duration=1.2,
            success=False,
            output={"tokens": []},
            error="parse error",
            metadata={"task_count": 5},
        )
        assert event.stage == "lexer"
        assert event.duration == 1.2
        assert event.success is False
        assert event.output == {"tokens": []}
        assert event.error == "parse error"
        assert event.metadata == {"task_count": 5}


class TestMetricsObserver:
    """Tests for MetricsObserver."""

    def test_records_stage_metrics(self):
        observer = MetricsObserver()
        event = StageEvent(
            stage="lexer",
            duration=0.5,
            success=True,
            output={"tokens": []},
            metadata={"task_count": 5},
        )
        observer.on_event(event)
        # Verify it doesn't crash and records via GlobalFeedbackLoop
        summary = observer._feedback.summary()
        assert summary["total_records"] >= 1


class TestDebugObserver:
    """Tests for DebugObserver."""

    def test_invokes_callback(self):
        callback = MagicMock()
        observer = DebugObserver(callback)
        event = StageEvent(
            stage="preprocess",
            duration=0.1,
            success=True,
            output={"normalized": "test"},
        )
        observer.on_event(event)
        callback.assert_called_once_with("preprocess", {"normalized": "test"})

    def test_no_callback_no_error(self):
        observer = DebugObserver()
        event = StageEvent(stage="test", duration=0.1, success=True)
        observer.on_event(event)


class TestPromptOptimizerObserver:
    """Tests for PromptOptimizerObserver."""

    def test_records_prompt_metrics(self):
        store = MetricsStore()
        observer = PromptOptimizerObserver(store)
        event = StageEvent(
            stage="preprocess",
            duration=0.3,
            success=True,
            metadata={"fallback_used": False},
        )
        observer.on_event(event)
        rate = store.get_prompt_success_rate("preprocess")
        assert rate == 1.0

    def test_ignores_non_prompt_stages(self):
        store = MetricsStore()
        observer = PromptOptimizerObserver(store)
        event = StageEvent(stage="lexer", duration=0.3, success=True)
        observer.on_event(event)
        rate = store.get_prompt_success_rate("lexer")
        assert rate == 1.0


class TestDashboardObserver:
    """Tests for DashboardObserver."""

    def test_stores_recent_events(self):
        observer = DashboardObserver(max_events=100)
        for i in range(5):
            observer.on_event(
                StageEvent(stage="test", duration=0.1, success=True),
            )
        assert observer.event_count == 5

    def test_recent_events_limit(self):
        observer = DashboardObserver(max_events=3)
        for i in range(5):
            observer.on_event(
                StageEvent(stage="test", duration=0.1, success=True),
            )
        assert observer.event_count == 3
        recent = observer.get_recent(10)
        assert len(recent) == 3

    def test_get_recent(self):
        observer = DashboardObserver()
        observer.on_event(
            StageEvent(stage="a", duration=0.1, success=True),
        )
        observer.on_event(
            StageEvent(stage="b", duration=0.2, success=True),
        )
        recent = observer.get_recent(1)
        assert len(recent) == 1
        assert recent[0].stage == "b"


class TestPipelineStageSubject:
    """Tests that PipelineStage.subject works with execute()."""

    def test_subject_notified_on_execute(self):
        class _MockStage(PipelineStage):
            name = "mock"

            def receive_mission(self, input_data):
                self.mission = input_data

            def act(self, plan):
                from agentic_pipeline.state_models import StageOutput

                return StageOutput(
                    stage=Stage.PREPROCESSOR,
                    output_data={"done": True},
                )

        subject = StageSubject()
        observer = MagicMock()
        subject.attach(observer)
        orig = PipelineStage.subject
        PipelineStage.subject = subject
        try:
            ctx = StageContext(
                stage=Stage.PREPROCESSOR,
                input_data="test",
            )
            stage = _MockStage(ctx)
            stage.execute("hello")
            assert observer.on_event.called
        finally:
            PipelineStage.subject = orig

    def test_subject_notified_on_failure(self):
        subject = StageSubject()
        observer = MagicMock()
        subject.attach(observer)
        orig = PipelineStage.subject
        PipelineStage.subject = subject
        try:

            class _FailingStage(PipelineStage):
                name = "fail"

                def receive_mission(self, input_data):
                    pass

                def act(self, plan):
                    msg = "intentional failure"
                    raise RuntimeError(msg)

            ctx = StageContext(
                stage=Stage.PREPROCESSOR,
                input_data="test",
            )
            stage = _FailingStage(ctx)
            with pytest.raises(RuntimeError):
                stage.execute("hello")
            assert observer.on_event.called
            call_args = observer.on_event.call_args[0][0]
            assert call_args.success is False
            assert "intentional failure" in call_args.error
        finally:
            PipelineStage.subject = orig


class TestStageSubjectConcurrency:
    """Tests that StageSubject handles concurrent attach/detach/notify safely."""

    def test_concurrent_attach_detach_notify(self):
        subject = StageSubject()
        results: list[bool] = []
        results_lock = threading.Lock()
        barrier = threading.Barrier(10)

        def worker() -> None:
            obs = MagicMock()
            barrier.wait()
            subject.attach(obs)
            event = StageEvent(stage="concurrent", duration=0.1, success=True)
            subject.notify(event)
            subject.detach(obs)
            subject.notify(event)
            with results_lock:
                results.append(True)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert subject.observer_count == 0
        assert subject._bus.has_subscribers("concurrent") is False

    def test_concurrent_attach_without_race(self):
        subject = StageSubject()
        barrier = threading.Barrier(10)
        observers: list[MagicMock] = []

        def worker() -> None:
            obs = MagicMock()
            barrier.wait()
            subject.attach(obs)
            with threading.Lock():
                observers.append(obs)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert subject.observer_count == 10
