#!/usr/bin/env bash
# MiniMax Image Generation CLI (pure bash)
#
# Usage:
#   bash scripts/image/generate_image.sh --prompt "A cat on a rooftop at sunset" -o minimax-output/cat.png
#   bash scripts/image/generate_image.sh --mode i2i --prompt "A girl reading in a library" --ref-image face.jpg -o minimax-output/girl.png
#   bash scripts/image/generate_image.sh --prompt "Mountain landscape" --aspect-ratio 16:9 -n 3 -o minimax-output/landscape.png
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
# Payload builder — avoids command-line length limits on Windows
# Uses temp files for jq when the payload may contain large base64 data.
# ============================================================================

# Build JSON payload, writing large fields (base64 image data) to temp files
# to avoid Windows cmd.exe argument-length limits (~32KB).
build_payload() {
  local model="$1" prompt="$2" response_format="$3" n="$4"
  local prompt_optimizer="$5" aigc_watermark="$6"
  local aspect_ratio="$7" width="$8" height="$9" seed="${10:-}"
  local ref_image="${11:-}"

  # Start with base payload using temp file to avoid long command lines
  local base_tmp
  base_tmp="$(mktemp)"
  trap "rm -f '$base_tmp'" EXIT INT TERM HUP

  jq -n \
    --arg model "$model" \
    --arg prompt "$prompt" \
    --arg rf "$response_format" \
    --argjson n "$n" \
    --argjson po "$prompt_optimizer" \
    --argjson aw "$aigc_watermark" \
    '{model: $model, prompt: $prompt, response_format: $rf, n: $n, prompt_optimizer: $po, aigc_watermark: $aw}' \
    > "$base_tmp"

  # Add optional fields, each via temp file to stay within Windows arg limits
  if [[ -n "$aspect_ratio" ]]; then
    local tmp2; tmp2="$(mktemp)"; trap "rm -f '$base_tmp' '$tmp2'" EXIT INT TERM HUP
    jq --arg ar "$aspect_ratio" '. + {aspect_ratio: $ar}' "$base_tmp" > "$tmp2"
    mv "$tmp2" "$base_tmp"
  fi
  if [[ -n "$width" ]]; then
    local tmp2; tmp2="$(mktemp)"; trap "rm -f '$base_tmp' '$tmp2'" EXIT INT TERM HUP
    jq --argjson w "$width" '. + {width: $w}' "$base_tmp" > "$tmp2"
    mv "$tmp2" "$base_tmp"
  fi
  if [[ -n "$height" ]]; then
    local tmp2; tmp2="$(mktemp)"; trap "rm -f '$base_tmp' '$tmp2'" EXIT INT TERM HUP
    jq --argjson h "$height" '. + {height: $h}' "$base_tmp" > "$tmp2"
    mv "$tmp2" "$base_tmp"
  fi
  if [[ -n "$seed" ]]; then
    local tmp2; tmp2="$(mktemp)"; trap "rm -f '$base_tmp' '$tmp2'" EXIT INT TERM HUP
    jq --argjson s "$seed" '. + {seed: $s}' "$base_tmp" > "$tmp2"
    mv "$tmp2" "$base_tmp"
  fi

  # Subject reference (i2i mode) — build via temp file to avoid huge command-line args
  if [[ -n "$ref_image" ]]; then
    local img_url
    img_url="$(resolve_image "$ref_image")"
    # Write the subject_reference array to a temp file, then merge using --from-file
    local ref_tmp; ref_tmp="$(mktemp)"; trap "rm -f '$base_tmp' '$ref_tmp'" EXIT INT TERM HUP
    jq -n --arg img "$img_url" \
      '[{type: "character", image_file: $img}]' \
      > "$ref_tmp"
    local tmp2; tmp2="$(mktemp)"; trap "rm -f '$base_tmp' '$ref_tmp' '$tmp2'" EXIT INT TERM HUP
    jq --from-file "$ref_tmp" '. + {subject_reference: .subject_reference}' "$base_tmp" > "$tmp2"
    mv "$tmp2" "$base_tmp"
  fi

  cat "$base_tmp"
  rm -f "$base_tmp"
  trap - EXIT INT TERM HUP
}

# ============================================================================
# Main
# ============================================================================

main() {
  load_env
  check_api_key

  local mode="t2i" prompt="" model="image-01"
  local aspect_ratio="" width="" height=""
  local response_format="url" n=1 seed=""
  local prompt_optimizer=false aigc_watermark=false
  local ref_image=""
  local output="" download=true

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --mode) mode="$2"; shift 2 ;;
      --prompt) prompt="$2"; shift 2 ;;
      --aspect-ratio|--ratio) aspect_ratio="$2"; shift 2 ;;
      --width) width="$2"; shift 2 ;;
      --height) height="$2"; shift 2 ;;
      --response-format) response_format="$2"; shift 2 ;;
      -n|--count) n="$2"; shift 2 ;;
      --seed) seed="$2"; shift 2 ;;
      --prompt-optimizer) prompt_optimizer=true; shift ;;
      --aigc-watermark) aigc_watermark=true; shift ;;
      --ref-image) ref_image="$2"; shift 2 ;;
      --no-download) download=false; shift ;;
      -o|--output) output="$2"; shift 2 ;;
      -h|--help)
        cat <<'USAGE'
MiniMax Image Generation CLI (model: image-01)

Usage:
  generate_image.sh [--mode MODE] [options] -o OUTPUT

Modes:
  t2i    Text-to-image (default) — generate image from text prompt
  i2i    Image-to-image — generate image using a character reference photo

