#!/usr/bin/env python3
"""Normalize YAML frontmatter field casing across all .md files in docs/.

Rules:
  - area: lowercase (strip quotes)
  - type: lowercase (strip quotes)
  - module: lowercase (strip quotes)
  - status, version, tags, summary, keywords, changelog, id: leave as-is
"""

import os
import re
import sys

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')

FIELDS_TO_NORMALIZE = {'area', 'type', 'module'}
FIELD_PATTERN = re.compile(r'^(?P<key>' + '|'.join(FIELDS_TO_NORMALIZE) + r'):\s*(?P<value>.+)$')


def normalize_value(value: str) -> str:
    value = value.strip()
    value = value.strip('"').strip("'")
    return value.lower()


def process_file(filepath: str) -> bool:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines or not lines[0].startswith('---'):
        return False

    # Find frontmatter boundaries
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].startswith('---'):
            end_idx = i
            break

    if end_idx is None:
        return False

    modified = False
    for i in range(1, end_idx):
        match = FIELD_PATTERN.match(lines[i])
        if match:
            original = lines[i]
            new_value = normalize_value(match.group('value'))
            new_line = f"{match.group('key')}: {new_value}\n"
            if new_line != original:
                lines[i] = new_line
                modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return modified


def main():
    modified_count = 0
    error_count = 0

    for root, dirs, files in os.walk(DOCS_DIR):
        # Skip contrib/ directory
        dirs[:] = [d for d in dirs if d not in ('contrib',)]
        for fname in files:
            if not fname.endswith('.md'):
                continue
            filepath = os.path.join(root, fname)
            try:
                if process_file(filepath):
                    relpath = os.path.relpath(filepath, DOCS_DIR)
                    print(f"  MODIFIED: {relpath}")
                    modified_count += 1
            except Exception as e:
                relpath = os.path.relpath(filepath, DOCS_DIR)
                print(f"  ERROR: {relpath}: {e}", file=sys.stderr)
                error_count += 1

    print(f"\nDone. {modified_count} files modified, {error_count} errors.")


if __name__ == '__main__':
    main()
