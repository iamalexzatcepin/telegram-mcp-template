from __future__ import annotations

from telegram_mcp.capabilities import READ, SEARCH, ToolDefinition
from telegram_mcp.client import telegram_client

from .common import clamp, display_name, entity_ref, message_dict


async def list_chats(limit: int = 50, account: str = "") -> dict:
    """List chats, stable references, unread counts, and pinned state."""
    rows = []
    async with telegram_client(account) as client:
        async for dialog in client.iter_dialogs(limit=clamp(limit)):
            rows.append(
                {
                    "name": display_name(dialog.entity),
                    "ref": entity_ref(dialog.entity),
                    "type": type(dialog.entity).__name__,
                    "unread": dialog.unread_count,
                    "unread_mentions": getattr(dialog, "unread_mentions_count", 0),
                    "pinned": bool(dialog.pinned),
                    "archived": bool(getattr(dialog, "archived", False)),
                }
            )
    return {"account": account, "count": len(rows), "chats": rows}


async def read_chat(chat: str, limit: int = 50, account: str = "") -> dict:
    """Read recent messages from a chat, returned oldest-first."""
    rows = []
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        async for message in client.iter_messages(entity, limit=clamp(limit)):
            rows.append(await message_dict(message))
    rows.reverse()
    return {"account": account, "chat": chat, "count": len(rows), "messages": rows}


async def get_unread(limit_chats: int = 25, limit_per_chat: int = 50, account: str = "") -> dict:
    """Return unread messages grouped by chat without marking them read."""
    chats = []
    async with telegram_client(account) as client:
        async for dialog in client.iter_dialogs(limit=200):
            if dialog.unread_count <= 0:
                continue
            messages = []
            take = min(dialog.unread_count, clamp(limit_per_chat))
            read_max = getattr(getattr(dialog, "dialog", None), "read_inbox_max_id", 0)
            scan_limit = max(take * 3, take + 25)
            async for message in client.iter_messages(dialog.entity, min_id=read_max, limit=scan_limit):
                if not getattr(message, "out", False):
                    messages.append(await message_dict(message))
                    if len(messages) >= take:
                        break
            messages.reverse()
            chats.append(
                {
                    "chat": entity_ref(dialog.entity),
                    "name": display_name(dialog.entity),
                    "unread_total": dialog.unread_count,
                    "messages": messages,
                }
            )
            if len(chats) >= clamp(limit_chats, upper=100):
                break
    return {"account": account, "count": len(chats), "chats": chats}


async def get_message_context(
    chat: str,
    message_id: int,
    before: int = 5,
    after: int = 5,
    account: str = "",
) -> dict:
    """Read one message and bounded surrounding context."""
    before = clamp(before, lower=0, upper=50)
    after = clamp(after, lower=0, upper=50)
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        earlier = await client.get_messages(entity, limit=before, max_id=message_id)
        center = await client.get_messages(entity, ids=message_id)
        later = await client.get_messages(entity, limit=after, min_id=message_id, reverse=True)
        center_items = center if isinstance(center, list) else ([center] if center else [])
        messages = [*earlier, *center_items, *later]
        unique = {item.id: item for item in messages if item}
        rows = [await message_dict(item) for item in unique.values()]
        rows.sort(key=lambda item: item["id"])
    return {"account": account, "chat": chat, "target_message_id": message_id, "messages": rows}


async def search_chat(
    chat: str,
    query: str,
    limit: int = 50,
    account: str = "",
) -> dict:
    """Search message text within one chat."""
    if not query.strip():
        raise ValueError("query must not be blank")
    rows = []
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        async for message in client.iter_messages(entity, search=query, limit=clamp(limit, upper=100)):
            rows.append(await message_dict(message))
    rows.reverse()
    return {"account": account, "chat": chat, "query": query, "count": len(rows), "messages": rows}


async def search_global(query: str, limit: int = 50, account: str = "") -> dict:
    """Search message text across all dialogs."""
    if not query.strip():
        raise ValueError("query must not be blank")
    rows = []
    async with telegram_client(account) as client:
        async for message in client.iter_messages(None, search=query, limit=clamp(limit, upper=100)):
            row = await message_dict(message)
            row["chat"] = display_name(await message.get_chat())
            rows.append(row)
    rows.reverse()
    return {"account": account, "query": query, "count": len(rows), "messages": rows}


TOOL_DEFINITIONS = (
    ToolDefinition("list_chats", READ, list_chats),
    ToolDefinition("read_chat", READ, read_chat),
    ToolDefinition("get_unread", READ, get_unread),
    ToolDefinition("get_message_context", READ, get_message_context),
    ToolDefinition("search_chat", SEARCH, search_chat),
    ToolDefinition("search_global", SEARCH, search_global),
)
