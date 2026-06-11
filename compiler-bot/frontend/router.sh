# ============================================================================
# router.sh - Router inteligente del pipeline RECPL
# ============================================================================
#
# PROPOSITO:
#   Decide si una instruccion debe procesarse con el pipeline deterministico
#   (rapido, sin costo) o con el LLM (flexible, con costo).
#
#   Implementa el patron Strategy: la estrategia de ruteo se selecciona
#   mediante la variable RECPL_LLM_MODE o el flag --llm.
#
# ESTRATEGIAS:
#   deterministic-first  (default): intenta pipeline deterministico,
#                                    si falla → fallback a LLM
#   llm-first:                       envia directamente al LLM,
#                                    evita el pipeline deterministico
#   deterministic-only:              solo deterministico, nunca LLM
#
# USO:
#   router "instruccion del usuario"
#   → IR.json (de cualquier camino)
#
# DEPENDENCIAS:
#   frontend/llm_classifier.sh
#   frontend/preprocessor.sh, lexer.sh, parser.sh, semantic.sh
#   middleend/ir_generator.sh
#
# VARIABLES DE ENTORNO:
#   RECPL_LLM_MODE       (auto|llm|deterministic, default: auto)
#   RECPL_LLM_PROVIDER   (claude|openai, default: claude)
#   RECPL_STATE_DIR      (directorio de estado persistente)
# ============================================================================

SCRIPT_DIR="$(dirname "$0")"

# ============================================================================
# SECTION: Estrategia de ruteo
# ============================================================================

# --- Determinar si la instruccion es candidata para pipeline deterministico ---
# Retorna 0 si es candidata, 1 si debe ir al LLM
is_deterministic_candidate() {
    instruction="$1"

    # Modo explicitamente LLM
    [ "${RECPL_LLM_MODE:-auto}" = "llm" ] && return 1

    # Modo deterministic-only
    [ "${RECPL_LLM_MODE:-auto}" = "deterministic" ] && return 0

    # Modo auto: criterios para deterministico
    # Criterio 1: instruccion corta (<= 10 palabras)
    word_count=$(echo "$instruction" | wc -w | tr -d ' ')
    [ "$word_count" -gt 10 ] && return 1

    # Criterio 2: contiene palabras conocidas por el lexer
    case "$instruction" in
        *crea*|*crear*|*genera*|*elimina*|*borra*|*muestra*|*mostrar*|*listar*|*modifica*)
            return 0
            ;;
    esac

    # Sin match claro → delegar al LLM
    return 1
}

# ============================================================================
# SECTION: Pipeline deterministico
# ============================================================================

# --- Ejecutar pipeline deterministico y retornar IR.json ---
run_deterministic() {
    instruction="$1"
    state_dir="${RECPL_STATE_DIR:-/tmp/recpl_state_$$}"

    # Asegurar que el directorio de estado existe
    mkdir -p "$state_dir"

    # Preprocesar
    preprocessed=$(FRONTEND_DIR="$SCRIPT_DIR" "$SCRIPT_DIR/preprocessor.sh" "$instruction" 2>/dev/null)
    [ -z "$preprocessed" ] && preprocessed="$instruction"

    # Lexer
    tokens=$(FRONTEND_DIR="$SCRIPT_DIR" "$SCRIPT_DIR/lexer.sh" "$preprocessed" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$tokens" ]; then
        return 1
    fi

    # Parser
    ast=$(echo "$tokens" | "$SCRIPT_DIR/parser.sh" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$ast" ]; then
        return 1
    fi

    # Semantic
    validated=$(echo "$ast" | RECPL_STATE_DIR="$state_dir" "$SCRIPT_DIR/semantic.sh" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$validated" ]; then
        return 1
    fi

    # IR generator
    ir=$(echo "$validated" | "$SCRIPT_DIR/../middleend/ir_generator.sh" 2>/dev/null)
    if [ $? -ne 0 ] || [ -z "$ir" ]; then
        return 1
    fi

    echo "$ir"
    return 0
}

# ============================================================================
# SECTION: Router principal
# ============================================================================

# --- Punto de entrada del router ---
# Retorna IR.json o {"accion":"respond",...} o {"accion":"error",...}
router() {
    instruction="$1"

    if [ -z "$instruction" ]; then
        echo "{\"accion\":\"error\",\"mensaje\":\"Instruccion vacia\"}"
        return 1
    fi

    if is_deterministic_candidate "$instruction"; then
        # Intentar pipeline deterministico
        result=$(run_deterministic "$instruction")
        if [ $? -eq 0 ] && [ -n "$result" ]; then
            echo "$result"
            return 0
        fi

        # Fallback a LLM si el deterministico falla
        if [ "${RECPL_LLM_MODE:-auto}" != "deterministic" ]; then
            if [ -f "$SCRIPT_DIR/llm_classifier.sh" ]; then
                result=$(RECPL_LLM_PROVIDER="${RECPL_LLM_PROVIDER:-claude}" \
                    "$SCRIPT_DIR/llm_classifier.sh" 2>/dev/null <<LLM_INPUT
$instruction
LLM_INPUT
)
                if [ $? -eq 0 ] && [ -n "$result" ]; then
                    echo "$result"
                    return 0
                fi
            fi
        fi

        # Si no hay LLM disponible ni deterministico funciona
        echo "{\"accion\":\"error\",\"mensaje\":\"La instruccion no pudo procesarse ni con el pipeline deterministico ni con LLM\"}"
        return 1
    else
        # Ruta LLM directa
        if [ -f "$SCRIPT_DIR/llm_classifier.sh" ]; then
            result=$(RECPL_LLM_PROVIDER="${RECPL_LLM_PROVIDER:-claude}" \
                "$SCRIPT_DIR/llm_classifier.sh" 2>/dev/null <<LLM_INPUT
$instruction
LLM_INPUT
)
            if [ $? -eq 0 ] && [ -n "$result" ]; then
                echo "$result"
                return 0
            fi
        fi

        echo "{\"accion\":\"error\",\"mensaje\":\"Modo LLM seleccionado pero llm_classifier.sh no esta disponible o fallo\"}"
        return 1
    fi
}

# ============================================================================
# SECTION: Entry point (standalone)
# ============================================================================

if echo "$0" | grep -q "router.sh"; then
    instruction="$1"
    router "$instruction"
fi
