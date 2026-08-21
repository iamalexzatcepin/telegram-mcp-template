import pytest

from telegram_mcp.safety import DestructiveActionRefused, require_confirmation
from telegram_mcp.tools.management import leave_chat, remove_member
from telegram_mcp.tools.write import cancel_scheduled, close_poll, delete_messages


@pytest.mark.parametrize("confirm,target", [(False, "chat:1"), (True, "chat:2"), (False, "")])
def test_destructive_guard_requires_boolean_and_exact_target(confirm, target):
    with pytest.raises(DestructiveActionRefused):
        require_confirmation("delete_messages", "chat:1", confirm, target)


def test_destructive_guard_accepts_exact_fresh_target():
    require_confirmation("delete_messages", "chat:1", True, "chat:1")


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
