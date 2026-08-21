#!/usr/bin/env python3
"""Compatibility entrypoint for local STDIO MCP clients."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent / "codex-plugin" / "telegram-mcp" / "mcp_server" / "src"),
)

from telegram_mcp.server import run_server


if __name__ == "__main__":
    run_server()
