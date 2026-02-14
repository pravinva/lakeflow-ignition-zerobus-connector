#!/usr/bin/env bash
# gates.sh — Mechanical completion gates for SDP analytics pipeline
# Run: bash gates.sh
# Exit 0 = all gates pass. Non-zero = at least one gate failed.

set -uo pipefail

PASS=0
FAIL=0
TOTAL=0

VENV_DIR="pipelines/sdp/.venv"

run_gate() {
  local name="$1"; shift
  ((TOTAL++))
  local output
  if output=$("$@" 2>&1); then
    printf "  %-20s ok\n" "$name"
    ((PASS++))
  else
    printf "  %-20s FAIL\n" "$name"
    echo "    $output" | head -5
    ((FAIL++))
  fi
}

# --- Create venv if needed ---
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR" 2>/dev/null || true
fi

# Use venv python/pip
PY="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

echo ""

# --- Pipeline Python gates ---
run_gate "Install" "$PIP" install -e "pipelines/sdp[dev]" --quiet
run_gate "Lint" "$PY" -m ruff check pipelines/sdp/src/ pipelines/sdp/tests/ pipelines/sdp/transformations/
run_gate "Format" "$PY" -m ruff format --check pipelines/sdp/src/ pipelines/sdp/tests/ pipelines/sdp/transformations/
run_gate "Tests" "$PY" -m pytest pipelines/sdp/tests/ -v --tb=short

echo ""
echo "All $TOTAL gate(s): $PASS passed, $FAIL failed"
echo ""
[ "$FAIL" -eq 0 ]
