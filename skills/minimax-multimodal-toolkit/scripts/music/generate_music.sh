#!/usr/bin/env bash
# MiniMax Music Generation CLI (pure bash)
#
# Usage:
#   bash scripts/music/generate_music.sh --lyrics "[verse]\nHello world" --output output/song.mp3 --download
#   bash scripts/music/generate_music.sh --instrumental --prompt "ambient electronic" -o output/ambient.mp3 --download
#   bash scripts/music/generate_music.sh --lyrics "[verse]\nStars" --genre pop --mood happy -o output/happy.mp3 --download
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# ============================================================================
# Common functions (shared with generate_voice.sh)
# ============================================================================

load_env() {
  local env_file
  for env_file in "$PROJECT_ROOT/.env" "$(pwd)/.env"; do
    if [[ -f "$env_file" ]]; then
      while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%%#*}"
        line="$(echo "$line" | xargs)"
        [[ -z "$line" || "$line" != *=* ]] && continue
        local key="${line%%=*}" val="${line#*=}"
        key="$(echo "$key" | xargs)"; val="$(echo "$val" | xargs)"
        if [[ ${#val} -ge 2 ]]; then
          case "$val" in
            \"*\") val="${val:1:${#val}-2}" ;;
            \'*\') val="${val:1:${#val}-2}" ;;
          esac
        fi
        [[ -z "${!key:-}" ]] && export "$key=$val"
      done < "$env_file"
      return 0
    fi
  done
}

check_api_key() {
  if [[ -z "${MINIMAX_API_KEY:-}" ]]; then
    echo "Error: MINIMAX_API_KEY environment variable is not set." >&2
    exit 1
  fi
}

# ============================================================================
# Main
# ============================================================================

main() {
  load_env
  check_api_key

  local lyrics="" prompt="" model="music-2.5" instrumental=false
  local genre="" mood="" tempo="" bpm="" key="" instruments="" vocals=""
  local use_case="" structure="" avoid="" references=""
  local output="" output_format="url" stream=false download=false
  local sample_rate="" bitrate="" format="" aigc_watermark=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --lyrics) lyrics="$2"; shift 2 ;;
      --prompt) prompt="$2"; shift 2 ;;
      --model) model="$2"; shift 2 ;;
      --instrumental) instrumental=true; shift ;;
      --genre) genre="$2"; shift 2 ;;
      --mood) mood="$2"; shift 2 ;;
      --tempo) tempo="$2"; shift 2 ;;
      --bpm) bpm="$2"; shift 2 ;;
      --key) key="$2"; shift 2 ;;
      --instruments) instruments="$2"; shift 2 ;;
      --vocals) vocals="$2"; shift 2 ;;
      --use-case) use_case="$2"; shift 2 ;;
      --structure) structure="$2"; shift 2 ;;
      --avoid) avoid="$2"; shift 2 ;;
      --references) references="$2"; shift 2 ;;
      -o|--output) output="$2"; shift 2 ;;
      --output-format) output_format="$2"; shift 2 ;;
      --stream) stream=true; shift ;;
      --download) download=true; shift ;;
      --sample-rate) sample_rate="$2"; shift 2 ;;
      --bitrate) bitrate="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      --aigc-watermark) aigc_watermark="$2"; shift 2 ;;
      -h|--help)
        cat <<'USAGE'
MiniMax Music Generation CLI

Usage:
  generate_music.sh [options]

Options:
  --lyrics TEXT        Song lyrics (with [verse]/[chorus] tags)
  --prompt TEXT        Music style/description prompt
  --instrumental       Generate instrumental (no vocals)
  --model MODEL        Model name (default: music-2.5)
  --genre TEXT         Genre (e.g. pop, rock, jazz)
  --mood TEXT          Mood (e.g. happy, melancholic)
  --tempo TEXT         Tempo description (e.g. fast, slow)
  --bpm NUMBER         Beats per minute
  --key TEXT           Musical key (e.g. C major, A minor)
  --instruments TEXT   Instruments to include
  --vocals TEXT        Vocal style description
  --use-case TEXT      Use case (e.g. background, theme song)
  --structure TEXT     Song structure
  --avoid TEXT         Elements to avoid
  --references TEXT    Reference tracks/artists
  --output-format FMT  Output format: url (default) or hex
  --download           Download audio file (for url format)
  --sample-rate N      Audio sample rate
  --bitrate N          Audio bitrate
  --format FMT         Audio format (mp3, wav, etc.)
  -o, --output FILE    Output file path (required)

Examples:
  generate_music.sh --instrumental --prompt "ambient electronic" -o ambient.mp3 --download
  generate_music.sh --lyrics "[verse]\nHello world" -o song.mp3 --download
  generate_music.sh --lyrics "[verse]\nStars" --genre pop --mood happy -o happy.mp3 --download
