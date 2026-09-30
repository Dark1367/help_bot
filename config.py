import os
import dotenv
import logging

dotenv.load_dotenv()

DB_PATH = os.getenv("DB_PATH", "bot.db") # файл базы SQLite, создаётся сам

BOT_TOKEN = os.getenv("BOT_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None # если ходите в OpenAI через прокси-сервис

def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger("aiogram").setLevel(logging.ERROR)
    logging.info(msg="Логи подключены")
