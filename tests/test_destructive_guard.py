import pytest

from telegram_mcp.safety import DestructiveActionRefused, confirmation_target, require_confirmation
from telegram_mcp.tools.management import leave_chat, remove_member
from telegram_mcp.tools.write import (
    cancel_scheduled,
    close_poll,
    create_poll,
    delete_messages,
    forward_messages,
    reply_message,
    schedule_message,
    send_media,
    send_message,
)


@pytest.mark.parametrize("confirm,target", [(False, "chat:1"), (True, "chat:2"), (False, "")])
def test_destructive_guard_requires_boolean_and_exact_target(confirm, target):
    with pytest.raises(DestructiveActionRefused):
        require_confirmation("delete_messages", "chat:1", confirm, target)


def test_destructive_guard_accepts_exact_fresh_target():
    require_confirmation("delete_messages", "chat:1", True, "chat:1")


def test_confirmation_target_is_stable_and_binds_every_detail():
    first = confirmation_target("schedule_message", chat="@user", text="Hello", schedule_at="2026-08-23T09:00:00+03:00")
    same = confirmation_target("schedule_message", schedule_at="2026-08-23T09:00:00+03:00", text="Hello", chat="@user")
    changed = confirmation_target("schedule_message", chat="@user", text="Changed", schedule_at="2026-08-23T09:00:00+03:00")
    assert first == same
    assert first != changed
    assert "Hello" not in first


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call",
    [
        lambda: delete_messages("chat", [1], confirm=False),
        lambda: cancel_scheduled("chat", [1], confirm=True, confirm_target="wrong"),
        lambda: remove_member("chat", "@user", confirm=False),
        lambda: leave_chat("chat", confirm=True, confirm_target="other"),
        lambda: close_poll("chat", 1, confirm=False),
    ],
)
async def test_every_destructive_tool_refuses_before_connecting(call):
    with pytest.raises(DestructiveActionRefused):
        await call()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "call",
    [
        lambda: send_message("@user", "hello"),
        lambda: reply_message("@user", 10, "hello"),
        lambda: forward_messages("@source", "@user", [1]),
        lambda: schedule_message("@user", "hello", "2026-08-23T09:00:00+03:00"),
        lambda: create_poll("@user", "Question?", ["One", "Two"]),
    ],
)
async def test_every_outbound_message_tool_requires_human_confirmation_before_connecting(call):
    with pytest.raises(DestructiveActionRefused):
        await call()


@pytest.mark.asyncio
async def test_media_send_requires_human_confirmation_before_connecting(
    monkeypatch, tmp_path
):
    upload = tmp_path / "uploads"
    upload.mkdir()
    file_path = upload / "photo.jpg"
    file_path.write_bytes(b"not-a-real-image")
    monkeypatch.setenv("TELEGRAM_MCP_UPLOAD_DIR", str(upload))

    with pytest.raises(DestructiveActionRefused):
        await send_media("@user", str(file_path), "caption")
