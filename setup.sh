#!/usr/bin/env bash
# Safe local setup for macOS and Linux.
set -euo pipefail

cd "$(dirname "$0")"

python_is_supported() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
    >/dev/null 2>&1
}

find_python() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    if command -v "$PYTHON_BIN" >/dev/null 2>&1 && python_is_supported "$PYTHON_BIN"; then
      printf '%s\n' "$PYTHON_BIN"
      return 0
    fi
    echo "PYTHON_BIN does not point to Python 3.10 or newer." >&2
    return 1
  fi

  local candidate
  for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && python_is_supported "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  echo "Python 3.10 or newer was not found." >&2
  echo "Install it from https://www.python.org/downloads/ and run this script again." >&2
  return 1
}

PYTHON_BIN="$(find_python)"
echo "==> Using $($PYTHON_BIN --version 2>&1)"

echo "==> Creating venv (.venv)"
if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi

if ! .venv/bin/python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
  echo "The existing .venv uses an unsupported Python version." >&2
  echo "Rename or remove .venv, then run setup.sh again." >&2
  exit 1
fi

echo "==> Installing dependencies (telethon, mcp, python-dotenv)"
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
  echo ""
  echo "A local .env file was created."
  echo "Open it and fill TELEGRAM_API_ID and TELEGRAM_API_HASH from https://my.telegram.org."
  echo "Do not paste API_HASH into an AI chat. Then run bash setup.sh again."
  exit 2
fi

chmod 600 .env
if ! grep -Eq '^TELEGRAM_API_ID=[0-9]+[[:space:]]*$' .env || \
   ! grep -Eq '^TELEGRAM_API_HASH=[0-9A-Fa-f]{32}[[:space:]]*$' .env; then
  echo "The .env file does not contain a valid TELEGRAM_API_ID and TELEGRAM_API_HASH." >&2
  echo "Edit .env locally. Secret values will not be printed." >&2
  exit 2
fi

echo ""
echo "==> Logging in to Telegram (first time only)"
echo "    You will be asked for your phone number and the login code."
.venv/bin/python login.py --account default

PYTHON_PATH="$(pwd)/.venv/bin/python"
SERVER_PATH="$(pwd)/telegram_mcp_server.py"

echo ""
echo "==> Done! Register the server in your agent:"
echo ""
echo "  Codex:       codex mcp add telegram -- \"$PYTHON_PATH\" \"$SERVER_PATH\""
echo "  Claude Code: claude mcp add --transport stdio --scope user telegram -- \"$PYTHON_PATH\" \"$SERVER_PATH\""
echo ""
echo "See README.md for desktop apps and other MCP clients."
