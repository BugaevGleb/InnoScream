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
    if today is None:  # pragma: no mutate
        today = datetime.now(timezone.utc).date()  # pragma: no mutate

    best_message_id = \
        await gateway.get_best_message_id(today)  # pragma: no mutate
    if best_message_id is None:  # pragma: no mutate
        logger.info("No messages to pin.")  # pragma: no mutate
        return

    logger.info("Pinning message %s", best_message_id)  # pragma: no mutate

    try:
        await bot.pin_chat_message(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            message_id=best_message_id,
            disable_notification=True,
        )
        logger.info("Pinned message %s successfully.",  # pragma: no mutate
                    best_message_id)    # pragma: no mutate
    except TelegramBadRequest as e:
        if "MESSAGE_ID_INVALID" in str(e):
            logger.warning(  # pragma: no mutate
                "Message %s not found or deleted. "
                "Removing from DB.",  # pragma: no mutate
                best_message_id,  # pragma: no mutate
            )
            await gateway.delete_user_message(best_message_id)
        else:
            logger.exception(  # pragma: no mutate
                "Failed to pin message %s: %s",  # pragma: no mutate
                best_message_id,  # pragma: no mutate
                e,  # pragma: no mutate
            )
