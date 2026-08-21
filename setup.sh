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

echo "==> Installing Telegram MCP v2"
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -e .

echo ""
echo "==> Choosing permissions"
.venv/bin/telegram-mcp setup

echo ""
echo "==> Logging in locally"
echo "    API hash, login code, and 2FA are entered only in this terminal."
.venv/bin/telegram-mcp login

PYTHON_PATH="$(pwd)/.venv/bin/python"
SERVER_PATH="$(pwd)/telegram_mcp_server.py"

echo ""
echo "==> Done! Register the server in your agent:"
echo ""
echo "  Codex:       codex mcp add telegram -- \"$PYTHON_PATH\" \"$SERVER_PATH\""
echo "  Claude Code: claude mcp add --transport stdio --scope user telegram -- \"$PYTHON_PATH\" \"$SERVER_PATH\""
echo ""
echo "Run '.venv/bin/telegram-mcp permissions' to inspect the exact exposed tools."
echo "See README.md for the Codex plugin and other MCP clients."
