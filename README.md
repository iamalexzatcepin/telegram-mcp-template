# Telegram MCP — локальный read-only доступ для ИИ-агентов

Локальный MCP-сервер даёт Codex, Claude и другим MCP-клиентам три инструмента:

| Инструмент | Назначение |
|---|---|
| `list_chats(limit, account)` | Список чатов и количество непрочитанных |
| `read_chat(chat, limit, account)` | Последние сообщения выбранного чата |
| `search_chat(chat, query, limit, account)` | Поиск текста в выбранном чате |

Сервер работает **только на чтение**. В коде нет инструментов отправки,
редактирования или удаления сообщений. Сервер запускается локально через
STDIO и намеренно не предоставляет сетевой HTTP/SSE-доступ.

## Поддерживаемые клиенты

- ChatGPT/Codex Desktop;
- Codex CLI и IDE extension;
- Claude Code;
- Claude Desktop;
- любой локальный MCP-клиент с поддержкой STDIO.

Локальный сервер не работает напрямую в `chatgpt.com`, `claude.ai`, на телефоне
или на другом компьютере: эти среды не могут запустить процесс на вашей машине.

## Что понадобится

- Windows 10/11, macOS или Linux;
- [Git](https://git-scm.com/downloads);
- [Python 3.10+](https://www.python.org/downloads/);
- хотя бы один поддерживаемый MCP-клиент.

## Установка для новичка

### 1. Откройте терминал

- **macOS:** `Command + Space` → введите `Terminal` → Enter.
- **Windows:** меню «Пуск» → введите `PowerShell` → откройте PowerShell.
- **Linux:** нажмите `Ctrl + Alt + T` или откройте приложение Terminal.

### 2. Скачайте проект

macOS/Linux:

```bash
git clone https://github.com/iamalexzatcepin/telegram-mcp-template.git ~/telegram-mcp
cd ~/telegram-mcp
```

Windows PowerShell:

```powershell
git clone https://github.com/iamalexzatcepin/telegram-mcp-template.git "$env:USERPROFILE\telegram-mcp"
cd "$env:USERPROFILE\telegram-mcp"
```

Если GitHub сообщает, что репозиторий не найден, у вашей учётной записи пока
нет доступа к приватному репозиторию.

### 3. Получите Telegram API ID и API Hash

1. Откройте [my.telegram.org](https://my.telegram.org).
2. Войдите по номеру телефона.
3. Откройте **API development tools**.
4. Создайте приложение, например `Local Telegram MCP`.
5. Сохраните `api_id` и `api_hash`.

Не отправляйте `api_hash`, код входа или облачный пароль в чат с ИИ.

Создайте локальный `.env`.

macOS/Linux:

```bash
cp .env.example .env
nano .env
```

Сохранение в Nano: `Ctrl + O` → Enter → `Ctrl + X`.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Заполните файл локально:

```dotenv
TELEGRAM_API_ID=ваш_api_id
TELEGRAM_API_HASH=ваш_api_hash
```

### 4. Установите зависимости и войдите в Telegram

macOS/Linux:

```bash
bash setup.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Скрипт сам найдёт Python 3.10+, создаст `.venv`, установит зависимости и
попросит номер телефона, код из Telegram и, если включён, облачный пароль.
Вводите их только в своём терминале.

## Подключение к агенту

Во всех примерах используйте абсолютные пути, которые напечатает setup-скрипт.
Команда — это Python внутри `.venv`, аргумент — `telegram_mcp_server.py`.

### Codex CLI и ChatGPT/Codex Desktop

macOS/Linux:

```bash
codex mcp add telegram -- "$HOME/telegram-mcp/.venv/bin/python" "$HOME/telegram-mcp/telegram_mcp_server.py"
codex mcp get telegram
```

Windows PowerShell:

```powershell
codex mcp add telegram -- "$env:USERPROFILE\telegram-mcp\.venv\Scripts\python.exe" "$env:USERPROFILE\telegram-mcp\telegram_mcp_server.py"
codex mcp get telegram
```

В ChatGPT/Codex Desktop также можно открыть `Settings → MCP servers → Add
server`, выбрать STDIO и указать те же Command и Arguments. После сохранения
нажмите Restart. Локальные клиенты одного Codex-хоста используют конфигурацию
`~/.codex/config.toml` совместно.

### Claude Code

macOS/Linux:

```bash
claude mcp add --transport stdio --scope user telegram -- "$HOME/telegram-mcp/.venv/bin/python" "$HOME/telegram-mcp/telegram_mcp_server.py"
claude mcp get telegram
```

Windows PowerShell:

```powershell
claude mcp add --transport stdio --scope user telegram -- "$env:USERPROFILE\telegram-mcp\.venv\Scripts\python.exe" "$env:USERPROFILE\telegram-mcp\telegram_mcp_server.py"
claude mcp get telegram
```

Запустите новый сеанс Claude Code и введите `/mcp`. Область `user` делает
сервер доступным в разных локальных проектах этого пользователя.

### Claude Desktop

Откройте настройки Developer/MCP и добавьте локальный STDIO-сервер. Если ваша
версия Claude Desktop использует JSON-конфигурацию, добавьте объект, сохранив
остальные серверы:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "/absolute/path/to/telegram-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/telegram-mcp/telegram_mcp_server.py"]
    }
  }
}
```

Типовые расположения файла:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`;
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`.

Полностью перезапустите Claude Desktop и откройте новый чат.

### Другой STDIO MCP-клиент

Используйте эквивалентную конфигурацию:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/telegram_mcp_server.py"]
    }
  }
}
```

## Финальная проверка

Попросите агента:

> Используй telegram `list_chats` с limit=10 и покажи название, тип и число
> непрочитанных сообщений.

Не считайте установку завершённой, пока агент действительно не вернул список
ваших чатов.

## Несколько аккаунтов

Сервер поддерживает отдельные локальные сессии `default`, `work`, `personal` и
другие. Инструкция находится в [docs/MULTI_ACCOUNT.md](docs/MULTI_ACCOUNT.md).

## Инструкция для ИИ-агента

Если установку выполняет Codex, Claude или другой агент, попросите его полностью
прочитать [docs/AGENT_SETUP.md](docs/AGENT_SETUP.md) и следовать ей по одному
шагу. В этом файле зафиксированы правила безопасности и развилки для разных ОС.

## Безопасность и ограничения

- `.env` и `sessions/` исключены из Git;
- файл `.session` даёт доступ к аккаунту — не копируйте и не публикуйте его;
- медиафайлы не скачиваются, возвращается только признак `has_media`;
- запросы к Telegram выполняются от имени вашего аккаунта и подчиняются лимитам Telegram;
- не запускайте две операции с одной `.session` одновременно;
- не выставляйте этот сервер в интернет.

Подробнее: [SECURITY.md](SECURITY.md).

## Если что-то не работает

См. [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Разработка

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Структура проекта:

| Файл | Назначение |
|---|---|
| `telegram_mcp_server.py` | Три read-only MCP-инструмента, STDIO only |
| `telegram_ro_common.py` | Загрузка настроек и локальных сессий Telethon |
| `login.py` | Вход и создание именованной сессии |
| `setup.sh` | Установка на macOS/Linux |
| `setup.ps1` | Установка на Windows |
| `docs/AGENT_SETUP.md` | Пошаговый протокол для ИИ-агентов |
| `docs/MULTI_ACCOUNT.md` | Подключение нескольких аккаунтов |
| `docs/TROUBLESHOOTING.md` | Диагностика типовых проблем |

## Лицензия

[MIT](LICENSE) — проект можно использовать, изменять и распространять с
сохранением уведомления об авторских правах и текста лицензии.
