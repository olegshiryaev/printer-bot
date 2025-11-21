from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def pagination_kb(items, page: int, total: int, prefix: str):
    builder = InlineKeyboardBuilder()
    
    for item in items:
        builder.button(text=item["name"], callback_data=f"{prefix}_select_{item['id']}")
    builder.adjust(1)

    total_pages = (total + 4) // 5  # PAGE_SIZE = 5

    nav = InlineKeyboardBuilder()
    if page > 1:
        nav.button(text="◀ Назад", callback_data=f"{prefix}_pg_{page-1}")
    nav.button(text=f"{page}/{total_pages}", callback_data="ignore")
    if page < total_pages:
        nav.button(text="Вперёд ▶", callback_data=f"{prefix}_pg_{page+1}")
    
    if nav.buttons:
        builder.row(*nav.buttons)

    builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
    return builder.as_markup()