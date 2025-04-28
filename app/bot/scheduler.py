import logging
import httpx
from aiogram import Bot

from app.bot.chart_utils import generate_weekly_stress_chart_url
from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_weekly_chart(bot: Bot):
    """Fetches weekly stats, generates a chart, and sends it to the admin chat."""
    logger.info("Running weekly chart job...")
    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.get(
                url=f"{settings.INNOSCREAM_API_URL}/stats/weekly",
            )
            response.raise_for_status()
            stats_data = (
                response.json()
            )  # Expects {'stats': [{'day': 'Mon', 'count': ...}, ...]}

        if (
            not stats_data
            or "stats" not in stats_data
            or not stats_data["stats"]
        ):
            logger.warning("No weekly stats data received from API.")
            # Optionally send a message indicating no data
            # await bot.send_message(settings.ADMIN_IDS[0], "No scream data from the past week.")
            return

        chart_url = generate_weekly_stress_chart_url(stats_data["stats"])

        # Send the chart URL to the first admin ID (or a dedicated channel ID)
        if settings.INNOSCREAM_CHANNEL_ID:
            target_chat_id = settings.INNOSCREAM_CHANNEL_ID
            await bot.send_message(
                chat_id=target_chat_id,
                text=f'Here is the <a href="{chart_url}">weekly stress chart</a>.',
                parse_mode="HTML",  # Use HTML for link formatting
            )
            logger.info(
                f"Successfully sent weekly chart to channel ID {target_chat_id}"
            )
        else:
            logger.warning(
                "INNOSCREAM_CHANNEL_ID not configured. Cannot send weekly chart."
            )

    except httpx.HTTPStatusError as e:
        logger.exception(f"HTTP error fetching weekly stats: {e}")
        # Optionally notify admin about the error
        if settings.ADMIN_IDS:
            await bot.send_message(
                settings.ADMIN_IDS[0], "Error generating weekly stress chart."
            )
    except Exception as e:
        logger.exception(f"Error in scheduled job send_weekly_chart: {e}")
        # Optionally notify admin about the error
        if settings.ADMIN_IDS:
            await bot.send_message(
                settings.ADMIN_IDS[0], "Error generating weekly stress chart."
            )
