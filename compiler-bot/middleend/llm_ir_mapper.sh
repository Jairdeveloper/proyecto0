# ============================================================================
# llm_ir_mapper.sh - Mapea tool call de LLM a IR.json canonico
# ============================================================================
#
# PROPOSITO:
#   Convierte una tool call del LLM (formato interno comun) al mismo
#   formato IR.json que produce ir_generator.sh (pipeline deterministico).
#   Esto asegura que synthesis.sh y scaffold.sh funcionen igual
#   independientemente de si la instruccion vino del LLM o del pipeline
#   deterministico.
#
# USO:
#   echo '{"tool":"scaffold_module","nombre":"Pagos","tech":"NestJS"}' \
#     | llm_ir_mapper.sh
#   → {"accion":"scaffold","tipo":"module","nombre":"Pagos","tech":"NestJS"}
#
# DEPENDENCIAS:
#   jq
# ============================================================================

# ============================================================================
# SECTION: Mapper principal
# ============================================================================

llm_ir_mapper() {
    input=$(cat)

    tool=$(echo "$input" | jq -r '.tool // ""')
    nombre=$(echo "$input" | jq -r '.nombre // ""')
    tech=$(echo "$input" | jq -r '.tech // ""')

    case "$tool" in
        scaffold_module)
            jq -n \
                --arg accion "scaffold" \
                --arg tipo "module" \
                --arg nombre "$nombre" \
                --arg tech "$tech" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre, tech: $tech}'
            ;;
        scaffold_entity)
            jq -n \
                --arg accion "scaffold" \
                --arg tipo "entity" \
                --arg nombre "$nombre" \
                --arg tech "$tech" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre, tech: $tech}'
            ;;
        delete_module)
            jq -n \
                --arg accion "delete" \
                --arg tipo "module" \
                --arg nombre "$nombre" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre}'
            ;;
        read_module)
            jq -n \
                --arg accion "read" \
                --arg tipo "module" \
                --arg nombre "$nombre" \
                '{accion: $accion, tipo: $tipo, nombre: $nombre}'
            ;;
        clarify|respond)
            mensaje=$(echo "$input" | jq -r '.mensaje // .pregunta // ""')
            jq -n \
                --arg accion "$tool" \
                --arg mensaje "$mensaje" \
                '{accion: $accion, mensaje: $mensaje}'
            ;;
        *)
            echo "{\"accion\":\"error\",\"mensaje\":\"Tool desconocida: $tool\"}"
            return 1
            ;;
    esac
}

# ============================================================================
# SECTION: Entry point
# ============================================================================

llm_ir_mapper
