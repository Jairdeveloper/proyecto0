"""Tests for dashboard static files — verify HTML elements, JS functions, CSS."""

from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "dashboard" / "static"


def _read(file: str) -> str:
    return (STATIC_DIR / file).read_text("utf-8")


class TestIndexHTML:
    """Verify required DOM elements exist in index.html."""

    def test_html_has_canvas(self) -> None:
        html = _read("index.html")
        assert 'id="distribution-chart"' in html
        assert "canvas" in html

    def test_html_has_timeline_svg(self) -> None:
        html = _read("index.html")
        assert 'id="timeline-svg"' in html

    def test_html_has_detail_distribution(self) -> None:
        html = _read("index.html")
        assert 'id="detail-distribution-chart"' in html

    def test_html_has_detail_timeline(self) -> None:
        html = _read("index.html")
        assert 'id="detail-timeline-svg"' in html

    def test_html_has_event_modal(self) -> None:
        html = _read("index.html")
        assert 'id="event-modal"' in html
        assert 'id="event-detail-json"' in html

    def test_html_has_live_badge(self) -> None:
        html = _read("index.html")
        assert 'id="live-badge"' in html
        assert 'id="live-counter"' in html

    def test_html_has_explorer(self) -> None:
        html = _read("index.html")
        assert 'id="detail-explorer"' in html
        assert 'id="explorer-body"' in html
        assert 'onclick="searchEvents()"' in html

    def test_html_has_usage_kpi(self) -> None:
        html = _read("index.html")
        assert 'id="kpi-usage"' in html

    def test_html_has_live_buttons(self) -> None:
        html = _read("index.html")
        assert "startLiveStream()" in html
        assert "stopLiveStream()" in html

    def test_html_has_detail_cards(self) -> None:
        html = _read("index.html")
        assert 'id="section-chart"' in html
        assert 'id="section-timeline"' in html


class TestDashboardJS:
    """Verify critical JS functions exist."""

    def test_js_has_render_distribution_chart(self) -> None:
        js = _read("dashboard.js")
        assert "function renderDistributionChart" in js

    def test_js_has_render_timeline_svg(self) -> None:
        js = _read("dashboard.js")
        assert "function renderTimelineSVG" in js

    def test_js_has_render_topic_list(self) -> None:
        js = _read("dashboard.js")
        assert "function renderTopicList" in js

    def test_js_has_search_events(self) -> None:
        js = _read("dashboard.js")
        assert "function searchEvents" in js

    def test_js_has_event_detail_modal(self) -> None:
        js = _read("dashboard.js")
        assert "function showEventDetail" in js
        assert "function closeEventModal" in js

    def test_js_has_live_stream_functions(self) -> None:
        js = _read("dashboard.js")
        assert "function startLiveStream" in js
        assert "function stopLiveStream" in js
        assert "EventSource" in js

    def test_js_has_fetch_and_render_timeline(self) -> None:
        js = _read("dashboard.js")
        assert "function fetchAndRenderTimeline" in js

    def test_js_loads_metrics_on_dashboard(self) -> None:
        js = _read("dashboard.js")
        assert "/api/events/distribution" in js
        assert "/api/health/metrics" in js

    def test_js_has_escape_html(self) -> None:
        js = _read("dashboard.js")
        assert "function escapeHTML" in js

    def test_js_has_sort_table(self) -> None:
        js = _read("dashboard.js")
        assert "function sortTable" in js


class TestDashboardCSS:
    """Verify critical CSS classes exist."""

    def test_css_has_chart_row(self) -> None:
        css = _read("dashboard.css")
        assert ".chart-row" in css

    def test_css_has_topic_list(self) -> None:
        css = _read("dashboard.css")
        assert ".topic-list" in css
        assert ".topic-item" in css

    def test_css_has_explorer_styles(self) -> None:
        css = _read("dashboard.css")
        assert ".explorer-filters" in css
        assert ".explorer-input" in css

    def test_css_has_modal_styles(self) -> None:
        css = _read("dashboard.css")
        assert ".modal" in css
        assert ".modal-content" in css
        assert ".modal-body" in css

    def test_css_has_live_badge_style(self) -> None:
        css = _read("dashboard.css")
        assert ".live-badge" in css
        assert "@keyframes pulse" in css

    def test_css_has_responsive_breakpoint(self) -> None:
        css = _read("dashboard.css")
        assert "@media (max-width: 768px)" in css
