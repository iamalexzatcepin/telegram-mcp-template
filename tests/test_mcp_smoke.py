import os
from pathlib import Path
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from telegram_mcp.config import AppConfig, save_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_stdio_server_exposes_safe_default_only(tmp_path: Path):
    env = dict(os.environ)
    env["TELEGRAM_MCP_CONFIG_DIR"] = str(tmp_path)
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "telegram_mcp_server.py")], cwd=str(ROOT), env=env)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.list_tools()
    assert {tool.name for tool in response.tools} == {
        "inspect_permissions", "telegram_diagnostics", "list_chats", "read_chat",
        "get_unread", "get_message_context", "search_chat", "search_global",
        "analyze_chat_activity",
    }


@pytest.mark.asyncio
async def test_power_user_stdio_schema_builds_all_tools(tmp_path: Path):
    config_path = tmp_path / "config.json"
    save_config(AppConfig(profile="power-user", cache_enabled=True), config_path)
    env = dict(os.environ)
    env["TELEGRAM_MCP_CONFIG"] = str(config_path)
    params = StdioServerParameters(command=sys.executable, args=[str(ROOT / "telegram_mcp_server.py")], cwd=str(ROOT), env=env)
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            response = await session.list_tools()
    names = {tool.name for tool in response.tools}
    assert "delete_messages" in names
    assert "create_group" in names
    assert "send_media" in names
    assert len(names) == 39
