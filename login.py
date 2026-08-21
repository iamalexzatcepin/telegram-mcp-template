#!/usr/bin/env python3
"""Compatibility login entrypoint; secrets are handled only in the local terminal."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent / "codex-plugin" / "telegram-mcp" / "mcp_server" / "src"),
)

from telegram_mcp.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["login", *sys.argv[1:]]))
