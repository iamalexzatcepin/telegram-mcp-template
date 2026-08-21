from __future__ import annotations

from collections import Counter

from telegram_mcp.capabilities import ANALYSIS, ToolDefinition
from telegram_mcp.client import telegram_client

from .common import clamp, display_name


async def analyze_chat_activity(chat: str, limit: int = 500, account: str = "") -> dict:
    """Compute deterministic activity statistics; the calling agent writes narrative analysis."""
    senders: Counter[str] = Counter()
    days: Counter[str] = Counter()
    media = 0
    total_chars = 0
    count = 0
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        async for message in client.iter_messages(entity, limit=clamp(limit, upper=5000)):
            count += 1
            sender = await message.get_sender() if getattr(message, "sender_id", None) else None
            senders[display_name(sender) or "unknown"] += 1
            if getattr(message, "date", None):
                days[message.date.date().isoformat()] += 1
            if getattr(message, "media", None):
                media += 1
            total_chars += len(getattr(message, "message", None) or "")
    return {
        "account": account,
        "chat": chat,
        "sample_size": count,
        "messages_by_sender": dict(senders.most_common()),
        "messages_by_day": dict(sorted(days.items())),
        "media_messages": media,
        "average_text_length": round(total_chars / count, 2) if count else 0,
    }


TOOL_DEFINITIONS = (ToolDefinition("analyze_chat_activity", ANALYSIS, analyze_chat_activity),)

