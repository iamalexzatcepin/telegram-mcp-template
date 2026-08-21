from __future__ import annotations

import argparse
import asyncio
from dataclasses import asdict
import getpass
import json
import os
from pathlib import Path
import sys

from telethon import TelegramClient
from telethon.sessions import StringSession

from .capabilities import ALL_CAPABILITIES, PROFILE_CAPABILITIES
from .config import AppConfig, default_config_path, load_config, save_config, secure_account_name
from .migration import migrate_v1
from .server import run_server
from .session_store import (
    MASTER_KEY_ENV,
    StoredSession,
    delete_session,
    inspect_storage,
    save_session,
)
from .tools.diagnostics import inspect_permissions, telegram_diagnostics


def _yes_no(prompt: str, default: bool = False) -> bool:
    suffix = " [Y/n] " if default else " [y/N] "
    value = input(prompt + suffix).strip().casefold()
    if not value:
        return default
    return value in {"y", "yes", "да", "д"}


def _choose_profile() -> str:
    profiles = ["read-only", "assistant", "power-user", "custom"]
    print("Profiles:")
    print("  1. read-only   Read, search, and local analysis (recommended)")
    print("  2. assistant   Adds cache, send/reply, drafts, schedule, media, polls")
    print("  3. power-user  All capabilities, including destructive tools")
    print("  4. custom      Select individual capabilities")
    value = input("Choose profile [1]: ").strip() or "1"
    if value not in {"1", "2", "3", "4"}:
        raise ValueError("Profile choice must be 1-4")
    return profiles[int(value) - 1]


def _choose_capabilities() -> tuple[str, ...]:
    names = sorted(ALL_CAPABILITIES - {"diagnostics"})
    print("Available capabilities:")
    for index, name in enumerate(names, 1):
        print(f"  {index:2}. {name}")
    raw = input("Enter comma-separated numbers (blank keeps diagnostics only): ").strip()
    if not raw:
        return ()
    selected = []
    for part in raw.split(","):
        index = int(part.strip())
        if not 1 <= index <= len(names):
            raise ValueError(f"Capability number out of range: {index}")
        selected.append(names[index - 1])
    return tuple(sorted(set(selected)))


def setup_wizard(args: argparse.Namespace) -> int:
    profile = args.profile or _choose_profile()
    capabilities = tuple(args.capability or ())
    if profile == "custom" and not capabilities and not args.non_interactive:
        capabilities = _choose_capabilities()
    accounts = tuple(args.account or ())
    if not accounts:
        value = "default" if args.non_interactive else (input("Local account names [default]: ").strip() or "default")
        accounts = tuple(item.strip() for item in value.split(",") if item.strip())
    default_account = secure_account_name(args.default_account or accounts[0])
    cache_requested = "cache" in (set(PROFILE_CAPABILITIES[profile]) | set(capabilities))
    cache_enabled = bool(args.cache) if args.non_interactive else (
        cache_requested and _yes_no("Enable local message cache?", default=True)
    )
    cache_encrypted = False
    if cache_enabled:
        cache_encrypted = bool(args.encrypted_cache) if args.non_interactive else _yes_no(
            "Require SQLCipher encryption for local cache?", default=False
        )
    config = AppConfig(
        profile=profile,
        capabilities=capabilities,
        denied_capabilities=tuple(args.deny or ()),
        default_account=default_account,
        accounts=accounts,
        cache_enabled=cache_enabled,
        cache_encrypted=cache_encrypted,
    ).normalized()
    path = save_config(config, Path(args.config).expanduser() if args.config else None)
    print(f"Saved owner-only config: {path}")
    print("Allowed capabilities:", ", ".join(sorted(config.resolved_capabilities())))
    print("Next: run `telegram-mcp login --account <name>` for each account.")
    return 0


