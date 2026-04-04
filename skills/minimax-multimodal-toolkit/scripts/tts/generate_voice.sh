#!/usr/bin/env bash
# MiniMax Voice CLI — Unified TTS command-line interface (pure bash)
#
# Usage:
#   bash scripts/tts/generate_voice.sh tts "Hello world" -o hello.mp3
#   bash scripts/tts/generate_voice.sh clone my_voice.mp3 --voice-id my-custom-voice
#   bash scripts/tts/generate_voice.sh design "A gentle female voice" --voice-id designed-voice-1
#   bash scripts/tts/generate_voice.sh list-voices
#   bash scripts/tts/generate_voice.sh validate segments.json
#   bash scripts/tts/generate_voice.sh generate segments.json -o output.mp3
#   bash scripts/tts/generate_voice.sh merge file1.mp3 file2.mp3 -o combined.mp3
#   bash scripts/tts/generate_voice.sh convert input.wav -o output.mp3
#   bash scripts/tts/generate_voice.sh check-env
set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================
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
        line="${line%%#*}"              # strip comments
        line="$(echo "$line" | xargs)"  # trim whitespace
        [[ -z "$line" || "$line" != *=* ]] && continue
        local key="${line%%=*}"
        local val="${line#*=}"
        key="$(echo "$key" | xargs)"
        val="$(echo "$val" | xargs)"
        # Remove surrounding quotes
        if [[ ${#val} -ge 2 ]]; then
          case "$val" in
            \"*\") val="${val:1:${#val}-2}" ;;
            \'*\') val="${val:1:${#val}-2}" ;;
          esac
        fi
        # Only set if not already in environment
        if [[ -z "${!key:-}" ]]; then
          export "$key=$val"
        fi
      done < "$env_file"
      return 0
    fi
  done
  return 0
}

check_api_key() {
  if [[ -z "${MINIMAX_API_KEY:-}" ]]; then
    echo "Error: MINIMAX_API_KEY environment variable is not set" >&2
    echo "  export MINIMAX_API_KEY='your-key'" >&2
    exit 1
  fi
}

ensure_dir() {
  local dir="$1"
  [[ -n "$dir" ]] && mkdir -p "$dir"
}

API_BASE="${MINIMAX_API_HOST:-https://api.minimaxi.com}/v1"

api_request() {
  # api_request METHOD ENDPOINT [JSON_BODY]
  # Outputs raw JSON response to stdout.
  local method="$1" endpoint="$2" body="${3:-}"
  local url="${API_BASE}/${endpoint#/}"

  local args=(
    -s -w "\n%{http_code}"
    -X "$method"
    -H "Authorization: Bearer ${MINIMAX_API_KEY}"
    -H "Accept-Encoding: gzip, deflate"
    --compressed
    --max-time 120
  )
  if [[ -n "$body" ]]; then
    args+=(-H "Content-Type: application/json" -d "$body")
  fi
  args+=("$url")

  local output http_code response
  output="$(curl "${args[@]}" 2>/dev/null)" || {
    echo "Error: curl request failed" >&2
    exit 1
  }
  http_code="${output##*$'\n'}"
  response="${output%$'\n'*}"

  if [[ "$http_code" -ge 400 ]] 2>/dev/null; then
    echo "Error: API returned HTTP $http_code" >&2
    echo "$response" >&2
    exit 1
  fi

  # Check API-level error
  local status_code
  status_code="$(echo "$response" | jq -r '.base_resp.status_code // 0')" 2>/dev/null || true
  if [[ "$status_code" != "0" && -n "$status_code" ]]; then
    local status_msg
    status_msg="$(echo "$response" | jq -r '.base_resp.status_msg // "Unknown error"')"
    echo "Error: API error [$status_code]: $status_msg" >&2
    exit 1
  fi

  echo "$response"
}

api_upload() {
  # api_upload ENDPOINT FILE_PATH PURPOSE
  local endpoint="$1" file_path="$2" purpose="$3"
  local url="${API_BASE}/${endpoint#/}"

  local output http_code response
  output="$(curl -s -w "\n%{http_code}" \
    -X POST \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Accept-Encoding: gzip, deflate" \
    --compressed \
    -F "file=@${file_path}" \
    -F "purpose=${purpose}" \
    --max-time 120 \
    "$url" 2>/dev/null)" || {
    echo "Error: curl upload failed" >&2
    exit 1
  }
  http_code="${output##*$'\n'}"
  response="${output%$'\n'*}"

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
    echo "Error: API error [$status_code]: $status_msg" >&2
    exit 1
  fi

  echo "$response"
}

hex_to_file() {
  # hex_to_file HEX_STRING OUTPUT_PATH
  local hex="$1" output="$2"
  ensure_dir "$(dirname "$output")"
  echo "$hex" | xxd -r -p > "$output"
}

# ============================================================================
# Subcommand: tts
# ============================================================================
cmd_tts() {
  local text="" voice_id="male-qn-qingse" output="" model="speech-2.8-hd"
  local speed=1.0 volume=1.0 pitch=0 emotion="" audio_format="mp3"
  local sample_rate=32000 language_boost=""

  # First positional arg is text
  if [[ $# -gt 0 && "$1" != -* ]]; then
    text="$1"; shift
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -v|--voice-id) voice_id="$2"; shift 2 ;;
      -o|--output) output="$2"; shift 2 ;;
      --model) model="$2"; shift 2 ;;
      --speed) speed="$2"; shift 2 ;;
      --volume) volume="$2"; shift 2 ;;
      --pitch) pitch="$2"; shift 2 ;;
      --emotion) emotion="$2"; shift 2 ;;
      --format) audio_format="$2"; shift 2 ;;
      --sample-rate) sample_rate="$2"; shift 2 ;;
      --language-boost) language_boost="$2"; shift 2 ;;
      *) text="$1"; shift ;;
    esac
  done

  if [[ -z "$text" ]]; then
    echo "Error: text is required" >&2
    echo "Usage: $(basename "$0") tts \"Text to speak\" -o output.mp3" >&2
    exit 1
  fi

  # Build voice_setting
  local voice_setting
  voice_setting=$(jq -n \
    --arg vid "$voice_id" \
    --argjson spd "$speed" \
    --argjson vol "$volume" \
    --argjson pit "$pitch" \
    '{voice_id: $vid, speed: $spd, vol: $vol, pitch: $pit}')

  if [[ -n "$emotion" ]]; then
    voice_setting=$(echo "$voice_setting" | jq --arg e "$emotion" '. + {emotion: $e}')
  fi

  # Build payload
  local payload
  payload=$(jq -n \
    --arg model "$model" \
    --arg text "$text" \
    --argjson vs "$voice_setting" \
    --arg fmt "$audio_format" \
    --argjson sr "$sample_rate" \
    '{
      model: $model,
      text: $text,
      voice_setting: $vs,
      audio_setting: {sample_rate: $sr, bitrate: 128000, format: $fmt, channel: 1},
      stream: false,
      subtitle_enable: false,
      output_format: "hex"
    }')

  if [[ -n "$language_boost" ]]; then
    payload=$(echo "$payload" | jq --arg lb "$language_boost" '. + {language_boost: $lb}')
  fi

  echo "Synthesizing: ${text:0:50}..."
  local response
  response="$(api_request POST t2a_v2 "$payload")"

  # Extract hex audio
  local audio_hex
  audio_hex="$(echo "$response" | jq -r '.data.audio // .extra_info.audio // empty')"

  if [[ -z "$audio_hex" ]]; then
    echo "Error: No audio data returned from API" >&2
    exit 1
  fi

  if [[ -n "$output" ]]; then
    hex_to_file "$audio_hex" "$output"
    echo "Done: $output"
  else
    echo "Generated ${#audio_hex} hex chars of audio"
  fi
}

