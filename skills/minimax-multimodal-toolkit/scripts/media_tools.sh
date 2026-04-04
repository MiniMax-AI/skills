#!/usr/bin/env bash
# MiniMax Multi-Modal Toolkit Media Tools CLI (pure bash)
#
# FFmpeg-based utilities for audio/video format conversion, concatenation,
# extraction, and trimming.
#
# Usage:
#   bash scripts/media_tools.sh convert-video input.webm -o output.mp4
#   bash scripts/media_tools.sh convert-audio input.wav -o output.mp3
#   bash scripts/media_tools.sh concat-video seg1.mp4 seg2.mp4 -o merged.mp4
#   bash scripts/media_tools.sh concat-audio part1.mp3 part2.mp3 -o combined.mp3
#   bash scripts/media_tools.sh extract-audio input.mp4 -o audio.mp3
#   bash scripts/media_tools.sh trim-video input.mp4 --start 5 --end 15 -o clip.mp4
#   bash scripts/media_tools.sh add-audio --video video.mp4 --audio bgm.mp3 -o output.mp4
#   bash scripts/media_tools.sh probe input.mp4
set -euo pipefail

# ============================================================================
# Probe / info helpers
# ============================================================================

probe_media() {
  ffprobe -v error -show_format -show_streams -of json "$1" 2>/dev/null
}

get_duration() {
  probe_media "$1" | jq -r '.format.duration // "0"'
}

get_video_fps() {
  local fps_str
  fps_str="$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$1" 2>/dev/null)" || { echo 25; return; }
  local num="${fps_str%/*}" den="${fps_str#*/}"
  echo $(( (num + den/2) / den )) 2>/dev/null || echo 25
}

has_audio_stream() {
  local out
  out="$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$1" 2>/dev/null)"
  [[ "$out" == *audio* ]]
}

has_video_stream() {
  local out
  out="$(ffprobe -v error -select_streams v -show_entries stream=codec_type -of csv=p=0 "$1" 2>/dev/null)"
  [[ "$out" == *video* ]]
}

# ============================================================================
# Video codec maps
# ============================================================================

video_codec_for() {
  case "$1" in
    mp4|mov|mkv|avi|ts|flv) echo "libx264" ;;
    webm) echo "libvpx-vp9" ;;
    *) echo "libx264" ;;
  esac
}

audio_codec_for_container() {
  case "$1" in
    mp4|mov|mkv|ts|flv) echo "aac" ;;
    webm) echo "libopus" ;;
    avi) echo "mp3" ;;
    *) echo "aac" ;;
  esac
}

audio_codec_for_format() {
  case "$1" in
    mp3) echo "libmp3lame" ;;
    wav) echo "pcm_s16le" ;;
    flac) echo "flac" ;;
    ogg) echo "libvorbis" ;;
    aac|m4a) echo "aac" ;;
    opus) echo "libopus" ;;
    wma) echo "wmav2" ;;
    *) echo "libmp3lame" ;;
  esac
}

get_ext() {
  local name="$1"
  echo "${name##*.}" | tr '[:upper:]' '[:lower:]'
}

