#!/usr/bin/env python3
"""First-time Telegram login: creates a session file in ./sessions.

Run once via setup.sh. After that the session is reused by the MCP server.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from telegram_ro_common import get_client


async def main() -> None:
    client = get_client()
    await client.start()
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username or 'no username'}, id={me.id})")
    print("Session saved. You can now register the MCP server.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