# ============================================================================
# Subcommand: clone
# ============================================================================
cmd_clone() {
  local audio_file="" voice_id="" preview_text="" preview_output=""

  # First positional arg is audio file
  if [[ $# -gt 0 && "$1" != -* ]]; then
    audio_file="$1"; shift
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --voice-id) voice_id="$2"; shift 2 ;;
      --preview) preview_text="$2"; shift 2 ;;
      --preview-output) preview_output="$2"; shift 2 ;;
      *) [[ -z "$audio_file" ]] && audio_file="$1"; shift ;;
    esac
  done

  if [[ -z "$audio_file" ]]; then
    echo "Error: audio file is required" >&2
    echo "Usage: $(basename "$0") clone audio.mp3 --voice-id my-voice" >&2
    exit 1
  fi
  if [[ ! -f "$audio_file" ]]; then
    echo "Error: Audio file not found: $audio_file" >&2
    exit 1
  fi
  if [[ -z "$voice_id" ]]; then
    echo "Error: --voice-id is required" >&2
    exit 1
  fi

  echo "Cloning voice from: $audio_file"
  echo "Voice ID: $voice_id"

  # Step 1: Upload audio
  local upload_response file_id
  upload_response="$(api_upload files/upload "$audio_file" voice_clone)"
  file_id="$(echo "$upload_response" | jq -r '.file.file_id // .file_id // empty')"

  if [[ -z "$file_id" ]]; then
    echo "Error: Upload succeeded but no file_id was returned" >&2
    exit 1
  fi

  # Step 2: Clone voice
  local clone_payload
  clone_payload=$(jq -n \
    --arg vid "$voice_id" \
    --argjson fid "$file_id" \
    '{voice_id: $vid, file_id: $fid}')

  api_request POST voice_clone "$clone_payload" > /dev/null
  echo "Voice cloned successfully: $voice_id"

  # Step 3: Preview if requested
  if [[ -n "$preview_text" ]]; then
    echo "Generating preview..."
    local pout="${preview_output:-${voice_id}_preview.mp3}"
    cmd_tts "$preview_text" -v "$voice_id" -o "$pout"
    echo "Preview saved to: $pout"
  fi
}

