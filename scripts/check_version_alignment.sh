#!/usr/bin/env bash
# check_version_alignment.sh — Verify VERSION, pyproject.toml, CHANGELOG.md match
#
# Usage: ./scripts/check_version_alignment.sh
# Exit 0 if all three match, 1 otherwise.
# No set -e, no eval.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

read_version_file() {
    local path="$1"
    local label="$2"
    local version

    if [ ! -f "$path" ]; then
        echo "FAIL: $label — file not found: $path"
        return 1
    fi

    version=$(tr -d '[:space:]' < "$path")
    if [ -z "$version" ]; then
        echo "FAIL: $label — file is empty: $path"
        return 1
    fi

    echo "$version"
}

read_pyproject_version() {
    local path="$1"
    local label="$2"
    local version

    if [ ! -f "$path" ]; then
        echo "FAIL: $label — file not found: $path"
        return 1
    fi

    version=$(sed -n 's/^version = "\(.*\)"/\1/p' "$path" | tr -d '[:space:]')
    if [ -z "$version" ]; then
        echo "FAIL: $label — could not extract version from: $path"
        return 1
    fi

    echo "$version"
}

read_changelog_version() {
    local path="$1"
    local label="$2"
    local version

    if [ ! -f "$path" ]; then
        echo "FAIL: $label — file not found: $path"
        return 1
    fi

    version=$(awk '/^## \[/{gsub(/[\[\]]/,""); print $2; exit}' "$path" | tr -d '[:space:]')
    if [ -z "$version" ]; then
        echo "FAIL: $label — could not extract version from: $path"
        return 1
    fi

    echo "$version"
}

echo "=== Version Alignment Check ==="
echo ""

version_file=$(read_version_file "$PROJECT_ROOT/VERSION" "VERSION") || FAIL=1
pyproject_ver=$(read_pyproject_version "$PROJECT_ROOT/compiler-bot/agentic_pipeline/pyproject.toml" "pyproject.toml") || FAIL=1
changelog_ver=$(read_changelog_version "$PROJECT_ROOT/CHANGELOG.md" "CHANGELOG.md") || FAIL=1

if [ "$FAIL" -ne 0 ]; then
    echo ""
    echo "FAIL: One or more versions could not be read."
    exit 1
fi

echo "  VERSION:        $version_file"
echo "  pyproject.toml: $pyproject_ver"
echo "  CHANGELOG.md:   $changelog_ver"
echo ""

if [ "$version_file" != "$pyproject_ver" ]; then
    echo "FAIL: VERSION ($version_file) != pyproject.toml ($pyproject_ver)"
    FAIL=1
fi

if [ "$version_file" != "$changelog_ver" ]; then
    echo "FAIL: VERSION ($version_file) != CHANGELOG.md ($changelog_ver)"
    FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
    echo "OK: All versions match at $version_file."
    exit 0
fi

exit 1
