from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.keyboards import main_keyboard

router = Router(name="start")


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я помогу найти совместимые картриджи и принтеры.\n"
        "Напиши модель или выбери ниже 👇"
    )
    menu = await message.answer("Выберите действие:", reply_markup=main_keyboard)
    await state.update_data(menu_message_id=menu.message_id)