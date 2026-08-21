from __future__ import annotations

from datetime import date, datetime
from typing import Any


def clamp(value: int, lower: int = 1, upper: int = 200) -> int:
    return max(lower, min(int(value), upper))


def display_name(entity: Any) -> str | None:
    if entity is None:
        return None
    title = getattr(entity, "title", None)
    if title:
        return str(title)
    name = " ".join(
        item for item in (getattr(entity, "first_name", None), getattr(entity, "last_name", None)) if item
    ).strip()
    if name:
        return name
    username = getattr(entity, "username", None)
    return f"@{username}" if username else str(getattr(entity, "id", "unknown"))


def entity_ref(entity: Any) -> str:
    username = getattr(entity, "username", None)
    return f"@{username}" if username else str(getattr(entity, "id", "unknown"))


def json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.hex()
    return value


async def message_dict(message: Any, *, include_text: bool = True) -> dict[str, Any]:
    sender = await message.get_sender() if getattr(message, "sender_id", None) else None
    reply_to = getattr(getattr(message, "reply_to", None), "reply_to_msg_id", None)
    return {
        "id": message.id,
        "chat_id": getattr(message, "chat_id", None),
        "date": json_value(getattr(message, "date", None)),
        "sender_id": getattr(message, "sender_id", None),
        "sender": display_name(sender),
        "text": (getattr(message, "message", None) or "").strip() if include_text else None,
        "reply_to_message_id": reply_to,
        "outgoing": bool(getattr(message, "out", False)),
        "mentioned": bool(getattr(message, "mentioned", False)),
        "silent": bool(getattr(message, "silent", False)),
        "has_media": bool(getattr(message, "media", None)),
        "media_type": type(message.media).__name__ if getattr(message, "media", None) else None,
    }

