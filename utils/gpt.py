from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_BASE_URL

client = AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

SYSTEM_PROMPT = """Ты помогаешь владельцу аккаунта отвечать на сообщения в Telegram.
Тебе присылают сообщение, которое написали владельцу. Напиши ответ от его имени:
коротко, вежливо, по делу, на языке сообщения. Не придумывай факты, цены и сроки —
если чего-то не знаешь, предложи уточнить. Пиши только текст ответа, без пояснений."""


# Генерирует ответ на сообщение.
# Если передан old_answer — переписывает его (с правками владельца, если они есть)
async def generate_answer(message_text: str, old_answer: str | None = None, edits: str | None = None) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Сообщение:\n{message_text}"},
    ]
    if old_answer:
        messages.append({"role": "assistant", "content": old_answer})
        if edits:
            messages.append({"role": "user", "content": f"Перепиши ответ с учётом правок владельца:\n{edits}"})
        else:
            messages.append({"role": "user", "content": "Перепиши ответ другими словами."})

    response = await client.chat.completions.create(model=OPENAI_MODEL, messages=messages)
    return response.choices[0].message.content.strip()
