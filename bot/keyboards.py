from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Найти картриджи по принтеру", callback_data="menu_printer_to_cartridges")],
        [InlineKeyboardButton(text="Найти принтеры по картриджу", callback_data="menu_cartridge_to_printers")],
    ]
)

def back_to_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Главное меню", callback_data="back_to_main")]]
    )