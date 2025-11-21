import base64
import json
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Dict, Any

# Надёжная сериализация callback-данных

def _encode_cb(data: Dict[str, Any]) -> str:
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode()


def _decode_cb(token: str) -> Dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        return json.loads(raw)
    except Exception:
        return {}


MAIN_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔍 По принтеру → картриджи", callback_data=_encode_cb({"a": "menu_printer"}))],
    [InlineKeyboardButton(text="🔍 По картриджу → принтеры", callback_data=_encode_cb({"a": "menu_cartridge"}))],
])


def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Главное меню", callback_data=_encode_cb({"a": "back"}))]])


def make_results_kb(items: list, action: str, page: int, total: int, q: str, per_page: int = 10):
    kb = []
    for it in items:
        kb.append([InlineKeyboardButton(text=it["name"], callback_data=_encode_cb({"a": "show", "type": action, "id": it["id"]}))])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=_encode_cb({"a": "page", "type": action, "page": page-1, "q": q})))
    total_pages = (total + per_page - 1) // per_page
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data=_encode_cb({"a": "noop"})))
    if (page + 1) * per_page < total:
        nav.append(InlineKeyboardButton(text="➡️ Далее", callback_data=_encode_cb({"a": "page", "type": action, "page": page+1, "q": q})))

    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data=_encode_cb({"a": "back"}))])
    return InlineKeyboardMarkup(inline_keyboard=kb)