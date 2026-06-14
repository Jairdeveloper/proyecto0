#!/bin/sh
# ============================================================================
# config.sh - Configuracion del agente Proyecto0(RECPL)
# ============================================================================
#
# Define variables de entorno con valores por defecto.
# Cargar al inicio de agent.sh: . "$AGENT_DIR/config.sh"
# ============================================================================

# --- Directorio base del agente ---
AGENT_DIR="$(dirname "$0")"

# --- Modo de operacion ---
# auto:          intenta RECPL deterministico → si falla, usa LLM
# llm:           envia directamente al LLM, saltea RECPL
# deterministic: solo RECPL via bridge, sin LLM
AGENT_LLM_MODE="${AGENT_LLM_MODE:-auto}"

# --- Proveedor LLM preferido ---
# apifreellm: gratuito via API externa (requiere API_FREE_KEY)
AGENT_LLM_PROVIDER="${AGENT_LLM_PROVIDER:-apifreellm}"

# --- Capa LLM ---
# free | paid | auto (ver propuesta 046)
AGENT_LLM_TIER="${AGENT_LLM_TIER:-auto}"

# --- Memoria ---
AGENT_MEMORY_DIR="${AGENT_MEMORY_DIR:-/tmp/agent_memory}"

# --- Logging ---
AGENT_LOG_FILE="${AGENT_LOG_FILE:-/tmp/agent.log}"
AGENT_LOG_LEVEL="${AGENT_LOG_LEVEL:-info}"

# --- Version ---
AGENT_VERSION="1.0.0"

# --- Emoji prefix ---
AGENT_PREFIX="🤖"
