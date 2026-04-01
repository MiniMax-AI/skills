#!/usr/bin/env bash
# MiniMax Multi-Modal Toolkit — Environment Check
#
# Usage:
#   bash scripts/check_environment.sh
#   bash scripts/check_environment.sh --test-api
set -euo pipefail

PASSED=0
FAILED=0
TOTAL=0

check() {
  TOTAL=$((TOTAL + 1))
  if "$@"; then
    PASSED=$((PASSED + 1))
  else
    FAILED=$((FAILED + 1))
  fi
}

check_curl() {
  if command -v curl &>/dev/null; then
    echo "[OK] curl installed"
    return 0
  fi
  echo "[FAIL] curl not installed"
  return 1
}

check_ffmpeg() {
  if command -v ffmpeg &>/dev/null; then
    echo "[OK] FFmpeg installed"
    return 0
  fi
  echo "[FAIL] FFmpeg not installed"
  return 1
}

check_ffprobe() {
  if command -v ffprobe &>/dev/null; then
    echo "[OK] ffprobe installed"
    return 0
  fi
  echo "[FAIL] ffprobe not installed"
  return 1
}

check_jq() {
  if command -v jq &>/dev/null; then
    echo "[OK] jq installed"
    return 0
  fi
  echo "[FAIL] jq not installed (brew install jq / apt install jq)"
  return 1
}

check_xxd() {
  if command -v xxd &>/dev/null; then
    echo "[OK] xxd installed"
    return 0
  fi
  echo "[FAIL] xxd not installed"
  return 1
}

check_api_host() {
  local api_host="${MINIMAX_API_HOST:-}"
  if [[ -z "$api_host" ]]; then
    echo "[FAIL] MINIMAX_API_HOST not set"
    echo "  China Mainland: export MINIMAX_API_HOST='https://api.minimaxi.com'"
    echo "  Global:         export MINIMAX_API_HOST='https://api.minimax.io'"
    echo "  If you stored it in ~/.zshrc or ~/.bashrc, restart your IDE/agent so the new value is inherited."
    echo "  In sandboxed runtimes, you may need to configure the variable in the app's own environment settings."
    return 1
  fi
  if [[ "$api_host" != "https://api.minimaxi.com" && "$api_host" != "https://api.minimax.io" ]]; then
    echo "[WARN] MINIMAX_API_HOST has non-standard value: $api_host"
    echo "  Expected: https://api.minimaxi.com (China) or https://api.minimax.io (Global)"
    return 0
  fi
  echo "[OK] MINIMAX_API_HOST set ($api_host)"
  return 0
}

check_api_key() {
  local api_key="${MINIMAX_API_KEY:-}"
  if [[ -z "$api_key" ]]; then
    echo "[FAIL] MINIMAX_API_KEY not set"
    echo "  export MINIMAX_API_KEY='your-key'"
    echo "  If you already added it to ~/.zshrc or ~/.bashrc, restart your IDE/agent or launch it from a shell where the variable is exported."
    echo "  In sandboxed runtimes, set the variable in the tool's environment settings if available."
    return 1
  fi
  if [[ "$api_key" != sk-api* && "$api_key" != sk-cp* ]]; then
    echo "[FAIL] Invalid API key format"
    echo "  Expected: sk-api-xxx... or sk-cp-xxx..."
    echo "  Got: ${api_key:0:20}..."
    return 1
  fi
  echo "[OK] MINIMAX_API_KEY set (${#api_key} chars)"
  return 0
}

check_api_connectivity() {
  local api_host="${MINIMAX_API_HOST:-}"
  local api_key="${MINIMAX_API_KEY:-}"
  if [[ -z "$api_key" ]]; then
    echo "[FAIL] API connectivity skipped (MINIMAX_API_KEY not set)"
    return 1
  fi
  if [[ -z "$api_host" ]]; then
    echo "[FAIL] API connectivity skipped (MINIMAX_API_HOST not set)"
    return 1
  fi
  local http_code
  http_code=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $api_key" \
    --max-time 10 \
    "$api_host" 2>/dev/null) || true
  if [[ -n "$http_code" && "$http_code" -lt 500 ]] 2>/dev/null; then
    echo "[OK] API host reachable (HTTP $http_code)"
    return 0
  fi
  echo "[FAIL] API host unreachable ($api_host)"
  return 1
}

# --- Main ---
TEST_API=false
for arg in "$@"; do
  case "$arg" in
    --test-api) TEST_API=true ;;
  esac
done

echo "MiniMax Multi-Modal Toolkit — Environment Check"
echo "========================================"

check check_curl
check check_ffmpeg
check check_ffprobe
check check_jq
check check_xxd
check check_api_host
check check_api_key

if $TEST_API; then
  check check_api_connectivity
fi

echo ""
echo "========================================"
if [[ $FAILED -eq 0 ]]; then
  echo "All $TOTAL checks passed!"
  exit 0
else
  echo "$FAILED check(s) failed out of $TOTAL"
  exit 1
fi
