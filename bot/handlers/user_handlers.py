import logging
from datetime import datetime, timezone

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import BusinessConnection, CallbackQuery, Message

from ..states.user_states import REPHRASE
from ..keyboards.user_keyboards import draft_kb, rephrase_kb
import utils.gpt as gpt

from data.models import Connection, Draft
import data.crud as db
from data import SessionDep

OUTDATED = "Кнопка устарела"
ALREADY_DONE = "Это сообщение уже обработано"
GPT_ERROR = "Не удалось получить ответ от GPT, попробуйте ещё раз"

START_TEXT = """👋 Я помогаю отвечать на сообщения в Telegram Business.

<b>Как подключить:</b>
Настройки → Telegram Business → Чат-боты → выберите меня и разрешите отвечать на сообщения.

<b>Как работаю:</b>
Когда вам напишут, я придумаю ответ и пришлю его сюда. Вы решаете:
✅ <b>Принять</b> — отправлю ответ собеседнику
✏️ <b>Переформулировать</b> — перепишу, можно добавить свои правки
❌ <b>Отказаться</b> — ничего не отправлю"""

router = Router()


# Текст черновика для владельца
def draft_text(draft: Draft) -> str:
    return f"""💬 Сообщение от {draft.client_name}:
{draft.message_text}

🤖 Ответ:
{draft.answer_text}"""


# Подключение из Telegram -> модель для базы
def to_connection(connection: BusinessConnection) -> Connection:
    return Connection(
        id=connection.id,
        user_id=connection.user.id,
        user_chat_id=connection.user_chat_id,
        is_enabled=connection.is_enabled,
        creation_date=datetime.now(timezone.utc),
    )


# Достаём подключение из базы, а если его там нет (бот подключили до запуска) — спрашиваем у Telegram
async def load_connection(connection_id: str, bot: Bot, session: SessionDep) -> Connection:
    connection = await db.get_connection(connection_id, session)
    if connection:
        return connection
    return await db.save_connection(to_connection(await bot.get_business_connection(connection_id)), session)


# /start
@router.message(CommandStart())
async def on_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(START_TEXT, parse_mode="HTML")


# Бота подключили / отключили / поменяли права в Telegram Business
@router.business_connection()
async def on_business_connection(connection: BusinessConnection, bot: Bot, session: SessionDep) -> None:
    await db.save_connection(to_connection(connection), session)

    if not connection.is_enabled:
        await bot.send_message(connection.user_chat_id, "Бот отключён от вашего аккаунта")
        return
    if connection.rights and not connection.rights.can_reply:
        await bot.send_message(connection.user_chat_id, "⚠️ Бот подключён, но не может отвечать. Разрешите ему отвечать на сообщения в настройках Telegram Business")
        return
    await bot.send_message(connection.user_chat_id, "✅ Бот подключён. Новые сообщения и ответы на них буду присылать сюда")


# Новое сообщение владельцу аккаунта: генерируем ответ и отправляем на апрув
@router.business_message(F.text)
async def on_business_message(message: Message, bot: Bot, session: SessionDep) -> None:
    connection = await load_connection(message.business_connection_id, bot, session)
    if not connection.is_enabled or message.from_user.id == connection.user_id:
        return # свои сообщения владельца не обрабатываем

    client_name = message.from_user.full_name
    if message.from_user.username:
        client_name += f" (@{message.from_user.username})"

    try:
        answer = await gpt.generate_answer(message.text)
    except Exception as e:
        logging.error(msg=f"Ошибка GPT: {e}")
        await bot.send_message(connection.user_chat_id, f"💬 Сообщение от {client_name}:\n{message.text}\n\n{GPT_ERROR}")
        return

    draft = await db.create_draft(
        Draft(
            connection_id=connection.id,
            chat_id=message.chat.id,
            client_name=client_name,
            message_text=message.text,
            answer_text=answer,
            status="pending",
            creation_date=datetime.now(timezone.utc),
        ),
        session,
    )
    await bot.send_message(connection.user_chat_id, draft_text(draft), reply_markup=draft_kb(draft.id))


