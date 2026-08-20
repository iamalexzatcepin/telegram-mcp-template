#!/bin/bash
set -euo pipefail
cd /opt/projects/telegram-mcp-template
if [ ! -d .venv ]; then
  /usr/bin/python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet "mcp>=1.0,<2" telethon python-dotenv
echo "deps ok"
python -c "from mcp.server.fastmcp import FastMCP; print('FastMCP import OK')"
if [ ! -f .env ]; then
  AI=$(grep -oP '(?<=^TELEGRAM_API_ID=).*' /root/.hermes/secret.env)
  AH=$(grep -oP '(?<=^TELEGRAM_API_HASH=).*' /root/.hermes/secret.env)
  printf 'TELEGRAM_API_ID=%s\nTELEGRAM_API_HASH=%s\n' "$AI" "$AH" > .env
  echo ".env written"
fi
echo "env ready"
