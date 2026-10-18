#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================="
echo "  Antigravity Coding Team Plugin Installer  "
echo "============================================="
echo "Plugin Directory: ${SCRIPT_DIR}"
echo ""

AGY_BIN="$(command -v agy || true)"
if [ -z "$AGY_BIN" ]; then
    if [ -n "$LOCALAPPDATA" ] && [ -f "$LOCALAPPDATA/agy/bin/agy.exe" ]; then
        AGY_BIN="$LOCALAPPDATA/agy/bin/agy.exe"
    elif [ -f "$HOME/.local/bin/agy" ]; then
        AGY_BIN="$HOME/.local/bin/agy"
    else
        echo "Error: 'agy' CLI command not found. Please ensure Antigravity is installed." >&2
        exit 1
    fi
fi

VALIDATE_ONLY=0
for arg in "$@"; do
    if [ "$arg" == "--validate-only" ]; then
        VALIDATE_ONLY=1
    fi
done

echo "[1/3] Validating plugin with 'agy plugin validate --strict'..."
"$AGY_BIN" plugin validate "$SCRIPT_DIR" --strict
echo "Validation passed successfully!"
echo ""

if [ "$VALIDATE_ONLY" -eq 1 ]; then
    echo "Validate-only mode specified. Skipping installation."
    exit 0
fi

echo "[2/3] Installing/Updating plugin in Antigravity..."
"$AGY_BIN" plugin install "$SCRIPT_DIR"
echo "Plugin installed/updated successfully!"
echo ""

echo "[3/3] Verifying installed plugins..."
"$AGY_BIN" plugin list
echo ""
echo "============================================="
echo " Plugin successfully installed / updated!    "
echo "============================================="
echo "NOTE: Restart any active agy sessions to apply changes."
