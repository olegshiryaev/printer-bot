from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers import search
from app.admin.setup import init_admin

app = FastAPI(title="Printer Cartridge API")

@app.on_event("startup")
async def startup_event():
    await create_db_and_tables()
    init_admin(app)

app.include_router(search.router)
