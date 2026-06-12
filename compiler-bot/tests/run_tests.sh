#!/bin/sh
# ============================================================================
# run_tests.sh - Suite de tests para el bot RECPL
# ============================================================================
#
# PRUEBAS:
#   1. Sintaxis de todos los scripts (bash -n)
#   2. Preprocesador
#   3. Lexer
#   4. Parser
#   5. Pipeline completo (preprocess → lexer → parser → semantic → IR → synthesis)
#   6. Scaffolding (generacion de archivos desde templates)
#   7. LOOP (batch mode)
#   8. Persistencia de tabla de simbolos
#   9. Manejo de errores
# ============================================================================

PASS=0
FAIL=0
TESTS_DIR="$(dirname "$0")"
BOT_DIR="${TESTS_DIR}/.."

assert() {
    _name="$1"
    _got="$2"
    _exp="$3"
    if [ "$_got" = "$_exp" ]; then
        echo "  PASS: $_name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $_name"
        echo "    esperado: $_exp"
        echo "    obtenido: $_got"
        FAIL=$((FAIL + 1))
    fi
}

assert_contains() {
    _name="$1"
    _haystack="$2"
    _needle="$3"
    if echo "$_haystack" | grep -q "$_needle"; then
        echo "  PASS: $_name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $_name"
        echo "    patrón no encontrado: $_needle"
        echo "    en: $_haystack"
        FAIL=$((FAIL + 1))
    fi
}

