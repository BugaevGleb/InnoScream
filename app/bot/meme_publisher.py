import logging
from datetime import date, datetime, timezone

from aiogram import Bot
from aiogram.types import BufferedInputFile

from app.bot.gateways import APIGateway
from app.bot.meme_generator import generate_meme
from app.core.config import settings

logger = logging.getLogger(__name__)

gateway = APIGateway(settings.INNOSCREAM_API_URL, settings.HTTP_TIMEOUT)

UNSPLASH_ACCESS_KEY = settings.UNSPLASH_ACCESS_KEY


async def generate_and_publish_meme(bot: Bot, today: date | None = None):
    """Generates and publishes memes from best posts."""
    try:
        if today is None:
            today = datetime.now(timezone.utc).date()

        best_message_id = await gateway.get_best_message_id(today)
        if best_message_id is None:
            logger.info("No best message id found for today %s.",
                        today)  # pragma: no mutate
            return

        message_text = await gateway.get_message_text(best_message_id)
        if message_text is None:
            logger.warning(  # pragma: no mutate
                "No message text found "
                "for message id %s.", best_message_id  # pragma: no mutate
            )
            return

        meme_buffer = generate_meme(
            message_text,
            UNSPLASH_ACCESS_KEY,
            output_filename="generated_meme.jpg",
        )
        if meme_buffer is None:
            logger.error(  # pragma: no mutate
                "Meme generation failed for "
                "message id %s.", best_message_id  # pragma: no mutate
            )  # pragma: no mutate
            return

        logger.info(
            "Meme generated in memory, "
            "now sending to channel.")  # pragma: no mutate
        meme_bytes = meme_buffer.getvalue()
        input_file = BufferedInputFile(meme_bytes, filename="meme.jpg")

        await bot.send_photo(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            photo=input_file,
            caption="Meme generated from most-voted today post",
            disable_notification=True,
        )
        logger.info(
            "Meme published successfully for "
            "message id %s.", best_message_id  # pragma: no mutate
        )
    except Exception as e:
        logger.exception(
            "Error in generate_and_publish_meme: %s", e)  # pragma: no mutate