async def login(account: str) -> int:
    safe = secure_account_name(account)
    api_id_raw = os.getenv("TELEGRAM_API_ID") or input("Telegram API ID: ").strip()
    api_hash = os.getenv("TELEGRAM_API_HASH") or getpass.getpass("Telegram API hash: ").strip()
    phone = input("Telegram phone (E.164, e.g. +15551234567): ").strip()
    if not api_id_raw or not api_hash or not phone:
        raise RuntimeError("API ID, API hash, and phone are required")
    client = TelegramClient(StringSession(), int(api_id_raw), api_hash)
    await client.start(
        phone=phone,
        code_callback=lambda: getpass.getpass("Telegram login code: ").strip(),
        password=lambda: getpass.getpass("Telegram 2FA password: "),
    )
    try:
        me = await client.get_me()
        record = StoredSession(
            api_id=int(api_id_raw),
            api_hash=api_hash,
            session_string=StringSession.save(client.session),
        )
        master_key = os.getenv(MASTER_KEY_ENV)
        try:
            backend = save_session(safe, record, master_key=master_key)
        except RuntimeError:
            master_key = getpass.getpass(
                f"OS keyring unavailable. Create {MASTER_KEY_ENV} for encrypted fallback: "
            ).strip()
            if not master_key:
                raise
            backend = save_session(safe, record, master_key=master_key)
        print(
            json.dumps(
                {
                    "ok": True,
                    "account": safe,
                    "storage": backend,
                    "user_id": me.id,
                    "username": getattr(me, "username", None),
                },
                ensure_ascii=False,
            )
        )
        if backend == "encrypted-file" and not os.getenv(MASTER_KEY_ENV):
            print(f"Set {MASTER_KEY_ENV} in the MCP process environment before starting the server.")
    finally:
        await client.disconnect()
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="telegram-mcp", description="Telegram MCP v2")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve", help="Run the local STDIO MCP server")

    setup = sub.add_parser("setup", help="Choose a capability profile and accounts")
    setup.add_argument("--profile", choices=sorted(PROFILE_CAPABILITIES))
    setup.add_argument("--capability", action="append", choices=sorted(ALL_CAPABILITIES))
    setup.add_argument("--deny", action="append", choices=sorted(ALL_CAPABILITIES))
    setup.add_argument("--account", action="append")
    setup.add_argument("--default-account")
    setup.add_argument("--cache", action="store_true")
    setup.add_argument("--encrypted-cache", action="store_true")
    setup.add_argument("--config")
    setup.add_argument("--non-interactive", action="store_true")

    login_parser = sub.add_parser("login", help="Authorize and securely store one account")
    login_parser.add_argument("--account")
    logout = sub.add_parser("logout", help="Delete one locally stored session")
    logout.add_argument("--account")
    logout.add_argument("--confirm", action="store_true")
    storage = sub.add_parser("storage", help="Inspect session backend state")
    storage.add_argument("--account")
    migrate = sub.add_parser("migrate-v1", help="Securely migrate an existing v1 SQLite session")
    migrate.add_argument("--repo", required=True)
    migrate.add_argument("--account")
    sub.add_parser("permissions", help="Inspect allowed capabilities and exposed tools")
    sub.add_parser("diagnostics", help="Inspect secret-free runtime state")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "serve":
        run_server()
        return 0
    if args.command == "setup":
        return setup_wizard(args)
    if args.command == "login":
        return asyncio.run(login(args.account or load_config().default_account))
    if args.command == "logout":
        if not args.confirm:
            raise RuntimeError("Refusing logout without --confirm")
        account = args.account or load_config().default_account
        print(json.dumps({"removed": delete_session(account), "account": secure_account_name(account)}))
        return 0
    if args.command == "storage":
        print(json.dumps(inspect_storage(args.account or load_config().default_account), indent=2))
        return 0
    if args.command == "migrate-v1":
        account = args.account or load_config().default_account
        print(json.dumps(migrate_v1(Path(args.repo), account, os.getenv(MASTER_KEY_ENV)), indent=2))
        return 0
    if args.command == "permissions":
        print(json.dumps(asyncio.run(inspect_permissions()), indent=2))
        return 0
    if args.command == "diagnostics":
        print(json.dumps(asyncio.run(telegram_diagnostics()), indent=2))
        return 0
    return 2
