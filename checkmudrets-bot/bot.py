"""Точка входа — запуск Telegram-бота ЧекМудрец."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.db import close_db, init_db
from handlers import start, receipt, stats, advice, history, report, callbacks
from utils.config import BOT_TOKEN, validate_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Основная функция запуска бота."""
    # Проверяем конфигурацию
    validate_config()

    # Инициализируем бота и диспетчер
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(receipt.router)
    dp.include_router(stats.router)
    dp.include_router(advice.router)
    dp.include_router(history.router)
    dp.include_router(report.router)
    dp.include_router(callbacks.router)

    # Инициализируем базу данных
    await init_db()

    logger.info("Бот ЧекМудрец запущен. Нажми Ctrl+C для остановки.")

    try:
        # Запускаем polling
        await dp.start_polling(bot, allowed_updates=["message"])
    finally:
        # Graceful shutdown
        await close_db()
        await bot.session.close()
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки.")
