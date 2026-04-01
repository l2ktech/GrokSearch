#!/bin/zsh
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export GROK_API_URL="http://192.168.193.13:8000/v1"
export GROK_API_KEY="grok2api"
export GROK_MODEL="grok-4.20-beta"
UV_BIN="/Users/wzy/.local/bin/uv"
CONFIG_DIR="/Users/wzy/.config/grok-search"
CONFIG_FILE="$CONFIG_DIR/config.json"

mkdir -p "$CONFIG_DIR"
printf '{\n  "model": "%s"\n}\n' "$GROK_MODEL" > "$CONFIG_FILE"

cd /Users/wzy/projects/21-GrokSearch
exec "$UV_BIN" run fastmcp run src/grok_search/server.py:mcp \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port 18001 \
  --path /mcp \
  --log-level INFO \
  --no-banner
