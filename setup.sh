#!/usr/bin/env bash
# One-shot setup for the Telegram MCP server.
# Usage: bash setup.sh
# Creates venv, installs deps, runs first login (asks for your Telegram phone + code).
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Creating venv (.venv)"
if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing dependencies (telethon, mcp, python-dotenv)"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet "mcp>=1.0,<2" telethon python-dotenv

if [ ! -f .env ]; then
  echo ""
  echo "!! No .env found. Copy the template:"
  echo "    cp .env.example .env"
  echo "  then fill TELEGRAM_API_ID and TELEGRAM_API_HASH (from https://my.telegram.org -> API development tools)"
  echo ""
  exit 1
fi

echo ""
echo "==> Logging in to Telegram (first time only)"
echo "    You will be asked for your phone number and the login code."
python login.py

echo ""
echo "==> Done! Register the server in your agent:"
echo ""
echo "  Codex:        codex mcp add telegram -- python \"$(pwd)/telegram_mcp_server.py\""
echo "  Claude Code:  claude mcp add telegram -- python \"$(pwd)/telegram_mcp_server.py\""
echo ""
echo "Test: codex exec 'Use telegram list_chats to show my first 10 chats'"
