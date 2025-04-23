import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Initializes and starts the Telegram bot."""
    logger.info("Starting bot...")

    bot = Bot(token=settings.INNOSCREAM_BOT_TOKEN)

    dp = Dispatcher()
    dp.include_router(router)

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
