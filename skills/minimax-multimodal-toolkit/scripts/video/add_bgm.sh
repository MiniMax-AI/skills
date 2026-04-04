#!/usr/bin/env bash
# Add background music to a video file (pure bash)
#
# Usage:
#   bash scripts/video/add_bgm.sh --video input.mp4 --audio bgm.mp3 -o output.mp4
#   bash scripts/video/add_bgm.sh --video input.mp4 --generate-bgm --music-prompt "upbeat pop" -o output.mp4
#   bash scripts/video/add_bgm.sh --video input.mp4 --audio bgm.mp3 --replace-audio -o output.mp4
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MUSIC_API_URL="${MINIMAX_API_HOST:-https://api.minimaxi.com}/v1/music_generation"

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

get_video_duration() {
  ffprobe -v error -show_entries format=duration -of json "$1" 2>/dev/null | jq -r '.format.duration'
}

video_has_audio() {
  local out
  out="$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$1" 2>/dev/null)"
  [[ "$out" == *audio* ]]
}

generate_music() {
  local prompt="$1" output_path="$2" instrumental="${3:-false}"

  local payload
  local effective_prompt="${prompt:-background music, cinematic, ambient}"

  if [[ "$instrumental" == "true" ]]; then
    payload=$(jq -n \
      --arg p "$effective_prompt. pure music, no lyrics" \
      '{model: "music-2.5", prompt: $p, lyrics: "[intro] [outro]", output_format: "url"}')
  else
    payload=$(jq -n \
      --arg p "$effective_prompt" \
      '{model: "music-2.5", prompt: $p, lyrics: "[Intro]\nla da da\nla la la", output_format: "url"}')
  fi

  echo "Generating ${instrumental:+instrumental }music..."
  echo "  Prompt: $prompt"

  local raw http_code response
  raw="$(curl -s -w "\n%{http_code}" -X POST "$MUSIC_API_URL" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time 300 -d "$payload")"
  http_code="${raw##*$'\n'}"; response="${raw%$'\n'*}"

  [[ "$http_code" -ge 400 ]] 2>/dev/null && { echo "Error: Music API HTTP $http_code" >&2; return 1; }

  local sc
  sc="$(echo "$response" | jq -r '.base_resp.status_code // 0')" 2>/dev/null || true
  [[ "$sc" != "0" && -n "$sc" ]] && { echo "Error: Music API error: $(echo "$response" | jq '.base_resp')" >&2; return 1; }

  local audio_url
  audio_url="$(echo "$response" | jq -r '.data.audio_url // .data.audio // .data.audio_file.download_url // empty')"
  [[ -z "$audio_url" ]] && { echo "Error: No audio URL in music response" >&2; return 1; }

  mkdir -p "$(dirname "$output_path")"

  # Download with retry
  local attempt
  for attempt in 1 2 3; do
    if curl -s -o "$output_path" --max-time 120 "$audio_url" 2>/dev/null; then
      local size; size="$(wc -c < "$output_path" | tr -d ' ')"
      echo "  Downloaded: $output_path ($size bytes)"
      return 0
    fi
    if [[ $attempt -lt 3 ]]; then
      local wait=$((2 ** attempt))
      echo "  Download attempt $attempt failed. Retrying in ${wait}s..."
      sleep "$wait"
    fi
  done
  echo "Error: Download failed after 3 attempts" >&2
  return 1
}

# ============================================================================
# Main
# ============================================================================

main() {
  load_env

  local video="" audio="" output=""
  local generate_bgm=false instrumental=false music_prompt=""
  local bgm_volume=0.3 fade_in=0 fade_out=0 replace_audio=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --video) video="$2"; shift 2 ;;
      --audio) audio="$2"; shift 2 ;;
      --generate-bgm) generate_bgm=true; shift ;;
      --instrumental) instrumental=true; shift ;;
      --music-prompt) music_prompt="$2"; shift 2 ;;
      --bgm-volume) bgm_volume="$2"; shift 2 ;;
      --fade-in) fade_in="$2"; shift 2 ;;
      --fade-out) fade_out="$2"; shift 2 ;;
      --replace-audio) replace_audio=true; shift ;;
      -o|--output) output="$2"; shift 2 ;;
      -h|--help)
        cat <<'USAGE'