# ============================================================================
# Subcommand: design
# ============================================================================
cmd_design() {
  local description="" voice_id="" preview_text="" preview_output=""

  if [[ $# -gt 0 && "$1" != -* ]]; then
    description="$1"; shift
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --voice-id) voice_id="$2"; shift 2 ;;
      --preview) preview_text="$2"; shift 2 ;;
      --preview-output) preview_output="$2"; shift 2 ;;
      *) [[ -z "$description" ]] && description="$1"; shift ;;
    esac
  done

  if [[ -z "$description" ]]; then
    echo "Error: description is required" >&2
    echo "Usage: $(basename \"$0\") design \"A warm female voice\" --voice-id narrator" >&2
    exit 1
  fi

  local ptext="${preview_text:-This is a preview of the designed voice.}"

  echo "Designing voice from: \"$description\""
  [[ -n "$voice_id" ]] && echo "Voice ID: $voice_id"

  local payload
  payload=$(jq -n \
    --arg prompt "$description" \
    --arg pt "$ptext" \
    '{prompt: $prompt, preview_text: $pt}')

  if [[ -n "$voice_id" ]]; then
    payload=$(echo "$payload" | jq --arg vid "$voice_id" '. + {voice_id: $vid}')
  fi

  local response
  response="$(api_request POST voice_design "$payload")"

  local actual_voice_id
  actual_voice_id="${voice_id:-$(echo "$response" | jq -r '.voice_id // "unknown"')}"
  echo "Voice designed: $actual_voice_id"

  local trial_audio
  trial_audio="$(echo "$response" | jq -r '.trial_audio // empty')"
  if [[ -n "$trial_audio" ]]; then
    local pout="${preview_output:-${actual_voice_id}_preview.mp3}"
    hex_to_file "$trial_audio" "$pout"
    echo "Preview saved to: $pout"
  fi
}

# ============================================================================
# Subcommand: list-voices
# ============================================================================
cmd_list_voices() {
  echo "=== System Voices ==="
  local sys_response
  sys_response="$(api_request POST voice/list '{"voice_type":"system"}' 2>/dev/null)" || true

  if [[ -n "$sys_response" ]]; then
    local count
    count="$(echo "$sys_response" | jq '.voice_list | length')" 2>/dev/null || count=0
    if [[ "$count" -gt 0 ]]; then
      echo "$sys_response" | jq -r '.voice_list[:10][] | "  \(.voice_id): \(.name // "N/A")"'
      if [[ "$count" -gt 10 ]]; then
        echo "  ... and $((count - 10)) more"
      fi
    else
      echo "  (None found)"
    fi
  else
    echo "  (Could not fetch system voices)"
  fi

  echo ""
  echo "=== Custom Voices ==="

  local clone_response design_response
  clone_response="$(api_request POST voice/list '{"voice_type":"voice_cloning"}' 2>/dev/null)" || true
  design_response="$(api_request POST voice/list '{"voice_type":"voice_generation"}' 2>/dev/null)" || true

  local has_custom=false

  if [[ -n "$clone_response" ]]; then
    local cc
    cc="$(echo "$clone_response" | jq '.voice_list | length')" 2>/dev/null || cc=0
    if [[ "$cc" -gt 0 ]]; then
      has_custom=true
      echo "Cloned ($cc):"
      echo "$clone_response" | jq -r '.voice_list[] | "  \(.voice_id)"'
    fi
  fi

  if [[ -n "$design_response" ]]; then
    local dc
    dc="$(echo "$design_response" | jq '.voice_list | length')" 2>/dev/null || dc=0
    if [[ "$dc" -gt 0 ]]; then
      has_custom=true
      echo "Designed ($dc):"
      echo "$design_response" | jq -r '.voice_list[] | "  \(.voice_id)"'
    fi
  fi

  if ! $has_custom; then
    echo "  (None found)"
  fi
}