Options:
  --mode MODE           Generation mode: t2i (default), i2i
  --prompt TEXT         Text description of the image (max 1500 chars, required)
  --aspect-ratio RATIO  Aspect ratio: 1:1, 16:9, 4:3, 3:2, 2:3, 3:4, 9:16, 21:9
  --width PX            Custom width in pixels (512-2048, multiple of 8)
  --height PX           Custom height in pixels (512-2048, multiple of 8)
  -n, --count N         Number of images to generate (1-9, default: 1)
  --seed N              Random seed for reproducibility
  --prompt-optimizer    Enable automatic prompt optimization
  --aigc-watermark     Add AIGC watermark to generated images
  --ref-image FILE      Character reference image (local file or URL, i2i mode)
  --response-format FMT Response format: url (default), base64
  --no-download         Don't download, just print URL(s)
  -o, --output FILE     Output file path (required)

Examples:
  # Text-to-image (default)
  generate_image.sh --prompt "A cat on a rooftop at sunset, cinematic" -o cat.png

  # Custom aspect ratio
  generate_image.sh --prompt "Mountain landscape" --aspect-ratio 16:9 -o landscape.png

  # Multiple images
  generate_image.sh --prompt "Abstract art" -n 3 -o art.png

  # Image-to-image with character reference
  generate_image.sh --mode i2i --prompt "A girl reading in a library" --ref-image face.jpg -o girl.png
USAGE
        exit 0
        ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done

  if [[ -z "$prompt" ]]; then
    echo "Error: --prompt is required" >&2; exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: --output / -o is required" >&2; exit 1
  fi

  # Validate n range
  if [[ "$n" -lt 1 || "$n" -gt 9 ]] 2>/dev/null; then
    echo "Error: -n must be between 1 and 9" >&2; exit 1
  fi

  # Build payload using temp-file method (avoids Windows cmd.exe arg-length limit)
  local payload
  payload=$(build_payload \
    "$model" "$prompt" "$response_format" "$n" \
    "$prompt_optimizer" "$aigc_watermark" \
    "$aspect_ratio" "$width" "$height" "$seed" \
    "$ref_image")

  local api_host="${MINIMAX_API_HOST:-https://api.minimaxi.com}"
  local api_url="${api_host}/v1/image_generation"

  echo "Mode: $mode"
  echo "Model: $model"
  echo "Generating $n image(s)..."

  local raw_output http_code response
  raw_output="$(curl -s -w "\n%{http_code}" \
    -X POST "$api_url" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time 120 \
    -d "$payload" 2>/dev/null)" || {
    echo "Error: curl request failed" >&2
    exit 1
  }

  http_code="${raw_output##*$'\n'}"
  response="${raw_output%$'\n'*}"

  if [[ "$http_code" -ge 400 ]] 2>/dev/null; then
    echo "Error: API returned HTTP $http_code" >&2
    echo "$response" >&2
    exit 1
  fi

  local status_code
  status_code="$(echo "$response" | jq -r '.base_resp.status_code // 0')" 2>/dev/null || true
  if [[ "$status_code" != "0" && -n "$status_code" ]]; then
    local status_msg
    status_msg="$(echo "$response" | jq -r '.base_resp.status_msg // "Unknown error"')"
    echo "Error: API error (code $status_code): $status_msg" >&2
    exit 1
  fi

  local success_count failed_count
  success_count="$(echo "$response" | jq -r '.metadata.success_count // 0')" 2>/dev/null || true
  failed_count="$(echo "$response" | jq -r '.metadata.failed_count // 0')" 2>/dev/null || true
  echo "Success: $success_count, Failed: $failed_count"

  mkdir -p "$(dirname "$output")"

  if [[ "$response_format" == "base64" ]]; then
    local count
    count="$(echo "$response" | jq '.data.image_base64 | length')" 2>/dev/null || count=0
    if [[ "$count" -eq 0 ]]; then
      echo "Error: No image data in response" >&2; exit 1
    fi

    if [[ "$count" -eq 1 ]]; then
      echo "$response" | jq -r '.data.image_base64[0]' | base64 -d > "$output"
      echo "Image saved to: $output"
    else
      local ext="${output##*.}"
      local base="${output%.*}"
      for ((i=0; i<count; i++)); do
        local out_file="${base}_$((i+1)).${ext}"
        echo "$response" | jq -r ".data.image_base64[$i]" | base64 -d > "$out_file"
        echo "Image saved to: $out_file"
      done
    fi

  elif [[ "$response_format" == "url" ]]; then
    local count
    count="$(echo "$response" | jq '.data.image_urls | length')" 2>/dev/null || count=0
    if [[ "$count" -eq 0 ]]; then
      echo "Error: No image URLs in response" >&2
      echo "$response" | jq . >&2
      exit 1
    fi

    if $download; then
      if [[ "$count" -eq 1 ]]; then
        local img_url
        img_url="$(echo "$response" | jq -r '.data.image_urls[0]')"
        echo "URL: $img_url"
        curl -s -o "$output" --max-time 120 "$img_url"
        echo "Image downloaded to: $output"
      else
        local ext="${output##*.}"
        local base="${output%.*}"
        for ((i=0; i<count; i++)); do
          local img_url out_file
          img_url="$(echo "$response" | jq -r ".data.image_urls[$i]")"
          out_file="${base}_$((i+1)).${ext}"
          echo "URL $((i+1)): $img_url"
          curl -s -o "$out_file" --max-time 120 "$img_url"
          echo "Image downloaded to: $out_file"
        done
      fi
    else
      for ((i=0; i<count; i++)); do
        local img_url
        img_url="$(echo "$response" | jq -r ".data.image_urls[$i]")"
        echo "Image URL $((i+1)): $img_url"
      done
      echo "Use without --no-download to save files automatically."
    fi
  fi

  echo "Done!"
}

main "$@"
