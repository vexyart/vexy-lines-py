#!/usr/bin/env bash
# install.sh - Install vexy-lines-py in editable mode
# Vexy Lines is a macOS vector art application.
# Pure-Python parser for the Vexy Lines .lines vector art format.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Installing vexy-lines-py in editable mode..."
uv pip install --system -e .

echo "==> Install complete."
