from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

from .capabilities import ALL_CAPABILITIES, DIAGNOSTICS, PROFILE_CAPABILITIES

CONFIG_ENV = "TELEGRAM_MCP_CONFIG"
CONFIG_HOME_ENV = "TELEGRAM_MCP_CONFIG_DIR"
DEFAULT_ACCOUNT = "default"


class ConfigError(ValueError):
    pass


def secure_account_name(value: str | None) -> str:
    raw = (value or DEFAULT_ACCOUNT).strip().strip("@")
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("._")[:64]
    if not safe:
        raise ConfigError("Account name must contain at least one letter or digit")
    return safe


def config_dir() -> Path:
    override = os.getenv(CONFIG_HOME_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if os.name == "nt" and os.getenv("APPDATA"):
        return Path(os.environ["APPDATA"]) / "telegram-mcp-v2"
    xdg = os.getenv("XDG_CONFIG_HOME")
    return (Path(xdg).expanduser() if xdg else Path.home() / ".config") / "telegram-mcp-v2"


def default_config_path() -> Path:
    override = os.getenv(CONFIG_ENV)
    return Path(override).expanduser().resolve() if override else config_dir() / "config.json"


@dataclass(frozen=True)
class AppConfig:
    profile: str = "read-only"
    capabilities: tuple[str, ...] = ()
    denied_capabilities: tuple[str, ...] = ()
    default_account: str = DEFAULT_ACCOUNT
    accounts: tuple[str, ...] = (DEFAULT_ACCOUNT,)
    cache_enabled: bool = False
    cache_encrypted: bool = False

    def resolved_capabilities(self) -> frozenset[str]:
        if self.profile not in PROFILE_CAPABILITIES:
            raise ConfigError(f"Unknown profile: {self.profile}")
        requested = set(PROFILE_CAPABILITIES[self.profile]) | set(self.capabilities)
        unknown = requested - ALL_CAPABILITIES
        denied_unknown = set(self.denied_capabilities) - ALL_CAPABILITIES
        if unknown or denied_unknown:
            names = sorted(unknown | denied_unknown)
            raise ConfigError(f"Unknown capabilities: {', '.join(names)}")
        requested -= set(self.denied_capabilities)
        requested.add(DIAGNOSTICS)
        if not self.cache_enabled:
            requested.discard("cache")
        return frozenset(requested)

    def normalized(self) -> "AppConfig":
        accounts = tuple(dict.fromkeys(secure_account_name(item) for item in self.accounts))
        default = secure_account_name(self.default_account)
        if default not in accounts:
            accounts = (default, *accounts)
        return AppConfig(
            profile=self.profile,
            capabilities=tuple(sorted(set(self.capabilities))),
            denied_capabilities=tuple(sorted(set(self.denied_capabilities))),
            default_account=default,
            accounts=accounts,
            cache_enabled=bool(self.cache_enabled),
            cache_encrypted=bool(self.cache_encrypted),
        )

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AppConfig":
        return cls(
            profile=str(raw.get("profile", "read-only")),
            capabilities=tuple(raw.get("capabilities") or ()),
            denied_capabilities=tuple(raw.get("denied_capabilities") or ()),
            default_account=str(raw.get("default_account", DEFAULT_ACCOUNT)),
            accounts=tuple(raw.get("accounts") or (DEFAULT_ACCOUNT,)),
            cache_enabled=bool(raw.get("cache_enabled", False)),
            cache_encrypted=bool(raw.get("cache_encrypted", False)),
        ).normalized()


def load_config(path: Path | None = None) -> AppConfig:
    target = path or default_config_path()
    if not target.exists():
        return AppConfig()
    if target.is_symlink():
        raise ConfigError(f"Refusing symlinked config file: {target}")
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Invalid config file {target}: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError("Config root must be an object")
    return AppConfig.from_dict(raw)


def resolve_account(value: str | None) -> str:
    """Resolve an explicit name or the configured default account."""
    return secure_account_name(value) if value else load_config().default_account


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        path.parent.chmod(0o700)
    except OSError:
        pass
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(temp_name)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        temp.unlink(missing_ok=True)
        raise


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    normalized = config.normalized()
    normalized.resolved_capabilities()
    target = path or default_config_path()
    atomic_write_json(target, asdict(normalized))
    return target
