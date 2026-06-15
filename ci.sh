#!/usr/bin/env bash
# CI script for RECPL Compiler Bot v2.0
set -u

PIPELINE_DIR="compiler-bot/agentic_pipeline"
FAIL=0

pass() { printf "\033[0;32m[PASS]\033[0m %s\n" "$1"; }
fail() { printf "\033[0;31m[FAIL]\033[0m %s\n" "$1"; FAIL=1; }

echo "=== CI: RECPL Compiler Bot v2.0 ==="
echo ""

# Python syntax check
echo "--- Python syntax check ---"
if python3 -c "
import py_compile, sys, os
root = '$PIPELINE_DIR'
errors = 0
for dirpath, _, filenames in os.walk(root):
    for fn in filenames:
        if fn.endswith('.py'):
            path = os.path.join(dirpath, fn)
            try:
                py_compile.compile(path, doraise=True)
            except py_compile.PyCompileError as e:
                print(f'  ERROR: {path}: {e}')
                errors += 1
sys.exit(errors)
"; then
    pass "Python syntax check"
else
    fail "Python syntax check"
fi

# Ruff linter
echo ""
echo "--- Ruff check ---"
if ruff check "$PIPELINE_DIR"; then
    pass "Ruff check"
else
    fail "Ruff check"
fi

# Pytest
echo ""
echo "--- Pytest ---"
if python3 -m pytest "$PIPELINE_DIR/tests/" -q --tb=short 2>&1 | tail -5; then
    pass "Pytest"
else
    fail "Pytest"
fi

# VERSION file
echo ""
echo "--- VERSION file ---"
if [ -f VERSION ] && [ -s VERSION ]; then
    pass "VERSION file exists: $(cat VERSION)"
else
    fail "VERSION file missing or empty"
fi

echo ""
echo "=== CI Summary ==="
if [ "$FAIL" -eq 0 ]; then
    printf "\033[0;32m%s\033[0m\n" "All checks passed"
    exit 0
else
    printf "\033[0;31m%s\033[0m\n" "Some checks failed"
    exit 1
fi
