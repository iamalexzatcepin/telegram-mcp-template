from __future__ import annotations

from datetime import UTC, datetime

from telegram_mcp.cache import cache_path, connect_cache, upsert_messages
from telegram_mcp.capabilities import CACHE, ToolDefinition
from telegram_mcp.config import load_config

from .read import read_chat


def _encrypted() -> bool:
    return load_config().cache_encrypted


async def cache_status(account: str = "") -> dict:
    """Inspect local cache location, encryption mode, and synced chats."""
    path = cache_path(account)
    connection = connect_cache(account, encrypted=_encrypted())
    try:
        rows = [dict(row) for row in connection.execute(
            "SELECT chat_ref, last_sync, message_count FROM sync_state WHERE account=? ORDER BY last_sync DESC",
            (account,),
        )]
    finally:
        connection.close()
    return {
        "account": account,
        "path": str(path),
        "encrypted": _encrypted(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "chats": rows,
    }


async def sync_chat_cache(chat: str, limit: int = 1000, account: str = "") -> dict:
    """Sync a bounded recent history window into the optional local cache."""
    payload = await read_chat(chat, limit=max(1, min(int(limit), 5000)), account=account)
    rows = payload["messages"]
    connection = connect_cache(account, encrypted=_encrypted())
    try:
        upsert_messages(connection, account, chat, rows)
        count = connection.execute(
            "SELECT count(*) FROM messages WHERE account=? AND chat_ref=?", (account, chat)
        ).fetchone()[0]
        now = datetime.now(UTC).isoformat()
        connection.execute(
            """INSERT INTO sync_state(account, chat_ref, last_sync, message_count) VALUES (?, ?, ?, ?)
               ON CONFLICT(account, chat_ref) DO UPDATE SET last_sync=excluded.last_sync, message_count=excluded.message_count""",
            (account, chat, now, count),
        )
        connection.commit()
    finally:
        connection.close()
    return {"account": account, "chat": chat, "synced": len(rows), "cached_total": count}


async def search_cache(
    chat: str,
    query: str,
    limit: int = 100,
    offset: int = 0,
    account: str = "",
) -> dict:
    """Search an already-synced chat locally without calling Telegram."""
    if not query.strip():
        raise ValueError("query must not be blank")
    connection = connect_cache(account, encrypted=_encrypted())
    try:
        rows = [dict(row) for row in connection.execute(
            """SELECT message_id AS id, date, sender_id, sender, text, outgoing, has_media
               FROM messages WHERE account=? AND chat_ref=? AND text LIKE ?
               ORDER BY message_id DESC LIMIT ? OFFSET ?""",
            (account, chat, f"%{query}%", max(1, min(int(limit), 500)), max(0, int(offset))),
        )]
    finally:
        connection.close()
    return {"account": account, "chat": chat, "query": query, "count": len(rows), "messages": rows}


async def aggregate_cache(chat: str, group_by: str = "day", account: str = "") -> dict:
    """Aggregate cached message counts by day or sender."""
    if group_by not in {"day", "sender"}:
        raise ValueError("group_by must be 'day' or 'sender'")
    expression = "substr(date, 1, 10)" if group_by == "day" else "coalesce(sender, 'unknown')"
    connection = connect_cache(account, encrypted=_encrypted())
    try:
        rows = [dict(row) for row in connection.execute(
            f"SELECT {expression} AS bucket, count(*) AS messages FROM messages WHERE account=? AND chat_ref=? GROUP BY bucket ORDER BY bucket",
            (account, chat),
        )]
    finally:
        connection.close()
    return {"account": account, "chat": chat, "group_by": group_by, "buckets": rows}


TOOL_DEFINITIONS = (
    ToolDefinition("cache_status", CACHE, cache_status),
    ToolDefinition("sync_chat_cache", CACHE, sync_chat_cache),
    ToolDefinition("search_cache", CACHE, search_cache),
    ToolDefinition("aggregate_cache", CACHE, aggregate_cache),
)