# ============================================================================
# Subcommand: validate
# ============================================================================
cmd_validate() {
  local segments_file="" model="speech-2.8-hd" strict=false verbose=false

  if [[ $# -gt 0 && "$1" != -* ]]; then
    segments_file="$1"; shift
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --model) model="$2"; shift 2 ;;
      --strict) strict=true; shift ;;
      -v|--verbose) verbose=true; shift ;;
      --validate-voices) shift ;; # Not implemented in bash version
      *) [[ -z "$segments_file" ]] && segments_file="$1"; shift ;;
    esac
  done

  if [[ -z "$segments_file" || ! -f "$segments_file" ]]; then
    echo "Error: Segments file not found: ${segments_file:-<none>}" >&2
    exit 1
  fi

  echo "Validating: $segments_file"
  echo "Model: $model"

  local valid_emotions="happy sad angry fearful disgusted surprised calm fluent whisper"
  echo "Valid emotions: $valid_emotions"
  echo ""

  # Parse JSON
  local segments count
  segments="$(jq -r 'if type == "array" then . elif type == "object" and has("segments") then .segments else empty end' "$segments_file" 2>/dev/null)" || {
    echo "Error: Invalid JSON in $segments_file" >&2
    exit 1
  }

  if [[ -z "$segments" || "$segments" == "null" ]]; then
    echo "Error: No segments found in file" >&2
    exit 1
  fi

  count="$(echo "$segments" | jq 'length')"
  local errors=0

  for ((i=0; i<count; i++)); do
    local text voice_id emotion
    text="$(echo "$segments" | jq -r ".[$i].text // \"\"")"
    voice_id="$(echo "$segments" | jq -r ".[$i].voice_id // \"\"")"
    emotion="$(echo "$segments" | jq -r ".[$i].emotion // \"\"")"

    if [[ -z "$text" ]]; then
      echo "  - Segment $i: 'text' is required and must not be empty"
      errors=$((errors + 1))
    fi
    if [[ -z "$voice_id" ]]; then
      echo "  - Segment $i: 'voice_id' is required"
      errors=$((errors + 1))
    fi
    if [[ -n "$emotion" ]]; then
      if ! echo "$valid_emotions" | grep -qw "$emotion"; then
        echo "  - Segment $i: invalid emotion '$emotion'"
        errors=$((errors + 1))
      fi
    fi
  done

  if [[ $errors -eq 0 ]]; then
    echo "Validation passed: $count segments"
    if $verbose; then
      echo ""
      echo "=== Segment Summary ==="
      for ((i=0; i<count; i++)); do
        local text voice_id emotion
        text="$(echo "$segments" | jq -r ".[$i].text // \"\"")"
        voice_id="$(echo "$segments" | jq -r ".[$i].voice_id // \"\"")"
        emotion="$(echo "$segments" | jq -r ".[$i].emotion // \"\"")"
        local elabel="${emotion:-AUTO}"
        printf "  %d: [%-10s] voice=%-20s \"%s\"\n" "$i" "${elabel^^}" "${voice_id:0:20}" "${text:0:40}"
      done
    fi
    return 0
  else
    echo "Validation failed ($errors errors)"
    return 1
  fi
}

