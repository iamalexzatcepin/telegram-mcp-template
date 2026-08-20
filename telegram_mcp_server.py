#!/usr/bin/env python3
"""MCP server: read-only Telegram access (list chats, read chat, search).

Run via stdio (default) so Codex / Claude Code / any MCP client can register it:
    codex mcp add telegram -- python telegram_mcp_server.py
    claude mcp add telegram -- python telegram_mcp_server.py
    claude mcp add telegram -- <abs path to this file>   (Claude Code also accepts the file directly)

All operations are READ-ONLY: the agent can view chats and messages but never
send anything.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp.server.fastmcp import FastMCP

from telegram_ro_common import chat_ref, display_name, get_client

mcp = FastMCP("hermes-telegram")


@mcp.tool()
async def list_chats(limit: int = 50, account: str = "default") -> str:
    """List Telegram chats/dialogs (name, ref, unread count). Use to discover where to read.

    Args:
        limit: max number of dialogs to return (default 50).
        account: session name (default 'default').
    """
    client = get_client(account)
    await client.start()
    try:
        rows = []
        async for dialog in client.iter_dialogs(limit=limit):
            e = dialog.entity
            rows.append({
                "name": display_name(e),
                "ref": chat_ref(e),
                "type": e.__class__.__name__,
                "unread": dialog.unread_count,
                "pinned": bool(dialog.pinned),
            })
        return json.dumps(rows, ensure_ascii=False, indent=2)
    finally:
        await client.disconnect()


@mcp.tool()
async def read_chat(chat: str, limit: int = 50, account: str = "default") -> str:
    """Read last messages of a Telegram chat (oldest-first).

    Args:
        chat: chat id, @username, or resolvable entity name.
        limit: number of most recent messages to read (default 50, max 200).
        account: session name (default 'default').
    """
    limit = max(1, min(int(limit), 200))
    client = get_client(account)
    await client.start()
    try:
        entity = await client.get_entity(chat)
        rows = []
        async for msg in client.iter_messages(entity, limit=limit):
            sender = await msg.get_sender() if msg.sender_id else None
            rows.append({
                "id": msg.id,
                "date": msg.date.isoformat() if msg.date else None,
                "sender": display_name(sender) if sender else None,
                "text": (msg.message or "").strip(),
                "has_media": bool(msg.media),
            })
        rows = list(reversed(rows))
        return json.dumps(rows, ensure_ascii=False, indent=2)
    finally:
        await client.disconnect()


@mcp.tool()
async def search_chat(chat: str, query: str, limit: int = 50, account: str = "default") -> str:
    """Search messages in a Telegram chat by text query (oldest-first).

    Args:
        chat: chat id, @username, or resolvable entity name.
        query: text to search for.
        limit: max matches (default 50, max 100).
        account: session name (default 'default').
    """
    limit = max(1, min(int(limit), 100))
    client = get_client(account)
    await client.start()
    try:
        entity = await client.get_entity(chat)
        rows = []
        async for msg in client.iter_messages(entity, search=query, limit=limit):
            sender = await msg.get_sender() if msg.sender_id else None
            rows.append({
                "id": msg.id,
                "date": msg.date.isoformat() if msg.date else None,
                "sender": display_name(sender) if sender else None,
                "text": (msg.message or "").strip(),
                "has_media": bool(msg.media),
            })
        rows = list(reversed(rows))
        return json.dumps(rows, ensure_ascii=False, indent=2)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--transport", default="stdio", choices=["stdio", "sse", "http"])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    if args.transport == "http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport=args.transport)
