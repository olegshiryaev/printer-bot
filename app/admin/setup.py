from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from fastapi import FastAPI, Request, Depends
from starlette.responses import RedirectResponse
from app.models import Printer, Cartridge
from app.database import engine
from app.config import settings

class PrinterAdmin(ModelView, model=Printer):
    column_list = [Printer.id, Printer.name, Printer.cartridges]
    column_searchable_list = [Printer.name]
    column_details_list = [Printer.id, Printer.name, Printer.cartridges]
    form_columns = ["name", "cartridges"]
    page_size = 50


class CartridgeAdmin(ModelView, model=Cartridge):
    column_list = [Cartridge.id, Cartridge.name, Cartridge.printers]
    column_searchable_list = [Cartridge.name]
    column_details_list = [Cartridge.id, Cartridge.name, Cartridge.printers]
    form_columns = ["name", "printers"]
    page_size = 50


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == "admin" and password == settings.ADMIN_SECRET:
            request.session.update({"admin_logged": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        if request.session.get("admin_logged"):
            return True
        return False


def init_admin(app: FastAPI):
    admin = Admin(
        app,
        engine,
        title="PrinterBot Admin",
        authentication_backend=AdminAuth(secret_key="super-secret-key-for-session"),
    )
    admin.add_view(PrinterAdmin)
    admin.add_view(CartridgeAdmin)