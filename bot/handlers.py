from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx
import logging
from functools import wraps

from bot.keyboards import main_keyboard
from app.config import settings

router = Router()
logger = logging.getLogger(__name__)

API_BASE = settings.API_BASE
PAGE_SIZE = 5


# ===================== ПРАВИЛЬНЫЙ ASYNC-КЭШ =====================
def async_lru_cache(maxsize=512):
    cache = {}
    order = []

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key in cache:
                return cache[key]

            result = await func(*args, **kwargs)

            # Ограничиваем размер кэша
            if len(cache) >= maxsize:
                oldest_key = order.pop(0)
                cache.pop(oldest_key, None)
            cache[key] = result
            order.append(key)
            return result
        return wrapper
    return decorator


# ===================== API-ФУНКЦИИ С КЭШЕМ =====================
@async_lru_cache(maxsize=512)
async def search_printers(q: str, page: int = 1):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_BASE}/printers", params={"q": q, "page": page, "limit": PAGE_SIZE})
        r.raise_for_status()
        return r.json()


@async_lru_cache(maxsize=512)
async def search_cartridges(q: str, page: int = 1):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_BASE}/cartridges", params={"q": q, "page": page, "limit": PAGE_SIZE})
        r.raise_for_status()
        return r.json()


@async_lru_cache(maxsize=256)
async def get_printer(printer_id: int):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_BASE}/printer/{printer_id}")
        r.raise_for_status()
        return r.json()


@async_lru_cache(maxsize=256)
async def get_cartridge(cartridge_id: int):
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{API_BASE}/cartridge/{cartridge_id}")
        r.raise_for_status()
        return r.json()


# ===================== Клавиатуры =====================
def make_pagination_kb(items: list[dict], page: int, total: int, prefix: str, q: str):
    kb = []
    for item in items:
        kb.append([InlineKeyboardButton(text=item["name"], callback_data=f"{prefix}_select_{item['id']}")])

    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="Назад", callback_data=f"{prefix}_page_{page-1}_{q}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore"))
    if page < total_pages:
        nav.append(InlineKeyboardButton(text="Вперёд", callback_data=f"{prefix}_page_{page+1}_{q}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="Главное меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ===================== Показ результата =====================
async def show_printer(target, data: dict):
    text = f"<b>Принтер:</b> {data['name']}\n\n<b>Совместимые картриджи:</b>\n{', '.join(data['cartridges']) or '—'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Новый поиск", callback_data="back_to_main")]])
    if isinstance(target, types.Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)


async def show_cartridge(target, data: dict):
    text = f"<b>Картридж:</b> {data['name']}\n\n<b>Подходит к принтерам:</b>\n{', '.join(data['printers']) or '—'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Новый поиск", callback_data="back_to_main")]])
    if isinstance(target, types.Message):
        await target.answer(text, reply_markup=kb)
    else:
        await target.message.edit_text(text, reply_markup=kb)


# ===================== FSM =====================
class SearchStates(StatesGroup):
    waiting_for_printer_name = State()
    waiting_for_cartridge_name = State()


# ===================== /start =====================
@router.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Я помогу найти совместимые картриджи и принтеры.\nНапиши модель.")
    menu_msg = await message.answer("Выберите:", reply_markup=main_keyboard)
    await state.update_data(menu_message=menu_msg.message_id)


# ===================== Меню =====================
@router.callback_query(F.data == "menu_printer_to_cartridges")
async def menu_printer(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_printer_name)
    await _edit_menu(call, state, "Введите модель принтера (мин. 2 символа):")
    await call.answer()

@router.callback_query(F.data == "menu_cartridge_to_printers")
async def menu_cartridge(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_cartridge_name)
    await _edit_menu(call, state, "Введите модель картриджа (мин. 2 символа):")
    await call.answer()

async def _edit_menu(call: types.CallbackQuery, state: FSMContext, text: str):
    data = await state.get_data()
    msg_id = data.get("menu_message")
    if msg_id:
        try:
            await call.bot.edit_message_text(chat_id=call.message.chat.id, message_id=msg_id, text=text, reply_markup=None)
        except Exception as e:
            logger.debug(f"Не удалось отредактировать меню: {e}")


@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except:
        pass
    menu = await call.message.answer("Выберите:", reply_markup=main_keyboard)
    await state.update_data(menu_message=menu.message_id)
    await call.answer()

@router.callback_query(F.data == "ignore")
async def ignore(call: types.CallbackQuery):
    await call.answer()


# ===================== Поиск =====================
@router.message(SearchStates.waiting_for_printer_name)
async def printer_search(message: types.Message, state: FSMContext):
    await _handle_search(message, state, search_printers, "printer", show_printer)

@router.message(SearchStates.waiting_for_cartridge_name)
async def cartridge_search(message: types.Message, state: FSMContext):
    await _handle_search(message, state, search_cartridges, "cartridge", show_cartridge)

async def _handle_search(message: types.Message, state: FSMContext, search_func, prefix: str, show_func):
    q = message.text.strip()
    if len(q) < 2:
        await message.answer("Минимум 2 символа")
        return

    resp = await search_func(q)
    items = resp.get("items", [])
    total = resp.get("total", 0)

    if not items:
        await message.answer(f"Ничего не найдено по «{q}»", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="Новый поиск", callback_data="back_to_main")
        ]]))
        await state.clear()
        return

    if len(items) == 1:
        data = await (get_printer if prefix == "printer" else get_cartridge)(items[0]["id"])
        await show_func(message, data)
        await state.clear()
        return

    kb = make_pagination_kb(items, 1, total, prefix, q)
    await message.answer(f"Найдено: {total}\nВыберите:", reply_markup=kb)
    await state.clear()


# ===================== Выбор и пагинация =====================
@router.callback_query(F.data.regexp(r"^(printer|cartridge)_select_\d+$"))
async def select_item(call: types.CallbackQuery):
    item_id = int(call.data.split("_")[-1])
    is_printer = call.data.startswith("printer")
    data = await (get_printer if is_printer else get_cartridge)(item_id)
    await (show_printer if is_printer else show_cartridge)(call, data)
    await call.answer()

@router.callback_query(F.data.regexp(r"^(printer|cartridge)_page_\d+_.+$"))
async def paginate(call: types.CallbackQuery):
    parts = call.data.split("_")
    prefix = parts[0]
    page = int(parts[2])
    q = "_".join(parts[3:])
    func = search_printers if prefix == "printer" else search_cartridges
    resp = await func(q, page=page)
    kb = make_pagination_kb(resp["items"], page, resp["total"], prefix, q)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()


# ===================== Любой текст =====================
@router.message(F.text, ~F.text.startswith("/"))
async def any_text(message: types.Message, state: FSMContext):
    if await state.get_state():
        return
    q = message.text.strip()
    if len(q) < 2:
        await message.answer("Напишите хотя бы 2 символа")
        return
    await state.set_state(SearchStates.waiting_for_printer_name)
    await message.answer("Ищу принтеры…")
    await printer_search(message, state)


@router.message(F.text.startswith("/"))
async def unknown_command(message: types.Message):
    await message.answer("Неизвестная команда\nНапиши /start или модель принтера/картриджа")