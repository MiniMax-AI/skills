#!/usr/bin/env bash
# MiniMax Long Video Generation CLI (pure bash)
#
# Generates multi-segment videos by chaining scenes together.
# Each segment's last frame becomes the next segment's first frame.
# Optionally adds AI-generated background music.
#
# Usage:
#   bash scripts/video/generate_long_video.sh \
#     --scenes "A sunrise" "Birds flying" "A calm lake" \
#     --output output/long_video.mp4
#
#   bash scripts/video/generate_long_video.sh \
#     --scenes "A robot waking up" "The robot walks outside" \
#     --music-prompt "cinematic orchestral" \
#     --output output/robot_story.mp4
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

API_BASE="${MINIMAX_API_HOST:-https://api.minimaxi.com}/v1"
MUSIC_API_URL="${API_BASE}/music_generation"
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

validate_model_constraints() {
  local model="$1" duration="$2" resolution="$3"
  case "$model" in
    MiniMax-Hailuo-2.3-Fast)
      if [[ "$duration" != "6" || "$resolution" != "768P" ]]; then
        echo "Error: MiniMax-Hailuo-2.3-Fast only supports duration=6 and resolution=768P." >&2
        exit 1
      fi
      ;;
    MiniMax-Hailuo-2.3)
      if [[ "$duration" != "6" || "$resolution" != "768P" ]]; then
        echo "Error: MiniMax-Hailuo-2.3 only supports duration=6 and resolution=768P." >&2
        exit 1
      fi
      ;;
    *)
      echo "Error: Unsupported model '$model'. Supported models: MiniMax-Hailuo-2.3-Fast, MiniMax-Hailuo-2.3." >&2
      exit 1
      ;;
  esac
}

image_to_data_url() {
  local path="$1"
  [[ -f "$path" ]] || { echo "Error: Image not found: $path" >&2; exit 1; }
  local mime; mime="$(file -b --mime-type "$path" 2>/dev/null)" || mime="image/jpeg"
  local b64; b64="$(base64 < "$path")"
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
# Video API helpers (duplicated from generate_video.sh for standalone use)
# ============================================================================

_create_task() {
  local payload="$1"
  local raw http_code response
  raw="$(curl -s -w "\n%{http_code}" -X POST "${API_BASE}/video_generation" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time "$REQUEST_TIMEOUT" -d "$payload")"
  http_code="${raw##*$'\n'}"; response="${raw%$'\n'*}"
  [[ "$http_code" -ge 400 ]] 2>/dev/null && { echo "Error: HTTP $http_code" >&2; echo "$response" >&2; exit 1; }
  local sc; sc="$(echo "$response" | jq -r '.base_resp.status_code // 0')" 2>/dev/null || true
  [[ "$sc" != "0" && -n "$sc" ]] && { echo "Error: $(echo "$response" | jq '.base_resp')" >&2; exit 1; }
  echo "$response" | jq -r '.task_id // empty'
}

_poll_task() {
  local task_id="$1" start_time cf=0
  start_time="$(date +%s)"
  while true; do
    local now=$(($(date +%s) - start_time))
    [[ $now -gt $MAX_WAIT_TIME ]] && { echo "Error: Timeout" >&2; exit 1; }
    local raw http_code response
    if raw="$(curl -s -w "\n%{http_code}" -G "${API_BASE}/query/video_generation" \
      -d "task_id=$task_id" -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
      --max-time "$REQUEST_TIMEOUT" 2>/dev/null)"; then
      http_code="${raw##*$'\n'}"; response="${raw%$'\n'*}"; cf=0
    else
      cf=$((cf+1)); [[ $cf -ge $MAX_CONSECUTIVE_FAILURES ]] && { echo "Error: Too many failures" >&2; exit 1; }
      sleep "$POLL_INTERVAL"; continue
    fi
    local status; status="$(echo "$response" | jq -r '.status // "Unknown"')"
    echo "  [${now}s] Status: $status" >&2
    [[ "$status" == "Success" ]] && { echo "$response" | jq -r '.file_id // empty'; return 0; }
    [[ "$status" == "Fail" || "$status" == "Failed" || "$status" == "Error" ]] && { echo "Error: Task failed" >&2; exit 1; }
    sleep "$POLL_INTERVAL"
  done
}

_download_video() {
  local file_id="$1" output_path="$2"
  local raw; raw="$(curl -s -G "${API_BASE}/files/retrieve" -d "file_id=$file_id" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" --max-time "$REQUEST_TIMEOUT")"
  local dl_url; dl_url="$(echo "$raw" | jq -r '.file.download_url // empty')"
  [[ -z "$dl_url" ]] && { echo "Error: No download_url" >&2; exit 1; }
  mkdir -p "$(dirname "$output_path")"
  curl -s -o "$output_path" --max-time $((REQUEST_TIMEOUT * 3)) "$dl_url"
  echo "  Video saved: $output_path ($(wc -c < "$output_path" | tr -d ' ') bytes)" >&2
}

