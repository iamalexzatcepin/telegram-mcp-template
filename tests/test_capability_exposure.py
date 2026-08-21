from telegram_mcp.capabilities import ALL_CAPABILITIES
from telegram_mcp.config import AppConfig
from telegram_mcp.server import exposed_tool_names

READ_ONLY_TOOLS = {
    "inspect_permissions", "telegram_diagnostics", "list_chats", "read_chat",
    "get_unread", "get_message_context", "search_chat", "search_global",
    "analyze_chat_activity",
}


def test_missing_config_defaults_to_safe_read_only_contract():
    assert exposed_tool_names(AppConfig()) == READ_ONLY_TOOLS


def test_read_only_physically_excludes_every_mutating_tool():
    names = exposed_tool_names(AppConfig(profile="read-only"))
    assert names == READ_ONLY_TOOLS
    assert not names & {"send_message", "edit_message", "delete_messages", "mark_as_read", "download_media", "create_group"}


def test_custom_profile_registers_only_requested_capability_and_diagnostics():
    names = exposed_tool_names(AppConfig(profile="custom", capabilities=("write",)))
    assert names == {"inspect_permissions", "telegram_diagnostics", "send_message", "reply_message"}


def test_explicit_deny_removes_tool_even_from_power_user():
    names = exposed_tool_names(AppConfig(profile="power-user", denied_capabilities=("delete", "groups"), cache_enabled=True))
    assert "delete_messages" not in names
    assert "create_group" not in names
    assert "send_message" in names
    assert "search_cache" in names


def test_power_user_covers_every_declared_capability():
    assert AppConfig(profile="power-user", cache_enabled=True).resolved_capabilities() == ALL_CAPABILITIES