Add Background Music to Video

Usage:
  add_bgm.sh --video INPUT --audio BGM -o OUTPUT
  add_bgm.sh --video INPUT --generate-bgm --music-prompt "style" -o OUTPUT

Options:
  --video FILE          Input video file (required)
  --audio FILE          Background music audio file
  --generate-bgm        Generate BGM via MiniMax API
  --instrumental        Make generated BGM instrumental
  --music-prompt TEXT    Prompt for BGM generation
  --bgm-volume FLOAT    BGM volume level (default: 0.3)
  --fade-in SECS        BGM fade-in duration
  --fade-out SECS       BGM fade-out duration
  --replace-audio       Replace original audio instead of mixing
  -o, --output FILE     Output video file (required)

Examples:
  add_bgm.sh --video input.mp4 --audio bgm.mp3 -o output.mp4
  add_bgm.sh --video input.mp4 --generate-bgm --music-prompt "upbeat pop" -o output.mp4
  add_bgm.sh --video input.mp4 --audio bgm.mp3 --replace-audio -o output.mp4
USAGE
        exit 0
        ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done

  if [[ -z "$video" || ! -f "$video" ]]; then
    echo "Error: Video file not found: ${video:-<none>}" >&2; exit 1
  fi
  if [[ -z "$audio" && "$generate_bgm" != "true" ]]; then
    echo "Error: Provide --audio or --generate-bgm" >&2; exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: --output / -o is required" >&2; exit 1
  fi

  local audio_path="$audio"

  if $generate_bgm; then
    if [[ -z "${MINIMAX_API_KEY:-}" ]]; then
      echo "Error: MINIMAX_API_KEY not set." >&2; exit 1
    fi
    audio_path="${output%.*}_bgm.mp3"
    generate_music "$music_prompt" "$audio_path" "$instrumental" || exit 1
  fi

  if [[ ! -f "$audio_path" ]]; then
    echo "Error: Audio file not found: $audio_path" >&2; exit 1
  fi

  local duration
  duration="$(get_video_duration "$video")"
  echo "Video duration: $(printf '%.1f' "$duration")s"

  mkdir -p "$(dirname "$output")"

  local has_audio=false
  video_has_audio "$video" && has_audio=true

  local bgm_filter="[1:a]volume=${bgm_volume}"
  [[ "$(echo "$fade_in > 0" | bc -l)" == "1" ]] && bgm_filter+=",afade=t=in:d=${fade_in}"
  if [[ "$(echo "$fade_out > 0" | bc -l)" == "1" ]]; then
    local fo_start
    fo_start="$(echo "$duration - $fade_out" | bc -l)"
    [[ "$(echo "$fo_start < 0" | bc -l)" == "1" ]] && fo_start=0
    bgm_filter+=",afade=t=out:st=${fo_start}:d=${fade_out}"
  fi

  if $has_audio && ! $replace_audio; then
    bgm_filter+="[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    echo "Merging video + audio (mixing with original, bgm_volume=${bgm_volume})..."
    ffmpeg -y \
      -i "$video" -i "$audio_path" \
      -filter_complex "$bgm_filter" \
      -map 0:v -map "[aout]" \
      -c:v copy -c:a aac -shortest "$output" 2>/dev/null
  else
    bgm_filter+="[bgm]"
    echo "Merging video + audio (${replace_audio:+replacing original}${replace_audio:-no original audio}, bgm_volume=${bgm_volume})..."
    ffmpeg -y \
      -i "$video" -i "$audio_path" \
      -filter_complex "$bgm_filter" \
      -map 0:v -map "[bgm]" \
      -c:v copy -c:a aac -shortest "$output" 2>/dev/null
  fi

  echo "Output saved: $output"
  echo "Done!"
}

main "$@"
