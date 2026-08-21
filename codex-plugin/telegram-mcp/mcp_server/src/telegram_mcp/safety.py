from __future__ import annotations

import hashlib
import json


class DestructiveActionRefused(RuntimeError):
    pass


def confirmation_target(action: str, **details: object) -> str:
    """Build a stable exact-action token without embedding message text in errors."""
    encoded = json.dumps(details, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:20]
    destination = str(details.get("chat") or details.get("to_chat") or "target")
    schedule_at = details.get("schedule_at")
    parts = [action, destination]
    if schedule_at:
        parts.append(str(schedule_at))
    parts.append(digest)
    return ":".join(parts)


def require_confirmation(action: str, target: str, confirm: bool, confirm_target: str) -> None:
    if confirm and confirm_target.strip() == target.strip():
        return
    raise DestructiveActionRefused(
        f"Refusing {action}. Retry only after the user confirms the exact target; "
        f"pass confirm=true and confirm_target={target!r}."
    )
