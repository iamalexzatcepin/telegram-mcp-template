from __future__ import annotations

import os
import platform

from telegram_mcp import __version__
from telegram_mcp.capabilities import DIAGNOSTICS, ToolDefinition
from telegram_mcp.config import default_config_path, load_config
from telegram_mcp.session_store import inspect_storage


async def inspect_permissions() -> dict:
    """Show the active profile, allowed capabilities, and physically exposed tools."""
    config = load_config()
    allowed = config.resolved_capabilities()
    from telegram_mcp.tools import ALL_TOOL_DEFINITIONS

    exposed = sorted(item.name for item in ALL_TOOL_DEFINITIONS if item.capability in allowed)
    hidden = sorted(item.name for item in ALL_TOOL_DEFINITIONS if item.capability not in allowed)
    return {
        "profile": config.profile,
        "allowed_capabilities": sorted(allowed),
        "denied_capabilities": sorted(set(config.denied_capabilities)),
        "exposed_tools": exposed,
        "hidden_tools": hidden,
        "default_account": config.default_account,
        "accounts": list(config.accounts),
    }


async def telegram_diagnostics() -> dict:
    """Inspect local runtime/config/storage state without returning secrets or messages."""
    config = load_config()
    return {
        "version": __version__,
        "transport": "stdio",
        "python": platform.python_version(),
        "platform": platform.system(),
        "config_path": str(default_config_path()),
        "config_exists": default_config_path().exists(),
        "cache_enabled": config.cache_enabled,
        "cache_encrypted": config.cache_encrypted,
        "accounts": [inspect_storage(account) for account in config.accounts],
        "upload_dir_configured": bool(os.getenv("TELEGRAM_MCP_UPLOAD_DIR")),
    }


TOOL_DEFINITIONS = (
    ToolDefinition("inspect_permissions", DIAGNOSTICS, inspect_permissions),
    ToolDefinition("telegram_diagnostics", DIAGNOSTICS, telegram_diagnostics),
)

