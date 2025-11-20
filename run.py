import asyncio
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings
from app.tasks.backup import send_daily_backup
from app.main import app as fastapi_app
from bot.main import main as bot_main


scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
scheduler.add_job(send_daily_backup, "cron", hour=settings.BACKUP_TIME_HOUR, minute=0)


async def run_server():
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    # Запускаем FastAPI и бота параллельно в одном event loop
    scheduler.start()
    await asyncio.gather(
        run_server(),
        bot_main(),
    )


if __name__ == "__main__":
    asyncio.run(main())