# ============================================================================
# FFmpeg helpers
# ============================================================================

get_video_duration() {
  ffprobe -v error -show_entries format=duration -of json "$1" 2>/dev/null | jq -r '.format.duration'
}

get_video_fps() {
  local fps_str
  fps_str="$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$1" 2>/dev/null)" || { echo 25; return; }
  local num den
  num="${fps_str%/*}"; den="${fps_str#*/}"
  echo $(( (num + den/2) / den )) 2>/dev/null || echo 25
}

video_has_audio() {
  local out
  out="$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$1" 2>/dev/null)"
  [[ "$out" == *audio* ]]
}

extract_last_frame() {
  local video_path="$1" output_image="$2"
  # Try frame-accurate method with sseof fallback
  if ! ffmpeg -y -sseof -0.04 -i "$video_path" -frames:v 1 -q:v 2 "$output_image" 2>/dev/null; then
    echo "Warning: Could not extract last frame" >&2
    return 1
  fi
  [[ -f "$output_image" ]] || return 1
  echo "  Extracted last frame: $output_image" >&2
}

concatenate_videos() {
  local output_path="$1" crossfade="$2"
  shift 2
  local video_paths=("$@")
  local n=${#video_paths[@]}

  if [[ $n -eq 1 ]]; then
    cp "${video_paths[0]}" "$output_path"
    return 0
  fi

  local fps
  fps="$(get_video_fps "${video_paths[0]}")"
  local has_audio=true
  for vp in "${video_paths[@]}"; do
    video_has_audio "$vp" || { has_audio=false; break; }
  done

  if [[ "$(echo "$crossfade > 0" | bc -l)" == "1" ]]; then
    # Get durations
    local durations=()
    for vp in "${video_paths[@]}"; do
      durations+=("$(get_video_duration "$vp")")
    done

    # Build inputs
    local inputs=()
    for vp in "${video_paths[@]}"; do
      inputs+=(-i "$(cd "$(dirname "$vp")" && pwd)/$(basename "$vp")")
    done

    # Calculate offsets
    local offsets=() cumulative=0
    for ((i=0; i<n-1; i++)); do
      local offset
      offset="$(echo "$cumulative + ${durations[$i]} - $crossfade" | bc -l)"
      offsets+=("$offset")
      cumulative="$offset"
    done

    # Build filter
    local vf_parts=() af_parts=()
    if [[ $n -eq 2 ]]; then
      vf_parts+=("[0:v][1:v]xfade=transition=fade:duration=${crossfade}:offset=${offsets[0]}[vout]")
      $has_audio && af_parts+=("[0:a][1:a]acrossfade=d=${crossfade}:c1=tri:c2=tri[aout]")
    else
      vf_parts+=("[0:v][1:v]xfade=transition=fade:duration=${crossfade}:offset=${offsets[0]}[xv1]")
      $has_audio && af_parts+=("[0:a][1:a]acrossfade=d=${crossfade}:c1=tri:c2=tri[xa1]")
      for ((i=2; i<n; i++)); do
        local out_v="[xv${i}]" out_a="[xa${i}]"
        [[ $i -eq $((n-1)) ]] && { out_v="[vout]"; out_a="[aout]"; }
        vf_parts+=("[xv$((i-1))][${i}:v]xfade=transition=fade:duration=${crossfade}:offset=${offsets[$((i-1))]}${out_v}")
        $has_audio && af_parts+=("[xa$((i-1))][${i}:a]acrossfade=d=${crossfade}:c1=tri:c2=tri${out_a}")
      done
    fi

    local filter_complex
    filter_complex="$(IFS=';'; echo "${vf_parts[*]}${af_parts[*]:+;${af_parts[*]}}")"

    local cmd=(ffmpeg -y "${inputs[@]}" -filter_complex "$filter_complex" -map "[vout]")
    $has_audio && cmd+=(-map "[aout]")
    cmd+=(-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r "$fps")
    $has_audio && cmd+=(-c:a aac -b:a 192k)
    cmd+=("$output_path")

    if "${cmd[@]}" 2>/dev/null; then
      echo "Concatenated $n segments -> $output_path" >&2
      return 0
    fi
    echo "  Crossfade failed, falling back to re-encode concat..." >&2
  fi

  # Fallback: concat demuxer with re-encode
  local concat_file
  concat_file="$(mktemp /tmp/concat_XXXXXX.txt)"
  for vp in "${video_paths[@]}"; do
    echo "file '$(cd "$(dirname "$vp")" && pwd)/$(basename "$vp")'" >> "$concat_file"
  done
  ffmpeg -y -f concat -safe 0 -i "$concat_file" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r "$fps" \
    -c:a aac -b:a 192k "$output_path" 2>/dev/null
  rm -f "$concat_file"
  echo "Concatenated $n segments -> $output_path" >&2
}

merge_video_audio() {
  local video_path="$1" audio_path="$2" output_path="$3"
  local bgm_volume="${4:-0.3}" fade_in="${5:-0}" fade_out="${6:-0}"

  local duration
  duration="$(get_video_duration "$video_path")"

  local af="[1:a]volume=${bgm_volume}"
  [[ "$(echo "$fade_in > 0" | bc -l)" == "1" ]] && af+=",afade=t=in:d=${fade_in}"
  if [[ "$(echo "$fade_out > 0" | bc -l)" == "1" ]]; then
    local fo_start
    fo_start="$(echo "$duration - $fade_out" | bc -l)"
    [[ "$(echo "$fo_start < 0" | bc -l)" == "1" ]] && fo_start=0
    af+=",afade=t=out:st=${fo_start}:d=${fade_out}"
  fi
  af+="[bgm]"

  mkdir -p "$(dirname "$output_path")"
  ffmpeg -y -i "$video_path" -i "$audio_path" \
    -filter_complex "$af" \
    -map 0:v -map "[bgm]" \
    -c:v copy -c:a aac -shortest "$output_path" 2>/dev/null

  echo "Merged video+audio -> $output_path" >&2
}

generate_music_instrumental() {
  local prompt="$1" output_path="$2"
  local payload
  payload=$(jq -n \
    --arg p "${prompt:-cinematic background music, orchestral, ambient}. pure music, no lyrics" \
    '{model: "music-2.5", prompt: $p, lyrics: "[intro] [outro]", output_format: "url"}')

  echo "Generating instrumental music: $prompt" >&2
  local raw http_code response
  raw="$(curl -s -w "\n%{http_code}" -X POST "$MUSIC_API_URL" \
    -H "Authorization: Bearer ${MINIMAX_API_KEY}" \
    -H "Content-Type: application/json" \
    --max-time 300 -d "$payload")"
  http_code="${raw##*$'\n'}"; response="${raw%$'\n'*}"
  [[ "$http_code" -ge 400 ]] 2>/dev/null && { echo "Error: Music API HTTP $http_code" >&2; return 1; }

  local audio_url
  audio_url="$(echo "$response" | jq -r '.data.audio_url // .data.audio // .data.audio_file.download_url // empty')"
  [[ -z "$audio_url" ]] && { echo "Error: No audio URL in music response" >&2; return 1; }

  mkdir -p "$(dirname "$output_path")"
  curl -s -o "$output_path" --max-time 120 "$audio_url"
  echo "  Music saved: $output_path" >&2
}

# ============================================================================
# Main
# ============================================================================

main() {
  load_env
  check_api_key

  local scenes=() model="" segment_duration=6 resolution="768P"
  local first_frame="" subject_reference="" crossfade=0.5
  local music_prompt="" bgm_volume=0.3 fade_in=0 fade_out=0
  local output=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --scenes)
        shift
        while [[ $# -gt 0 && "$1" != --* ]]; do
          scenes+=("$1"); shift
        done
        ;;
      --model) model="$2"; shift 2 ;;
      --segment-duration) segment_duration="$2"; shift 2 ;;
      --resolution) resolution="$2"; shift 2 ;;
      --first-frame) first_frame="$2"; shift 2 ;;
      --subject-reference) subject_reference="$2"; shift 2 ;;
      --crossfade) crossfade="$2"; shift 2 ;;
      --music-prompt) music_prompt="$2"; shift 2 ;;
      --bgm-volume) bgm_volume="$2"; shift 2 ;;
      --fade-in) fade_in="$2"; shift 2 ;;
      --fade-out) fade_out="$2"; shift 2 ;;
      -o|--output) output="$2"; shift 2 ;;
      -h|--help)
        cat <<'USAGE'
