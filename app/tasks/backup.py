import asyncio
import gzip
from datetime import datetime
from pathlib import Path

import asyncpg
from aiogram import Bot
from app.config import settings


async def create_pg_dump() -> Path:
    """Создаёт дамп базы через asyncpg (работает в Docker/Render)."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup_path = Path("/tmp") / f"backup_{timestamp}.sql.gz"

    # Подключаемся напрямую к БД (как pg_dump, но в коде)
    conn = await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""))
    try:
        # Получаем весь дамп в виде строк
        dump = await conn.fetch("SELECT pg_dump('template1', 'postgres')")
        # Лучше — используем pg_dump через subprocess (самое надёжное)
    finally:
        await conn.close()

    # Самый надёжный способ — subprocess + pg_dump (он уже есть в Render PostgreSQL)
    import subprocess
    result = subprocess.run(
        [
            "pg_dump",
            "--no-owner",
            "--no-acl",
            "--format=custom",
            settings.DATABASE_URL.replace("+asyncpg", ""),
        ],
        capture_output=True,
        check=True,
    )
    compressed = gzip.compress(result.stdout)
    backup_path.write_bytes(compressed)
    return backup_path


async def send_daily_backup():
    """Ежедневный таск — делает бэкап и шлёт тебе в Избранное."""
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        backup_file = await create_pg_dump()
        await bot.send_document(
            chat_id=settings.ADMIN_TELEGRAM_ID,  # ← твой Telegram ID
            document=backup_file.open("rb"),
            caption=f"Автобэкап базы\n{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )
        print(f"Бэкап отправлен: {backup_file.name}")
    except Exception as e:
        await bot.send_message(settings.ADMIN_TELEGRAM_ID, f"Ошибка бэкапа: {e}")
    finally:
        await bot.session.close()
        # Удаляем временный файл
        try:
            backup_file.unlink()
        except:
            pass


if __name__ == "__main__":
    asyncio.run(send_daily_backup())