assert_exit() {
    _name="$1"
    _code="$2"
    _exp="$3"
    if [ "$_code" -eq "$_exp" ]; then
        echo "  PASS: $_name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $_name (exit code: $_code, esperado: $_exp)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================="
echo "RECPL Compiler Bot - Suite de Tests"
echo "=========================================="
echo

# === Test 1: Syntax validation ===
echo "--- Test 1: Syntax validation (bash -n) ---"

scripts="
  ${BOT_DIR}/frontend/preprocessor.sh
  ${BOT_DIR}/frontend/lexer.sh
  ${BOT_DIR}/frontend/parser.sh
  ${BOT_DIR}/frontend/semantic.sh
  ${BOT_DIR}/frontend/router.sh
  ${BOT_DIR}/frontend/llm_classifier.sh
  ${BOT_DIR}/middleend/ir_generator.sh
  ${BOT_DIR}/middleend/llm_ir_mapper.sh
  ${BOT_DIR}/backend/synthesis.sh
  ${BOT_DIR}/backend/scaffold.sh
  ${BOT_DIR}/providers/provider_common.sh
  ${BOT_DIR}/providers/claude.sh
  ${BOT_DIR}/providers/openai.sh
  ${BOT_DIR}/recpl.sh
  ${TESTS_DIR}/test_router.sh
"

for script in $scripts; do
    name=$(basename "$script")
    if bash -n "$script" 2>/dev/null; then
        echo "  PASS: syntax $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: syntax $name"
        FAIL=$((FAIL + 1))
    fi
done
echo

# === Test 2: Preprocesador ===
echo "--- Test 2: Preprocesador ---"

result=$("${BOT_DIR}/frontend/preprocessor.sh" "  CREA   MODULO!! " 2>/dev/null)
assert "trim + lowercase + collapse punct" "$result" "crea   modulo"

result=$("${BOT_DIR}/frontend/preprocessor.sh" "Crea. Modulo." 2>/dev/null)
assert "split sentences" "$result" "crea
modulo"

result=$("${BOT_DIR}/frontend/preprocessor.sh" "" 2>/dev/null)
assert "empty input" "$result" ""

echo

# === Test 3: Lexer ===
echo "--- Test 3: Lexer ---"

result=$("${BOT_DIR}/frontend/lexer.sh" "crea modulo pagos en nestjs" 2>/dev/null)
tokens=$(echo "$result" | wc -l)
assert "token count (5 tokens)" "$tokens" "5"

assert_contains "ACTION_CREATE token" "$result" "ACTION_CREATE"
assert_contains "MODULE token" "$result" "MODULE"
assert_contains "ENTITY token" "$result" "ENTITY"
assert_contains "PREP_IN token" "$result" "PREP_IN"
assert_contains "TECH_NESTJS token" "$result" "TECH_NESTJS"

result=$("${BOT_DIR}/frontend/preprocessor.sh" "CREA" 2>/dev/null)
result=$("${BOT_DIR}/frontend/lexer.sh" "$result" 2>/dev/null)
assert_contains "case insensitive (via preprocessor)" "$result" "crea"

result=$("${BOT_DIR}/frontend/lexer.sh" "crear modulo" 2>/dev/null)
assert_contains "maximal munch (crear > crea)" "$result" "crear"

echo

# === Test 4: Parser ===
echo "--- Test 4: Parser ---"

result=$(echo '{"type":"ACTION_CREATE","lexeme":"crea","position":{"line":1,"col":1}}
{"type":"MODULE","lexeme":"modulo","position":{"line":1,"col":6}}
{"type":"ENTITY","lexeme":"Payments","position":{"line":1,"col":13}}
{"type":"PREP_IN","lexeme":"en","position":{"line":1,"col":22}}
{"type":"TECH_NESTJS","lexeme":"NestJS","position":{"line":1,"col":25}}' | "${BOT_DIR}/frontend/parser.sh" 2>/dev/null)
assert_contains "AST tiene accion CREATE" "$result" '"accion":"CREATE"'
assert_contains "AST tiene tipo module" "$result" '"tipo":"module"'
assert_contains "AST tiene entidad Payments" "$result" '"Payments"'
assert_contains "AST tiene tech" "$result" '"tech"'

result=$(echo '{"type":"ACTION_READ","lexeme":"listar","position":{"line":1,"col":1}}
{"type":"ENTITY","lexeme":"users","position":{"line":1,"col":8}}' | "${BOT_DIR}/frontend/parser.sh" 2>/dev/null)
assert_contains "AST entity directa" "$result" '"tipo":"entity"'

echo

# === Test 5: Pipeline completo ===
echo "--- Test 5: Pipeline completo ---"

input=$("${BOT_DIR}/frontend/preprocessor.sh" "crea un modulo de pagos en nestjs" 2>/dev/null)
full_out=$( "${BOT_DIR}/frontend/lexer.sh" "$input" 2>/dev/null | "${BOT_DIR}/frontend/parser.sh" 2>/dev/null | "${BOT_DIR}/frontend/semantic.sh" 2>/dev/null | "${BOT_DIR}/middleend/ir_generator.sh" 2>/dev/null | "${BOT_DIR}/backend/synthesis.sh" 2>/dev/null)
assert_contains "respuesta tiene tipo_respuesta" "$full_out" "tipo_respuesta"
assert_contains "respuesta tiene mensaje" "$full_out" "mensaje"
assert_contains "respuesta tiene payload" "$full_out" "payload"
assert_contains "accion scaffold" "$full_out" "scaffold:module"

input2=$("${BOT_DIR}/frontend/preprocessor.sh" "crea modulo payments" 2>/dev/null)
full_out2=$( "${BOT_DIR}/frontend/lexer.sh" "$input2" 2>/dev/null | "${BOT_DIR}/frontend/parser.sh" 2>/dev/null | "${BOT_DIR}/frontend/semantic.sh" 2>/dev/null | "${BOT_DIR}/middleend/ir_generator.sh" 2>/dev/null | "${BOT_DIR}/backend/synthesis.sh" 2>/dev/null)
assert_contains "sin tech: template generic" "$full_out2" "module-generic"

echo

# === Test 6: Errores semanticos ===
echo "--- Test 6: Errores semanticos ---"

# READ non-existent should fail
input3=$("${BOT_DIR}/frontend/preprocessor.sh" "mostrar nonexistent" 2>/dev/null)
"${BOT_DIR}/frontend/lexer.sh" "$input3" 2>/dev/null | "${BOT_DIR}/frontend/parser.sh" 2>/dev/null | "${BOT_DIR}/frontend/semantic.sh" 2>/dev/null
assert_exit "READ undefined entity" $? 1

# Invalid tech should fail
echo '{"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["x"]},"tech":"BadTech"}' | "${BOT_DIR}/frontend/semantic.sh" 2>/dev/null
assert_exit "invalid tech" $? 1

echo

# === Test 7: LOOP batch mode ===
echo "--- Test 7: LOOP batch mode ---"

loop_out=$(printf "crea modulo usuarios en nestjs\nmostrar usuarios\nquit\n" | "${BOT_DIR}/recpl.sh" 2>/dev/null)
assert_contains "LOOP: CREATE" "$loop_out" "Generando"
assert_contains "LOOP: READ" "$loop_out" "Mostrando"
assert_contains "LOOP: scaffold" "$loop_out" "scaffold:module"

# Error recovery: error should not break the loop
loop_out2=$(printf "mostrar nonexistent\ncrea modulo test\nquit\n" | "${BOT_DIR}/recpl.sh" 2>/dev/null)
lines=$(echo "$loop_out2" | grep -c ".")
assert "LOOP: error recovery (at least 2 outputs)" "$(echo "$loop_out2" | grep -c "tipo_respuesta")" "2"

echo

# === Test 8: Scaffolding ===
echo "--- Test 8: Scaffolding ---"

template_dir="${BOT_DIR}/templates/module-nestjs"
scaffold_out=$("${BOT_DIR}/backend/scaffold.sh" "$template_dir" "TestModule" "/tmp/recpl_test_scaffold" 2>/dev/null)
assert_contains "scaffold genera archivos" "$scaffold_out" "controller"
assert_contains "scaffold genera module.ts" "$scaffold_out" "module.ts"
file_exists=0
ls /tmp/recpl_test_scaffold/*.module.ts >/dev/null 2>&1 && file_exists=1
assert_exit "scaffold files exist on disk" "$file_exists" "1"
rm -rf /tmp/recpl_test_scaffold

echo

# === Test 9: Persistencia de estado ===
echo "--- Test 9: Persistencia de estado ---"

state_dir="/tmp/recpl_test_state"
mkdir -p "$state_dir"
echo '{"tipo":"Comando","accion":"CREATE","objetivo":{"tipo":"module","entidades":["persist"]},"tech":"nestjs"}' | RECPL_STATE_DIR="$state_dir" "${BOT_DIR}/frontend/semantic.sh" 2>/dev/null > /dev/null
echo '{"tipo":"Comando","accion":"READ","objetivo":{"tipo":"entity","entidades":["persist"]},"tech":null}' | RECPL_STATE_DIR="$state_dir" "${BOT_DIR}/frontend/semantic.sh" 2>/dev/null
assert_exit "persist: READ after CREATE" $? 0
rm -rf "$state_dir"

echo

# === Test 11: Router (deterministic path) ===
echo "--- Test 11: Router ---"

result=$(RECPL_LLM_MODE=deterministic \
    RECPL_STATE_DIR="/tmp/recpl_test_router_$$" \
    "${BOT_DIR}/frontend/router.sh" "crea modulo pagos en nestjs" 2>/dev/null)
assert_contains "router: scaffold action" "$result" "scaffold"
assert_contains "router: module type" "$result" "module"
assert_contains "router: nombre pagos" "$result" "pagos"

result=$(RECPL_LLM_MODE=llm \
    RECPL_STATE_DIR="/tmp/recpl_test_router_$$" \
    "${BOT_DIR}/frontend/router.sh" "test" 2>/dev/null)
assert_contains "router: LLM mode error" "$result" "error"

result=$("${BOT_DIR}/frontend/router.sh" "" 2>/dev/null)
assert_contains "router: empty input error" "$result" "error"

rm -rf "/tmp/recpl_test_router_$$"

echo

# === Test 10: Executables ===
echo "--- Test 10: Scripts executables ---"

for script in $scripts; do
    name=$(basename "$script")
    if [ -x "$script" ]; then
        echo "  PASS: $name es ejecutable"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name no es ejecutable"
        FAIL=$((FAIL + 1))
    fi
done

echo

# === Test 12: Composite pattern (source/exec) ===
echo "--- Test 12: Composite pattern (source/exec) ---"

# Test 12a: source con archivo valido
seed_file="/tmp/recpl_test_source_valid_$$"
echo "crea modulo validmod en nestjs" > "$seed_file"
result=$(printf "source %s\nquit\n" "$seed_file" | "${BOT_DIR}/recpl.sh" 2>/dev/null)
assert_contains "source: archivo valido" "$result" "scaffold:module"
rm -f "$seed_file"

# Test 12b: source con archivo inexistente
result=$(printf "source /tmp/nonexistent_%d.txt\nquit\n" "$$" | "${BOT_DIR}/recpl.sh" 2>/dev/null)
assert_contains "source: archivo inexistente" "$result" "Error: archivo no encontrado"

# Test 12c: exec con instruccion valida
result=$(printf "exec crea modulo execmod en nestjs\nquit\n" | "${BOT_DIR}/recpl.sh" 2>/dev/null)
assert_contains "exec: instruccion valida" "$result" "scaffold:module"

# Test 12d: exec sin argumento
result=$(printf "exec\nquit\n" | "${BOT_DIR}/recpl.sh" 2>/dev/null)
assert_contains "exec: sin argumento" "$result" "Uso: exec <instruccion>"

# Test 12e: Estado compartido entre source y comandos manuales
seed_file2="/tmp/recpl_test_shared_$$"
echo "crea modulo sharedmod en nestjs" > "$seed_file2"
result=$(printf "source %s\nmostrar sharedmod\nquit\n" "$seed_file2" | "${BOT_DIR}/recpl.sh" 2>/dev/null)
assert_contains "estado compartido: CREATE via source" "$result" "scaffold:module"
assert_contains "estado compartido: READ manual" "$result" "Mostrando"
rm -f "$seed_file2"

echo

# === Resumen ===
echo "=========================================="
echo "RESUMEN: $PASS pasaron, $FAIL fallaron"
echo "=========================================="

# Cleanup generated modules
rm -rf "${BOT_DIR}/../modules"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
