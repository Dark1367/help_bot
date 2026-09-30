# Business GPT Bot

Telegram-бот для Telegram Business: получает сообщения, которые пишут владельцу аккаунта,
генерирует ответ через ChatGPT и присылает его владельцу на апрув.

Кнопки под черновиком:
- ✅ **Принять** — ответ уходит собеседнику от имени владельца
- ✏️ **Переформулировать** — владелец пишет правки (или жмёт «Без правок»), GPT переписывает ответ
- ❌ **Отказаться** — ничего не отправляется

## Запуск

1. В @BotFather: `/mybots` → бот → Bot Settings → **Business Mode** → включить.
2. Заполнить `.env` по образцу `.env.example` (нужны только `BOT_TOKEN` и `OPENAI_API_KEY`).
3. Установить зависимости и запустить:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```
   База — SQLite: файл `bot.db` и таблицы создаются автоматически при первом запуске.
4. В Telegram (нужен Premium): Настройки → Telegram Business → Чат-боты → выбрать бота,
   разрешить ему отвечать на сообщения.
5. Написать боту `/start`.

## Структура

```
main.py                         запуск, подключение роутера и middleware
config.py                       настройки из .env
bot/handlers/user_handlers.py   вся логика бота
bot/keyboards/user_keyboards.py клавиатуры
bot/states/user_states.py       состояния FSM
bot/middlewares/db.py           сессия БД в хендлеры
data/models.py                  таблицы connections и drafts
data/crud.py                    запросы к БД
utils/gpt.py                    запрос к ChatGPT и промпт
```

## Ограничения Telegram

- Бот может ответить собеседнику только в течение 24 часов после его последнего сообщения.
- Обрабатываются только текстовые сообщения.
