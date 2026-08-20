# Протокол установки для ИИ-агента

Этот файл предназначен для Codex, Claude Code и других агентов. Цель — провести
человека без технического опыта через локальную read-only настройку Telegram.

## Обязательные правила

1. Выполняй только один шаг за раз.
2. Завершай каждый шаг фразой `Статус: сделано` или `Статус: жду от тебя`.
3. Не проси присылать в чат API Hash, код Telegram, облачный пароль или GitHub-токен.
4. Не печатай содержимое `.env` и `sessions/*.session`.
5. Не передавай секреты в аргументах команд.
6. Авторизацию Telegram выполняет только человек в своём терминале.
7. Не удаляй существующие файлы и конфигурации без отдельного подтверждения.
8. Не перезаписывай целиком чужой JSON/TOML — аккуратно добавляй секцию.
9. Используй абсолютные пути к Python из `.venv` и файлу сервера.
10. Не включай полный доступ к системе, если клиент может запустить сервер с меньшими правами.
11. Не настраивай HTTP, SSE, туннель или публичный URL. Этот шаблон STDIO-only.
12. Не объявляй успех до реального вызова `list_chats(limit=10)`.

## Шаг 0. Определи среду

Определи Windows/macOS/Linux. Проверь `git`, Python 3.10+ и доступные клиенты:

```text
git --version
python / python3 / python3.10+ --version
codex --version
claude --version
```

Проверь альтернативные Python: `python3.13`, `python3.12`, `python3.11`,
`python3.10`, а на Windows также launcher `py`.

Если человеку нужно открыть терминал:

- macOS: `Command + Space` → Terminal;
- Windows: Пуск → PowerShell;
- Linux: `Ctrl + Alt + T`.

Уточни целевые клиенты: Codex CLI/Desktop, Claude Code/Desktop или другой
STDIO MCP-клиент. Если выбрано несколько клиентов, настрой каждый отдельно.

## Шаг 1. Клонируй репозиторий

macOS/Linux:

```bash
git clone https://github.com/iamalexzatcepin/telegram-mcp-template.git ~/telegram-mcp
```

Windows PowerShell:

```powershell
git clone https://github.com/iamalexzatcepin/telegram-mcp-template.git "$env:USERPROFILE\telegram-mcp"
```

Если папка существует, не удаляй её: проверь remote и состояние. Если приватный
репозиторий требует доступ, предложи безопасный вход GitHub через браузер или
GitHub CLI. Не принимай токен в чате.

## Шаг 2. Подготовь `.env`

Если `.env` отсутствует, скопируй `.env.example`. Объясни человеку путь:
`my.telegram.org → API development tools → Create new application`.

Пусть человек сам откроет `.env` в Nano/Notepad и заполнит:

```dotenv
TELEGRAM_API_ID=...
TELEGRAM_API_HASH=...
```

После подтверждения проверь только присутствие и формат непустых переменных.
Никогда не выводи значения. На macOS/Linux установи права `chmod 600 .env`.

## Шаг 3. Установка и вход

macOS/Linux:

```bash
cd ~/telegram-mcp && bash setup.sh
```

Windows PowerShell:

```powershell
cd "$env:USERPROFILE\telegram-mcp"
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Скажи человеку ввести номер, код и облачный пароль только в терминале. Дождись
`готово`, затем проверь наличие непустой `sessions/default.session`, не читая её.

## Шаг 4. Подключи выбранный клиент

Получай абсолютные пути программно. Не подставляй `USERNAME` буквально.

### Codex

```bash
codex mcp add telegram -- <ABS_PYTHON> <ABS_SERVER>
codex mcp get telegram
```

Для Desktop можно использовать `Settings → MCP servers → Add server → STDIO`:
Command = `<ABS_PYTHON>`, Arguments = `<ABS_SERVER>`. После сохранения Restart.

### Claude Code

```bash
claude mcp add --transport stdio --scope user telegram -- <ABS_PYTHON> <ABS_SERVER>
claude mcp get telegram
```

Затем новый сеанс и `/mcp`. Если синтаксис изменился, сначала вызови
`claude mcp add --help` и адаптируй только форму команды.

### Claude Desktop или другой клиент

Добавь, сохранив существующие настройки:

```json
{
  "mcpServers": {
    "telegram": {
      "command": "<ABS_PYTHON>",
      "args": ["<ABS_SERVER>"]
    }
  }
}
```

Полностью перезапусти приложение и открой новый чат.

## Шаг 5. Проверь инструменты

Найди `list_chats`, `read_chat`, `search_chat`. Если их нет, проверь:

1. сервер включён;
2. пути абсолютные и существуют;
3. открыта новая сессия клиента;
4. `.env` заполнен;
5. `sessions/default.session` существует;
6. сервер не запускается параллельно другим процессом с той же сессией.

## Шаг 6. Финальный тест

Вызови `list_chats(limit=10, account="default")`. Покажи только название, тип и
число непрочитанных. Спроси, узнаёт ли человек свои чаты.

После подтверждения напиши:

> Готово! Telegram подключён. Теперь ты можешь просить меня: «прочитай последние
> сообщения в чате X», «найди в чате Y слово Z», «сделай дайджест непрочитанных».
> Это работает только на чтение — отправлять, изменять или удалять сообщения я
> не могу.

Заверши: `Статус: сделано.`
