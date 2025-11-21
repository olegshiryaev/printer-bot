from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.handlers.search import (
    search_printers, search_cartridges,
    get_printer, get_cartridge,
    show_printer, show_cartridge,
    pagination_kb, Search
)
from bot.keyboards import main_keyboard

router = Router(name="callbacks")


@router.callback_query(F.data == "menu_printer")
async def menu_printer(call: CallbackQuery, state: FSMContext):
    await state.set_state(Search.printer)
    await call.message.edit_text("Введите модель принтера (мин. 2 символа):")
    await call.answer()


@router.callback_query(F.data == "menu_cartridge")
async def menu_cartridge(call: CallbackQuery, state: FSMContext):
    await state.set_state(Search.cartridge)
    await call.message.edit_text("Введите модель картриджа (мин. 2 символа):")
    await call.answer()


@router.callback_query(F.data == "main_menu")
async def back_to_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Выберите действие:", reply_markup=main_keyboard)
    await call.answer()


@router.callback_query(F.data.regexp(r"^(printer|cartridge)_select_(\d+)$"))
async def select_item(call: CallbackQuery):
    prefix, item_id = call.data.split("_select_")
    item_id = int(item_id)
    func_get = get_printer if prefix == "printer" else get_cartridge
    func_show = show_printer if prefix == "printer" else show_cartridge

    data = await func_get(item_id)
    await func_show(call, data)
    await call.answer()


@router.callback_query(F.data.regexp(r"^(printer|cartridge)_pg_(\d+)$"))
async def paginate(call: CallbackQuery, state: FSMContext):
    prefix, page_str = call.data.split("_pg_")
    page = int(page_str)

    data = await state.get_data()
    q = data.get("last_query")
    if not q:
        await call.answer("Сессия устарела, начните поиск заново", show_alert=True)
        return

    search_func = search_printers if prefix == "printer" else search_cartridges
    resp = await search_func(q, page=page)

    kb = pagination_kb(resp["items"], page, resp["total"], prefix)
    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer()