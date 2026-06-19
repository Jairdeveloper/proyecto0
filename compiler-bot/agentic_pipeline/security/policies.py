"""Security policies — blocked patterns for BanditScanner."""

from __future__ import annotations

import re

BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\beval\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"\bos\.system\s*\("),
    re.compile(r"\bsubprocess\.call\s*\("),
    re.compile(r"\bpickle\.loads\s*\("),
    re.compile(r"\b__import__\s*\("),
]
"""Regex patterns for dangerous code constructs that should never appear
in generated code. Matches cases like eval(...), exec(...), os.system(...),
subprocess.call(...), pickle.loads(...), __import__(...)."""
