#!/bin/zsh
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export GROK_API_URL="http://192.168.193.13:8000/v1"
export GROK_API_KEY="grok2api"
UV_BIN="/Users/wzy/.local/bin/uv"

cd /Users/wzy/projects/21-GrokSearch
exec "$UV_BIN" run fastmcp run src/grok_search/server.py:mcp \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port 18001 \
  --path /mcp \
  --log-level INFO \
  --no-banner
