import json
import logging
import urllib.parse

import httpx
from aiogram import Bot

from app.core.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://quickchart.io/chart"


async def send_weekly_chart(bot: Bot):
    """Fetches weekly stats, generates a chart,\
        and sends it to the admin chat."""
    logger.info("Running weekly chart job...")
    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.get(
                url=f"{settings.INNOSCREAM_API_URL}/stats/weekly",
            )
            response.raise_for_status()
            stats_data = (
                response.json()
            )

        if (
            not stats_data
            or "stats" not in stats_data
            or not stats_data["stats"]
        ):
            logger.warning("No weekly stats data received from API.")
            return

        chart_url = generate_weekly_stress_chart_url(stats_data["stats"])

        if settings.INNOSCREAM_CHANNEL_ID:
            target_chat_id = settings.INNOSCREAM_CHANNEL_ID
            await bot.send_message(
                chat_id=target_chat_id,
                text=f'Here is the <a href="{chart_url}">weekly stress\
chart</a>.',
                parse_mode="HTML",
            )
            logger.info(
                f"Successfully sent weekly \
chart to channel ID {target_chat_id}"
            )
        else:
            logger.warning(
                "INNOSCREAM_CHANNEL_ID not \
configured. Cannot send weekly chart."
            )

    except httpx.HTTPStatusError as e:
        logger.exception(f"HTTP error fetching weekly stats: {e}")
        if settings.ADMIN_IDS:
            await bot.send_message(
                settings.ADMIN_IDS[0], "Error generating weekly stress chart."
            )
    except Exception as e:
        logger.exception(f"Error in scheduled job send_weekly_chart: {e}")
        if settings.ADMIN_IDS:
            await bot.send_message(
                settings.ADMIN_IDS[0], "Error generating weekly stress chart."
            )


def generate_weekly_stress_chart_url(
    daily_stats: list[dict[str, str | int]],
) -> str:
    """Generates a QuickChart URL for the weekly stress bar chart.

    Args:
        daily_stats: A list of dictionaries, e.g.,
            [{'day': 'Mon', 'count': 10}, {'day': 'Tue', 'count': 5}, ...]
            Expected to contain 7 entries, one for each day Mon-Sun.

    Returns:
        The QuickChart URL string.
    """
    days_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    stats_dict = {item["day"]: item["count"] for item in daily_stats}

    labels = days_order
    data = [stats_dict.get(day, 0) for day in days_order]

    chart_config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": "Screams per Day",
                    "data": data,
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                }
            ],
        },
        "options": {
            "title": {
                "display": True,
                "text": "Weekly Stress Levels (Screams per Day)",
            },
            "scales": {
                "yAxes": [
                    {
                        "ticks": {
                            "beginAtZero": True,
                            "stepSize": 1,
                        }
                    }
                ]
            },
            "legend": {"display": False},
        },
    }

    chart_json = json.dumps(chart_config)
    encoded_chart_json = urllib.parse.quote(chart_json)

    chart_url = f"{BASE_URL}?c={encoded_chart_json}"

    logger.info(f"Generated QuickChart URL: {chart_url}")
    return chart_url


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_stats = [
        {"day": "Mon", "count": 12},
        {"day": "Tue", "count": 19},
        {"day": "Wed", "count": 3},
        {"day": "Thu", "count": 5},
        {"day": "Fri", "count": 2},
        {"day": "Sat", "count": 3},
        {"day": "Sun", "count": 8},
    ]
    url = generate_weekly_stress_chart_url(example_stats)
    print(f"Example Chart URL: {url}")

    example_stats_missing = [
        {"day": "Mon", "count": 12},
        {"day": "Wed", "count": 3},
        {"day": "Fri", "count": 2},
    ]
    url_missing = generate_weekly_stress_chart_url(example_stats_missing)
    print(f"Example Chart URL (missing data): {url_missing}")
