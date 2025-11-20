from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from app.database import create_db_and_tables
from app.routers import search
from app.admin.setup import init_admin

app = FastAPI(title="Printer Cartridge API")

@app.get("/health")
async def health_check():
    try:
        from app.database import get_session
        async with get_session() as session:
            await session.execute("SELECT 1")
        return {"status": "healthy", "service": "printer-bot"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.on_event("startup")
async def startup_event():
    await create_db_and_tables()
    init_admin(app)

app.include_router(search.router)
