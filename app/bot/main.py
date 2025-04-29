import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher

from app.bot.chart_utils import send_weekly_chart
from app.bot.handlers import channel_router, router
from app.bot.meme_publisher import generate_and_publish_meme
from app.bot.pin_most_voted import pin_best_message
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def pin_best_message_scheduler(bot: Bot):
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
            "Next pin best message run: %s. Sleeping for %s seconds...",
            target,
            sleep_seconds,
        )
        await asyncio.sleep(sleep_seconds)

        await pin_best_message(bot, target.date())
        await generate_and_publish_meme(bot, target.date())


async def weekly_chart_scheduler(bot: Bot):
    """Scheduler that sends the weekly chart every Monday at 08:00 UTC."""
    while True:
        now = datetime.now(timezone.utc)
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0 and now.hour >= 8:
            days_until_monday = 7

        next_run_date = (now + timedelta(days=days_until_monday)).date()
        target_time = datetime(
            next_run_date.year,
            next_run_date.month,
            next_run_date.day,
            8,
            0,
            0,
            tzinfo=timezone.utc,
        )

        sleep_seconds = (target_time - now).total_seconds()
        if sleep_seconds < 0:
            logger.warning(
                (
                    "Calculated sleep time is negative, "
                    "skipping this weekly chart run."
                )
            )
            await asyncio.sleep(60)
            continue

        logger.info(
            "Next weekly chart run: %s. Sleeping for %s seconds...",
            target_time,
            sleep_seconds,
        )
        await asyncio.sleep(sleep_seconds)

        await send_weekly_chart(bot)


async def main() -> None:
    """Initializes and starts the Telegram bot."""
    logger.info("Starting bot...")

    bot = Bot(token=settings.INNOSCREAM_BOT_TOKEN)

    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(channel_router)

    asyncio.create_task(pin_best_message_scheduler(bot))
    asyncio.create_task(weekly_chart_scheduler(bot))

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
