import logging
from datetime import date, datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from app.bot.gateways import APIGateway
from app.core.config import settings

logger = logging.getLogger(__name__)

gateway = APIGateway(settings.INNOSCREAM_API_URL, settings.HTTP_TIMEOUT)


async def pin_best_message(bot: Bot, today: date | None = None):
    """Pins the best message from the database.

    Args:
        bot: Bot instance
        today: The date for the best message search. If not provided, the
            current date will be used.
    """
    if today is None:
        today = datetime.now(timezone.utc).date()

    best_message_id = await gateway.get_best_message_id(today)
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
            await gateway.delete_user_message(best_message_id)
        else:
            logger.exception(
                "Failed to pin message %s: %s",
                best_message_id,
                e,
            )
