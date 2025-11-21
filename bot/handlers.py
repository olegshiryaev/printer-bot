import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from bot.fsm import SearchFSM
from bot.keyboards import make_results_kb, back_to_main_kb
from bot.api import (
    search_printers,
    search_cartridges,
    get_printer,
    get_cartridge,
)
from bot.utils import decode_payload
from bot.limiter import anti_flood

router = Router()
log = logging.getLogger(__name__)


# ======================================================
# /start
# ======================================================
@router.message(F.text == "/start")
@anti_flood
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Отправьте название *принтера* или *картриджа*.\n"
        "Я найду все совместимые варианты.\n\n"
        "Пример: *HP LaserJet 1020* или *CB435A*."
    )
    await SearchFSM.waiting_for_query.set()


# ======================================================
# Основной обработчик строки поиска
# ======================================================
@router.message(SearchFSM.waiting_for_query)
@anti_flood
async def search_handler(message: Message, state: FSMContext):
    query = message.text.strip()

    if len(query) < 2:
        await message.answer("❗ Запрос должен содержать минимум 2 символа.")
        return

    await state.update_data(query=query)

    # Делаем два запроса к API параллельно
    printers_task = search_printers(query, page=1, limit=50)
    cartridges_task = search_cartridges(query, page=1, limit=50)

    printers, cartridges = await printers_task, await cartridges_task

    # Если API упало — вернуть пустые
    printers = printers or {"items": []}
    cartridges = cartridges or {"items": []}

    # Объединяем в единый список
    results = []

    for p in printers.get("items", []):
        results.append({"id": p["id"], "name": p["name"], "type": "printer"})

    for c in cartridges.get("items", []):
        results.append({"id": c["id"], "name": c["name"], "type": "cartridge"})

    # Если ничего не найдено
    if not results:
        await message.answer("❌ Ничего не найдено.", reply_markup=back_to_main_kb())
        return

    # Один найден — сразу показываем
    if len(results) == 1:
        await show_item(message, results[0])
        return

    # Несколько — выбираем
    await SearchFSM.selecting_result.set()
    await state.update_data(results=results)

    await message.answer(
        f"🔎 Найдено вариантов: *{len(results)}*\nВыберите нужный:",
        reply_markup=make_results_kb(results),
    )


# ======================================================
# Пользователь нажал на кнопку выбора
# ======================================================
@router.callback_query(F.data.startswith("pick:"))
@anti_flood
async def pick_item(call: CallbackQuery, state: FSMContext):
    await call.answer()

    try:
        payload = decode_payload(call.data)
    except Exception:
        await call.message.answer("Ошибка обработки кнопки. Повторите запрос.")
        return

    item_type = payload.get("type")
    item_id = payload.get("id")

    if not item_type or not item_id:
        await call.message.answer("Некорректные данные.")
        return

    # Получаем полные данные о принтере или картридже
    if item_type == "printer":
        item = await get_printer(item_id)
    else:
        item = await get_cartridge(item_id)

    if not item:
        await call.message.answer("⚠️ Ошибка API. Повторите запрос.")
        return

    # Приводим к единому виду
    normalized = {
        "id": item_id,
        "type": item_type,
        "name": item["name"],
        "cartridges": item.get("cartridges", []),
        "printers": item.get("printers", []),
    }

    await show_item(call.message, normalized)


# ======================================================
# Новый поиск
# ======================================================
@router.callback_query(F.data == "new_search")
async def new_search(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.answer("Введите новый запрос:")
    await SearchFSM.waiting_for_query.set()


# ======================================================
# Универсальная функция вывода результата
# ======================================================
async def show_item(message: Message, item: dict):
    text = []

    if item["type"] == "printer":
        text.append(f"🖨 Принтер: *{item['name']}*")
        if item.get("cartridges"):
            text.append("\nПодходящие картриджи:")
            text.extend(f"• {c}" for c in item["cartridges"])

    elif item["type"] == "cartridge":
        text.append(f"🧩 Картридж: *{item['name']}*")
        if item.get("printers"):
            text.append("\nСовместимые принтеры:")
            text.extend(f"• {p}" for p in item["printers"])

    else:
        text.append("Ошибка данных 🙁")

    try:
        await message.answer("\n".join(text), reply_markup=back_to_main_kb())
    except TelegramBadRequest:
        await message.answer("⚠️ Ошибка вывода сообщения.")
