# bot/handlers.py — финальная версия с идеальным UX (одно главное меню)
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import httpx
import logging

from bot.keyboards import main_keyboard

router = Router()
logger = logging.getLogger(__name__)

API_BASE = "http://127.0.0.1:8000/api"

class SearchStates(StatesGroup):
    waiting_for_printer_name = State()
    waiting_for_cartridge_name = State()

PAGE_SIZE = 5


# ===================== API =====================
async def search_printers(q: str, page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/printers", params={"q": q, "page": page, "limit": PAGE_SIZE})
        r.raise_for_status()
        return r.json()


async def search_cartridges(q: str, page: int = 1) -> list:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/cartridges", params={"q": q, "page": page, "limit": PAGE_SIZE})
        r.raise_for_status()
        return r.json()


async def get_printer(printer_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/printer/{printer_id}")
        r.raise_for_status()
        return r.json()


async def get_cartridge(cartridge_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/cartridge/{cartridge_id}")
        r.raise_for_status()
        return r.json()


# ===================== Клавиатуры =====================
def make_pagination_kb(items: list[dict], page: int, total: int, prefix: str):
    kb = []
    for item in items:
        kb.append([InlineKeyboardButton(text=item["name"], callback_data=f"{prefix}_select_{item['id']}")])

    nav = []
    if page > 1:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}_page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page}/{(total + PAGE_SIZE - 1)//PAGE_SIZE}", callback_data="ignore"))
    if page * PAGE_SIZE < total:
        nav.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"{prefix}_page_{page+1}"))
    if nav:
        kb.append(nav)

    kb.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


# ===================== Вывод результата =====================
async def show_printer(message_or_call, data: dict):
    text = f"<b>Принтер:</b> {data['name']}\n\n<b>Совместимые картриджи:</b>\n{', '.join(data['cartridges']) or '—'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Новый поиск", callback_data="back_to_main")
    ]])
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message_or_call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


async def show_cartridge(message_or_call, data: dict):
    text = f"<b>Картридж:</b> {data['name']}\n\n<b>Подходит к принтерам:</b>\n{', '.join(data['printers']) or '—'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Новый поиск", callback_data="back_to_main")
    ]])
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message_or_call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


# ===================== Основные хендлеры =====================
@router.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "👋 Привет! Я бот-помощник для поиска совместимых картриджей и принтеров.\n\n"
    )
    
    menu_msg = await message.answer(
        "Выберите вариант поиска:",
        reply_markup=main_keyboard
    )
    
    await state.update_data(menu_message=menu_msg.message_id)


@router.callback_query(F.data == "menu_printer_to_cartridges")
async def menu_printer(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_printer_name)
    data = await state.get_data()
    menu_msg_id = data.get("menu_message")
    
    if menu_msg_id:
        await call.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=menu_msg_id,
            text="Введите название принтера (можно частично):",
            reply_markup=None
        )
    await call.answer()


@router.callback_query(F.data == "menu_cartridge_to_printers")
async def menu_cartridge(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(SearchStates.waiting_for_cartridge_name)
    data = await state.get_data()
    menu_msg_id = data.get("menu_message")
    
    if menu_msg_id:
        await call.bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=menu_msg_id,
            text="Введите название картриджа (можно частично):",
            reply_markup=None
        )
    await call.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except:
        pass

    data = await state.get_data()
    menu_msg_id = data.get("menu_message")
    
    if not menu_msg_id:
        new_menu = await call.message.answer("Выберите вариант поиска:", reply_markup=main_keyboard)
        await state.update_data(menu_message=new_menu.message_id)
    else:
        try:
            await call.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=menu_msg_id,
                text="Выберите вариант поиска:",
                reply_markup=main_keyboard
            )
        except Exception as e:
            new_menu = await call.message.answer("Выберите вариант поиска:", reply_markup=main_keyboard)
            await state.update_data(menu_message=new_menu.message_id)
    
    await call.answer()


@router.callback_query(F.data == "ignore")
async def ignore(call: types.CallbackQuery):
    await call.answer()


# ===================== Поиск =====================
@router.message(SearchStates.waiting_for_printer_name)
async def printer_search(message: types.Message, state: FSMContext):
    q = message.text.strip()
    if len(q) < 2:
        await message.answer("⚠️ Минимум 2 символа")
        return

    data = await search_printers(q)
    if not data:
        await message.answer("❌ Принтеры не найдены")
        await state.clear()
        return

    if len(data) == 1:
        await show_printer(message, data[0])
    else:
        kb = make_pagination_kb(data, 1, len(data), "printer")
        await message.answer(f"🔍 Найдено принтеров: {len(data)}\nВыберите нужный:", reply_markup=kb)
    await state.clear()


@router.message(SearchStates.waiting_for_cartridge_name)
async def cartridge_search(message: types.Message, state: FSMContext):
    q = message.text.strip()
    if len(q) < 2:
        await message.answer("⚠️ Минимум 2 символа")
        return

    data = await search_cartridges(q)
    if not data:
        await message.answer("❌ Картриджи не найдены")
        await state.clear()
        return

    if len(data) == 1:
        await show_cartridge(message, data[0])
    else:
        kb = make_pagination_kb(data, 1, len(data), "cartridge")
        await message.answer(f"🔍 Найдено картриджей: {len(data)}\nВыберите:", reply_markup=kb)
    await state.clear()


# ===================== Выбор и пагинация =====================
@router.callback_query(F.data.regexp(r"^(printer|cartridge)_select_\d+$"))
async def select_item(call: types.CallbackQuery):
    item_id = int(call.data.split("_")[-1])
    if "printer" in call.data:
        data = await get_printer(item_id)
        await show_printer(call, data)
    else:
        data = await get_cartridge(item_id)
        await show_cartridge(call, data)
    await call.answer()