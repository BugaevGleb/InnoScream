import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher

from app.bot.handlers import router, channel_router
from app.core.config import settings

from app.bot.pin_most_voted import pin_best_message

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def scheduler(bot: Bot):
    """Scheduler that pins the best message every day at 23:59."""
    target = datetime.now(timezone.utc).replace(
        hour=20, minute=59, second=0, microsecond=0
    )  # time in UTC, wanting to pin at 23:59 in Moscow time
    while True:
        now = datetime.now(timezone.utc)
        if now > target:
            target = target + timedelta(days=1)

        sleep_seconds = (target - now).total_seconds()
        logger.info(
            "Target: %s. Sleeping for %s seconds...",
            target,
            sleep_seconds,
        )
        await asyncio.sleep(sleep_seconds)

        await pin_best_message(bot, target.date())


async def main() -> None:
    """Initializes and starts the Telegram bot."""
    logger.info("Starting bot...")

    bot = Bot(token=settings.INNOSCREAM_BOT_TOKEN)

    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(channel_router)

    asyncio.create_task(scheduler(bot))

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