# ============================================================================
# Subcommand: generate (multi-segment pipeline)
# ============================================================================
cmd_generate() {
  local segments_file="" output="" model="speech-2.8-hd" crossfade=200
  local no_normalize=false temp_dir="" continue_on_error=false

  if [[ $# -gt 0 && "$1" != -* ]]; then
    segments_file="$1"; shift
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --model) model="$2"; shift 2 ;;
      --crossfade) crossfade="$2"; shift 2 ;;
      --no-normalize) no_normalize=true; shift ;;
      --temp-dir) temp_dir="$2"; shift 2 ;;
      --continue-on-error) continue_on_error=true; shift ;;
      *) [[ -z "$segments_file" ]] && segments_file="$1"; shift ;;
    esac
  done

  if [[ -z "$segments_file" || ! -f "$segments_file" ]]; then
    echo "Error: Segments file not found: ${segments_file:-<none>}" >&2
    exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: -o/--output is required" >&2
    exit 1
  fi

  # Validate first
  echo "Validating segments file..."
  local segments count
  segments="$(jq -r 'if type == "array" then . elif type == "object" and has("segments") then .segments else empty end' "$segments_file")"
  count="$(echo "$segments" | jq 'length')"

  if [[ "$count" -eq 0 ]]; then
    echo "Error: No segments found" >&2
    exit 1
  fi
  echo "Found $count valid segments"
  echo ""

  # Setup temp dir
  if [[ -z "$temp_dir" ]]; then
    temp_dir="$(dirname "$(cd "$(dirname "$output")" 2>/dev/null && pwd || echo ".")/$(basename "$output")")/tmp"
  fi
  mkdir -p "$temp_dir"
  echo "Temp directory: $temp_dir"

  # Generate each segment
  local succeeded=0 failed=0
  local segment_files=()

  for ((i=0; i<count; i++)); do
    local text voice_id emotion speed vol pitch
    text="$(echo "$segments" | jq -r ".[$i].text")"
    voice_id="$(echo "$segments" | jq -r ".[$i].voice_id")"
    emotion="$(echo "$segments" | jq -r ".[$i].emotion // \"\"")"
    speed="$(echo "$segments" | jq -r ".[$i].speed // 1.0")"
    vol="$(echo "$segments" | jq -r ".[$i].volume // 1.0")"
    pitch="$(echo "$segments" | jq -r ".[$i].pitch // 0")"

    printf "  Generating segment %d/%d: %s...\n" "$((i+1))" "$count" "${text:0:40}"

    local seg_output="$temp_dir/segment_$(printf '%04d' "$i").mp3"

    # Build voice_setting
    local voice_setting
    voice_setting=$(jq -n \
      --arg vid "$voice_id" \
      --argjson spd "$speed" \
      --argjson vol "$vol" \
      --argjson pit "$pitch" \
      '{voice_id: $vid, speed: $spd, vol: $vol, pitch: $pit}')
    if [[ -n "$emotion" ]]; then
      voice_setting=$(echo "$voice_setting" | jq --arg e "$emotion" '. + {emotion: $e}')
    fi

    local payload
    payload=$(jq -n \
      --arg model "$model" \
      --arg text "$text" \
      --argjson vs "$voice_setting" \
      '{
        model: $model,
        text: $text,
        voice_setting: $vs,
        audio_setting: {sample_rate: 32000, bitrate: 128000, format: "mp3", channel: 1},
        stream: false,
        output_format: "hex"
      }')

    local response audio_hex
    if response="$(api_request POST t2a_v2 "$payload" 2>&1)"; then
      audio_hex="$(echo "$response" | jq -r '.data.audio // .extra_info.audio // empty')"
      if [[ -n "$audio_hex" ]]; then
        hex_to_file "$audio_hex" "$seg_output"
        segment_files+=("$seg_output")
        succeeded=$((succeeded + 1))
        echo "    ✓ Saved: $seg_output"
      else
        failed=$((failed + 1))
        echo "    ✗ Error: No audio data in response"
        if ! $continue_on_error; then break; fi
      fi
    else
      failed=$((failed + 1))
      echo "    ✗ Error: $response"
      if ! $continue_on_error; then break; fi
    fi
  done

  if [[ ${#segment_files[@]} -eq 0 ]]; then
    echo "Error: No segments were generated successfully" >&2
    exit 1
  fi

  # Merge segments
  ensure_dir "$(dirname "$output")"

  if [[ ${#segment_files[@]} -eq 1 ]]; then
    cp "${segment_files[0]}" "$output"
  else
    _merge_audio_files "$output" "$crossfade" "$no_normalize" "${segment_files[@]}"
  fi

  echo ""
  echo "Audio saved to: $output"
  echo "  Generated: $succeeded/$count segments"
  echo ""
  echo "  Intermediate files in: $temp_dir"
  echo "  Delete with: rm -rf $temp_dir"
}

# ============================================================================
# Subcommand: merge
# ============================================================================
cmd_merge() {
  local output="" format="mp3" crossfade=300 normalize=true
  local input_files=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      --crossfade) crossfade="$2"; shift 2 ;;
      --no-normalize) normalize=false; shift ;;
      *) input_files+=("$1"); shift ;;
    esac
  done

  if [[ ${#input_files[@]} -lt 2 ]]; then
    echo "Error: At least 2 input files required" >&2
    exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: -o/--output is required" >&2
    exit 1
  fi

  for f in "${input_files[@]}"; do
    if [[ ! -f "$f" ]]; then
      echo "Error: File not found: $f" >&2
      exit 1
    fi
  done

  echo "Merging ${#input_files[@]} files..."
  local no_norm="false"
  $normalize || no_norm="true"
  _merge_audio_files "$output" "$crossfade" "$no_norm" "${input_files[@]}"
  echo "Merged audio saved to: $output"
}

_merge_audio_files() {
  # _merge_audio_files OUTPUT CROSSFADE_MS NO_NORMALIZE FILE1 FILE2 ...
  local output="$1" crossfade_ms="$2" no_normalize="$3"
  shift 3
  local files=("$@")
  local n=${#files[@]}

  ensure_dir "$(dirname "$output")"

  if [[ "$crossfade_ms" -gt 0 && $n -ge 2 ]]; then
    # Use acrossfade filter for crossfade between segments
    local crossfade_sec
    crossfade_sec=$(echo "scale=3; $crossfade_ms / 1000" | bc)

    local inputs=()
    local filter_parts=()

    for ((i=0; i<n; i++)); do
      inputs+=(-i "${files[$i]}")
      filter_parts+=("[${i}:a]aresample=32000,aformat=sample_fmts=fltp:channel_layouts=mono[s${i}]")
    done

    # Build acrossfade chain
    if [[ $n -eq 2 ]]; then
      filter_parts+=("[s0][s1]acrossfade=d=${crossfade_sec}[merged]")
    else
      filter_parts+=("[s0][s1]acrossfade=d=${crossfade_sec}[m1]")
      for ((i=2; i<n; i++)); do
        local prev="[m$((i-1))]"
        if [[ $i -eq $((n-1)) ]]; then
          filter_parts+=("${prev}[s${i}]acrossfade=d=${crossfade_sec}[merged]")
        else
          filter_parts+=("${prev}[s${i}]acrossfade=d=${crossfade_sec}[m${i}]")
        fi
      done
    fi

    local final_filter="[merged]aformat=sample_fmts=fltp"
    if [[ "$no_normalize" != "true" ]]; then
      final_filter+=",loudnorm=I=-16:TP=-1.5:LRA=11"
    fi
    final_filter+="[final]"
    filter_parts+=("$final_filter")

    local filter_complex
    filter_complex="$(IFS=';'; echo "${filter_parts[*]}")"

    if ffmpeg -y "${inputs[@]}" \
      -filter_complex "$filter_complex" \
      -map "[final]" \
      -ar 32000 -ac 1 -acodec libmp3lame \
      "$output" 2>/dev/null; then
      return 0
    fi
    echo "  Crossfade merge failed, falling back to concat demuxer..." >&2
  fi

  # Fallback: concat demuxer (no crossfade)
  local concat_file
  concat_file="$(mktemp /tmp/concat_XXXXXX.txt)"
  for f in "${files[@]}"; do
    echo "file '$(cd "$(dirname "$f")" && pwd)/$(basename "$f")'" >> "$concat_file"
  done

  if [[ "$no_normalize" != "true" ]]; then
    local tmp_concat
    tmp_concat="$(mktemp /tmp/concat_out_XXXXXX.mp3)"
    ffmpeg -y -f concat -safe 0 -i "$concat_file" -c copy "$tmp_concat" 2>/dev/null
    ffmpeg -y -i "$tmp_concat" -af "loudnorm=I=-16:TP=-1.5:LRA=11" -acodec libmp3lame "$output" 2>/dev/null
    rm -f "$tmp_concat"
  else
    ffmpeg -y -f concat -safe 0 -i "$concat_file" -c copy "$output" 2>/dev/null
  fi

  rm -f "$concat_file"
}

# ============================================================================
# Subcommand: convert
# ============================================================================
cmd_convert() {
  local input_file="" output="" format="mp3" sample_rate="" bitrate="" channels=""

  if [[ $# -gt 0 && "$1" != -* ]]; then
    input_file="$1"; shift
  fi

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      --sample-rate) sample_rate="$2"; shift 2 ;;
      --bitrate) bitrate="$2"; shift 2 ;;
      --channels) channels="$2"; shift 2 ;;
      *) [[ -z "$input_file" ]] && input_file="$1"; shift ;;
    esac
  done

  if [[ -z "$input_file" || ! -f "$input_file" ]]; then
    echo "Error: Input file not found: ${input_file:-<none>}" >&2
    exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: -o/--output is required" >&2
    exit 1
  fi

  ensure_dir "$(dirname "$output")"

  # Determine codec
  local codec="copy"
  case "$format" in
    mp3) codec="libmp3lame" ;;
    wav) codec="pcm_s16le" ;;
    flac) codec="flac" ;;
    ogg) codec="libvorbis" ;;
    aac) codec="aac" ;;
    m4a) codec="aac" ;;
    *) codec="copy" ;;
  esac

  local args=(-y -i "$input_file" -acodec "$codec")
  [[ -n "$sample_rate" ]] && args+=(-ar "$sample_rate")
  [[ -n "$channels" ]] && args+=(-ac "$channels")
  [[ -n "$bitrate" ]] && args+=(-b:a "$bitrate")
  args+=("$output")

  echo "Converting $input_file to $format..."
  ffmpeg "${args[@]}" 2>/dev/null
  echo "Converted audio saved to: $output"
}

