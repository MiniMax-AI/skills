#!/usr/bin/env bash
# MiniMax Template Video Generation CLI (pure bash)
#
# Usage:
#   bash scripts/video/generate_template_video.sh \
#     --template-id T00001 \
#     --media image1.jpg image2.jpg \
#     --text "Title" "Subtitle" \
#     -o output/template_video.mp4
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

API_BASE="${MINIMAX_API_HOST:-https://api.minimaxi.com}/v1"
TEMPLATE_URL="${API_BASE}/video_template_generation"
QUERY_URL="${API_BASE}/query/video_template_generation"

POLL_INTERVAL=10
MAX_WAIT_TIME=600
REQUEST_TIMEOUT=60
MAX_CONSECUTIVE_FAILURES=5

# ============================================================================
# Common functions
# ============================================================================

load_env() {
  local env_file
  for env_file in "$PROJECT_ROOT/.env" "$(pwd)/.env"; do
    if [[ -f "$env_file" ]]; then
      while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%%#*}"; line="$(echo "$line" | xargs)"
        [[ -z "$line" || "$line" != *=* ]] && continue
        local key="${line%%=*}" val="${line#*=}"
        key="$(echo "$key" | xargs)"; val="$(echo "$val" | xargs)"
        if [[ ${#val} -ge 2 ]]; then
          case "$val" in \"*\") val="${val:1:${#val}-2}" ;; \'*\') val="${val:1:${#val}-2}" ;; esac
        fi
        [[ -z "${!key:-}" ]] && export "$key=$val"
      done < "$env_file"
    fi
  done
}

check_api_key() {
  if [[ -z "${MINIMAX_API_KEY:-}" ]]; then
    echo "Error: MINIMAX_API_KEY not set." >&2; exit 1
  fi
}

resolve_media_input() {
  local value="$1"
  case "$value" in
    http://*|https://*|data:*) echo "$value"; return ;;
  esac
  [[ -f "$value" ]] || { echo "Error: Media file not found: $value" >&2; exit 1; }
  local mime; mime="$(file -b --mime-type "$value" 2>/dev/null)" || mime="application/octet-stream"
  local b64; b64="$(base64 < "$value")"
  echo "data:${mime};base64,${b64}"
}

# ============================================================================
# Main
# ============================================================================

main() {
  load_env
  check_api_key

  local template_id="" output=""
  local media_inputs=() text_inputs=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --template-id) template_id="$2"; shift 2 ;;
      --media)
        shift
        while [[ $# -gt 0 && "$1" != --* ]]; do
          media_inputs+=("$1"); shift
        done
        ;;
      --text)
        shift
        while [[ $# -gt 0 && "$1" != --* ]]; do
          text_inputs+=("$1"); shift
        done
        ;;
      -o|--output) output="$2"; shift 2 ;;
      -h|--help)
        cat <<'USAGE'
MiniMax Template Video Generation CLI

Usage:
  generate_template_video.sh --template-id ID [--media FILE...] [--text TEXT...] -o OUTPUT

Options:
  --template-id ID    Template ID (required)
  --media FILE...     Media inputs (local files or URLs)
  --text TEXT...      Text inputs for template slots
  -o, --output FILE   Output video file (required)

Examples:
  generate_template_video.sh --template-id T00001 --media image1.jpg image2.jpg --text "Title" "Subtitle" -o video.mp4
USAGE
        exit 0
        ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done

  if [[ -z "$template_id" ]]; then
    echo "Error: --template-id is required" >&2; exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: --output / -o is required" >&2; exit 1
  fi

  # Build payload
  local payload
  payload=$(jq -n --arg tid "$template_id" '{template_id: $tid}')

  # Add media inputs
  if [[ ${#media_inputs[@]} -gt 0 ]]; then
    local media_json="[]"
    for i in "${!media_inputs[@]}"; do
      local resolved
      resolved="$(resolve_media_input "${media_inputs[$i]}")"
      media_json=$(echo "$media_json" | jq --arg url "$resolved" '. + [{value: $url}]')
      echo "  Media [$i]: ${media_inputs[$i]}"
    done
    payload=$(echo "$payload" | jq --argjson mi "$media_json" '. + {media_inputs: $mi}')
  fi

  # Add text inputs
  if [[ ${#text_inputs[@]} -gt 0 ]]; then
    local text_json="[]"
    for i in "${!text_inputs[@]}"; do
      text_json=$(echo "$text_json" | jq --arg t "${text_inputs[$i]}" '. + [{value: $t}]')
      echo "  Text [$i]: ${text_inputs[$i]}"
    done
    payload=$(echo "$payload" | jq --argjson ti "$text_json" '. + {text_inputs: $ti}')
  fi

  # Create task
  echo "Creating template video task (template: $template_id)..."
  local raw http_code response
  raw="$(curl -s -w "\n%{http_code}" -X POST "$TEMPLATE_URL" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time "$REQUEST_TIMEOUT" -d "$payload")"
  http_code="${raw##*$'\n'}"; response="${raw%$'\n'*}"

  [[ "$http_code" -ge 400 ]] 2>/dev/null && { echo "Error: HTTP $http_code" >&2; echo "$response" >&2; exit 1; }

  local sc
  sc="$(echo "$response" | jq -r '.base_resp.status_code // 0')" 2>/dev/null || true
  [[ "$sc" != "0" && -n "$sc" ]] && { echo "Error: $(echo "$response" | jq '.base_resp')" >&2; exit 1; }

  local task_id
  task_id="$(echo "$response" | jq -r '.task_id // empty')"
  [[ -z "$task_id" ]] && { echo "Error: No task_id in response" >&2; exit 1; }
  echo "Task created: $task_id"

  # Poll task
  echo "Polling task $task_id..."
  local start_time cf=0
  start_time="$(date +%s)"
  local video_url=""

  while true; do
    local elapsed=$(( $(date +%s) - start_time ))
    [[ $elapsed -gt $MAX_WAIT_TIME ]] && { echo "Error: Timeout" >&2; exit 1; }

    local poll_raw poll_code poll_resp
    if poll_raw="$(curl -s -w "\n%{http_code}" -G "$QUERY_URL" \
      -d "task_id=$task_id" \
      -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
      --max-time "$REQUEST_TIMEOUT" 2>/dev/null)"; then
      poll_code="${poll_raw##*$'\n'}"; poll_resp="${poll_raw%$'\n'*}"; cf=0
    else
      cf=$((cf+1))
      echo "  Poll error ($cf/$MAX_CONSECUTIVE_FAILURES)"
      [[ $cf -ge $MAX_CONSECUTIVE_FAILURES ]] && { echo "Error: Too many failures" >&2; exit 1; }
      sleep "$POLL_INTERVAL"; continue
    fi

    local status
    status="$(echo "$poll_resp" | jq -r '.status // "Unknown"')"
    echo "  [${elapsed}s] Status: $status"

    if [[ "$status" == "Success" ]]; then
      local video_url
      video_url="$(echo "$poll_resp" | jq -r '.video_url // empty')"
      [[ -z "$video_url" ]] && { echo "Error: No video_url in response" >&2; exit 1; }
      break
    fi

    [[ "$status" == "Fail" || "$status" == "Failed" || "$status" == "Error" ]] && {
      echo "Error: Task failed: $(echo "$poll_resp" | jq -r '.base_resp.status_msg // "Unknown"')" >&2
      exit 1
    }

    sleep "$POLL_INTERVAL"
  done

  # Download video directly from video_url
  echo "Downloading video..."
  mkdir -p "$(dirname "$output")"
  curl -s -o "$output" --max-time $((REQUEST_TIMEOUT * 3)) "$video_url"
  local size; size="$(wc -c < "$output" | tr -d ' ')"
  echo "Video saved to: $output ($size bytes)"
  echo "Done!"
}

main "$@"
