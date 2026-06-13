#!/bin/sh
# ============================================================================
# agent-robot.sh - Entrypoint global para el agente Proyecto0(RECPL)
# ============================================================================
#
# Delegado en agent-robot/agent.sh
# ============================================================================

SCRIPT_DIR="$(dirname "$0")"
exec "$SCRIPT_DIR/agent-robot/agent.sh" "$@"
