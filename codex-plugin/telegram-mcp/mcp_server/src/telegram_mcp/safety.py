from __future__ import annotations


class DestructiveActionRefused(RuntimeError):
    pass


def require_confirmation(action: str, target: str, confirm: bool, confirm_target: str) -> None:
    if confirm and confirm_target.strip() == target.strip():
        return
    raise DestructiveActionRefused(
        f"Refusing {action}. Retry only after the user confirms the exact target; "
        f"pass confirm=true and confirm_target={target!r}."
    )

