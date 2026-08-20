#!/usr/bin/env python3
"""Read-only Telegram MTProto helpers for the Telegram MCP template.

Secrets are loaded from .env next to this file (or environment variables).
This module intentionally exposes only read/list/search helpers.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telethon import TelegramClient

# Config files searched in order: .env next to this file, then env vars.
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SESSION_DIR = BASE_DIR / "sessions"
DEFAULT_ACCOUNT = "default"


def load_settings(account: Optional[str] = None) -> tuple[int, str, Path]:
    # Prefer explicit env vars, then .env file in repo dir.
    load_dotenv(BASE_DIR / ".env", override=False)

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    # Fallback for local machines that already have Hermes-style secrets.
    if not api_id or not api_hash:
        hermes_secret = Path("/root/.hermes/secret.env")
        if hermes_secret.exists():
            load_dotenv(hermes_secret, override=False)
            api_id = api_id or os.getenv("TELEGRAM_API_ID")
            api_hash = api_hash or os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        raise RuntimeError(
            "Missing TELEGRAM_API_ID / TELEGRAM_API_HASH. "
            "Copy .env.example to .env and fill in your values (from my.telegram.org)."
        )

    session_dir = Path(os.getenv("TELEGRAM_SESSION_DIR", str(DEFAULT_SESSION_DIR)))
    session_dir.mkdir(parents=True, exist_ok=True)
    try:
        session_dir.chmod(0o700)
    except OSError:
        pass

    account = account or os.getenv("TELEGRAM_ACCOUNT") or DEFAULT_ACCOUNT
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", account.strip("@")).strip("_") or "user"
    session_path = session_dir / f"{safe}.session"
    return int(api_id), api_hash, session_path


def get_client(account: Optional[str] = None) -> TelegramClient:
    api_id, api_hash, session_path = load_settings(account)
    return TelegramClient(str(session_path), api_id, api_hash)


def display_name(entity) -> str:
    title = getattr(entity, "title", None)
    if title:
        return title
    first = getattr(entity, "first_name", None) or ""
    last = getattr(entity, "last_name", None) or ""
    username = getattr(entity, "username", None)
    name = (first + " " + last).strip()
    if name:
        return name
    if username:
        return "@" + username
    return str(getattr(entity, "id", "unknown"))


def chat_ref(entity) -> str:
    username = getattr(entity, "username", None)
    if username:
        return "@" + username
    return str(getattr(entity, "id", "unknown"))
