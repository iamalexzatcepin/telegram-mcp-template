# Telegram MCP: читай переписки из любого ИИ-агента

Даёт ИИ-агенту (Codex, Claude Code, Cursor, Cline, Windsurf, n8n и любой другой MCP-клиент) **read-only доступ к вашему Telegram**: список чатов, чтение переписок, поиск по чату. Агент видит переписку как вы сами (через MTProto-сессию вашего аккаунта), но **не может отправлять сообщения**.

## Что вы получаете

Три инструмента, доступных агенту в любом режиме:

| Инструмент | Что делает |
|---|---|
| `list_chats(limit)` | Список диалогов: имя, @username/id, тип, непрочитанные |
| `read_chat(chat, limit)` | Последние сообщения чата (от старых к новым) |
| `search_chat(chat, query)` | Поиск по сообщениям в чате |

## Установка (2 минуты)

Требуется: Python 3.10+ и любой MCP-клиент (Codex CLI / Claude Code / Cursor / другое).

### Шаг 1. Клонируйте и настройте

```bash
git clone <repo-url> telegram-mcp
cd telegram-mcp
cp .env.example .env
```

Откройте `.env` и вставьте свои **API ID** и **API Hash**:
- Зайдите на https://my.telegram.org (войдите своим номером телефона)
- Меню **API development tools** → Create new application
- Скопируйте `api_id` (число) и `api_hash` (строка) в `.env`

### Шаг 2. Установка и вход

```bash
bash setup.sh
```

Скрипт создаст venv, поставит зависимости и попросит:
1. Ваш номер телефона (в формате `+79123456789`)
2. Код из Telegram (придёт в приложение)

Вход нужен **один раз** — дальше сессия переиспользуется.

### Шаг 3. Подключите к вашему агенту

```bash
# Codex CLI
codex mcp add telegram -- python "$(pwd)/telegram_mcp_server.py"

# Claude Code
claude mcp add telegram -- python "$(pwd)/telegram_mcp_server.py"

# Cursor: Settings → MCP → Add new MCP server (stdio):
#   Command: python "$(pwd)/telegram_mcp_server.py"

# n8n: MCP Server Trigger (stdio) → command: python "$(pwd)/telegram_mcp_server.py"
```

> **Проверка регистрации:**
> - Codex: `codex mcp list` — должен быть `telegram`
> - Claude Code: `claude mcp list` — должен быть `telegram`

### Шаг 4. Проверка

```bash
codex exec "Используй telegram list_chats, чтобы показать мои 10 последних чатов"
```

> **Важно для Codex**: MCP-сервер запускается Codex как внешний процесс, поэтому используйте песочницу с полным доступом — `codex exec -s danger-full-access ...` или в интерактивном режиме `/sandbox danger-full-access`. В `read-only`/`workspace-write` Codex не даст серверу стартовать (`MCP tool call failed/cancelled`). Интерактивная сессия в доверенной папке работает сразу.

## Как пользоваться

Просто просите агента в обычном разговоре:

- «Прочитай последние сообщения в чате с Иваном»
- «Найди в чате CRM Project обсуждение КП за апрель»
- «Собери все непрочитанные из рабочих чатов и сделай выжимку»

Агент сам вызовет `list_chats` → `read_chat` → `search_chat`.

## Безопасность

- **Read-only**: сервер не содержит ни одной операции отправки/редактирования.
- Секреты — в `.env` и `sessions/` — в `.gitignore`, в git не попадают.
- Сессии (`.session`) — это полный доступ к аккаунту, не коммитьте их и не передавайте никому.
- Каждый использует **свою** сессию (свой аккаунт Telegram).

## Известные ограничения

- Агент видит сообщения, но не медиафайлы (фото/видео/документы) — только факт их наличия.
- Для отправки сообщений нужен отдельный бот-аккаунт (Telegram Bot API), здесь намеренно нет.

## Устранение проблем

| Проблема | Решение |
|---|---|
| `Missing TELEGRAM_API_ID...` | Не заполнен `.env`, повторите шаг 1 |
| Ошибка входа «AUTH_KEY_UNREGISTERED» | Удалите `sessions/*.session` и повторите `bash setup.sh` |
| Codex: `MCP tool call failed/cancelled` | Используйте песочницу с полным доступом (см. Шаг 4) |
| Codex не видит инструменты | `codex mcp list`; перезапустите сессию |
| Claude Code не видит инструменты | `claude mcp list`; перезапустите сессию |

## Файлы

| Файл | Назначение |
|---|---|
| `telegram_mcp_server.py` | MCP-сервер (stdio), регистрируется в любом MCP-клиенте |
| `telegram_ro_common.py` | Read-only MTProto-хелперы, секреты из `.env` |
| `login.py` | Одноразовый вход, создаёт сессию |
| `setup.sh` | venv + зависимости + вход |
| `.env.example` | Шаблон настроек |
