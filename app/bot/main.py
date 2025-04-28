import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.bot.pin_most_voted import pin_best_message
from app.bot.scheduler import send_weekly_chart
from app.core.config import settings

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


async def weekly_chart_scheduler(bot: Bot):
    """Scheduler that sends the weekly chart every Monday at 08:00 UTC."""
    while True:
        now = datetime.now(timezone.utc)
        # Calculate days until next Monday
        days_until_monday = (7 - now.weekday()) % 7
        # If it's Monday but already past 8 AM, schedule for next week
        if days_until_monday == 0 and now.hour >= 8:
            days_until_monday = 7

        # Calculate the exact datetime for next Monday 8:00 UTC
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

        # sleep_seconds = (target_time - now).total_seconds()
        sleep_seconds = 10

        # Ensure sleep time is positive (should be, but as a safeguard)
        if sleep_seconds < 0:
            # This might happen if the calculation is slightly off or clock changes
            # Skip this run and wait for the next cycle
            logger.warning(
                "Calculated sleep time is negative, skipping this weekly chart run."
            )
            await asyncio.sleep(60)  # Sleep for a minute before recalculating
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

    asyncio.create_task(scheduler(bot))
    asyncio.create_task(weekly_chart_scheduler(bot))

    logger.info("Starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
