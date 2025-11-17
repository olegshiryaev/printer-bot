import asyncio
import threading
from fastapi import FastAPI
import uvicorn
from app.main import app as fastapi_app
from bot.main import main as run_bot

def run_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)

def run_bot_app():
    asyncio.run(run_bot())

if __name__ == "__main__":
    # Запуск FastAPI в отдельном потоке
    api_thread = threading.Thread(target=run_fastapi, daemon=True)
    api_thread.start()
    
    # Запуск бота в основном потоке
    run_bot_app()