"""Deprecated v1 import shim backed by the secure v2 session store."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent / "codex-plugin" / "telegram-mcp" / "mcp_server" / "src"),
)

from telethon import TelegramClient
from telethon.sessions import StringSession

from telegram_mcp.session_store import load_session
from telegram_mcp.tools.common import display_name


def get_client(account: str = "default") -> TelegramClient:
    stored = load_session(account)
    return TelegramClient(StringSession(stored.session_string), stored.api_id, stored.api_hash)


def chat_ref(entity) -> str:
    username = getattr(entity, "username", None)
    return f"@{username}" if username else str(getattr(entity, "id", "unknown"))
