import asyncio
import uvicorn
from app.main import app as fastapi_app
from bot.main import main as bot_main


async def run_server():
    config = uvicorn.Config(
        fastapi_app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        # В продакшене можно добавить workers, но с aiogram лучше 1 процесс
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    # Запускаем FastAPI и бота параллельно в одном event loop
    await asyncio.gather(
        run_server(),
        bot_main(),
    )


if __name__ == "__main__":
    asyncio.run(main())