from aiogram.utils.keyboard import InlineKeyboardBuilder


# Клавиатура черновика ответа
def draft_kb(draft_id):
    return (
        InlineKeyboardBuilder()
        .button(text="✅ Принять", callback_data=f"draft:accept:{draft_id}")
        .button(text="✏️ Переформулировать", callback_data=f"draft:rephrase:{draft_id}")
        .button(text="❌ Отказаться", callback_data=f"draft:reject:{draft_id}")
        .adjust(1)
        .as_markup()
    )

# Клавиатура при переформулировании: ждём правки или переписываем без них
def rephrase_kb(draft_id):
    return (
        InlineKeyboardBuilder()
        .button(text="🔄 Без правок", callback_data=f"draft:regen:{draft_id}")
        .button(text="Отмена", callback_data=f"draft:back:{draft_id}")
        .adjust(1)
        .as_markup()
    )
