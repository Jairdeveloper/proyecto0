#!/usr/bin/env bash
# demo.sh — RECPL demo: 3 example prompts
# Usage: bash scripts/demo.sh

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTIC="$PROJECT_DIR/compiler-bot/agentic"
EXAMPLES_DIR="$PROJECT_DIR/output/demo"

mkdir -p "$EXAMPLES_DIR"

echo "========================================"
echo "  RECPL — Natural Language to Code"
echo "  Demo Pipeline v2.0"
echo "========================================"
echo ""

# --- Demo 1: NestJS module ---
echo ">>> Demo 1: NestJS module"
echo '    Prompt: "crea un modulo de pagos en NestJS"'
echo ""
"$AGENTIC" --prompt "crea un modulo de pagos en NestJS" --output "$EXAMPLES_DIR/demo1" 2>/dev/null
echo ""
echo "    Output: $EXAMPLES_DIR/demo1/"
ls "$EXAMPLES_DIR/demo1/" 2>/dev/null || echo "    (no files generated)"
echo ""

# --- Demo 2: Prisma entity ---
echo ">>> Demo 2: Prisma entity"
echo '    Prompt: "crea una entidad Usuario con nombre email y edad en Prisma"'
echo ""
"$AGENTIC" --prompt "crea una entidad Usuario con nombre email y edad en Prisma" --output "$EXAMPLES_DIR/demo2" 2>/dev/null
echo ""
echo "    Output: $EXAMPLES_DIR/demo2/"
ls "$EXAMPLES_DIR/demo2/" 2>/dev/null || echo "    (no files generated)"
echo ""

# --- Demo 3: Full stack ---
echo ">>> Demo 3: Full stack"
echo '    Prompt: "crea un sistema de autenticacion con login y registro"'
echo ""
"$AGENTIC" --prompt "crea un sistema de autenticacion con login y registro" --output "$EXAMPLES_DIR/demo3" 2>/dev/null
echo ""
echo "    Output: $EXAMPLES_DIR/demo3/"
ls "$EXAMPLES_DIR/demo3/" 2>/dev/null || echo "    (no files generated)"
echo ""

echo "========================================"
echo "  Demo complete."
echo "  Run 'docker build -t recpl .' to"
echo "  build the containerized version."
echo "========================================"
