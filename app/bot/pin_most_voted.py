import logging
from datetime import date, datetime, timezone

import httpx
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.core.config import settings

logger = logging.getLogger(__name__)


async def get_best_message_id(today: date | None = None) -> int | None:
    """Gets the best message ID from the database.

    Args:
        today: The date to get the best message ID for. If not provided, the
            current date will be used.

    Returns:
        The best message ID or None if no reactions are found.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    try:
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.get(
                url=f"{settings.INNOSCREAM_API_URL}/user_messages/best",
                params={"today": today},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.warning(
                "No reactions found for today %s",
                today,
            )
            return None
        logger.exception(
            "HTTP error occurred while getting best message: %s",
            e,
        )
    except Exception as e:
        logger.exception(
            "Error occurred while getting best message: %s",
            e,
        )
    return None


async def pin_best_message(bot: Bot, today: date | None = None):
    """Pins the best message from the database.

    Args:
        bot: Bot instance
        today: The date for the best message search. If not provided, the
            current date will be used.
    """
    best_message_id = await get_best_message_id(today)
    if best_message_id is None:
        logger.info("No messages to pin.")
        return

    logger.info("Pinning message %s", best_message_id)

    try:
        await bot.pin_chat_message(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            message_id=best_message_id,
            disable_notification=True,
        )
        logger.info("Pinned message %s successfully.", best_message_id)
    except TelegramBadRequest as e:
        if "MESSAGE_ID_INVALID" in str(e):
            logger.warning(
                "Message %s not found or deleted. Removing from DB.",
                best_message_id,
            )
            try:
                async with httpx.AsyncClient(
                    timeout=settings.HTTP_TIMEOUT
                ) as client:
                    response = await client.delete(
                        url=(
                            f"{settings.INNOSCREAM_API_URL}/user_messages"
                            f"/{best_message_id}"
                        )
                    )
                    response.raise_for_status()
            except Exception as e:
                logger.exception(
                    "Error occurred while deleting message %s: %s",
                    best_message_id,
                    e,
                )
        else:
            logger.exception(
                "Failed to pin message %s: %s",
                best_message_id,
                e,
            )