MiniMax Long Video Generation CLI

Usage:
  generate_long_video.sh --scenes "scene1" "scene2" ... -o OUTPUT

Options:
  --scenes TEXT...          Scene prompts (2+ required)
  --model MODEL             Model name (default: auto)
  --segment-duration SECS   Duration per segment (default: 6)
  --resolution RES          Resolution: 512P, 768P (default: 768P)
  --first-frame FILE        First frame for scene 1 (local file or URL)
  --subject-reference FILE  Subject reference image
  --crossfade SECS          Crossfade duration between scenes (default: 0.5)
  --music-prompt TEXT        Generate BGM with this prompt
  --bgm-volume FLOAT        BGM volume level (default: 0.3)
  --fade-in SECS             BGM fade-in duration
  --fade-out SECS            BGM fade-out duration
  -o, --output FILE         Output video file (required)

Examples:
  generate_long_video.sh --scenes "A sunrise" "Birds flying" "Sunset" -o long.mp4
  generate_long_video.sh --scenes "Scene 1" "Scene 2" --crossfade 1 --music-prompt "cinematic" -o movie.mp4
USAGE
        exit 0
        ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done

  if [[ ${#scenes[@]} -eq 0 ]]; then
    echo "Error: --scenes is required" >&2; exit 1
  fi
  if [[ -z "$output" ]]; then
    echo "Error: --output / -o is required" >&2; exit 1
  fi

  if [[ -z "$model" ]]; then
    model="MiniMax-Hailuo-2.3"
  fi
  validate_model_constraints "$model" "$segment_duration" "$resolution"

  local output_dir
  output_dir="$(dirname "$output")"
  mkdir -p "$output_dir"
  local tmpdir="$output_dir/tmp"
  mkdir -p "$tmpdir"
  echo "Temp directory: $tmpdir"

  local segment_paths=()
  local current_first_frame="$first_frame"

  echo "=== Generating ${#scenes[@]} video segments ==="
  echo ""

  for i in "${!scenes[@]}"; do
    local scene="${scenes[$i]}"
    echo "--- Segment $((i+1))/${#scenes[@]} ---"
    echo "  Prompt: $scene"

    local seg_output="$tmpdir/segment_$(printf '%03d' "$i").mp4"

    # Determine mode
    local seg_mode="t2v"
    [[ -n "$current_first_frame" ]] && seg_mode="i2v"
    [[ -n "$subject_reference" && -z "$current_first_frame" ]] && seg_mode="ref"

    # Determine model
    local seg_model="$model"

    # Build payload
    local payload
    payload=$(jq -n \
      --arg m "$seg_model" \
      --arg p "$scene" \
      --argjson d "$segment_duration" \
      --arg r "$resolution" \
      '{model: $m, prompt: $p, duration: $d, resolution: $r}')

    if [[ "$seg_mode" == "i2v" ]]; then
      local ff_url; ff_url="$(resolve_image "$current_first_frame")"
      payload=$(echo "$payload" | jq --arg ff "$ff_url" '. + {first_frame_image: $ff, prompt_optimizer: false}')
    elif [[ "$seg_mode" == "ref" ]]; then
      local si_url; si_url="$(resolve_image "$subject_reference")"
      payload=$(echo "$payload" | jq --arg si "$si_url" '. + {subject_reference: [{type: "character", image: [$si]}]}')
    fi

    # Generate segment
    local task_id file_id
    if task_id="$(_create_task "$payload")" && [[ -n "$task_id" ]]; then
      echo "  Task created: $task_id"
      if file_id="$(_poll_task "$task_id")" && [[ -n "$file_id" ]]; then
        _download_video "$file_id" "$seg_output"
        segment_paths+=("$seg_output")

        # Extract last frame for next segment
        local last_frame_path="$tmpdir/last_frame_$(printf '%03d' "$i").jpg"
        if extract_last_frame "$seg_output" "$last_frame_path"; then
          current_first_frame="$last_frame_path"
        else
          current_first_frame=""
        fi
      else
        echo "  Error: Polling failed for segment $((i+1))" >&2
        [[ ${#segment_paths[@]} -eq 0 ]] && exit 1
        break
      fi
    else
      echo "  Error generating segment $((i+1))" >&2
      [[ ${#segment_paths[@]} -eq 0 ]] && exit 1
      break
    fi
  done

  if [[ ${#segment_paths[@]} -eq 0 ]]; then
    echo "Error: No segments were generated." >&2; exit 1
  fi

  # Concatenate
  local final_video="$output"
  [[ -n "$music_prompt" ]] && final_video="$tmpdir/concatenated.mp4"

  if [[ ${#segment_paths[@]} -eq 1 ]]; then
    cp "${segment_paths[0]}" "$final_video"
  else
    concatenate_videos "$final_video" "$crossfade" "${segment_paths[@]}"
  fi

  # Add BGM if requested
  if [[ -n "$music_prompt" ]]; then
    echo ""
    echo "--- Generating background music ---"
    local music_path="$tmpdir/bgm.mp3"
    if generate_music_instrumental "$music_prompt" "$music_path"; then
      merge_video_audio "$final_video" "$music_path" "$output" "$bgm_volume" "$fade_in" "$fade_out" || {
        echo "Warning: Failed to add BGM, using video without music" >&2
        [[ "$final_video" != "$output" ]] && cp "$final_video" "$output"
      }
    else
      echo "Warning: Failed to generate BGM" >&2
      [[ "$final_video" != "$output" ]] && cp "$final_video" "$output"
    fi
  fi

  echo ""
  echo "=== Done! Output: $output ==="
  echo "  Intermediate files in: $tmpdir"
  echo "  Delete with: rm -rf $tmpdir"
}

main "$@"
