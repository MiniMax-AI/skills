#!/usr/bin/env bash
# minimax-docx Quick Environment Check
# Cross-platform: macOS, Linux, WSL, Git Bash
# Run this BEFORE any minimax-docx operation. Use setup.sh for initial installation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DOTNET_DIR="$SCRIPT_DIR/dotnet"
CLI_PROJECT="$DOTNET_DIR/MiniMaxAIDocx.Cli/MiniMaxAIDocx.Cli.csproj"
DEFAULT_NUGET_SOURCE="https://api.nuget.org/v3/index.json"

# Force English output for dotnet CLI
export DOTNET_CLI_UI_LANGUAGE=en

echo "=== minimax-docx Environment Check ==="
echo ""

STATUS="READY"
WARNINGS=0

trim() {
    local value="$1"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    printf '%s' "$value"
}

append_default_restore_sources() {
    RESTORE_SOURCE_ARGS+=("--source" "$DEFAULT_NUGET_SOURCE")
    RESTORE_SOURCE_LABELS+=("$DEFAULT_NUGET_SOURCE")

    local local_feed
    for local_feed in "$DOTNET_DIR/packages" "$PROJECT_DIR/assets/nuget"; do
        if [ -d "$local_feed" ]; then
            RESTORE_SOURCE_ARGS+=("--source" "$local_feed")
            RESTORE_SOURCE_LABELS+=("$local_feed")
        fi
    done
}

collect_restore_sources() {
    RESTORE_SOURCE_ARGS=()
    RESTORE_SOURCE_LABELS=()

    local raw_sources="${MINIMAX_DOCX_NUGET_SOURCES:-}"
    local source

    if [ -n "$raw_sources" ]; then
        local OLDIFS="$IFS"
        IFS=';'
        read -r -a configured_sources <<< "$raw_sources"
        IFS="$OLDIFS"

        for source in "${configured_sources[@]}"; do
            source="$(trim "$source")"
            [ -n "$source" ] || continue
            RESTORE_SOURCE_ARGS+=("--source" "$source")
            RESTORE_SOURCE_LABELS+=("$source")
        done

        if [ "${#RESTORE_SOURCE_ARGS[@]}" -gt 0 ]; then
            return
        fi
    fi

    append_default_restore_sources
}

quote_for_display() {
    local value="$1"
    printf '"%s"' "$value"
}

# --- Detect platform ---
OS="unknown"
case "$(uname -s)" in
    Darwin)  OS="macos" ;;
    Linux)
        OS="linux"
        grep -qi microsoft /proc/version 2>/dev/null && OS="wsl"
        ;;
    MINGW*|MSYS*|CYGWIN*) OS="windows-shell" ;;
esac

# --- Critical: .NET SDK ---
if ! command -v dotnet &>/dev/null; then
    printf "[FAIL]    %-14s not found\n" "dotnet"
    echo ""
    echo "  .NET SDK is REQUIRED. Install it:"
    case "$OS" in
        macos)   echo "    brew install --cask dotnet-sdk" ;;
        linux|wsl)
            echo "    # Option 1: Microsoft install script"
            echo "    wget https://dot.net/v1/dotnet-install.sh -O /tmp/dotnet-install.sh"
            echo "    chmod +x /tmp/dotnet-install.sh && /tmp/dotnet-install.sh --channel 8.0"
            echo "    # Option 2 (Ubuntu/Debian): sudo apt-get install -y dotnet-sdk-8.0"
            ;;
        windows-shell) echo "    winget install Microsoft.DotNet.SDK.8" ;;
        *) echo "    https://dotnet.microsoft.com/download" ;;
    esac
    echo ""
    echo "  Or run the full setup: bash scripts/setup.sh"
    echo ""
    STATUS="NOT READY"
else
    local_ver=$(dotnet --version 2>/dev/null || echo "0.0.0")
    local_major="${local_ver%%.*}"
    if [ "$local_major" -ge 8 ] 2>/dev/null; then
        printf "[OK]      %-14s %s (>= 8.0)\n" "dotnet" "$local_ver"
    else
        printf "[FAIL]    %-14s %s (requires >= 8.0)\n" "dotnet" "$local_ver"
        STATUS="NOT READY"
    fi
fi

# --- Critical: NuGet packages ---
if [ -d "$DOTNET_DIR" ]; then
    collect_restore_sources
    if [ -f "$DOTNET_DIR/MiniMaxAIDocx.Cli/bin/Debug/net10.0/MiniMaxAIDocx.Cli.dll" ] || \
       [ -f "$DOTNET_DIR/MiniMaxAIDocx.Cli/bin/Debug/net8.0/MiniMaxAIDocx.Cli.dll" ]; then
        printf "[OK]      %-14s built\n" "project"
    else
        # Try restore + build
        if dotnet restore "$CLI_PROJECT" --verbosity quiet --ignore-failed-sources "${RESTORE_SOURCE_ARGS[@]}" &>/dev/null; then
            printf "[OK]      %-14s packages restored\n" "nuget"
            if dotnet build "$CLI_PROJECT" --verbosity quiet --no-restore &>/dev/null; then
                printf "[OK]      %-14s build succeeded\n" "project"
            else
                printf "[FAIL]    %-14s build failed (run: dotnet build %s)\n" "project" "$(quote_for_display "$CLI_PROJECT")"
                STATUS="NOT READY"
            fi
        else
            printf "[FAIL]    %-14s restore failed\n" "nuget"
            echo ""
            echo "  Common causes:"
            echo "    - No internet access to the configured NuGet source(s)"
            echo "    - Corporate proxy or sandbox DNS blocking nuget.org"
            echo "    - Custom/local feed missing required packages"
            echo "    - SSL certificate issues (try: dotnet nuget list source)"
            echo "  Source(s): ${RESTORE_SOURCE_LABELS[*]}"
            echo "  Override sources: export MINIMAX_DOCX_NUGET_SOURCES='https://mirror.example/v3/index.json;/path/to/local/feed'"
            echo ""
            STATUS="NOT READY"
        fi
    fi