USAGE
        exit 0
        ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done

  if [[ -z "$output" ]]; then
    echo "Error: --output / -o is required" >&2
    exit 1
  fi

  # Build prompt from structured fields
  local field_parts=()
  [[ -n "$genre" ]] && field_parts+=("Genre: $genre")
  [[ -n "$mood" ]] && field_parts+=("Mood: $mood")
  [[ -n "$tempo" ]] && field_parts+=("Tempo: $tempo")
  [[ -n "$bpm" ]] && field_parts+=("BPM: $bpm")
  [[ -n "$key" ]] && field_parts+=("Key: $key")
  [[ -n "$instruments" ]] && field_parts+=("Instruments: $instruments")
  [[ -n "$vocals" ]] && field_parts+=("Vocals: $vocals")
  [[ -n "$use_case" ]] && field_parts+=("Use case: $use_case")
  [[ -n "$structure" ]] && field_parts+=("Structure: $structure")
  [[ -n "$avoid" ]] && field_parts+=("Avoid: $avoid")
  [[ -n "$references" ]] && field_parts+=("References: $references")

  local field_prompt=""
  if [[ ${#field_parts[@]} -gt 0 ]]; then
    field_prompt="$(IFS='. '; echo "${field_parts[*]}")"
  fi

  if [[ -n "$field_prompt" ]]; then
    if [[ -n "$prompt" ]]; then
      prompt="$prompt. $field_prompt"
    else
      prompt="$field_prompt"
    fi
  fi

  # Build payload
  local payload
  payload=$(jq -n \
    --arg model "$model" \
    --arg prompt "$prompt" \
    --arg of "$output_format" \
    --argjson stream "$stream" \
    '{model: $model, prompt: $prompt, output_format: $of, stream: $stream}')

  if $instrumental; then
    # music-2.5 does not support is_instrumental — use lyrics workaround
    payload=$(echo "$payload" | jq '. + {lyrics: "[intro] [outro]"}')
    local current_prompt
    current_prompt="$(echo "$payload" | jq -r '.prompt // ""')"
    if [[ -n "$current_prompt" ]]; then
      payload=$(echo "$payload" | jq --arg p "$current_prompt. pure music, no lyrics" '.prompt = $p')
    else
      payload=$(echo "$payload" | jq '.prompt = "pure music, no lyrics"')
    fi
  else
    payload=$(echo "$payload" | jq --arg l "$lyrics" '. + {lyrics: $l}')
  fi

  # Audio settings
  local audio_setting="{}"
  [[ -n "$sample_rate" ]] && audio_setting=$(echo "$audio_setting" | jq --argjson sr "$sample_rate" '. + {sample_rate: $sr}')
  [[ -n "$bitrate" ]] && audio_setting=$(echo "$audio_setting" | jq --argjson br "$bitrate" '. + {bitrate: $br}')
  [[ -n "$format" ]] && audio_setting=$(echo "$audio_setting" | jq --arg f "$format" '. + {format: $f}')
  if [[ "$audio_setting" != "{}" ]]; then
    payload=$(echo "$payload" | jq --argjson as "$audio_setting" '. + {audio_setting: $as}')
  fi

  [[ -n "$aigc_watermark" ]] && payload=$(echo "$payload" | jq --argjson aw "$aigc_watermark" '. + {aigc_watermark: $aw}')

  local api_host="${MINIMAX_API_HOST:-https://api.minimaxi.com}"
  local api_url="${api_host}/v1/music_generation"

  echo "Generating music with model: $model"
  echo "Output format: $output_format"

  # Send request via curl
  local raw_output http_code response
  raw_output="$(curl -s -w "\n%{http_code}" \
    -X POST "$api_url" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time 300 \
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
    echo "API error: $(echo "$response" | jq '.base_resp')" >&2
    exit 1
  fi

  mkdir -p "$(dirname "$output")"

  if [[ "$output_format" == "hex" ]]; then
    local audio_hex
    audio_hex="$(echo "$response" | jq -r '.data.audio // empty')"
    if [[ -z "$audio_hex" ]]; then
      echo "Error: No audio hex data in response." >&2
      exit 1
    fi
    echo "$audio_hex" | xxd -r -p > "$output"
    echo "Audio saved to: $output"

  elif [[ "$output_format" == "url" ]]; then
    local audio_url
    audio_url="$(echo "$response" | jq -r '.data.audio_url // .data.audio // .data.audio_file.download_url // empty')"
    if [[ -z "$audio_url" ]]; then
      echo "Error: No audio URL in response." >&2
      echo "$response" | jq . >&2
      exit 1
    fi
    echo "Audio URL: $audio_url"
    if $download; then
      curl -s -o "$output" --max-time 120 "$audio_url"
      echo "Audio downloaded to: $output"
    else
      echo "Use --download to save the file, or download manually from the URL above."
      echo "$audio_url" > "$output"
      echo "URL written to: $output"
    fi
  fi

  # Print extra info if present
  local extra
  extra="$(echo "$response" | jq -r '.extra_info // .data.extra_info // empty')" 2>/dev/null || true
  if [[ -n "$extra" && "$extra" != "null" ]]; then
    echo "Extra info: $extra"
  fi
}

main "$@"
