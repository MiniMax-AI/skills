#!/usr/bin/env bash
# MiniMax Video Generation CLI (pure bash)
#
# Usage:
#   bash scripts/video/generate_video.sh --mode t2v --prompt "A cat playing piano" -o output/cat.mp4
#   bash scripts/video/generate_video.sh --mode i2v --prompt "Gentle breeze" --first-frame image.jpg -o output/anim.mp4
#   bash scripts/video/generate_video.sh --mode sef --first-frame start.jpg --last-frame end.jpg -o output/sef.mp4
#   bash scripts/video/generate_video.sh --mode ref --prompt "Person dancing" --subject-image person.jpg -o output/ref.mp4
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

API_BASE="${MINIMAX_API_HOST:-https://api.minimaxi.com}/v1"
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
    echo "Error: MINIMAX_API_KEY environment variable is not set." >&2; exit 1
  fi
}

image_to_data_url() {
  local path="$1"
  [[ -f "$path" ]] || { echo "Error: Image not found: $path" >&2; exit 1; }
  local mime
  mime="$(file -b --mime-type "$path" 2>/dev/null)" || mime="image/jpeg"
  local b64
  b64="$(base64 < "$path")"
  echo "data:${mime};base64,${b64}"
}

resolve_image() {
  local input="$1"
  [[ -z "$input" ]] && return
  case "$input" in
    http://*|https://*|data:*) echo "$input" ;;
    *) image_to_data_url "$input" ;;
  esac
}

# ============================================================================
# Video generation functions
# ============================================================================

create_task() {
  local payload="$1"
  echo "Creating video generation task..." >&2
  local raw_output http_code response
  raw_output="$(curl -s -w "\n%{http_code}" \
    -X POST "${API_BASE}/video_generation" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time "$REQUEST_TIMEOUT" \
    -d "$payload")"
  http_code="${raw_output##*$'\n'}"
  response="${raw_output%$'\n'*}"

  if [[ "$http_code" -ge 400 ]] 2>/dev/null; then
    echo "Error: API returned HTTP $http_code" >&2; echo "$response" >&2; exit 1
  fi

  local sc
  sc="$(echo "$response" | jq -r '.base_resp.status_code // 0')" 2>/dev/null || true
  if [[ "$sc" != "0" && -n "$sc" ]]; then
    echo "Error: API error: $(echo "$response" | jq '.base_resp')" >&2; exit 1
  fi

  local task_id
  task_id="$(echo "$response" | jq -r '.task_id // empty')"
  if [[ -z "$task_id" ]]; then
    echo "Error: No task_id in response" >&2; echo "$response" >&2; exit 1
  fi

  echo "Task created: $task_id" >&2
  echo "$task_id"
}

poll_task() {
  local task_id="$1"
  echo "Polling task $task_id..." >&2
  local start_time consecutive_failures=0
  start_time="$(date +%s)"

  while true; do
    local now elapsed
    now="$(date +%s)"
    elapsed=$((now - start_time))
    if [[ $elapsed -gt $MAX_WAIT_TIME ]]; then
      echo "Error: Task $task_id timed out after ${MAX_WAIT_TIME}s" >&2; exit 1
    fi

    local raw_output http_code response
    if raw_output="$(curl -s -w "\n%{http_code}" \
      -G "${API_BASE}/query/video_generation" \
      -d "task_id=$task_id" \
      -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
      --max-time "$REQUEST_TIMEOUT" 2>/dev/null)"; then
      http_code="${raw_output##*$'\n'}"
      response="${raw_output%$'\n'*}"
      consecutive_failures=0
    else
      consecutive_failures=$((consecutive_failures + 1))
      echo "  Poll error ($consecutive_failures/$MAX_CONSECUTIVE_FAILURES)" >&2
      if [[ $consecutive_failures -ge $MAX_CONSECUTIVE_FAILURES ]]; then
        echo "Error: Too many consecutive poll failures" >&2; exit 1
      fi
      sleep "$POLL_INTERVAL"; continue
    fi

    local status
    status="$(echo "$response" | jq -r '.status // "Unknown"')"
    echo "  [${elapsed}s] Status: $status" >&2

    if [[ "$status" == "Success" ]]; then
      local file_id
      file_id="$(echo "$response" | jq -r '.file_id // empty')"
      if [[ -z "$file_id" ]]; then
        echo "Error: Task succeeded but no file_id" >&2; exit 1
      fi
      echo "$file_id"
      return 0
    fi

    if [[ "$status" == "Fail" || "$status" == "Failed" || "$status" == "Error" ]]; then
      local err_msg
      err_msg="$(echo "$response" | jq -r '.base_resp.status_msg // "Unknown error"')"
      echo "Error: Task failed: $err_msg" >&2; exit 1
    fi

    sleep "$POLL_INTERVAL"
  done
}