else
    printf "[FAIL]    %-14s directory not found: %s\n" "project" "$DOTNET_DIR"
    STATUS="NOT READY"
fi

# --- Optional: pandoc ---
if command -v pandoc &>/dev/null; then
    pandoc_ver=$(pandoc --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || echo "?")
    printf "[OK]      %-14s %s (content preview)\n" "pandoc" "$pandoc_ver"
else
    printf "[WARN]    %-14s not found — docx_preview.sh will use fallback\n" "pandoc"
    WARNINGS=$((WARNINGS + 1))
    case "$OS" in
        macos)        echo "           Install: brew install pandoc" ;;
        linux|wsl)    echo "           Install: sudo apt-get install pandoc  # or dnf/pacman" ;;
        windows-shell) echo "           Install: winget install JohnMacFarlane.Pandoc" ;;
    esac
fi

# --- Optional: LibreOffice ---
if command -v soffice &>/dev/null; then
    soffice_ver=$(soffice --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+(\.[0-9]+)?' | head -1 || echo "?")
    printf "[OK]      %-14s %s (.doc conversion)\n" "soffice" "$soffice_ver"
else
    # Check common paths
    soffice_found=false
    for p in \
        "/Applications/LibreOffice.app/Contents/MacOS/soffice" \
        "/usr/lib/libreoffice/program/soffice" \
        "/snap/bin/libreoffice" \
        "/opt/libreoffice/program/soffice"; do
        if [ -x "$p" ]; then
            printf "[OK]      %-14s found at %s (.doc conversion)\n" "soffice" "$p"
            soffice_found=true
            break
        fi
    done
    if ! $soffice_found; then
        printf "[WARN]    %-14s not found — .doc files cannot be converted\n" "soffice"
        WARNINGS=$((WARNINGS + 1))
        case "$OS" in
            macos)        echo "           Install: brew install --cask libreoffice" ;;
            linux|wsl)    echo "           Install: sudo apt-get install libreoffice-core" ;;
            windows-shell) echo "           Install: winget install TheDocumentFoundation.LibreOffice" ;;
        esac
    fi
fi

# --- Optional: zip/unzip ---
zip_ok=true
if ! command -v zip &>/dev/null; then
    printf "[WARN]    %-14s not found (optional, .NET handles DOCX natively)\n" "zip"
    zip_ok=false
    WARNINGS=$((WARNINGS + 1))
fi
if ! command -v unzip &>/dev/null; then
    printf "[WARN]    %-14s not found (optional, .NET handles DOCX natively)\n" "unzip"
    zip_ok=false
    WARNINGS=$((WARNINGS + 1))
fi
if $zip_ok; then
    printf "[OK]      %-14s available\n" "zip/unzip"
fi

# --- Encoding check ---
current_lang="${LANG:-}"
if [ -n "$current_lang" ] && echo "$current_lang" | grep -qi "utf-8\|utf8"; then
    printf "[OK]      %-14s %s\n" "locale" "$current_lang"
else
    if [ -z "$current_lang" ]; then
        printf "[WARN]    %-14s LANG not set (CJK text may have issues)\n" "locale"
    else
        printf "[WARN]    %-14s %s (not UTF-8, CJK text may have issues)\n" "locale" "$current_lang"
    fi
    WARNINGS=$((WARNINGS + 1))
    echo "           Fix: export LANG=en_US.UTF-8"
fi

# --- Shell script permissions ---
perm_issues=0
for s in "$SCRIPT_DIR"/*.sh; do
    if [ -f "$s" ] && [ ! -x "$s" ]; then
        perm_issues=$((perm_issues + 1))
    fi
done
if [ "$perm_issues" -gt 0 ]; then
    printf "[WARN]    %-14s %d script(s) not executable\n" "permissions" "$perm_issues"
    echo "           Fix: chmod +x scripts/*.sh"
    WARNINGS=$((WARNINGS + 1))
else
    printf "[OK]      %-14s all scripts executable\n" "permissions"
fi

# --- Result ---
echo ""
if [ "$STATUS" = "READY" ]; then
    if [ "$WARNINGS" -gt 0 ]; then
        echo "Status: READY (with $WARNINGS warning(s) — optional features may be limited)"
    else
        echo "Status: READY"
    fi
else
    echo "Status: NOT READY"
    echo ""
    echo "Critical dependencies missing. Run the full setup:"
    echo "  bash scripts/setup.sh          # macOS / Linux / WSL"
    echo "  powershell scripts/setup.ps1   # Windows PowerShell"
    exit 1
fi
