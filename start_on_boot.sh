#!/bin/zsh
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export GROK_API_URL="http://192.168.193.13:8000/v1"
export GROK_API_KEY="grok2api"
DEFAULT_GROK_MODEL="${GROK_MODEL:-grok-4.1-fast}"
UV_BIN="/Users/wzy/.local/bin/uv"
CONFIG_DIR="/Users/wzy/.config/grok-search"
CONFIG_FILE="$CONFIG_DIR/config.json"

mkdir -p "$CONFIG_DIR"
if [ ! -s "$CONFIG_FILE" ]; then
  printf '{\n  "model": "%s"\n}\n' "$DEFAULT_GROK_MODEL" > "$CONFIG_FILE"
fi
export GROK_MODEL="$DEFAULT_GROK_MODEL"

cd /Users/wzy/projects/21-GrokSearch
exec "$UV_BIN" run fastmcp run src/grok_search/server.py:mcp \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port 18001 \
  --path /mcp \
  --log-level INFO \
  --no-banner