download_video() {
  local file_id="$1" output_path="$2"
  echo "Retrieving file $file_id..." >&2

  local raw_output http_code response
  raw_output="$(curl -s -w "\n%{http_code}" \
    -G "${API_BASE}/files/retrieve" \
    -d "file_id=$file_id" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    --max-time "$REQUEST_TIMEOUT")"
  http_code="${raw_output##*$'\n'}"
  response="${raw_output%$'\n'*}"

  local dl_url
  dl_url="$(echo "$response" | jq -r '.file.download_url // empty')"
  if [[ -z "$dl_url" ]]; then
    echo "Error: No download_url in file response" >&2; exit 1
  fi

  echo "Downloading video..." >&2
  mkdir -p "$(dirname "$output_path")"
  curl -s -o "$output_path" --max-time $((REQUEST_TIMEOUT * 3)) "$dl_url"
  local size
  size="$(wc -c < "$output_path" | tr -d ' ')"
  echo "Video saved to: $output_path ($size bytes)" >&2
}

# ============================================================================
# Main
# ============================================================================

main() {
  load_env
  check_api_key

  local mode="" prompt="" model="" duration=10 resolution="768P"
  local first_frame="" last_frame="" subject_image=""
  local prompt_optimizer="" fast_pretreatment="" callback_url="" aigc_watermark=""
  local output=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode) mode="$2"; shift 2 ;;
      --prompt) prompt="$2"; shift 2 ;;
      --model) model="$2"; shift 2 ;;
      --duration) duration="$2"; shift 2 ;;
      --resolution) resolution="$2"; shift 2 ;;
      --first-frame) first_frame="$2"; shift 2 ;;
      --last-frame) last_frame="$2"; shift 2 ;;
      --subject-image) subject_image="$2"; shift 2 ;;
      --prompt-optimizer) prompt_optimizer="$2"; shift 2 ;;
      --fast-pretreatment) fast_pretreatment="$2"; shift 2 ;;
      --callback-url) callback_url="$2"; shift 2 ;;
      --aigc-watermark) aigc_watermark="$2"; shift 2 ;;
      -o|--output) output="$2"; shift 2 ;;
      -h|--help)
        cat <<'USAGE'
MiniMax Video Generation CLI

Usage:
  generate_video.sh --mode MODE [options] -o OUTPUT

Modes:
  t2v    Text-to-video
  i2v    Image-to-video (requires --first-frame)
  sef    Start-end frame (requires --first-frame and --last-frame)
  ref    Subject reference (requires --subject-image)

Options:
  --mode MODE           Generation mode: t2v, i2v, sef, ref (required)
  --prompt TEXT          Text prompt describing the video
  --model MODEL         Model name (default: T2V-01)
  --first-frame FILE    First frame image (local file or URL)
  --last-frame FILE     Last frame image (local file or URL)
  --subject-image FILE  Subject reference image (local file or URL)
  -o, --output FILE     Output video file (required)

Examples:
  generate_video.sh --mode t2v --prompt "A cat playing piano" -o cat.mp4
  generate_video.sh --mode i2v --prompt "Gentle breeze" --first-frame photo.jpg -o anim.mp4
  generate_video.sh --mode sef --first-frame start.jpg --last-frame end.jpg -o sef.mp4
  generate_video.sh --mode ref --prompt "Person dancing" --subject-image person.jpg -o ref.mp4
