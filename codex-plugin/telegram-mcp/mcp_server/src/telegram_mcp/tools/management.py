from __future__ import annotations

from telethon import functions, types

from telegram_mcp.capabilities import CHANNELS, GROUPS, ToolDefinition
from telegram_mcp.client import telegram_client
from telegram_mcp.safety import require_confirmation


async def create_group(title: str, member_refs: list[str], account: str = "") -> dict:
    """Create a basic Telegram group with initial members."""
    if not title.strip() or not member_refs:
        raise ValueError("title and at least one member are required")
    async with telegram_client(account) as client:
        users = [await client.get_input_entity(item) for item in member_refs]
        result = await client(functions.messages.CreateChatRequest(users=users, title=title))
    return {"account": account, "title": title, "members": member_refs, "result": str(result)}


async def create_channel(
    title: str,
    about: str = "",
    megagroup: bool = False,
    account: str = "",
) -> dict:
    """Create a broadcast channel or megagroup."""
    if not title.strip():
        raise ValueError("title must not be blank")
    async with telegram_client(account) as client:
        result = await client(
            functions.channels.CreateChannelRequest(
                title=title,
                about=about,
                broadcast=not megagroup,
                megagroup=megagroup,
            )
        )
    return {"account": account, "title": title, "megagroup": megagroup, "result": str(result)}


async def update_chat_title(chat: str, title: str, account: str = "") -> dict:
    """Rename a group or channel."""
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        if isinstance(entity, types.Chat):
            await client(functions.messages.EditChatTitleRequest(chat_id=entity.id, title=title))
        else:
            await client(functions.channels.EditTitleRequest(channel=entity, title=title))
    return {"account": account, "chat": chat, "title": title}


async def invite_members(chat: str, member_refs: list[str], account: str = "") -> dict:
    """Invite users to a group or channel."""
    if not member_refs:
        raise ValueError("member_refs must not be empty")
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        users = [await client.get_input_entity(item) for item in member_refs]
        if isinstance(entity, types.Chat):
            for user in users:
                await client(functions.messages.AddChatUserRequest(chat_id=entity.id, user_id=user, fwd_limit=0))
        else:
            await client(functions.channels.InviteToChannelRequest(channel=entity, users=users))
    return {"account": account, "chat": chat, "invited": member_refs}


async def remove_member(
    chat: str,
    member_ref: str,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Remove a member after exact-target runtime confirmation."""
    target = f"{chat}:{member_ref}"
    require_confirmation("remove_member", target, confirm, confirm_target)
    async with telegram_client(account) as client:
        entity = await client.get_entity(chat)
        user = await client.get_input_entity(member_ref)
        if isinstance(entity, types.Chat):
            await client(functions.messages.DeleteChatUserRequest(chat_id=entity.id, user_id=user))
        else:
            rights = types.ChatBannedRights(until_date=None, view_messages=True)
            await client(functions.channels.EditBannedRequest(channel=entity, participant=user, banned_rights=rights))
    return {"account": account, "chat": chat, "removed": member_ref}


async def leave_chat(
    chat: str,
    confirm: bool = False,
    confirm_target: str = "",
    account: str = "",
) -> dict:
    """Leave a group or channel after exact-target runtime confirmation."""
    require_confirmation("leave_chat", chat, confirm, confirm_target)
    async with telegram_client(account) as client:
        await client.delete_dialog(await client.get_entity(chat), revoke=False)
    return {"account": account, "chat": chat, "left": True}


TOOL_DEFINITIONS = (
    ToolDefinition("create_group", GROUPS, create_group),
    ToolDefinition("invite_members", GROUPS, invite_members),
    ToolDefinition("remove_member", GROUPS, remove_member, destructive=True),
    ToolDefinition("create_channel", CHANNELS, create_channel),
    ToolDefinition("update_chat_title", CHANNELS, update_chat_title),
    ToolDefinition("leave_chat", CHANNELS, leave_chat, destructive=True),
)
