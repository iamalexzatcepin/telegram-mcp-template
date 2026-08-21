from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable

ToolCallable = Callable[..., Awaitable[dict]]

DIAGNOSTICS = "diagnostics"
READ = "read"
SEARCH = "search"
ANALYSIS = "analysis"
CACHE = "cache"
WRITE = "write"
EDIT = "edit"
DELETE = "delete"
FORWARD = "forward"
REACTIONS = "reactions"
READ_STATE = "read-state"
PIN = "pin"
DRAFTS = "drafts"
SCHEDULE = "schedule"
MEDIA = "media"
POLLS = "polls"
GROUPS = "groups"
CHANNELS = "channels"

ALL_CAPABILITIES = frozenset(
    {
        DIAGNOSTICS,
        READ,
        SEARCH,
        ANALYSIS,
        CACHE,
        WRITE,
        EDIT,
        DELETE,
        FORWARD,
        REACTIONS,
        READ_STATE,
        PIN,
        DRAFTS,
        SCHEDULE,
        MEDIA,
        POLLS,
        GROUPS,
        CHANNELS,
    }
)

DESTRUCTIVE_CAPABILITIES = frozenset({DELETE, GROUPS, CHANNELS, SCHEDULE})

PROFILE_CAPABILITIES: dict[str, frozenset[str]] = {
    "read-only": frozenset({DIAGNOSTICS, READ, SEARCH, ANALYSIS}),
    "assistant": frozenset(
        {
            DIAGNOSTICS,
            READ,
            SEARCH,
            ANALYSIS,
            CACHE,
            WRITE,
            FORWARD,
            REACTIONS,
            READ_STATE,
            DRAFTS,
            SCHEDULE,
            MEDIA,
            POLLS,
        }
    ),
    "power-user": ALL_CAPABILITIES,
    "custom": frozenset({DIAGNOSTICS}),
}


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    capability: str
    function: ToolCallable
    destructive: bool = False

