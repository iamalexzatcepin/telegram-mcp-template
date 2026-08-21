---
name: telegram-send
description: Draft, send, reply, forward, edit, schedule, react to, or attach media to Telegram messages when the active profile allows it.
---

# Telegram Send

Confirm an ambiguous destination with `list_chats`. If the user asks for wording or has not clearly authorized immediate delivery, return or save a draft; do not send. For an authorized send, use the narrow tool matching the request and report the destination and result. Media uploads must remain inside `TELEGRAM_MCP_UPLOAD_DIR`. Editing, cancellation, or deletion must respect the exposed capability; destructive tools additionally require a fresh exact-target confirmation.
