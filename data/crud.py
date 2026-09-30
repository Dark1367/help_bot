from data.models import Connection, Draft
from data import SessionDep


# Выбор подключения по id
async def get_connection(id: str, session: SessionDep) -> Connection | None:
    return await session.get(Connection, id)

# Сохранить подключение (новое или обновить существующее)
async def save_connection(connection: Connection, session: SessionDep) -> Connection:
    connection = await session.merge(connection)
    await session.commit()
    return connection

# Выбор черновика по id
async def get_draft(id: int, session: SessionDep) -> Draft | None:
    return await session.get(Draft, id)

# Добавить черновик
async def create_draft(draft: Draft, session: SessionDep) -> Draft:
    session.add(draft)
    await session.commit()
    await session.refresh(draft)
    return draft

# Изменить текст ответа в черновике
async def set_draft_answer(id: int, answer: str, session: SessionDep) -> Draft | None:
    draft = await get_draft(id, session)
    if draft is None:
        return None

    draft.answer_text = answer
    await session.commit()
    return draft

# Изменить статус черновика
async def set_draft_status(id: int, status: str, session: SessionDep) -> Draft | None:
    draft = await get_draft(id, session)
    if draft is None:
        return None

    draft.status = status
    await session.commit()
    return draft