# Правки владельца к ответу
@router.message(REPHRASE)
async def rephrase_edits(message: Message, state: FSMContext, session: SessionDep) -> None:
    draft_id = await state.get_value("draft_id")
    await state.clear()

    draft = await db.get_draft(draft_id, session)
    if not draft or draft.status != "pending":
        await message.answer(ALREADY_DONE)
        return
    if not message.text:
        await message.answer("Отправьте правки текстом")
        await state.set_state(REPHRASE)
        await state.update_data(draft_id=draft_id)
        return

    wait = await message.answer("⏳ Переформулирую...")
    try:
        answer = await gpt.generate_answer(draft.message_text, draft.answer_text, message.text)
    except Exception as e:
        logging.error(msg=f"Ошибка GPT: {e}")
        await wait.edit_text(GPT_ERROR, reply_markup=draft_kb(draft.id))
        return

    draft = await db.set_draft_answer(draft.id, answer, session)
    await wait.edit_text(draft_text(draft), reply_markup=draft_kb(draft.id))


# Кнопки черновика: draft:{action}:{id}
@router.callback_query(F.data.startswith("draft:"))
async def on_draft_callback(callback: CallbackQuery, bot: Bot, state: FSMContext, session: SessionDep) -> None:
    _, action, draft_id = callback.data.split(":")
    draft = await db.get_draft(int(draft_id), session)
    connection = await db.get_connection(draft.connection_id, session) if draft else None
    if not draft or connection.user_id != callback.from_user.id:
        await callback.answer(OUTDATED)
        return
    if draft.status != "pending":
        await callback.answer(ALREADY_DONE)
        return

    if action == "accept":
        try:
            await bot.send_message(chat_id=draft.chat_id, text=draft.answer_text, business_connection_id=draft.connection_id)
        except TelegramAPIError as e:
            await callback.answer(f"Не удалось отправить: {e.message}", show_alert=True)
            return
        await db.set_draft_status(draft.id, "sent", session)
        await state.clear()
        await callback.message.edit_text(f"{draft_text(draft)}\n\n✅ Отправлено")
        await callback.answer()

    elif action == "reject":
        await db.set_draft_status(draft.id, "rejected", session)
        await state.clear()
        await callback.message.edit_text(f"{draft_text(draft)}\n\n❌ Отклонено")
        await callback.answer()

    elif action == "rephrase":
        await state.set_state(REPHRASE)
        await state.update_data(draft_id=draft.id)
        await callback.message.edit_text(
            f"{draft_text(draft)}\n\n✏️ Напишите, что поправить в ответе, или нажмите «Без правок»",
            reply_markup=rephrase_kb(draft.id),
        )
        await callback.answer()

    elif action == "regen": # переформулировать без правок
        await state.clear()
        await callback.answer("⏳ Переформулирую...")
        try:
            answer = await gpt.generate_answer(draft.message_text, draft.answer_text)
        except Exception as e:
            logging.error(msg=f"Ошибка GPT: {e}")
            await callback.message.edit_text(f"{draft_text(draft)}\n\n{GPT_ERROR}", reply_markup=draft_kb(draft.id))
            return
        draft = await db.set_draft_answer(draft.id, answer, session)
        await callback.message.edit_text(draft_text(draft), reply_markup=draft_kb(draft.id))

    elif action == "back": # отмена правок
        await state.clear()
        await callback.message.edit_text(draft_text(draft), reply_markup=draft_kb(draft.id))
        await callback.answer()

    else:
        await callback.answer(OUTDATED)


# Любое другое сообщение боту
@router.message()
async def unknown_message(message: Message) -> None:
    await message.answer(START_TEXT, parse_mode="HTML")
