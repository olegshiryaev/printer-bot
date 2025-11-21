from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import FastAPI, Request, Depends
from starlette.responses import RedirectResponse
from app.models import Printer, Cartridge
from app.database import engine
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

class PrinterAdmin(ModelView, model=Printer):
    # Колонки в списке
    column_list = [Printer.id, Printer.name, Printer.cartridges]
    # Поиск по имени
    column_searchable_list = [Printer.name]
    # Колонки для просмотра деталей
    column_details_list = [Printer.id, Printer.name, Printer.cartridges]
    # Поля формы
    form_columns = ["name", "cartridges"]
    page_size = 50

    # Подписи на русском
    column_labels = {
        "id": "ID",
        "name": "Название принтера",
        "cartridges": "Картриджи"
    }
    form_labels = {
        "name": "Название принтера",
        "cartridges": "Картриджи"
    }

    # Форматирование списка связей
    async def _format_cartridges(self, view, context, model, name):
        return ", ".join([c.name for c in model.cartridges])

    column_formatters = {
        "cartridges": _format_cartridges
    }


class CartridgeAdmin(ModelView, model=Cartridge):
    column_list = [Cartridge.id, Cartridge.name, Cartridge.printers]
    column_searchable_list = [Cartridge.name]
    column_details_list = [Cartridge.id, Cartridge.name, Cartridge.printers]
    form_columns = ["name", "printers"]
    page_size = 50

    column_labels = {
        "id": "ID",
        "name": "Название картриджа",
        "printers": "Принтеры"
    }
    form_labels = {
        "name": "Название картриджа",
        "printers": "Принтеры"
    }

    async def _format_printers(self, view, context, model, name):
        return ", ".join([p.name for p in model.printers])

    column_formatters = {
        "printers": _format_printers
    }


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not (username and password):
            return False

        if (username == settings.ADMIN_LOGIN and 
            pwd_context.verify(password, settings.ADMIN_PASSWORD_HASH)):
            request.session["admin_logged"] = True
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin_logged", False)


def init_admin(app: FastAPI):
    admin = Admin(
        app,
        engine,
        title="PrinterBot Admin",
        authentication_backend=AdminAuth(secret_key=settings.ADMIN_SECRET_KEY),
    )
    admin.add_view(PrinterAdmin)
    admin.add_view(CartridgeAdmin)