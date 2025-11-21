import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.fsm import SearchFSM
from bot.keyboards import make_results_keyboard, back_to_search_kb
from bot.api import api
from bot.utils import decode_payload
from bot.limiter import anti_flood

router = Router()
log = logging.getLogger(__name__)


# -----------------------------
# /start
# -----------------------------
@router.message(F.text == "/start")
@anti_flood
async def start_handler(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "👋 Отправьте название *принтера* или *картриджа*. "
        "Я найду все совместимые варианты.\n\n"
        "Пример: *HP LaserJet 1020* или *CB435A*."
    )


# -----------------------------
# Ввод строки поиска
# -----------------------------
@router.message(SearchFSM.waiting_for_query)
@router.message()
@anti_flood
async def search_handler(message: Message, state: FSMContext):
    query = message.text.strip()

    if len(query) < 2:
        await message.answer("❗ Запрос должен содержать минимум 2 символа.")
        return

    await state.update_data(query=query)

    try:
        results = await api.search(query)
    except Exception:
        log.exception("API error during search")
        await message.answer("⚠️ Ошибка API. Повторите запрос позже.")
        return

    if not results:
        await message.answer(
            "❌ Ничего не найдено.", reply_markup=back_to_search_kb()
        )
        return

    # Если найден один — показываем сразу
    if len(results) == 1:
        await show_result(message, results[0])
        return

    # Много результатов — показываем кнопки
    await SearchFSM.selecting_result.set()

    await message.answer(
        f"🔎 Найдено вариантов: *{len(results)}*\nВыберите нужный:",
        reply_markup=make_results_keyboard(results),
    )


# -----------------------------
# Выбор результата из списка
# -----------------------------
@router.callback_query(F.data.startswith("pick:"))
@anti_flood
async def pick_result_callback(call: CallbackQuery, state: FSMContext):
    await call.answer()

    try:
        item = decode_payload(call.data)
    except Exception:
        await call.message.answer("Ошибка обработки кнопки. Повторите запрос.")
        return

    await show_result(call.message, item)


# -----------------------------
# Кнопка "Новый поиск"
# -----------------------------
@router.callback_query(F.data == "new_search")
async def new_search(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()

    await call.message.answer(
        "Введите новый запрос:",
    )
    await SearchFSM.waiting_for_query.set()


# -----------------------------
# Утилита отображения результата
# -----------------------------
async def show_result(message: Message, item: dict):
    """
    Унифицированный вывод карточки принтера или картриджа.
    """
    text_lines = []

    if item.get("type") == "printer":
        text_lines.append(f"🖨 Принтер: *{item['name']}*")
        if cartridges := item.get("cartridges"):
            text_lines.append("\nПодходящие картриджи:")
            for c in cartridges:
                text_lines.append(f"• {c}")

    elif item.get("type") == "cartridge":
        text_lines.append(f"🧩 Картридж: *{item['name']}*")
        if printers := item.get("printers"):
            text_lines.append("\nСовместимые принтеры:")
            for p in printers:
                text_lines.append(f"• {p}")

    else:
        text_lines.append("Неверный формат данных 😕")
        log.error("Unexpected item format: %s", item)

    try:
        await message.answer(
            "\n".join(text_lines),
            reply_markup=back_to_search_kb(),
        )
    except TelegramBadRequest:
        await message.answer("⚠️ Ошибка вывода сообщения.")
