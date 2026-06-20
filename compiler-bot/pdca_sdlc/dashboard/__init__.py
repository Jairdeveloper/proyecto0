"""PDCA-sdlc dashboard — lightweight SDLC project visualization.

Zero external dependencies. Uses stdlib http.server + vanilla JS.
"""

from pdca_sdlc.dashboard.app import create_server, run_server
from pdca_sdlc.dashboard.service import SdlcDashboardService

__all__ = [
    "SdlcDashboardService",
    "create_server",
    "run_server",
]
