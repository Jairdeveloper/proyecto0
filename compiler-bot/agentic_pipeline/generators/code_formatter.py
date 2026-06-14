from __future__ import annotations

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeFormatter:
    """Format code files using external formatters with fallback."""

    FORMATTERS: dict[str, list[str]] = {
        ".ts": ["npx", "prettier", "--write"],
        ".tsx": ["npx", "prettier", "--write"],
        ".js": ["npx", "prettier", "--write"],
        ".jsx": ["npx", "prettier", "--write"],
        ".css": ["npx", "prettier", "--write"],
        ".json": ["npx", "prettier", "--write"],
        ".yml": ["npx", "prettier", "--write"],
        ".yaml": ["npx", "prettier", "--write"],
        ".py": ["black"],
        ".prisma": [],
    }

    def format_file(self, filepath: Path) -> bool:
        ext = filepath.suffix
        cmd_template = self.FORMATTERS.get(ext)
        if not cmd_template:
            return False

        cmd = [*cmd_template, str(filepath)]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return True
        except FileNotFoundError:
            logger.warning("Formatter not found for %s: %s", ext, cmd[0])
            return False
        except subprocess.TimeoutExpired:
            logger.warning("Formatter timed out for %s", filepath)
            return False
        except Exception:
            logger.exception("Formatter failed for %s", filepath)
            return False

    def format_directory(
        self,
        directory: Path,
        extensions: list[str] | None = None,
    ) -> int:
        count = 0
        for filepath in directory.rglob("*"):
            if not filepath.is_file():
                continue
            if extensions and filepath.suffix not in extensions:
                continue
            if self.format_file(filepath):
                count += 1
        return count
