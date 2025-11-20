from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker, health_check_db
from app.database import create_db_and_tables
from app.routers import search
from app.admin.setup import init_admin

app = FastAPI(title="Printer Cartridge API")

@app.get("/health")
async def health_check():
    try:
        await health_check_db()
        return {"status": "healthy", "service": "printer-bot"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "unhealthy", "error": str(e)})

@app.on_event("startup")
async def startup_event():
    await create_db_and_tables()
    init_admin(app)

app.include_router(search.router)
