from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from telethon import TelegramClient
from telethon.sessions import StringSession

from .config import resolve_account
from .session_store import load_session


@asynccontextmanager
async def telegram_client(account: str) -> AsyncIterator[TelegramClient]:
    safe = resolve_account(account)
    stored = load_session(safe)
    client = TelegramClient(StringSession(stored.session_string), stored.api_id, stored.api_hash)
    await client.connect()
    try:
        if not await client.is_user_authorized():
            raise RuntimeError(f"Telegram account '{safe}' is not authorized; run login again")
        yield client
    finally:
        await client.disconnect()