# ============================================================================
# Subcommand: convert-video
# ============================================================================
cmd_convert_video() {
  local input="" output="" crf=18 preset="medium" resolution="" fps=""

  if [[ $# -gt 0 && "$1" != -* ]]; then input="$1"; shift; fi
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --crf) crf="$2"; shift 2 ;;
      --preset) preset="$2"; shift 2 ;;
      --resolution) resolution="$2"; shift 2 ;;
      --fps) fps="$2"; shift 2 ;;
      *) [[ -z "$input" ]] && input="$1"; shift ;;
    esac
  done

  [[ -z "$input" || ! -f "$input" ]] && { echo "Error: Input file not found: ${input:-<none>}" >&2; exit 1; }
  [[ -z "$output" ]] && { echo "Error: -o/--output required" >&2; exit 1; }

  local ext; ext="$(get_ext "$output")"
  local v_codec; v_codec="$(video_codec_for "$ext")"
  local a_codec; a_codec="$(audio_codec_for_container "$ext")"

  mkdir -p "$(dirname "$output")"

  local cmd=(ffmpeg -y -i "$input")

  # Video filters
  if [[ -n "$resolution" ]]; then
    local w="${resolution%%x*}" h="${resolution##*x}"
    cmd+=(-vf "scale=${w}:${h}")
  fi

  cmd+=(-c:v "$v_codec")
  case "$v_codec" in
    libx264|libx265) cmd+=(-crf "$crf" -preset "$preset" -pix_fmt yuv420p) ;;
    libvpx-vp9) cmd+=(-crf "$crf" -b:v 0) ;;
  esac

  [[ -n "$fps" ]] && cmd+=(-r "$fps")

  if has_audio_stream "$input"; then
    cmd+=(-c:a "$a_codec" -b:a 192k)
  else
    cmd+=(-an)
  fi

  cmd+=("$output")

  echo "Converting: $input -> $output ($v_codec/$a_codec)"
  "${cmd[@]}" 2>/dev/null
  echo "  Done: $output"
}

# ============================================================================
# Subcommand: convert-audio
# ============================================================================
cmd_convert_audio() {
  local input="" output="" bitrate="192k" sample_rate="" channels=""

  if [[ $# -gt 0 && "$1" != -* ]]; then input="$1"; shift; fi
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --bitrate) bitrate="$2"; shift 2 ;;
      --sample-rate) sample_rate="$2"; shift 2 ;;
      --channels) channels="$2"; shift 2 ;;
      *) [[ -z "$input" ]] && input="$1"; shift ;;
    esac
  done

  [[ -z "$input" || ! -f "$input" ]] && { echo "Error: Input file not found: ${input:-<none>}" >&2; exit 1; }
  [[ -z "$output" ]] && { echo "Error: -o/--output required" >&2; exit 1; }

  local ext; ext="$(get_ext "$output")"
  local codec; codec="$(audio_codec_for_format "$ext")"

  mkdir -p "$(dirname "$output")"

  local cmd=(ffmpeg -y -i "$input" -c:a "$codec" -b:a "$bitrate")
  [[ -n "$sample_rate" ]] && cmd+=(-ar "$sample_rate")
  [[ -n "$channels" ]] && cmd+=(-ac "$channels")
  cmd+=("$output")

  echo "Converting audio: $input -> $output ($codec)"
  "${cmd[@]}" 2>/dev/null
  echo "  Done: $output"
}