# ============================================================================
# Subcommand: check-env
# ============================================================================
cmd_check_env() {
  local check_script="$SCRIPT_DIR/../check_environment.sh"
  if [[ -f "$check_script" ]]; then
    bash "$check_script" "$@"
  else
    echo "check_environment.sh not found" >&2
    exit 1
  fi
}

# ============================================================================
# Main dispatcher
# ============================================================================
usage() {
  cat <<'EOF'
MiniMax Voice CLI — Unified TTS interface

Usage:
  generate_voice.sh <command> [options]

Commands:
  tts          Basic text-to-speech
  clone        Clone voice from audio sample
  design       Design voice from description
  list-voices  List available voices
  validate     Validate segments.json file
  generate     Generate audio from segments.json
  merge        Merge multiple audio files
  convert      Convert audio format
  check-env    Check environment setup

Examples:
  generate_voice.sh tts "Hello world" -o hello.mp3
  generate_voice.sh tts "你好" -v female-shaonv -o hello_cn.mp3
  generate_voice.sh clone my_voice.mp3 --voice-id my-custom-voice
  generate_voice.sh design "A warm female voice" --voice-id narrator-1
  generate_voice.sh list-voices
  generate_voice.sh validate segments.json --verbose
  generate_voice.sh generate segments.json -o output.mp3
  generate_voice.sh merge part1.mp3 part2.mp3 -o combined.mp3
  generate_voice.sh convert input.wav -o output.mp3
  generate_voice.sh check-env --test-api
EOF
}

main() {
  load_env

  if [[ $# -eq 0 ]]; then
    usage
    exit 0
  fi

  local command="$1"; shift

  case "$command" in
    tts)
      check_api_key
      cmd_tts "$@"
      ;;
    clone)
      check_api_key
      cmd_clone "$@"
      ;;
    design)
      check_api_key
      cmd_design "$@"
      ;;
    list-voices)
      check_api_key
      cmd_list_voices "$@"
      ;;
    validate)
      cmd_validate "$@"
      ;;
    generate)
      check_api_key
      cmd_generate "$@"
      ;;
    merge)
      cmd_merge "$@"
      ;;
    convert)
      cmd_convert "$@"
      ;;
    check-env)
      cmd_check_env "$@"
      ;;
    -h|--help|help)
      usage
      ;;
    *)
      echo "Unknown command: $command" >&2
      usage >&2
      exit 1
      ;;
  esac
}

main "$@"