USAGE
        exit 0
        ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done

  if [[ -z "$mode" ]]; then
    echo "Error: --mode is required (t2v, i2v, sef, ref)" >&2; exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: --output / -o is required" >&2; exit 1
  fi

  # Default model per mode
  if [[ -z "$model" ]]; then
    case "$mode" in
      t2v) model="MiniMax-Hailuo-2.3" ;;
      i2v) model="MiniMax-Hailuo-2.3" ;;
      sef) model="MiniMax-Hailuo-02" ;;
      ref) model="S2V-01" ;;
    esac
  fi

  # Build payload
  local payload
  payload=$(jq -n --arg m "$model" '{model: $m}')

  [[ -n "$prompt" ]] && payload=$(echo "$payload" | jq --arg p "$prompt" '. + {prompt: $p}')
  payload=$(echo "$payload" | jq --argjson d "$duration" '. + {duration: $d}')
  payload=$(echo "$payload" | jq --arg r "$resolution" '. + {resolution: $r}')

  [[ -n "$prompt_optimizer" ]] && payload=$(echo "$payload" | jq --argjson po "$(echo "$prompt_optimizer" | tr '[:upper:]' '[:lower:]' | jq -R 'test("true")')" '. + {prompt_optimizer: $po}')
  [[ -n "$callback_url" ]] && payload=$(echo "$payload" | jq --arg cu "$callback_url" '. + {callback_url: $cu}')
  [[ -n "$aigc_watermark" ]] && payload=$(echo "$payload" | jq --argjson aw "$aigc_watermark" '. + {aigc_watermark: $aw}')

  case "$mode" in
    t2v) ;;
    i2v)
      if [[ -z "$first_frame" ]]; then
        echo "Error: --first-frame is required for i2v mode" >&2; exit 1
      fi
      local ff_url
      ff_url="$(resolve_image "$first_frame")"
      payload=$(echo "$payload" | jq --arg ff "$ff_url" '. + {first_frame_image: $ff}')
      [[ -n "$fast_pretreatment" ]] && payload=$(echo "$payload" | jq --argjson fp "$(echo "$fast_pretreatment" | tr '[:upper:]' '[:lower:]' | jq -R 'test("true")')" '. + {fast_pretreatment: $fp}')
      ;;
    sef)
      if [[ -z "$first_frame" ]]; then
        echo "Error: --first-frame is required for sef mode" >&2; exit 1
      fi
      local ff_url
      ff_url="$(resolve_image "$first_frame")"
      payload=$(echo "$payload" | jq --arg ff "$ff_url" '. + {first_frame_image: $ff}')
      if [[ -n "$last_frame" ]]; then
        local lf_url
        lf_url="$(resolve_image "$last_frame")"
        payload=$(echo "$payload" | jq --arg lf "$lf_url" '. + {last_frame_image: $lf}')
      fi
      ;;
    ref)
      if [[ -z "$subject_image" ]]; then
        echo "Error: --subject-image is required for ref mode" >&2; exit 1
      fi
      local si_url
      si_url="$(resolve_image "$subject_image")"
      payload=$(echo "$payload" | jq --arg si "$si_url" '. + {subject_reference: [{type: "character", image: [$si]}]}')
      if [[ -n "$first_frame" ]]; then
        local ff_url
        ff_url="$(resolve_image "$first_frame")"
        payload=$(echo "$payload" | jq --arg ff "$ff_url" '. + {first_frame_image: $ff}')
      fi
      ;;
    *)
      echo "Error: Unknown mode: $mode" >&2; exit 1 ;;
  esac

  echo "Mode: $mode"
  echo "Model: $model"

  local task_id file_id
  task_id="$(create_task "$payload")"
  file_id="$(poll_task "$task_id")"
  download_video "$file_id" "$output"
  echo "Done!"
}

main "$@"
