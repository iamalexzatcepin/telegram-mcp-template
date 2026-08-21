from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import random
import re

from telethon import functions, types

from telegram_mcp.capabilities import (
    DELETE,
    DRAFTS,
    EDIT,
    FORWARD,
    MEDIA,
    PIN,
    POLLS,
    REACTIONS,
    READ_STATE,
    SCHEDULE,
    WRITE,
    ToolDefinition,
)
from telegram_mcp.client import telegram_client
from telegram_mcp.config import config_dir
from telegram_mcp.safety import confirmation_target, require_confirmation

from .common import message_dict


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("datetime must include a timezone offset")
    return parsed


async def send_message(
    chat: str,
    text: str,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Send text only after fresh human confirmation of recipient and final text."""
    if not text.strip():
        raise ValueError("text must not be blank")
    target = confirmation_target("send_message", chat=chat, text=text)
    require_confirmation("send_message", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        sent = await client.send_message(await client.get_entity(chat), text)
        return await message_dict(sent)


async def reply_message(
    chat: str,
    message_id: int,
    text: str,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Reply only after fresh human confirmation of recipient and final text."""
    if not text.strip():
        raise ValueError("text must not be blank")
    target = confirmation_target("reply_message", chat=chat, message_id=message_id, text=text)
    require_confirmation("reply_message", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        sent = await client.send_message(await client.get_entity(chat), text, reply_to=message_id)
        return await message_dict(sent)


async def edit_message(chat: str, message_id: int, text: str, account: str = "") -> dict:
    """Edit one of the account's messages."""
    async with telegram_client(account) as client:
        edited = await client.edit_message(await client.get_entity(chat), message_id, text)
        return await message_dict(edited)


async def delete_messages(
    chat: str,
    message_ids: list[int],
    revoke: bool = True,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Delete messages after exact-target runtime confirmation."""
    ids = sorted({int(item) for item in message_ids})
    if not ids:
        raise ValueError("message_ids must not be empty")
    target = f"{chat}:{','.join(str(item) for item in ids)}"
    require_confirmation("delete_messages", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        result = await client.delete_messages(await client.get_entity(chat), ids, revoke=revoke)
    return {"account": account, "chat": chat, "deleted_ids": ids, "revoke": revoke, "result": str(result)}


async def forward_messages(
    from_chat: str,
    to_chat: str,
    message_ids: list[int],
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Forward messages only after fresh human confirmation of source, ids, and recipient."""
    ids = sorted({int(item) for item in message_ids})
    if not ids:
        raise ValueError("message_ids must not be empty")
    target = confirmation_target(
        "forward_messages", from_chat=from_chat, to_chat=to_chat, message_ids=ids
    )
    require_confirmation("forward_messages", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        source = await client.get_entity(from_chat)
        target = await client.get_entity(to_chat)
        sent = await client.forward_messages(target, ids, from_peer=source)
        items = sent if isinstance(sent, list) else [sent]
        return {"account": account, "from_chat": from_chat, "to_chat": to_chat, "messages": [await message_dict(item) for item in items]}


async def set_reaction(
    chat: str,
    message_id: int,
    emoji: str | None = None,
    account: str = "",
) -> dict:
    """Set one emoji reaction, or remove the account's reaction when emoji is omitted."""
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        peer = await client.get_input_entity(entity)
        reactions = [types.ReactionEmoji(emoticon=emoji)] if emoji else []
        await client(functions.messages.SendReactionRequest(peer=peer, msg_id=message_id, reaction=reactions))
    return {"account": account, "chat": chat, "message_id": message_id, "reaction": emoji}


async def mark_as_read(chat: str, message_id: int | None = None, account: str = "") -> dict:
    """Mark a dialog read up to an optional message id."""
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        await client.send_read_acknowledge(entity, max_id=message_id)
    return {"account": account, "chat": chat, "marked_read_through": message_id}


async def pin_message(chat: str, message_id: int, notify: bool = False, account: str = "") -> dict:
    """Pin a message in a chat."""
    async with telegram_client(account) as client:
        await client.pin_message(await client.get_entity(chat), message_id, notify=notify)
    return {"account": account, "chat": chat, "message_id": message_id, "pinned": True}


async def unpin_message(chat: str, message_id: int, account: str = "") -> dict:
    """Unpin a message in a chat."""
    async with telegram_client(account) as client:
        await client.unpin_message(await client.get_entity(chat), message_id)
    return {"account": account, "chat": chat, "message_id": message_id, "pinned": False}


async def save_draft(
    chat: str,
    text: str,
    reply_to_message_id: int | None = None,
    account: str = "",
) -> dict:
    """Save or replace a Telegram draft."""
    async with telegram_client(account) as client:
        peer = await client.get_input_entity(await client.get_entity(chat))
        reply = types.InputReplyToMessage(reply_to_msg_id=reply_to_message_id) if reply_to_message_id else None
        await client(functions.messages.SaveDraftRequest(peer=peer, message=text, reply_to=reply))
    return {"account": account, "chat": chat, "draft_saved": True, "text": text}


async def list_drafts(chat: str | None = None, account: str = "") -> dict:
    """List saved drafts across dialogs or for one selected chat."""
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat) if chat else None
        raw = await client.get_drafts(entity)
        drafts = raw if isinstance(raw, list) else ([raw] if raw else [])
        rows = [
            {
                "chat": getattr(getattr(item, "entity", None), "title", None)
                or getattr(getattr(item, "entity", None), "username", None)
                or str(getattr(getattr(item, "entity", None), "id", "unknown")),
                "text": item.text,
                "reply_to_message_id": item.reply_to_msg_id,
                "link_preview": item.link_preview,
            }
            for item in drafts
        ]
    return {"account": account, "count": len(rows), "drafts": rows}


async def clear_draft(chat: str, account: str = "") -> dict:
    """Clear a saved draft without sending it."""
    async with telegram_client(account) as client:
        peer = await client.get_input_entity(await client.get_entity(chat))
        await client(functions.messages.SaveDraftRequest(peer=peer, message=""))
    return {"account": account, "chat": chat, "draft_cleared": True}


async def schedule_message(
    chat: str,
    text: str,
    schedule_at: str,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Schedule text only after fresh human confirmation of recipient, text, and time."""
    if not text.strip():
        raise ValueError("text must not be blank")
    parsed = _parse_datetime(schedule_at)
    target = confirmation_target(
        "schedule_message", chat=chat, text=text, schedule_at=schedule_at
    )
    require_confirmation("schedule_message", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        sent = await client.send_message(
            await client.get_entity(chat), text, schedule=parsed
        )
        return await message_dict(sent)


async def list_scheduled(chat: str, limit: int = 100, account: str = "") -> dict:
    """List scheduled messages for a chat."""
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        messages = await client.get_messages(entity, limit=max(1, min(int(limit), 100)), scheduled=True)
        return {"account": account, "chat": chat, "messages": [await message_dict(item) for item in messages]}


async def cancel_scheduled(
    chat: str,
    message_ids: list[int],
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Cancel selected scheduled messages after exact-target confirmation."""
    ids = sorted({int(item) for item in message_ids})
    if not ids:
        raise ValueError("message_ids must not be empty")
    target = f"{chat}:{','.join(str(item) for item in ids)}"
    require_confirmation("cancel_scheduled", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        peer = await client.get_input_entity(await client.get_entity(chat))
        await client(functions.messages.DeleteScheduledMessagesRequest(peer=peer, id=ids))
    return {"account": account, "chat": chat, "cancelled_ids": ids}


def _download_dir() -> Path:
    root = Path(os.getenv("TELEGRAM_MCP_DOWNLOAD_DIR", str(config_dir() / "downloads"))).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    return root


def _upload_path(value: str) -> Path:
    root_value = os.getenv("TELEGRAM_MCP_UPLOAD_DIR")
    if not root_value:
        raise RuntimeError("Set TELEGRAM_MCP_UPLOAD_DIR before enabling media uploads")
    root = Path(root_value).expanduser().resolve()
    candidate = Path(value).expanduser().resolve()
    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Upload path must stay inside {root}")
    if not candidate.is_file():
        raise FileNotFoundError(candidate)
    return candidate


async def download_media(chat: str, message_id: int, account: str = "") -> dict:
    """Download media into the configured owner-local download directory."""
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        message = await client.get_messages(entity, ids=message_id)
        if not message or not getattr(message, "media", None):
            raise RuntimeError("Target message has no downloadable media")
        path = await client.download_media(message, file=_download_dir())
    return {"account": account, "chat": chat, "message_id": message_id, "path": path}


async def send_media(
    chat: str,
    file_path: str,
    caption: str = "",
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Send a confined file only after fresh human confirmation."""
    path = _upload_path(file_path)
    target = confirmation_target(
        "send_media", chat=chat, file_path=str(path), caption=caption
    )
    require_confirmation("send_media", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        sent = await client.send_file(await client.get_entity(chat), path, caption=caption)
        return await message_dict(sent)


def _text(value: str) -> types.TextWithEntities:
    return types.TextWithEntities(text=value, entities=[])


async def create_poll(
    chat: str,
    question: str,
    options: list[str],
    multiple_choice: bool = False,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Create a poll only after fresh human confirmation of destination and content."""
    if not 2 <= len(options) <= 10:
        raise ValueError("poll requires 2 to 10 options")
    target = confirmation_target(
        "create_poll",
        chat=chat,
        question=question,
        options=options,
        multiple_choice=multiple_choice,
    )
    require_confirmation("create_poll", target, confirm, confirm_target)
    answers = [types.PollAnswer(text=_text(item), option=str(index).encode()) for index, item in enumerate(options)]
    poll = types.Poll(
        id=random.getrandbits(63),
        question=_text(question),
        answers=answers,
        hash=0,
        multiple_choice=multiple_choice,
    )
    async with telegram_client(account) as client:
        peer = await client.get_input_entity(await client.get_entity(chat))
        await client(functions.messages.SendMediaRequest(peer=peer, media=types.InputMediaPoll(poll=poll), message=""))
    return {"account": account, "chat": chat, "question": question, "options": options}


async def vote_poll(chat: str, message_id: int, option_indices: list[int], account: str = "") -> dict:
    """Vote in a Telegram poll by zero-based option indices."""
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        message = await client.get_messages(entity, ids=message_id)
        poll = getattr(getattr(message, "media", None), "poll", None)
        if not poll:
            raise RuntimeError("Target message is not a poll")
        if any(item < 0 or item >= len(poll.answers) for item in option_indices):
            raise ValueError("poll option index out of range")
        peer = await client.get_input_entity(entity)
        await client(functions.messages.SendVoteRequest(peer=peer, msg_id=message_id, options=[poll.answers[item].option for item in option_indices]))
    return {"account": account, "chat": chat, "message_id": message_id, "voted_indices": option_indices}


async def close_poll(
    chat: str,
    message_id: int,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Close a poll after exact-target runtime confirmation."""
    target = f"{chat}:{message_id}"
    require_confirmation("close_poll", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        message = await client.get_messages(entity, ids=message_id)
        poll = getattr(getattr(message, "media", None), "poll", None)
        if not poll:
            raise RuntimeError("Target message is not a poll")
        closed = types.Poll(
            id=poll.id,
            question=poll.question,
            answers=poll.answers,
            hash=poll.hash,
            closed=True,
            public_voters=poll.public_voters,
            multiple_choice=poll.multiple_choice,
            quiz=poll.quiz,
            close_period=poll.close_period,
            close_date=poll.close_date,
        )
        peer = await client.get_input_entity(entity)
        await client(functions.messages.EditMessageRequest(peer=peer, id=message_id, media=types.InputMediaPoll(poll=closed)))
    return {"account": account, "chat": chat, "message_id": message_id, "closed": True}


TOOL_DEFINITIONS = (
    ToolDefinition("send_message", WRITE, send_message),
    ToolDefinition("reply_message", WRITE, reply_message),
    ToolDefinition("edit_message", EDIT, edit_message),
    ToolDefinition("delete_messages", DELETE, delete_messages, destructive=True),
    ToolDefinition("forward_messages", FORWARD, forward_messages),
    ToolDefinition("set_reaction", REACTIONS, set_reaction),
    ToolDefinition("mark_as_read", READ_STATE, mark_as_read),
    ToolDefinition("pin_message", PIN, pin_message),
    ToolDefinition("unpin_message", PIN, unpin_message),
    ToolDefinition("save_draft", DRAFTS, save_draft),
    ToolDefinition("list_drafts", DRAFTS, list_drafts),
    ToolDefinition("clear_draft", DRAFTS, clear_draft),
    ToolDefinition("schedule_message", SCHEDULE, schedule_message),
    ToolDefinition("list_scheduled", SCHEDULE, list_scheduled),
    ToolDefinition("cancel_scheduled", SCHEDULE, cancel_scheduled, destructive=True),
    ToolDefinition("download_media", MEDIA, download_media),
    ToolDefinition("send_media", MEDIA, send_media),
    ToolDefinition("create_poll", POLLS, create_poll),
    ToolDefinition("vote_poll", POLLS, vote_poll),
    ToolDefinition("close_poll", POLLS, close_poll, destructive=True),
)
