from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.http import api_get
from bot.cache import cache
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.keyboards.inline import pagination_kb

router = Router(name="search")
PAGE_SIZE = 5


class Search(StatesGroup):
    printer = State()
    cartridge = State()


@cache
async def search_printers(q: str, page: int = 1):
    return await api_get("/printers", params={"q": q, "page": page, "limit": PAGE_SIZE})


@cache
async def search_cartridges(q: str, page: int = 1):
    return await api_get("/cartridges", params={"q": q, "page": page, "limit": PAGE_SIZE})


@cache
async def get_printer(printer_id: int):
    return await api_get(f"/printer/{printer_id}")


@cache
async def get_cartridge(cartridge_id: int):
    return await api_get(f"/cartridge/{cartridge_id}")


async def show_printer(target, data: dict):
    text = f"<b>Принтер:</b> {data['name']}\n\n<b>Совместимые картриджи:</b>\n" \
           f"{', '.join(data.get('cartridges') or []) or '—'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)


async def show_cartridge(target, data: dict):
    text = f"<b>Картридж:</b> {data['name']}\n\n<b>Подходит к принтерам:</b>\n" \
           f"{', '.join(data.get('printers') or []) or '—'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)


# ==================== Ввод текста ====================
@router.message(Search.printer)
@router.message(Search.cartridge)
async def process_search(message: Message, state: FSMContext):
    q = message.text.strip()
    if len(q) < 2:
        await message.answer("Минимум 2 символа")
        return

    current = await state.get_state()
    is_printer = current == Search.printer
    search_func = search_printers if is_printer else search_cartridges
    prefix = "printer" if is_printer else "cartridge"

    await message.answer("🔍 Ищу…")
    resp = await search_func(q)

    items = resp.get("items", [])
    total = resp.get("total", 0)

    if not items:
        await message.answer(
            f"Ничего не найдено по «{q}»",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
            ]])
        )
        await state.clear()
        return

    # Сохраняем запрос для пагинации
    await state.update_data(last_query=q, last_prefix=prefix)

    if len(items) == 1:
        func = get_printer if is_printer else get_cartridge
        data = await func(items[0]["id"])
        await show_printer(message, data) if is_printer else show_cartridge(message, data)
        await state.clear()
        return

    kb = pagination_kb(items, page=1, total=total, prefix=prefix)
    await message.answer(f"Найдено: {total}\nВыберите:", reply_markup=kb)
    await state.clear()