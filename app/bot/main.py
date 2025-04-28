import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.bot.pin_most_voted import pin_best_message
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def scheduler(bot: Bot):
    """Scheduler that pins the best message every day at 23:59."""
    while True:
        now = datetime.now()
        target = now.replace(hour=15, minute=33, second=0, microsecond=0)

        if now > target:
            target = target.replace(day=now.day + 1)

        sleep_seconds = (target - now).total_seconds()
        await asyncio.sleep(sleep_seconds)
        logger.info(f"Pinning best message in {sleep_seconds} seconds...")
        await pin_best_message(bot)


async def main() -> None:
    """Initializes and starts the Telegram bot."""
    logger.info("Starting bot...")

    bot = Bot(token=settings.INNOSCREAM_BOT_TOKEN)

    dp = Dispatcher()
    dp.include_router(router)

    asyncio.create_task(scheduler(bot))

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
