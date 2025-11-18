import logging
import sys
from pathlib import Path

# Создаём папку logs, если нет
Path("logs").mkdir(exist_ok=True)

# Настраиваем логгер
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("Логирование настроено: пишется в logs/bot.log и в консоль")