"""Test package for agentic_pipeline."""

import sys
from pathlib import Path

# Ensure compiler-bot/ is on sys.path so agentic_pipeline is importable.
# tests/__init__.py path: .../compiler-bot/agentic_pipeline/tests/__init__.py
# We need .../compiler-bot/ which is parent.parent
_src = str(Path(__file__).resolve().parent.parent.parent)
if _src not in sys.path:
    sys.path.insert(0, _src)