# ============================================================================
# Subcommand: concat-video
# ============================================================================
cmd_concat_video() {
  local output="" crossfade=0.5
  local inputs=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --crossfade) crossfade="$2"; shift 2 ;;
      *) inputs+=("$1"); shift ;;
    esac
  done

  [[ ${#inputs[@]} -lt 2 ]] && { echo "Error: At least 2 input files required" >&2; exit 1; }
  [[ -z "$output" ]] && { echo "Error: -o/--output required" >&2; exit 1; }

  mkdir -p "$(dirname "$output")"

  if [[ ${#inputs[@]} -eq 1 ]]; then
    cp "${inputs[0]}" "$output"
    return 0
  fi

  local fps; fps="$(get_video_fps "${inputs[0]}")"
  local has_audio=true
  for vp in "${inputs[@]}"; do
    has_audio_stream "$vp" || { has_audio=false; break; }
  done

  if [[ "$(echo "$crossfade > 0" | bc -l)" == "1" ]]; then
    local durations=()
    for vp in "${inputs[@]}"; do durations+=("$(get_duration "$vp")"); done

    local ff_inputs=()
    for vp in "${inputs[@]}"; do ff_inputs+=(-i "$(cd "$(dirname "$vp")" && pwd)/$(basename "$vp")"); done

    local n=${#inputs[@]}
    local offsets=() cumulative=0
    for ((i=0; i<n-1; i++)); do
      local offset; offset="$(echo "$cumulative + ${durations[$i]} - $crossfade" | bc -l)"
      offsets+=("$offset"); cumulative="$offset"
    done

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

    local fc
    fc="$(IFS=';'; echo "${vf_parts[*]}${af_parts[*]:+;${af_parts[*]}}")"

    local cmd=(ffmpeg -y "${ff_inputs[@]}" -filter_complex "$fc" -map "[vout]")
    $has_audio && cmd+=(-map "[aout]")
    cmd+=(-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r "$fps")
    $has_audio && cmd+=(-c:a aac -b:a 192k)
    cmd+=("$output")

    echo "Concatenating $n videos with ${crossfade}s crossfade..."
    if "${cmd[@]}" 2>/dev/null; then
      echo "  Done: $output"
      return 0
    fi
    echo "  Crossfade failed, falling back to re-encode..."
  fi

  # Fallback
  local concat_file; concat_file="$(mktemp /tmp/concat_XXXXXX.txt)"
  for vp in "${inputs[@]}"; do
    echo "file '$(cd "$(dirname "$vp")" && pwd)/$(basename "$vp")'" >> "$concat_file"
  done
  ffmpeg -y -f concat -safe 0 -i "$concat_file" \
    -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r "$fps" \
    -c:a aac -b:a 192k "$output" 2>/dev/null
  rm -f "$concat_file"
  echo "  Done: $output"
}

# ============================================================================
# Subcommand: concat-audio
# ============================================================================
cmd_concat_audio() {
  local output="" crossfade=0
  local inputs=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --crossfade) crossfade="$2"; shift 2 ;;
      *) inputs+=("$1"); shift ;;
    esac
  done

  [[ ${#inputs[@]} -lt 1 ]] && { echo "Error: At least 1 input file required" >&2; exit 1; }
  [[ -z "$output" ]] && { echo "Error: -o/--output required" >&2; exit 1; }

  mkdir -p "$(dirname "$output")"

  if [[ ${#inputs[@]} -eq 1 ]]; then
    cp "${inputs[0]}" "$output"
    echo "  Done: $output"
    return 0
  fi

  local ext; ext="$(get_ext "$output")"
  local codec; codec="$(audio_codec_for_format "$ext")"
  local n=${#inputs[@]}

  if [[ "$(echo "$crossfade > 0" | bc -l)" == "1" ]]; then
    local ff_inputs=()
    for ap in "${inputs[@]}"; do ff_inputs+=(-i "$(cd "$(dirname "$ap")" && pwd)/$(basename "$ap")"); done

    local af_parts=()
    if [[ $n -eq 2 ]]; then
      af_parts+=("[0:a][1:a]acrossfade=d=${crossfade}:c1=tri:c2=tri[aout]")
    else
      af_parts+=("[0:a][1:a]acrossfade=d=${crossfade}:c1=tri:c2=tri[xa1]")
      for ((i=2; i<n; i++)); do
        local prev="[xa$((i-1))]" out="[xa${i}]"
        [[ $i -eq $((n-1)) ]] && out="[aout]"
        af_parts+=("${prev}[${i}:a]acrossfade=d=${crossfade}:c1=tri:c2=tri${out}")
      done
    fi

    local fc; fc="$(IFS=';'; echo "${af_parts[*]}")"

    echo "Concatenating $n audio files with ${crossfade}s crossfade..."
    if ffmpeg -y "${ff_inputs[@]}" -filter_complex "$fc" -map "[aout]" \
      -c:a "$codec" -b:a 192k "$output" 2>/dev/null; then
      echo "  Done: $output"
      return 0
    fi
    echo "  Crossfade failed, falling back..."
  fi

  # Fallback: concat demuxer
  local concat_file; concat_file="$(mktemp /tmp/concat_XXXXXX.txt)"
  for ap in "${inputs[@]}"; do
    echo "file '$(cd "$(dirname "$ap")" && pwd)/$(basename "$ap")'" >> "$concat_file"
  done
  ffmpeg -y -f concat -safe 0 -i "$concat_file" -c:a "$codec" -b:a 192k "$output" 2>/dev/null
  rm -f "$concat_file"
  echo "  Done: $output"
}

# ============================================================================
# Subcommand: extract-audio
# ============================================================================
cmd_extract_audio() {
  local input="" output="" bitrate="192k"

  if [[ $# -gt 0 && "$1" != -* ]]; then input="$1"; shift; fi
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --bitrate) bitrate="$2"; shift 2 ;;
      *) [[ -z "$input" ]] && input="$1"; shift ;;
    esac
  done

  [[ -z "$input" || ! -f "$input" ]] && { echo "Error: Input not found: ${input:-<none>}" >&2; exit 1; }
  [[ -z "$output" ]] && { echo "Error: -o/--output required" >&2; exit 1; }
  has_audio_stream "$input" || { echo "Error: No audio stream in $input" >&2; exit 1; }

  local ext; ext="$(get_ext "$output")"
  local codec; codec="$(audio_codec_for_format "$ext")"

  mkdir -p "$(dirname "$output")"

  echo "Extracting audio: $input -> $output"
  ffmpeg -y -i "$input" -vn -c:a "$codec" -b:a "$bitrate" "$output" 2>/dev/null
  echo "  Done: $output"
}

# ============================================================================
# Subcommand: trim-video
# ============================================================================
cmd_trim_video() {
  local input="" output="" start="" end="" duration=""

  if [[ $# -gt 0 && "$1" != -* ]]; then input="$1"; shift; fi
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -o|--output) output="$2"; shift 2 ;;
      --start) start="$2"; shift 2 ;;
      --end) end="$2"; shift 2 ;;
      --duration) duration="$2"; shift 2 ;;
      *) [[ -z "$input" ]] && input="$1"; shift ;;
    esac
  done

  [[ -z "$input" || ! -f "$input" ]] && { echo "Error: Input not found: ${input:-<none>}" >&2; exit 1; }
  [[ -z "$output" ]] && { echo "Error: -o/--output required" >&2; exit 1; }

  mkdir -p "$(dirname "$output")"

  local cmd=(ffmpeg -y)
  [[ -n "$start" ]] && cmd+=(-ss "$start")
  cmd+=(-i "$input")

  if [[ -n "$duration" ]]; then
    cmd+=(-t "$duration")
  elif [[ -n "$end" ]]; then
    local actual_start="${start:-0}"
    local dur; dur="$(echo "$end - $actual_start" | bc -l)"
    cmd+=(-t "$dur")
  fi

  cmd+=(-c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p)
  has_audio_stream "$input" && cmd+=(-c:a aac -b:a 192k)
  cmd+=("$output")

  local start_str="${start:-0}s"
  local end_str="${end:+${end}s}"
  [[ -z "$end_str" && -n "$duration" ]] && end_str="+${duration}s"
  [[ -z "$end_str" ]] && end_str="end"
  echo "Trimming: $input [$start_str - $end_str] -> $output"
  "${cmd[@]}" 2>/dev/null
  echo "  Done: $output"
}

# ============================================================================
# Subcommand: add-audio
# ============================================================================
cmd_add_audio() {
  local video="" audio="" output="" volume=1.0 fade_in=0 fade_out=0 replace=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --video) video="$2"; shift 2 ;;
      --audio) audio="$2"; shift 2 ;;
      -o|--output) output="$2"; shift 2 ;;
      --volume) volume="$2"; shift 2 ;;
      --fade-in) fade_in="$2"; shift 2 ;;
      --fade-out) fade_out="$2"; shift 2 ;;
      --replace) replace=true; shift ;;
      *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
  done

  [[ -z "$video" || ! -f "$video" ]] && { echo "Error: Video not found: ${video:-<none>}" >&2; exit 1; }
  [[ -z "$audio" || ! -f "$audio" ]] && { echo "Error: Audio not found: ${audio:-<none>}" >&2; exit 1; }
  [[ -z "$output" ]] && { echo "Error: -o/--output required" >&2; exit 1; }

  mkdir -p "$(dirname "$output")"

  local duration; duration="$(get_duration "$video")"
  local video_audio=false
  has_audio_stream "$video" && video_audio=true

  local af="[1:a]volume=${volume}"
  [[ "$(echo "$fade_in > 0" | bc -l)" == "1" ]] && af+=",afade=t=in:d=${fade_in}"
  if [[ "$(echo "$fade_out > 0" | bc -l)" == "1" ]]; then
    local fo_start; fo_start="$(echo "$duration - $fade_out" | bc -l)"
    [[ "$(echo "$fo_start < 0" | bc -l)" == "1" ]] && fo_start=0
    af+=",afade=t=out:st=${fo_start}:d=${fade_out}"
  fi

  if $video_audio && ! $replace; then
    af+="[newaudio];[0:a][newaudio]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    local mode="mixing with"
  else
    af+="[aout]"
    local mode="replacing"
  fi

  echo "Adding audio ($mode original): $output"
  ffmpeg -y -i "$video" -i "$audio" \
    -filter_complex "$af" \
    -map 0:v -map "[aout]" \
    -c:v copy -c:a aac -b:a 192k -shortest "$output" 2>/dev/null
  echo "  Done: $output"
}

# ============================================================================
# Subcommand: probe
# ============================================================================
cmd_probe() {
  local input=""
  if [[ $# -gt 0 ]]; then input="$1"; fi

  [[ -z "$input" || ! -f "$input" ]] && { echo "Error: File not found: ${input:-<none>}" >&2; exit 1; }

  local info; info="$(probe_media "$input")"

  local fmt_name dur size br
  fmt_name="$(echo "$info" | jq -r '.format.format_long_name // "unknown"')"
  dur="$(echo "$info" | jq -r '.format.duration // "0"')"
  size="$(echo "$info" | jq -r '.format.size // "0"')"
  br="$(echo "$info" | jq -r '.format.bit_rate // "0"')"

  echo "File:     $input"
  echo "Format:   $fmt_name"
  printf "Duration: %.2fs\n" "$dur"
  printf "Size:     %.2f MB\n" "$(echo "$size / 1048576" | bc -l)"
  printf "Bitrate:  %.0f kbps\n" "$(echo "$br / 1000" | bc -l)"

  echo "$info" | jq -r '.streams[] | if .codec_type == "video" then "Video:    \(.codec_name) \(.width)x\(.height) @ \(.r_frame_rate) fps" elif .codec_type == "audio" then "Audio:    \(.codec_name) \(.sample_rate)Hz \(.channels)ch" else empty end'
}

# ============================================================================
# Main dispatcher
# ============================================================================

usage() {
  cat <<'EOF'
MiniMax Multi-Modal Toolkit Media Tools

Usage:
  media_tools.sh <command> [options]

Commands:
  convert-video  Convert video format
  convert-audio  Convert audio format
  concat-video   Concatenate videos with crossfade
  concat-audio   Concatenate audio files
  extract-audio  Extract audio from video
  trim-video     Trim video by time range
  add-audio      Add/overlay audio on video
  probe          Show media file info

Examples:
  media_tools.sh convert-video input.webm -o output.mp4
  media_tools.sh convert-audio input.wav -o output.mp3
  media_tools.sh concat-video seg1.mp4 seg2.mp4 -o merged.mp4
  media_tools.sh extract-audio video.mp4 -o audio.mp3
  media_tools.sh trim-video input.mp4 --start 5 --end 15 -o clip.mp4
  media_tools.sh add-audio --video video.mp4 --audio bgm.mp3 -o output.mp4
  media_tools.sh probe input.mp4
EOF
}

main() {
  if [[ $# -eq 0 ]]; then
    usage; exit 0
  fi

  local command="$1"; shift

  case "$command" in
    convert-video) cmd_convert_video "$@" ;;
    convert-audio) cmd_convert_audio "$@" ;;
    concat-video) cmd_concat_video "$@" ;;
    concat-audio) cmd_concat_audio "$@" ;;
    extract-audio) cmd_extract_audio "$@" ;;
    trim-video) cmd_trim_video "$@" ;;
    add-audio) cmd_add_audio "$@" ;;
    probe) cmd_probe "$@" ;;
    -h|--help|help) usage ;;
    *) echo "Unknown command: $command" >&2; usage >&2; exit 1 ;;
  esac
}

main "$@"
