#!/usr/bin/env bash
# pipeline_stats.sh — Minimal dashboard for pipeline metrics
# Reads from MetricsStore JSON fallback dir (/tmp/agentic_metrics_json_fallback/)
# Usage: ./scripts/pipeline_stats.sh [--json]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${METRICS_DIR:-/tmp/agentic_metrics_json_fallback}"
JSON_FLAG=0

if [ "${1:-}" = "--json" ]; then
    JSON_FLAG=1
fi

if [ ! -d "$DATA_DIR" ]; then
    echo "No metrics data found at $DATA_DIR"
    echo "Run the pipeline first to generate metrics."
    exit 1
fi

total_runs=0
total_errors=0
declare -A stage_runs
declare -A stage_errors

for f in "$DATA_DIR"/*.json; do
    [ -f "$f" ] || continue
    stage_name=$(basename "$f" .json)
    entries=$(python3 -c "
import json
with open('$f') as fh:
    data = json.load(fh)
runs = len(data)
errs = sum(1 for e in data if e.get('metrics', {}).get('success') is False or e.get('metrics', {}).get('errors', 0) > 0)
print(f'{runs}|{errs}')
")
    runs="${entries%|*}"
    errs="${entries#*|}"
    stage_runs["$stage_name"]=$runs
    stage_errors["$stage_name"]=$errs
    total_runs=$((total_runs + runs))
    total_errors=$((total_errors + errs))
done

if [ "$JSON_FLAG" -eq 1 ]; then
    echo "{"
    echo "  \"total_runs\": $total_runs,"
    echo "  "total_errors": $total_errors,"
    echo "  \"success_rate\": \"$(printf '%.1f' "$(echo "scale=4; ($total_runs - $total_errors) * 100 / $total_runs" | bc 2>/dev/null || echo 0)" )%\","
    echo "  \"stages\": {"
    first=1
    for stage in "${!stage_runs[@]}"; do
        [ "$first" -eq 1 ] && first=0 || echo ","
        rate=$(printf '%.1f' "$(echo "scale=4; (${stage_runs[$stage]} - ${stage_errors[$stage]}) * 100 / ${stage_runs[$stage]}" | bc 2>/dev/null || echo 0)")
        echo -n "    \"$stage\": { \"runs\": ${stage_runs[$stage]}, \"errors\": ${stage_errors[$stage]}, \"success_rate\": \"$rate%\" }"
    done
    echo ""
    echo "  }"
    echo "}"
else
    echo "=== Pipeline Stats Dashboard ==="
    echo "Total runs:  $total_runs"
    echo "Total errors: $total_errors"
    if [ "$total_runs" -gt 0 ]; then
        rate=$(echo "scale=1; ($total_runs - $total_errors) * 100 / $total_runs" | bc)
        echo "Success rate: $rate%"
    fi
    echo ""
    echo "Per-stage:"
    printf "  %-25s %8s %8s %10s\n" "Stage" "Runs" "Errors" "Success%"
    for stage in "${!stage_runs[@]}"; do
        rate=$(echo "scale=1; (${stage_runs[$stage]} - ${stage_errors[$stage]}) * 100 / ${stage_runs[$stage]}" | bc 2>/dev/null || echo "0")
        printf "  %-25s %8d %8d %9.1f%%\n" "$stage" "${stage_runs[$stage]}" "${stage_errors[$stage]}" "$rate"
    done
fi
