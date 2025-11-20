import subprocess
from datetime import datetime
from pathlib import Path

from aiogram import Bot
from app.config import settings


def _clean_db_url(url: str) -> str:
    """Убирает +asyncpg / +psycopg2, чтобы pg_dump понял URL."""
    return url.replace("+asyncpg", "").replace("+psycopg2", "")


async def create_pg_dump() -> Path:
    """Делает сжатый дамп через pg_dump (самый надёжный способ)."""
    timestamp = datetime.now().strftime("%Y-%m-%d")
    backup_path = Path("/tmp") / f"backup_{timestamp}.sql.gz"

    clean_url = _clean_db_url(settings.DATABASE_URL)

    # pg_dump сразу пишет сжатый файл — не нужно gzip вручную
    result = subprocess.run(
        [
            "pg_dump",
            "--verbose",
            "--no-owner",
            "--no-acl",
            "--format=custom",      # бинарный компактный формат
            "--compress=9",         # максимальное сжатие
            f"--file={backup_path}",  # сразу в /tmp/backup_2025-11-20.sql.gz
            clean_url,
        ],
        capture_output=True,
        text=True,   # чтобы в ошибках видеть текст
    )

    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr.strip()}")

    return backup_path


async def send_daily_backup():
    """Ежедневно делает бэкап и шлёт тебе в Telegram."""
    bot = Bot(token=settings.BOT_TOKEN)
    try:
        backup_file = await create_pg_dump()
        await bot.send_document(
            chat_id=int(settings.ADMIN_TELEGRAM_ID),   # твой ID из @userinfotip
            document=backup_file.open("rb"),
            caption=f"Автобэкап базы\n{datetime.now():%Y-%m-%d %H:%M}",
        )
        print(f"Бэкап отправлен: {backup_file.name}")
    except Exception as e:
        await bot.send_message(
            chat_id=int(settings.ADMIN_TELEGRAM_ID),
            text=f"Ошибка бэкапа:\n{e}",
        )
    finally:
        await bot.session.close()
        # Чистим временный файл
        try:
            backup_file.unlink()
        except:
            pass


# Для ручного запуска: python -m app.tasks.backup
if __name__ == "__main__":
    import asyncio
    asyncio.run(send_daily_backup())