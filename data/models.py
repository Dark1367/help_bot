from sqlalchemy.types import BigInteger, Integer, Text, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey
import datetime
from data.database import Base

# Подключение Telegram Business: один владелец аккаунта = одно подключение
class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String, primary_key=True) # business_connection_id от Telegram
    user_id: Mapped[int] = mapped_column(BigInteger) # владелец аккаунта
    user_chat_id: Mapped[int] = mapped_column(BigInteger) # чат владельца с ботом, сюда шлём черновики
    is_enabled: Mapped[bool] = mapped_column(Boolean)
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

# Черновик ответа: сообщение клиента + ответ GPT, ждёт решения владельца
class Draft(Base):
    __tablename__ = "drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    connection_id: Mapped[str] = mapped_column(ForeignKey("connections.id"))
    chat_id: Mapped[int] = mapped_column(BigInteger) # чат с клиентом
    client_name: Mapped[str] = mapped_column(String)
    message_text: Mapped[str] = mapped_column(Text)
    answer_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String) # pending / sent / rejected
    creation_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
